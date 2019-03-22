
# Work with Python 3.6
import asyncio
from collections import Counter
import json
import os
from modules.jmw.readLog import readLog
import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, CheckFailure

class CommandJMW:
    def __init__(self, bot):
        self.bot = bot
        self.path = os.path.dirname(os.path.realpath(__file__))
        
        
        #checking depencies 
        if("Commandconfig" in bot.cogs.keys()):
            self.cfg = bot.cogs["Commandconfig"].cfg
        else: 
            sys.exit("Module 'Commandconfig' not loaded, but required")
            
        self.readLog = readLog(self.cfg)    
        self.user_data = {}
        if(os.path.isfile(self.path+"/userdata.json")):
            self.user_data = json.load(open(self.path+"/userdata.json","r"))
    
        
        
###################################################################################################
#####                                  common functions                                        ####
###################################################################################################
         
    
    async def set_user_data(self, user_id=0, field="", data=[]):
        if(user_id != 0):
            self.user_data[user_id] = {field: data}
        #save data
        with open(self.path+"/userdata.json", 'w') as outfile:
            json.dump(self.user_data, outfile, sort_keys=True, indent=4, separators=(',', ': '))

    async def dm_users_new_game(self):
        msg = "A game just ended, now is the best time to join for a new game!"
        for user in self.user_data:
            if "nextgame" in self.user_data[user] and self.user_data[user]["nextgame"] == True:
                print("sending DM to: "+str(user))
                puser = await self.bot.get_user_info(user)
                await self.bot.send_message(puser, msg)  
                self.user_data[user]["nextgame"] = False
        await self.set_user_data() #save changes
            
    def hasPermission(self, author, lvl=1):
        roles = self.cfg['Roles']
        if(roles['Default'] >= lvl):
            return True
            
        if hasattr(author, 'roles'):
            for role in roles:
                if (roles[role] >= lvl and role.lower() in [y.name.lower() for y in author.roles]):
                    return True
        return False

    async def processGame(self, channel, admin=False, gameindex=1, sendraw=False):
        if(gameindex>=0 and gameindex <= 10):
            game = self.readLog.readData(admin, gameindex)   
            if(game == None):
                await self.bot.send_message(channel, "No Data found, wrong log path? '"+self.cfg['logs_path']+"'")
                return None
            timestamp = game["date"]+" "+game["time"]
            msg="Sorry, I could not find any games"
            if(admin == True): #post additional info
                if(game["gameduration"] < 2):
                    gameindex+=1
                    await self.bot.send_message(channel, "Selected game is too short, displaying lastgame="+gameindex+" instead")
                    game = self.readLog.readData(admin, gameindex)  
                filename = game["picname"]
                if(sendraw == True):
                    filename = game["dataname"]
                log_graph = filename
                msg="["+timestamp+"] "+str(game["gameduration"])+"min game. Winner:"+game["lastwinner"]
                await self.bot.send_file(channel, log_graph, content=msg)
                com_east = "EAST_com:"+str(Counter(self.readLog.featchValues(game["data"], "commander_east")))
                com_west = "WEST_com:"+str(Counter(self.readLog.featchValues(game["data"], "commander_west")))
                await self.bot.send_message(channel, com_east)
                await self.bot.send_message(channel, com_west)
            else: #normal dislay
                if(game["gameduration"]<30):
                    if(game["gameduration"]<10):
                        game["gameduration"] = 10
                    if(game["lastwinner"] == "WEST"):
                        loser = "EAST"
                    else:
                        loser = "WEST"
                    msg="["+timestamp+"] "+"A "+str(game["gameduration"])+"min game was just finished because "+loser+" lost their HQ."
                    await self.bot.send_message(channel, msg)
                else:
                    msg="["+timestamp+"] Congratulation, "+game["lastwinner"]+"! You beat the other team after "+str(game["gameduration"])+"min of intense fighting. A new game is about to start, time to join!"
                    filename = game["picname"]
                    log_graph = filename
                    await self.bot.send_file(channel, log_graph, content=msg)

        else:
            await self.bot.send_message(channel, "Invalid Index. has to be >0 and <10")

                
    #this will be used for watching for a game end     
    async def watch_Log(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(self.cfg["Channel_post_status"])
        while(True):
            logs = self.readLog.getLogs()
            if(len(logs) > 0):
                current_log = logs[-1]
                print("current log: "+current_log)
                file = open(self.cfg["logs_path"]+current_log, "r")
                file.seek(0, 2)
                waitfor_newsession = False
                while not self.bot.is_closed:
                    where = file.tell()
                    try:
                        line = file.readline()
                    except:
                        line = "Error"
                    if not line:
                        await asyncio.sleep(10)
                        file.seek(where)
                        if(current_log != self.readLog.getLogs()[-1]):
                            current_log = self.readLog.getLogs()[-1] #update to new recent log
                            file = open(self.cfg["logs_path"]+current_log, "r")
                            print("current log: "+current_log)
                    else:
                        #newline found
                        if(line.find("BattlEye") ==-1):
                            if(waitfor_newsession == False and "CTI_Mission_Performance: GameOver" in line):
                                await self.dm_users_new_game()
                                await self.processGame(channel)
                                self.readLog.readData(True, 1) #Generate advaced data as well, for later use.
                                waitfor_newsession = True
                            if("CTI_Mission_Performance: Starting Server" in line):
                                msg="Let the game go on! The Server is now continuing the mission."
                                await self.bot.send_message(channel, msg)
                                waitfor_newsession = False
            else:
                await asyncio.sleep(10*60)


    ###################################################################################################
    #####                                   Bot commands                                           ####
    ###################################################################################################

    #await bot.send_message(message.channel, msg)

    @commands.command(  name='ping',
                        pass_context=True)
    async def command_ping(self, *args):
        msg = 'Pong!'
        await self.bot.say(msg)
          
    @commands.command(  name='nextgame',
                        brief="TODO",
                        description="TODO",
                        pass_context=True)
    async def command_nextgame(self, ctx):
        message = ctx.message
         #get user ID
        if hasattr(message, 'author'):
            tauthor = message.author.id
        else:
            tauthor = message.channel.user.id
        if(" " in message.content):
            val = message.content.split(" ")[1]
            if(val=="stop"):
                await self.set_user_data(tauthor, "nextgame" , False)
                msg = ':x: Ok, I will send no message'
            else:
                msg = ':question: Sorry, I did not understand'
        else:
            #store data, to remind user later on
            await self.set_user_data(tauthor, "nextgame" , True)
            msg = ':white_check_mark: Ok, I will send you a message when you can join for a new round.'
        puser = await self.bot.get_user_info(tauthor)
        await self.bot.send_message(puser, msg)  

        
    @commands.command(  name='lastgame',
                        brief="TODO",
                        description="TODO",
                        pass_context=True)
    async def command_lastgame(self, ctx):
        message = ctx.message
        if(" " in message.content):
            val = message.content.split(" ")[1]
            if(val.isdigit()):
                val = int(val)
            else:
                val = 1
        else:
            val = 1
        if self.hasPermission(message.author, lvl=10):
            await self.processGame(message.channel, True, val)
        #else:
        #   await self.processGame(message.channel, False, val)
        
        
        
    @commands.command(  name='lastdata',
                        brief="TODO",
                        description="TODO",
                        pass_context=True)
    async def command_lastdata(self, ctx):
        message = ctx.message
        if(" " in message.content):
            val = message.content.split(" ")[1]
            if(val.isdigit()):
                val = int(val)
            else:
                val = 1
        else:
            val = 1
        if self.hasPermission(message.author, lvl=10):
            await self.processGame(message.channel, True, val, True)
        
    ###################################################################################################
    #####                                  Debug Commands                                          ####
    ###################################################################################################
       
    @commands.command(  name='trigger_nextgame',
                        brief="TODO",
                        description="TODO",
                        pass_context=True)
    async def command_trigger_nextgame(self, ctx):
        author = ctx.message.author
        if self.hasPermission(author, lvl=10):
            msg = 'triggering nextgame reminder'
            await self.bot.send_message(ctx.message.channel, msg)
            await dm_users_new_game()
            
def setup(bot):
    bot.add_cog(CommandJMW(bot))
    