
# Work with Python 3.6
import asyncio
from collections import Counter
import json
import os
import readLog
import discord
from discord.ext import commands

config_name = "config.json"
modules = ["error_handle"]
modules_commands = []

def cfg(field):
    if(field in _cfg):
        return _cfg[field]
    else:
        _cfg_default = json.load(open("config_default.json","r"))
        if(field in _cfg_default):
            _cfg.update({field: cfg_default[field]})
            with open(config_name, 'w') as outfile:
                json.dump(_cfg, outfile, indent=4, separators=(',', ': '))
            return _cfg_default[field]
        else:
            print("Error, cound not find config value for: "+str(field))
    return None
    
#Load Config
_cfg = {}
if(os.path.isfile(config_name)):
    _cfg = json.load(open(config_name,"r"))
else:
    _cfg = json.load(open("config_default.json","r"))
    with open(config_name, 'w') as outfile:
        json.dump(_cfg, outfile, indent=4, separators=(',', ': '))
        
bot = commands.Bot(command_prefix=cfg("BOT_PREFIX"))
bot.remove_command("help")

user_data = {}
if(os.path.isfile(cfg('user_path')+"userdata.json")):
    user_data = json.load(open(cfg('user_path')+"userdata.json","r"))
    

###################################################################################################
#####                                  common functions                                        ####
###################################################################################################
          
    
def set_user_data(user_id=0, field="", data=[]):
    global user_data
    if(user_id != 0):
        user_data[user_id] = {field: data}
    #save data
    with open(cfg("user_path")+"userdata.json", 'w') as outfile:
        json.dump(user_data, outfile, sort_keys=True, indent=4, separators=(',', ': '))

async def dm_users_new_game():
    global user_data
    msg = "A game just ended, now is the best time to join for a new game!"
    for user in user_data:
        if "nextgame" in user_data[user] and user_data[user]["nextgame"] == True:
            print("sending DM to: "+str(user))
            puser = await bot.get_user_info(user)
            await bot.send_message(puser, msg)  
            user_data[user]["nextgame"] = False
    await set_user_data() #save changes
        
def hasPermission(author, lvl=1):
    roles = cfg('Roles')
    if(roles['Default'] >= lvl):
        return True
        
    if hasattr(author, 'roles'):
        for role in roles:
            if (roles[role] >= lvl and role.lower() in [y.name.lower() for y in author.roles]):
                return True
    return False

async def processGame(channel, admin=False, gameindex=1, sendraw=False):
    if(gameindex>=0 and gameindex <= 10):
        game = readLog.readData(admin, gameindex)   
        timestamp = game["date"]+" "+game["time"]
        msg="Sorry, I could not find any games"
        if(admin == True): #post additional info
            filename = game["picname"]
            if(sendraw == True):
                filename = game["dataname"]
            log_graph = filename
            msg="["+timestamp+"] "+str(game["gameduration"])+"min game. Winner:"+game["lastwinner"]
            await bot.send_file(channel, log_graph, content=msg)
            com_east = "EAST_com:"+str(Counter(readLog.featchValues(game["data"], "commander_east")))
            com_west = "WEST_com:"+str(Counter(readLog.featchValues(game["data"], "commander_west")))
            await bot.send_message(channel, com_east)
            await bot.send_message(channel, com_west)
        else: #normal dislay
            if(game["gameduration"]<30):
                if(game["gameduration"]<10):
                    game["gameduration"] = 10
                if(game["lastwinner"] == "WEST"):
                    loser = "EAST"
                else:
                    loser = "WEST"
                msg="["+timestamp+"] "+"A "+str(game["gameduration"])+"min game was just finished because "+loser+" lost their HQ."
                await bot.send_message(channel, msg)
            else:
                msg="["+timestamp+"] Congratulation, "+game["lastwinner"]+"! You beat the other team after "+str(game["gameduration"])+"min of intense fighting. A new game is about to start, time to join!"
                filename = game["picname"]
                log_graph = filename
                await bot.send_file(channel, log_graph, content=msg)

    else:
        await bot.send_message(channel, "Invalid Index. has to be >0 and <10")

            
#this will be used for watching for a game end     
async def watch_Log():
    await bot.wait_until_ready()
    channel = bot.get_channel(cfg("Channel_post_status"))
    current_log = readLog.getLogs()[-1]
    print("current log: "+current_log)
    file = open(readLog.cfg("logs_path")+current_log, "r")
    file.seek(0, 2)
    while not bot.is_closed:
        where = file.tell()
        try:
            line = file.readline()
        except:
            line = "Error"
        if not line:
            await asyncio.sleep(10)
            file.seek(where)
            if(current_log != readLog.getLogs()[-1]):
                current_log = readLog.getLogs()[-1] #update to new recent log
                file = open(readLog.log_path+current_log, "r")
                print("current log: "+current_log)
        else:
            #newline found
            if(line.find("BattlEye") ==-1):
                if("CTI_Mission_Performance: GameOver" in line):
                    await dm_users_new_game()
                    await processGame(channel)
                if("CTI_Mission_Performance: Starting Server" in line):
                    msg="Let the game go on! The Server is now continuing the mission."
                    await bot.send_message(channel, msg)



###################################################################################################
#####                                   Bot commands                                           ####
###################################################################################################

#await bot.send_message(message.channel, msg)

@bot.command(name='ping')
async def command_ping(*args):
    msg = 'Pong!'
    await bot.say(msg)
      
    
@bot.command(name='help', pass_context=True)
async def command_help(ctx):
    author = ctx.message.author
    cmd =       [   ["help", "Displays this message."],
                    ["ping", "returns Pong!"],
                    ["nextgame [stop]", "Sends you a DM when a new game starts. Use 'stop' to stop the reminder"],
                ]
    
    cmdAdmin =  [   ["lastgame [index]", "Displays a datasheet for a game, where index=0 is the current game."],
                    ["lastdata [index]", "Returns the raw data for a game, where index=0 is the current game."],
                    ["trigger_nextgame", "Manually triggers game end reminder for all users that have !nextgame == true"],]
                    
                    
    embed = discord.Embed(
        color = discord.Colour.orange()
    )
    embed.set_author(name='Commands that are available to you:')

    for command in cmd:
        embed.add_field(name=command[0], value=command[1], inline=False)
    if hasPermission(author, lvl=10):
        for command in cmdAdmin:
            embed.add_field(name=command[0], value=command[1], inline=False)

    await bot.send_message(author, embed=embed)    
         
@bot.command(name='nextgame', pass_context=True)
async def command_nextgame(ctx):
    message = ctx.message
     #get user ID
    if hasattr(message, 'author'):
        tauthor = message.author.id
    else:
        tauthor = message.channel.user.id
    if(" " in message.content):
        val = message.content.split(" ")[1]
        if(val=="stop"):
            await set_user_data(tauthor, "nextgame" , False)
            msg = ':x: Ok, I will send no message'
        else:
            msg = ':question: Sorry, I did not understand'
    else:
        #store data, to remind user later on
        await set_user_data(tauthor, "nextgame" , True)
        msg = ':white_check_mark: Ok, I will send you a message when you can join for a new round.'
    puser = await bot.get_user_info(tauthor)
    await bot.send_message(puser, msg)  

    
@bot.command(name='lastgame', pass_context=True)
async def command_lastgame(ctx):
    message = ctx.message
    if(" " in message.content):
        val = message.content.split(" ")[1]
        if(val.isdigit()):
            val = int(val)
        else:
            val = 1
    else:
        val = 1
    if hasPermission(message.author, lvl=10):
        await processGame(message.channel, True, val)
    #else:
    #   await processGame(message.channel, False, val)
    
    
    
@bot.command(name='lastdata', pass_context=True)
async def command_lastdata(ctx):
    message = ctx.message
    if(" " in message.content):
        val = message.content.split(" ")[1]
        if(val.isdigit()):
            val = int(val)
        else:
            val = 1
    else:
        val = 1
    if hasPermission(message.author, lvl=10):
        await processGame(message.channel, True, val, True)
    
###################################################################################################
#####                                  Debug Commands                                          ####
###################################################################################################
   
@bot.command(name='trigger_nextgame', pass_context=True)
async def command_trigger_nextgame(ctx):
    author = ctx.message.author
    if hasPermission(author, lvl=10):
        msg = 'triggering nextgame reminder'
        await bot.send_message(ctx.message.channel, msg)
        await dm_users_new_game()
        
###################################################################################################
#####                                  Initialization                                          ####
###################################################################################################     
   
@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------------')
    #bot.add_command(square)   

    
if __name__ == '__main__':
    if(cfg('TOKEN') == "WRITE_TOKEN_HERE"):
        print("Please enter the discord bot token into the config: "+config_name)
        exit()
    else:
        for extension in modules:
            try:
                bot.load_extension(extension)
            except (discord.ClientException, ModuleNotFoundError):
                print(f'Failed to load extension {extension}.')
                traceback.print_exc()
        for extension in modules_commands:
            try:
                bot.load_extension("commands/"+extension)
            except (discord.ClientException, ModuleNotFoundError):
                print(f'Failed to load extension {extension}.')
                traceback.print_exc()
        
        bot.loop.create_task(watch_Log())
        bot.run(cfg('TOKEN'))
    
    

