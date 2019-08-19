
# Work with Python 3.6
import asyncio
from collections import Counter
import json
import os
from modules.jmw.readLog import readLog
import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, CheckFailure
import ast
import sys

new_path = os.path.dirname(os.path.realpath(__file__))+'/../core/'
if new_path not in sys.path:
    sys.path.append(new_path)
from utils import CommandChecker, sendLong


class CommandJMW(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.path = os.path.dirname(os.path.realpath(__file__))
        
        #checking depencies 
        if("Commandconfig" in bot.cogs.keys()):
            self.cfg = bot.cogs["Commandconfig"].cfg
        else: 
            sys.exit("Module 'Commandconfig' not loaded, but required")
        
        self.readLog = readLog(self.cfg)    
        self.readLog.add_Event("on_missionHeader", self.gameStart)
        self.readLog.add_Event("on_missionGameOver", self.gameEnd)
        
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
                puser = self.bot.get_user(int(user))
                await puser.send(msg)  
                self.user_data[user]["nextgame"] = False
        await self.set_user_data() #save changes
    
    async def processGame(self, channel, admin=False, gameindex=1, sendraw=False):
        try:
            game = self.readLog.readData(admin, gameindex)   
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

        except Exception as e:
            await channel.send("Unable to find game: "+str(e))

    


    async def gameEnd(self, data):
        channel = self.bot.get_channel(int(self.cfg["Channel_post_status"]))
        await self.dm_users_new_game()
        await self.processGame(channel)
        self.readLog.readData(True, 1) #Generate advaced data as well, for later use.  
        
    async def gameStart(self, data):
        channel = self.bot.get_channel(int(self.cfg["Channel_post_status"]))
        msg="Let the game go on! The Server is now continuing the mission."
        await channel.send(msg)
        
    ###################################################################################################
    #####                                   Bot commands                                           ####
    ###################################################################################################

    @commands.command(  name='ping',
                        pass_context=True)
    async def command_ping(self, *args):
        msg = 'Pong!'
        await self.bot.say(msg)
    

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
                await self.set_user_data(str(tauthor), "nextgame" , False)
                msg = ':x: Ok, I will send no message'
            else:
                msg = ':question: Sorry, I did not understand'
        else:
            #store data, to remind user later on
            await self.set_user_data(str(tauthor), "nextgame" , True)
            msg = ':white_check_mark: Ok, I will send you a message when you can join for a new round.'
        puser = self.bot.get_user(tauthor)
        await puser.send(msg)  

        
    @commands.command(  name='lastgame',
                        brief="Posts a summary of select game",
                        description="Takes up to 2 arguments, 1st: index of the game, 2nd: sending 'normal'",
                        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def command_lastgame(self, ctx, index=0):
        message = ctx.message
        admin = True
        await self.processGame(message.channel, admin, index)

    @commands.command(  name='lastdata',
                        brief="sends the slected game as raw .json",
                        description="Takes up to 2 arguments, 1st: index of the game, 2nd: sending 'normal'",
                        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def command_lastdata(self, ctx, index=0):
        message = ctx.message
        admin = True
        await self.processGame(message.channel, admin, index, True)
        
    @commands.command(name='dump',
        brief="dumps array data into a dump.json file",
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def dump(self, ctx):
        await ctx.send("Dumping {} packets to file".format(len(self.readLog.dataRows)))
        with open(self.path+"/dump.json", 'w') as outfile:
            json.dump(list(self.readLog.dataRows), outfile)      
    
    @commands.command(name='getData',
        brief="gets recent log entry (0 = first, -1 = last)",
        aliases=['getdata'],
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def getData(self, ctx, index=0):
        msg = "There are {} packets: ```{}```".format(len(self.readLog.dataRows), self.readLog.dataRows[index])
        await sendLong(ctx,msg)
                
    @commands.command(name='r',
        brief="terminates the bot",
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def setRestart(self, ctx):
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
                user=self.bot.get_user(165810842972061697)
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
    