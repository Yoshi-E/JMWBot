
# Work with Python 3.6
import discord
from discord.ext import commands
import readLog
import asyncio
import config
from collections import Counter

TOKEN = config.discord_token
BOT_PREFIX = ("?", "!")

client = commands.Bot(command_prefix=BOT_PREFIX)


@client.command()
async def square(number):
    squared_value = int(number) * int(number)
    await client.say(str(number) + " squared is " + str(squared_value))



@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    if message.content.startswith('!ping'):
        
        msg = 'Pong!'
        await client.send_message(message.channel, msg)
    
    if message.content.startswith('!lastgame'):
        if(" " in message.content):
            val = message.content.split(" ")[1]
            if(val.isdigit()):
                val = int(val)
            else:
                val = 1
        else:
            val = 1
        if "admin" in [y.name.lower() for y in message.author.roles]:
            await processGame(message.channel, True, val)
        else:
            await processGame(message.channel, False, val)
        
async def processGame(channel, admin=False, gameindex=1):
    games = readLog.readData(admin, gameindex)   
    if(gameindex <= len(games) and gameindex >=0):
        game = games[gameindex] #most recent game (0 = current, 1 last finished....)
        
        
        timestamp = game["date"]+" "+game["time"]
        msg="Sorry, I could not find any games"
        if(game["gameduration"]<30):
            if(game["gameduration"]<10):
                game["gameduration"] = 10
            if(game["lastwinner"] == "WEST"):
                loser = "EAST"
            else:
                loser = "WEST"
            msg="["+timestamp+"] "+"A "+str(game["gameduration"])+"min game was just finished because "+loser+" lost their HQ."
            await client.send_message(channel, msg)
        else:
            msg="["+timestamp+"] Congratulation, "+game["lastwinner"]+"! You beat the other team after "+str(game["gameduration"])+"min of intense fighting. A new game is about to start, time to join!"
            filename = game["filename"]
            log_graph = filename
            await client.send_file(channel, log_graph, content=msg)
        if(admin == True): #post additional info
            com_east = "EAST_com:"+str(Counter(readLog.featchValues(game["data"], "commander_east")))
            com_west = "WEST_com:"+str(Counter(readLog.featchValues(game["data"], "commander_west")))
            await client.send_message(channel, com_east)
            await client.send_message(channel, com_west)
    else:
        await client.send_message(channel, "Index to big. Not enoguh games found: has to be >0 and <"+str(len(games)))

            
#this will be used for watching for a game end     
async def watch_Log():
    await client.wait_until_ready()
    channel = client.get_channel('503285457019207690')
    current_log = readLog.getLogs()[-1]
    print("current log: "+current_log)
    file = open(readLog.log_path+current_log, "r")
    file.seek(0, 2)
    while not client.is_closed:
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
                    await processGame(channel)
                if("CTI_Mission_Performance: Starting Server" in line):
                    msg="Let the game go on! The Server is now continuing the mission."
                    await client.send_message(channel, msg)

   
#async def list_servers():
#    await client.wait_until_ready()
#    while not client.is_closed:
#        print("Current servers:")
#        for server in client.servers:
#            print(server.name)
#        await asyncio.sleep(600)        
           
@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    #client.add_command(square)   

client.loop.create_task(watch_Log())
client.run(TOKEN)

