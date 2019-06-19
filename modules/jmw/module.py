
# Work with Python 3.6
import asyncio
from collections import Counter
import json
import os
from modules.jmw.readLog import readLog
from modules.jmw import a3cfgreader
import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, CheckFailure
import ast
import sys


class CommandJMW(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.path = os.path.dirname(os.path.realpath(__file__))
        
        
        #checking depencies 
        if("Commandconfig" in bot.cogs.keys()):
            self.cfg = bot.cogs["Commandconfig"]
        else: 
            sys.exit("Module 'Commandconfig' not loaded, but required")
        
        self.cfgreader = a3cfgreader.readcfg(self.cfg.get("config_path"), self.path+"/"+"mission_cycle.cfg")
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
                await puser.send(msg)  
                self.user_data[user]["nextgame"] = False
        await self.set_user_data() #save changes
    
    def hasPermission(self, author, lvl=1):
        roles = self.cfg.get('Roles')
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
                await channel.send("No Data found, wrong log path? '"+self.cfg.get('logs_path')+"'")
                return None
            timestamp = game["date"]+" "+game["time"]
            msg="Sorry, I could not find any games"
            if(admin == True): #post additional info
                if(game["gameduration"] < 2):
                    gameindex+=1
                    await channel.send("Selected game is too short, displaying lastgame="+str(gameindex)+" instead")
                    game = self.readLog.readData(admin, gameindex)  
                filename = game["picname"]
                if(sendraw == True):
                    filename = game["dataname"]
                log_graph = filename
                msg="["+timestamp+"] "+str(game["gameduration"])+"min game. Winner:"+game["lastwinner"]
                await channel.send(file=discord.File(log_graph), content=msg)
                com_east = "EAST_com:"+str(Counter(self.readLog.featchValues(game["data"], "commander_east")))
                com_west = "WEST_com:"+str(Counter(self.readLog.featchValues(game["data"], "commander_west")))
                await channel.send(com_east)
                await channel.send(com_west)
            else: #normal dislay
                if(game["gameduration"]<30):
                    if(game["gameduration"]<10):
                        game["gameduration"] = 10
                    if(game["lastwinner"] == "WEST"):
                        loser = "EAST"
                    else:
                        loser = "WEST"
                    msg="["+timestamp+"] "+"A "+str(game["gameduration"])+"min game was just finished because "+loser+" lost their HQ."
                    await channel.send(msg)
                else:
                    msg="["+timestamp+"] Congratulation, "+game["lastwinner"]+"! You beat the other team after "+str(game["gameduration"])+"min of intense fighting. A new game is about to start, time to join!"
                    filename = game["picname"]
                    log_graph = filename
                    await channel.send(file=discord.File(log_graph), content=msg)

        else:
            await channel.send("Invalid Index. has to be >0 and <10")

                
    #this will be used for watching for a game end     
    async def watch_Log(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(self.cfg.get("Channel_post_status"))
        while(True):
            logs = self.readLog.getLogs()
            if(len(logs) > 0):
                current_log = logs[-1]
                print("current log: "+current_log)
                file = open(self.cfg.get("logs_path")+current_log, "r")
                file.seek(0, 2)
                while (True):
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
                            file = open(self.cfg.get("logs_path")+current_log, "r")
                            print("current log: "+current_log)
                    else:
                        #newline found
                        if(line.find("BattlEye") ==-1 and line.find("[") > 0 and "CTI_DataPacket" in line and line.rstrip()[-2:] == "]]"):
                            try:
                                splitat = line.find("[")
                                r = line[splitat:]  #remove timestamp
                                timestamp = line[:splitat]
                                r = r.rstrip() #remove /n
                                r = r.replace(",WEST]", ',"WEST"]')
                                r = r.replace(",EAST]", ',"EAST"]') #this still needs working
                                r = r.replace("true", "True")
                                r = r.replace("false", "False")
                                datarow = ast.literal_eval(r) #convert string into array object
                                datarow = dict(datarow)
                                if(datarow["CTI_DataPacket"] == "GameOver"):
                                    await self.dm_users_new_game()
                                    await self.processGame(channel)
                                    self.readLog.readData(True, 1) #Generate advaced data as well, for later use.
                                if(datarow["CTI_DataPacket"] == "Header"):
                                    if(self.cfg.get("cycle_assist") == True):
                                        self.cfgreader.writeMission(self.cfgreader.parseMissions(), datarow["Map"])
                                    msg="Let the game go on! The Server is now continuing the mission."
                                    await channel.send(msg)
                            except Exception as e:
                                print(line)
                                print(e)
            else:
                await asyncio.sleep(10*60)
    #TODO
    def updateConfigMap(self, Map):
        _readcfg = readcfg(self.cfg.get("config_path"), self.path+"/"+"mission_cycle.cfg")
        cycle = _readcfg.parseMissions()
    ###################################################################################################
    #####                                   Bot commands                                           ####
    ###################################################################################################

    @commands.command(  name='ping',
                        pass_context=True)
    async def command_ping(self, *args):
        msg = 'Pong!'
        await self.bot.say(msg)
    
    
    ####################################
    #Cycle Assist                      #
    ####################################
    @commands.command(  name='cycleassist',
                        brief="Enables the Cycle assist",
                        description="The cycle assist rewrites an arma 3 config in a way that after crash the correct map is loaded.",
                        pass_context=True)
    @has_permissions(administrator=True)
    async def command_cycleassist(self, ):
        if(" " in message.content):
            val = message.content.split(" ")[1]
            if(val in ["false", "off", "0", "disable"]):
                self.cfg.set("cycle_assist", False)
                msg = ':x: Ok, Mission cycle assist disabled'
            else:
                self.cfg.set("cycle_assist", True)
                msg = ':white_check_mark: Ok, Mission cycle assist enabled.'
        else:
            msg = ':question: Usage: cycleassist [true/false]'
        await ctx.send(msg)    

    @commands.command(  name='cycleassistList',
                        brief="List the current cycle",
                        description="List the default order of mission playback",
                        pass_context=True)
    @has_permissions(administrator=True)
    async def command_cycleassistList(self, ):
        msg = str(self.cfgreader.parseMissions()).replace("\\t","").replace("\\n","")
        await ctx.send(msg)    
    
    
    
    ####################################
    #Game tools                        #
    ####################################
    @commands.command(  name='nextgame',
                        brief="You'll receive a DM when a game has ended",
                        description="Send 'nextgame stop' to stop the notification",
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
        await puser.send(msg)  

        
    @commands.command(  name='lastgame',
                        brief="Posts a summary of select game",
                        description="Takes up to 2 arguments, 1st: index of the game, 2nd: sending 'normal'",
                        pass_context=True)
    async def command_lastgame(self, ctx):
        message = ctx.message
        admin = True
        if(" " in message.content):
            args = message.content.split(" ")
            val = args[1]
            if(val.isdigit()):
                val = int(val)
            else:
                val = 1
            if(len(args)>2):
                admin = False
        else:
            val = 1
        if self.hasPermission(message.author, lvl=10):
            await self.processGame(message.channel, admin, val)

        
        
        
    @commands.command(  name='lastdata',
                        brief="sends the slected game as raw .json",
                        description="Takes up to 2 arguments, 1st: index of the game, 2nd: sending 'normal'",
                        pass_context=True)
    async def command_lastdata(self, ctx):
        message = ctx.message
        admin = True
        if(" " in message.content):
            args = message.content.split(" ")
            val = args[1]
            if(val.isdigit()):
                val = int(val)
            else:
                val = 1
            if(len(args)>2):
                admin = False
        else:
            val = 1
        if self.hasPermission(message.author, lvl=10):
            await self.processGame(message.channel, admin, val, True)
    
    @commands.command(name='restart',
        brief="terminates the bot and auto restarts",
        pass_context=True)
    async def setRestart(self, ):
        if self.hasPermission(ctx.message.author, lvl=10):
            await ctx.send("Restarting...")
            sys.exit()     
    ###################################################################################################
    #####                                  Debug Commands                                          ####
    ###################################################################################################
    async def handle_exception(self, myfunction):
        coro = getattr(self, myfunction)
        for i in range (0,5):
            try:
                await coro()
            except Exception as ex:
                ex = str(ex)+"/n"+str(traceback.format_exc())
                user=await self.bot.get_user_info(165810842972061697)
                await user.send("Caught exception")
                await user.send(ex[:1800] + '..' if len(ex) > 1800 else ex)
                logging.error('Caught exception')
                await asyncio.sleep(10)  
                  

local_module = None     
def setup(bot):
    global local_module
    module = CommandJMW(bot)
    bot.loop.create_task(module.handle_exception("watch_Log"))
    bot.add_cog(module)
    