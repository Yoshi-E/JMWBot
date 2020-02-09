
# Works with Python 3.6
# Discord 1.2.2
import asyncio
from collections import Counter
from collections import deque
import concurrent.futures
import json
import os
import sys
import traceback
import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, CheckFailure
import prettytable
import geoip2.database
import datetime
import shlex, subprocess
import psutil
import traceback
import inspect
import bec_rcon

new_path = os.path.dirname(os.path.realpath(__file__))+'/../core/'
if new_path not in sys.path:
    sys.path.append(new_path)
from utils import CommandChecker, RateBucket, RateBucketLimit, sendLong, CoreConfig, Tools


class CommandRconSettings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.path = os.path.dirname(os.path.realpath(__file__))
        self.rcon_adminNotification = CoreConfig.cfg.new(self.path+"/rcon_notifications.json")
        self.server_pid = None
        asyncio.ensure_future(self.on_ready())
        
    async def on_ready(self):
        await self.bot.wait_until_ready()
        self.CommandRcon = self.bot.cogs["CommandRcon"]
        
###################################################################################################
#####                                   General functions                                      ####
###################################################################################################         
        
    async def sendPMNotification(self, id, keyword, msg):
        if(self.bot.is_closed()):
            return False
        ctx = self.bot.get_user(int(id))
        
        userEle = self.getAdminSettings(id)
        if(userEle["muted"] == True):
            return
        #online idle dnd offline
        if(userEle["sendAlways"] == True or str(ctx.message.author.status) in ["online", "idle"]):
            #msg = "\n".join(message_list)
            msg = self.CommandRcon.generateChat(10)
            if(len(msg)>0 and len(msg.strip())>0):
                await sendLong(ctx, "The Keyword '{}' was triggered: \n {}".format(keyword, msg))

    async def checkKeyWords(self, message):
        for id, value in self.rcon_adminNotification.items():
            if(value["muted"] == False):
                for keyword in value["keywords"]:
                    if(keyword.lower() in message.lower()):
                        await self.sendPMNotification(id, keyword, message)
                        break
                        
    def getAdminSettings(self, id): 
        if(str(id) not in  self.rcon_adminNotification):
             self.rcon_adminNotification[str(id)] = {}
        userEle = self.rcon_adminNotification[str(id)]

        if(not "keywords" in userEle):
            userEle["keywords"] = []
            userEle["muted"] = False
            userEle["sendAlways"] = True
        return userEle
        
###################################################################################################
#####                              Arma 3 Server start - stop                                  ####
###################################################################################################         
    def start_server(self):
        
        #subprocess.call(shlex.split(self.CommandRcon.rcon_settings["start_server"]))  
        self.server_pid = subprocess.Popen(shlex.split(self.CommandRcon.rcon_settings["start_server"]))  
        
    def stop_server(self):
        if(self.server_pid != None):
            self.server_pid.kill()
            self.server_pid = None
        else:
            return False
            
    def stop_all_server(self):
        for proc in psutil.process_iter():
            if(proc.name()==self.CommandRcon.rcon_settings["stop_server"]):
                proc.kill()
        #os.system('taskkill /f /im {}'.format(self.CommandRcon.rcon_settings["stop_server"])) 
        
    @commands.command(name='start',
            brief="Starts the arma server",
            pass_context=True)
    @commands.check(CommandChecker.checkAdmin) #disabled until properly configured
    async def start(self, ctx):
        await ctx.send("Starting Server...")  
        self.start_server()
        self.CommandRcon.autoReconnect = True
   
    @commands.command(name='stop',
            brief="Stops the arma server (If server was started with !start)",
            pass_context=True)
    @commands.check(CommandChecker.checkAdmin) #disabled until properly configured
    async def stop(self, ctx):
        self.CommandRcon.autoReconnect = False
        if(self.stop_server()==False):
            await ctx.send("Failed to stop server. You might want to try '!stop_all' to stop all arma 3 instances")
        else:
            await ctx.send("Stopped the Server.")      

    @commands.command(name='stopall',
            brief="Stop all configured arma servers",
            pass_context=True)
    @commands.check(CommandChecker.checkAdmin) #disabled until properly configured
    async def stop_all(self, ctx):
        self.CommandRcon.autoReconnect = False
        self.stop_all_server()
        await ctx.send("Stop all Servers.")  
        
###################################################################################################
#####                              Admin notification commands                                 ####
###################################################################################################  

    @commands.command(name='addKeyWord',
        brief="Add Keyword to Admin notifications (use '\_' as a space)",
        aliases=['addkeyword'],
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def addKeyWord(self, ctx, *keyword):
        keyword = " ".join(keyword)
        keyword = keyword.replace("\_", " ")
        userEle = self.getAdminSettings(ctx.message.author.id)
        userEle["keywords"].append(keyword)  
        self.rcon_adminNotification.json_save()
        await ctx.send("Added Keyword.")
    
    @commands.command(name='removeKeyWord',
        brief="Remove Keyword to Admin notifications  (use '\_' as a space)",
        aliases=['removekeyword'],
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def removeKeyWord(self, ctx, *keyword):
        keyword = " ".join(keyword)
        keyword = keyword.replace("\_", " ")
        id = ctx.message.author.id
        if(str(id) in  self.rcon_adminNotification and keyword in self.rcon_adminNotification[str(id)]["keywords"] ):
            self.rcon_adminNotification[str(id)]["keywords"].remove(keyword)
            await ctx.send("Removed Keyword.")
        else:
            await ctx.send("Keyword not found.")
        self.rcon_adminNotification.json_save()   

    @commands.command(name='listKeyWords',
        brief="Lists all your Keywords for Admin notifications",
        aliases=['listkeywords'],
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def listKeyWords(self, ctx):
        id = ctx.message.author.id
        if(str(id) in  self.rcon_adminNotification and len(self.rcon_adminNotification[str(id)]["keywords"])>0 ):
            keywords = "\n".join(self.rcon_adminNotification[str(id)]["keywords"])
            await sendLong(ctx, "```{}```".format(keywords))
        else:
            await ctx.send("You dont have any keywords.")
        self.rcon_adminNotification.json_save()  

    @commands.command(name='setNotification',
        brief="Args = [mute, unmute, online, always]",
        aliases=['setnotification'],
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def setNotification(self, ctx, status):
        args = ["mute", "unmute", "online", "always"]
        await ctx.send("mute = Will never send you a message. \n unmute = allows me to send you a message. \n online = Sending a message only when you are online or AFK. \n always = Will always send you a message.")
        if(status in args):
            userEle = self.getAdminSettings(ctx.message.author.id)
            if(status == "mute"):
                userEle["muted"] == True
            else:
                userEle["muted"] == False
            if(status == "online"):
                userEle["sendAlways"] = False
            else:
                userEle["sendAlways"] = True
            await ctx.send("Your current settings are: muted: {}, sendAlways: {}".format(userEle["muted"] , userEle["sendAlways"]))
        else:
            await ctx.send("Invalid argument. Valid arguments are: [{}]".format(", ".join(args)))

        self.rcon_adminNotification.json_save() 
        
        
###################################################################################################
#####                                    Other commands                                        ####
###################################################################################################  

    @commands.command(name='debug',
        brief="Toggles RCon debug mode",
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def cmd_debug(self, ctx, limit=20): 
        if(self.CommandRcon.arma_rcon.options['debug']==True):
            self.CommandRcon.arma_rcon.options['debug'] = False
        else:
            self.CommandRcon.arma_rcon.options['debug'] = True
        msg= "Set debug mode to:"+str(self.CommandRcon.arma_rcon.options['debug'])
        await ctx.send(msg)     


class CommandRcon(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.path = os.path.dirname(os.path.realpath(__file__))

        self.arma_chat_channels = ["Side", "Global", "Vehicle", "Direct", "Group", "Command"]
        
        self.arma_rcon = None
        self.stayDisconnected = False
        self.rcon_settings = CoreConfig.cfg.new(self.path+"/rcon_cfg.json", self.path+"/rcon_cfg.default_json")
        self.lastReconnect = deque()
        self.ipReader = geoip2.database.Reader(self.path+"/GeoLite2-Country.mmdb")
        
        asyncio.ensure_future(self.on_ready())
        
    async def on_ready(self):
        await self.bot.wait_until_ready()
        
        self.CommandRconSettings = self.bot.cogs["CommandRconSettings"]
        
        self.RateBucket = RateBucket(self.streamMsg)
        
        if("streamChat" in self.rcon_settings and self.rcon_settings["streamChat"] != None):
            self.streamChat = self.bot.get_channel(self.rcon_settings["streamChat"])
            #self.streamChat.send("TEST")
        else:
            self.streamChat = None
        await self.setupRcon()
        
        #await asyncio.sleep(5)
        #await self.process_parseCommand("04:21:52 | (Side) facon: ?players")
            
    async def setupRcon(self, serverMessage=None):
        self.stayDisconnected = True
        if(self.arma_rcon != None):
            self.arma_rcon.disconnect()
        self.arma_rcon = bec_rcon.ARC(self.rcon_settings["ip"], 
                                 self.rcon_settings["password"], 
                                 self.rcon_settings["port"], 
                                 {'timeoutSec' : self.rcon_settings["timeoutSec"]}
                                )
        
        #Add Event Handlers
        self.arma_rcon.add_Event("received_ServerMessage", self.rcon_on_msg_received)
        self.arma_rcon.add_Event("on_disconnect", self.rcon_on_disconnect)
        if(serverMessage):
            self.arma_rcon.serverMessage = serverMessage
        else:   
            #Extend the chat storage
            data = self.arma_rcon.serverMessage.copy()
            self.arma_rcon.serverMessage = deque(maxlen=500) #Default: 100
            data.reverse()
            for d in data:
                self.arma_rcon.serverMessage.append(d)
        self.stayDisconnected = False
###################################################################################################
#####                                  common functions                                        ####
###################################################################################################
    
    #converts unicode to ascii, until utf-8 is supported by rcon
    def setEncoding(self, msg):
        return bytes(msg.encode()).decode("ascii","ignore") 
    

    def escapeMarkdown(self, msg):
        #Markdown: *_`~#
        msg = msg.replace("*", "\*")
        msg = msg.replace("_", "\_")
        msg = msg.replace("`", "\`")
        msg = msg.replace("~", "\~")
        msg = msg.replace("#", "\#")
        return msg    
        
    def getPlayerFromMessage(self, message: str):
        if(":" in message):
            header, body = message.split(":", 1)
            if(self.isChannel(header)): #was written in a channel
                player_name = header.split(") ")[1]
                return player_name
        return False
        
    def isChannel(self, msg):
        for channel in self.arma_chat_channels:
            if(channel in msg):
                return True
        return False
        
    def playerTypesMessage(self, player_name):
        data = self.arma_rcon.serverMessage.copy()
        data.reverse()
        for pair in data: #checks all recent chat messages
            msg = pair[1]
            diff = datetime.datetime.now() - pair[0]
            #cancel search if chat is older than 25min
            if(diff.total_seconds() > 0 and diff.total_seconds()/60 >= 25): 
                break
            msg_player = self.getPlayerFromMessage(msg)
            if(msg_player != False and player_name == msg_player or 
               (" "+player_name+" disconnected") in msg or
               (player_name in msg and " has been kicked by BattlEye" in msg)): #if player wrote something return True
                return True
        return False
    
    async def streamMsg(self, message_list):
        msg = "\n".join(message_list)
        if(len(msg.strip())>0):
            await self.streamChat.send(msg)    
        
                    
###################################################################################################
#####                                BEC Rcon Event handler                                    ####
###################################################################################################  
    #function called when a new message is received by rcon
    def rcon_on_msg_received(self, args):
        message=self.escapeMarkdown(args[0])

        if("CommandRconIngameComs" in self.bot.cogs):
            asyncio.ensure_future(self.process_parseCommand(args[0]))
        #example: getting player name
        
        if(self.bot.is_closed()):
            return False
        if(":" in message):
            header, body = message.split(":", 1)
            if(self.isChannel(header)): #was written in a channel
                #check for admin notification keywords
                asyncio.ensure_future(self.CommandRconSettings.checkKeyWords(body))
                player_name = header.split(") ")[1]
                #print(player_name)
                #print(body)
            #else: is join or disconnect, or similaar
            
        #check if the chat is streamed or not
        if(self.streamChat != None):
            self.RateBucket.add(message)
    
    async def process_parseCommand(self, msg):
        ctx = await RconCommandEngine.parseCommand(msg)
        if(ctx == None):
            return ctx
        #Handle failed executions and errors
        if(ctx.executed==False and ctx.error==False):
            await ctx.say("{}".format(msg))
        
        if(ctx.error != False):
            if(int(ctx.user_beid) > -1):
                await ctx.say("Error '{}'".format(ctx.error))
            raise Exception("Error in: {}".format(ctx))

  
    #event supports async functions
    #function is called when rcon disconnects
    async def rcon_on_disconnect(self):
        if(self.stayDisconnected==True):
            return

        await asyncio.sleep(10)

        # cleanup old records
        try:
            while self.lastReconnect[0] < datetime.datetime.now() - datetime.timedelta(seconds=60):
                self.lastReconnect.popleft()
        except IndexError:
            pass # there are no records in the queue.
        if len(self.lastReconnect) > self.rcon_settings["max_reconnects_per_minute"]:
            print("Stopped Reconnecting - Too many reconnects!")
            if(self.streamChat):
                await self.streamChat.send(":warning: Stopped Reconnecting - Too many reconnects!\n Reconnect with '!reconnect'")
        else:
            self.lastReconnect.append(datetime.datetime.now())
            print("Reconnecting to BEC Rcon")
            await self.setupRcon(self.arma_rcon.serverMessage) #restarts form scratch (due to weird behaviour on reconnect)


    def generateChat(self, limit):
        msg = ""
        data = self.arma_rcon.serverMessage.copy()
        start = len(data)-1
        if(start > limit):
            end = start-limit
        else:
            end = 0
        i = end
        while(i<=start):
            pair = data[i]
            time = pair[0]
            msg += time.strftime("%H:%M:%S")+" | "+ pair[1]+"\n"
            i+=1
        return msg

###################################################################################################
#####                                BEC Rcon custom commands                                  ####
###################################################################################################  

    @commands.command(name='reconnect',
        brief="Reconnects to the Rcon Server",
        aliases=['reconnectrcon'],
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def reconnectrcon(self, ctx): 
        if(self.arma_rcon.disconnected==True):
            await self.setupRcon(self.arma_rcon.serverMessage)
            await ctx.send("Reconnected Rcon")   
        else:
            self.stayDisconnected = True
            self.arma_rcon.disconnect()
            await ctx.send("Disconnecting and waiting for 45s before reconnecting...")
            await asyncio.sleep(50)
            await self.setupRcon(self.arma_rcon.serverMessage)
            await ctx.send("Reconnected.")    
            self.stayDisconnected = False
            
    @commands.command(name='disconnect',
        brief="Terminates the connection to Rcon",
        aliases=['disconnectrcon'],
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def disconnectrcon(self, ctx): 
        self.stayDisconnected = True
        self.arma_rcon.disconnect()
        await ctx.send("Disconnected Rcon")
        await asyncio.sleep(self.rcon_settings["timeoutSec"])
        self.stayDisconnected = False
     
    @commands.command(name='streamChat',
        brief="Streams the arma 3 chat live into the current channel",
        aliases=['streamchat'],
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def stream(self, ctx): 
        self.streamChat = ctx
        self.rcon_settings["streamChat"] = ctx.message.channel.id
        
        await ctx.send("Streaming chat...")
    
    @commands.command(name='stopStream',
        brief="Stops the stream",
        aliases=['stopstream'],
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def streamStop(self, ctx): 
        self.streamChat = None
        self.rcon_settings["streamChat"] = None
        await ctx.send("Stream stopped")
            
    @commands.command(name='checkAFK',
        brief="Checks if a player is AFK (5min)",
        aliases=['checkafk'],
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def checkAFK(self, ctx, player_id: int): 
        players = await self.arma_rcon.getPlayersArray()
        player_name = None
        for player in players:
            if(int(player[0]) == player_id):
                player_name = player[4]
        if(player_name.endswith(" (Lobby)")): #Strip lobby from name
            player_name = player_name[:-8]
        if(player_name == None):
            await ctx.send("Player not found")
            return
        msg= "Starting AFK check for: ``"+str(player_name)+"``"
        await ctx.send(msg)  
        already_active = False
        for i in range(0, 300): #checks for 5min (10*30s)
            if(self.playerTypesMessage(player_name)):
                if(i==0):
                    already_active = True
                await ctx.send("Player responded in chat. Canceling AFK check.")  
                if(already_active == False):
                    await self.arma_rcon.sayPlayer(player_id,  "Thank you for responding in chat.")
                return
            if((i % 30) == 0):
                try:
                    for k in range(0, 3):
                        await self.arma_rcon.sayPlayer(player_id, "Type something in chat or you will be kicked for being AFK. ("+str(round(i/30)+1)+"/10)")
                except: 
                    print("Failed to send command sayPlayer (checkAFK)")
            await asyncio.sleep(1)
        if(self.playerTypesMessage(player_name)):
            if(i==0):
                already_active = True
            await ctx.send("Player responded in chat. Canceling AFK check.")  
            if(already_active == False):
                try:
                    await self.arma_rcon.sayPlayer(player_id, "Thank you for responding in chat.")
                except:
                    print("Failed to send command sayPlayer")
            return
        else:
            await self.arma_rcon.kickPlayer(player_id, "AFK too long")
            await ctx.send("``"+str(player_name)+"`` did not respond and was kicked for being AFK") 

    @commands.command(name='status',
        brief="Current connection status",
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def status(self, ctx, limit=20): 
        msg = ""
        if(self.arma_rcon.disconnected==False):
           msg+= "Connected to: "+ self.arma_rcon.serverIP+"\n"
        else:
            msg+= "Currently not connected: "+ self.arma_rcon.serverIP+"\n"
        msg+= str(len(self.arma_rcon.serverMessage))+ " Messages collected"
        await ctx.send(msg) 
            
    @commands.command(name='getChat',
        brief="Get the last ingame chat messages",
        aliases=['getchat'],
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def getChat(self, ctx, limit=20): 
        msg = self.generateChat(limit)
        await sendLong(ctx, msg)

    @commands.command(name='players+',
        brief="Lists current players on the server",
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def playersPlus(self, ctx):
        players = await self.arma_rcon.getPlayersArray()

        limit = 100
        i = 1
        new = False
        msg  = "Players: \n"
        for player in players:
            if(i <= limit):
                id,ip,ping,guid,name = player
                #fetch country
                response = self.ipReader.country(ip.split(":")[0])
                region = str(response.country.iso_code).lower()
                if(region == "none"):
                    flag = ":question:" #symbol if no country was found
                else:
                    flag = ":flag_{}:".format(region)
                msg+= "#{} | {} {}".format(id, flag, name)+"\n"

        await sendLong(ctx, msg)
        
###################################################################################################
#####                                   BEC Rcon commands                                      ####
###################################################################################################    

    @commands.command(name='command',
        brief="Sends a custom command to the server",
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def command(self, ctx, *message): 
        message = " ".join(message)
        message = self.setEncoding(message)
        data = await self.arma_rcon.command(message)
        if(len(data) == 0):
            msg = "Executed command: ``"+str(message)+"`` and returned nothing (confirmed its execution)"
        else:
            msg = "Executed command: ``"+str(message)+"`` wich returned: "+str(data)
        await sendLong(ctx,msg)

    @commands.command(name='kickPlayer',
        brief="Kicks a player who is currently on the server",
        aliases=['kickplayer'],
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def kickPlayer(self, ctx, player_id: int, *message): 
        message = " ".join(message)
        message = self.setEncoding(message)
        await self.arma_rcon.kickPlayer(player_id, message)
            
        msg = "kicked player: "+str(player_id)
        await ctx.send(msg)

    @commands.command(name='say',
        brief="Sends a global message",
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def sayGlobal(self, ctx, *message): 
        name = ctx.message.author.name
        message = " ".join(message)
        message = self.setEncoding(message)
        await self.arma_rcon.sayGlobal(name+": "+message)
        msg = "Send: ``"+message+"``"
        await ctx.send(msg)    

    @commands.command(name='sayPlayer',
        brief="Sends a message to a specific player",
        aliases=['sayplayer', 'sayp'],
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def sayPlayer(self, ctx, player_id: int, *message): 
        message = " ".join(message)
        message = self.setEncoding(message)
        name = ctx.message.author.name
        if(len(message)<2):
            message = "Ping"
        await self.arma_rcon.sayPlayer(player_id, name+": "+message)
        msg = "Send msg: ``"+str(player_id)+"``"+message
        await ctx.send(msg)

    @commands.command(name='loadScripts',
        brief="Loads the 'scripts.txt' file without the need to restart the server",
        aliases=['loadscripts'],
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def loadScripts(self, ctx): 
        await self.arma_rcon.loadScripts()
        msg = "Loaded Scripts!"
        await ctx.send(msg)        

    @commands.command(name='loadEvents',
        aliases=['loadevents'],
        brief="Loads Events",
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def loadEvents(self, ctx): 
        await self.arma_rcon.loadEvents()
        msg = "Loaded Events!"
        await ctx.send(msg)    

    @commands.command(name='maxPing',
        brief="Changes the MaxPing value. If a player has a higher ping, he will be kicked from the server",
        aliases=['maxping'],
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def maxPing(self, ctx, ping: int): 
        await self.arma_rcon.maxPing(ping)
        msg = "Set maxPing to: "+ping
        await ctx.send(msg)       

    @commands.command(name='changePassword',
        brief="Changes the RCon password",
        aliases=['changepassword'],
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def changePassword(self, ctx, *password): 
        password = " ".join(password)
        await self.arma_rcon.changePassword(password)
        msg = "Set Password to: ``"+password+"``"
        await ctx.send(msg)        

    @commands.command(name='loadBans',
        brief="(Re)load the BE ban list from bans.txt",
        aliases=['loadbans'],
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def loadBans(self, ctx): 
        await self.arma_rcon.loadBans()
        msg = "Loaded Bans!"
        await ctx.send(msg)    

    @commands.command(name='players',
        brief="Lists current players on the server",
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def players(self, ctx):
        players = await self.arma_rcon.getPlayersArray()
        msgtable = prettytable.PrettyTable()
        msgtable.field_names = ["ID", "Name", "IP", "GUID"]
        msgtable.align["ID"] = "r"
        msgtable.align["Name"] = "l"
        msgtable.align["IP"] = "l"
        msgtable.align["GUID"] = "l"

        limit = 100
        i = 1
        new = False
        msg  = ""
        for player in players:
            if(i <= limit):
                msgtable.add_row([player[0], player[4], player[1],player[3]])
                if(len(str(msgtable)) < 1800):
                    i += 1
                    new = False
                else:
                    msg += "```"
                    msg += str(msgtable)
                    msg += "```"
                    await ctx.send(msg)
                    msgtable.clear_rows()
                    msg = ""
                    new = True
        if(new==False):
            msg += "```"
            msg += str(msgtable)
            msg += "```"
            await ctx.send(msg)    

    @commands.command(name='admins',
        brief="Lists current admins on the server",
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def admins(self, ctx):
        admins = await self.arma_rcon.getAdminsArray()
        msgtable = prettytable.PrettyTable()
        msgtable.field_names = ["ID", "IP"]
        msgtable.align["ID"] = "r"
        msgtable.align["IP"] = "l"

        limit = 100
        i = 1
        new = False
        msg  = ""
        for admin in admins:
            if(i <= limit):
                msgtable.add_row([admin[0], admin[1]])
                if(len(str(msgtable)) < 1800):
                    i += 1
                    new = False
                else:
                    msg += "```"
                    msg += str(msgtable)
                    msg += "```"
                    await ctx.send(msg)
                    msgtable.clear_rows()
                    msg = ""
                    new = True
        if(new==False):
            msg += "```"
            msg += str(msgtable)
            msg += "```"
            await ctx.send(msg)  
            
    @commands.command(name='getMissions',
        brief="Gets a list of all Missions",
        aliases=['getmissions'],
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def getMissions(self, ctx):
        missions = await self.arma_rcon.getMissions()
        await sendLong(ctx, missions)
        
    @commands.command(name='loadMission',
        brief="Loads a mission",
        aliases=['loadmission'],
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def loadMission(self, ctx, mission: str):
        if(mission.endswith(".pbo",-4)): #Strips PBO
            mission = mission[:-4]
        await self.arma_rcon.loadMission(mission)
        msg = "Loaded mission: ``"+str(missions)+"``"
        await ctx.send(msg)  
    
    @commands.command(name='banPlayer',
        brief="Ban a player's BE GUID from the server. If time is not specified or 0, the ban will be permanent.",
        aliases=['banplayer'],
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def banPlayer(self, ctx, player_id, time=0, *message): 
        message = " ".join(message)
        message = self.setEncoding(message)
        if(len(message)<2):
            await self.arma_rcon.banPlayer(player=player_id, time=time)
        else:
            await self.arma_rcon.banPlayer(player, message, time)
            
        msg = "Banned player: ``"+str(player)+" - "+matches[0]+"`` with reason: "+message
        await ctx.send(msg)    
        
    @commands.command(name='addBan',
        brief="Ban a player with GUID (even if they are offline)",
        aliases=['addban'],
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def addBan(self, ctx, GUID: str, time=0, *message): 
        message = " ".join(message)
        message = self.setEncoding(message)
        player = player_id
        matches = ["?"]
        if(len(GUID) != 32):
            raise Exception("Invalid GUID")
        if(len(message)<2):
            await self.arma_rcon.addBan(player=player, time=time)
        else:
            await self.arma_rcon.addBan(player, message, time)
            
        msg = "Banned player: ``"+str(player)+" - "+matches[0]+"`` with reason: "+message
        await ctx.send(msg)   

    @commands.command(name='removeBan',
        brief="Removes a ban",
        aliases=['removeban'],
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def removeBan(self, ctx, banID: int): 
        await self.arma_rcon.removeBan(banID)
            
        msg = "Removed ban: ``"+str(banID)+"``"
        await ctx.send(msg)    
        
    @commands.command(name='getBans',
        brief="Removes a ban",
        aliases=['getbans'],
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def getBans(self, ctx): 
        bans = await self.arma_rcon.getBansArray()
        bans.reverse() #news bans first
        msgtable = prettytable.PrettyTable()
        msgtable.field_names = ["ID", "GUID", "Time", "Reason"]
        msgtable.align["ID"] = "r"
        msgtable.align["Name"] = "l"
        msgtable.align["IP"] = "l"
        msgtable.align["GUID"] = "l"

        limit = 20
        i = 1
        new = False
        msg  = ""
        for ban in bans:
            if(i <= limit):
                if(len(str(msgtable)) < 1700):
                    msgtable.add_row([ban[0], ban[1], ban[2],ban[3]])
                    i += 1
                    new = False
                else:
                    msg += "```"
                    msg += str(msgtable)
                    msg += "```"
                    await ctx.send(msg)
                    msgtable.clear_rows()
                    msg = ""
                    new = True
        if(new==False):
            msg += "```"
            msg += str(msgtable)
            msg += "```"
            await ctx.send(msg)   
        if(i>=limit):
            msg = "Limit of "+str(limit)+" reached. There are still "+str(len(bans)-i)+" more bans"
            await ctx.send(msg)   
            
    @commands.command(name='getBEServerVersion',
        brief="Gets the current version of the BE server",
        aliases=['beversion', 'BEversion', 'BEVersion'],
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def getBEServerVersion(self, ctx): 
        version = await self.arma_rcon.getBEServerVersion()
        msg = "BE version: ``"+str(version)+"``"
        await ctx.send(msg)         
        
    @commands.command(name='lock',
        brief="Locks the server. No one will be able to join",
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def lock(self, ctx): 
        data = await self.arma_rcon.lock()
        msg = "Locked the Server"
        await ctx.send(msg)    

    @commands.command(name='unlock',
        brief="Unlocks the Server",
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def unlock(self, ctx): 
        data = await self.arma_rcon.unlock()
        msg = "Unlocked the Server"
        await ctx.send(msg)       

    @commands.command(name='shutdown',
        brief="Shutdowns the Server",
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def shutdown(self, ctx): 
        data = await self.arma_rcon.shutdown()
        msg = "Shutdown the Server"
        await ctx.send(msg)           

    @commands.command(name='restart',
        brief="Restart mission with current player slot selection",
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def restart(self, ctx): 
        data = await self.arma_rcon.restart()
        msg = "Restarting the Mission"
        await ctx.send(msg)          

    @commands.command(name='restartServer',
        brief="Shuts down and restarts the server immediately",
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def restartServer(self, ctx): 
        data = await self.arma_rcon.restartServer()
        msg = "Restarting the Server"
        await ctx.send(msg)           

    @commands.command(name='restartM',
        brief="Shuts down and restarts the server after mission ends",
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def restartserveraftermission(self, ctx): 
        data = await self.arma_rcon.restartserveraftermission()
        msg = "Restarting the Server after mission ends"
        await ctx.send(msg)       

    @commands.command(name='shutdownM',
        brief="Shuts down the server after mission ends",
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def shutdownserveraftermission(self, ctx): 
        data = await self.arma_rcon.shutdownserveraftermission()
        msg = "Restarting the Server after mission ends"
        await ctx.send(msg)       

    @commands.command(name='reassign',
        brief="Shuts down the server after mission ends",
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def reassign(self, ctx): 
        data = await self.arma_rcon.reassign()
        msg = "Restart the mission with new player slot selection"
        await ctx.send(msg)          

    @commands.command(name='monitords',
        brief="Shows performance information in the dedicated server console. Interval 0 means to stop monitoring.",
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def monitords(self, ctx, interval: int): 
        data = await self.arma_rcon.monitords(interval)
        msg = "Restart the mission with new player slot selection"
        await ctx.send(msg)        

    @commands.command(name='goVote',
        brief="Users can vote for the mission selection.",
        aliases=['govote'],
        pass_context=True)
    @commands.check(CommandChecker.checkAdmin)
    async def goVote(self, ctx): 
        data = await self.arma_rcon.goVote()
        msg = "Restart the mission with new player slot selection"
        await ctx.send(msg)       


class CommandRconTaskScheduler(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.path = os.path.dirname(os.path.realpath(__file__))
        
        #self.rcon_adminNotification = CoreConfig.cfg.new(self.path+"/rcon_scheduler.json")
    
        asyncio.ensure_future(self.on_ready())
        
    async def on_ready(self):
        await self.bot.wait_until_ready()
        self.CommandRcon = self.bot.cogs["CommandRcon"]


class RconCommandEngine(object):

    #context object for players
    class context(object):
        def __init__(self):
            RconCommandEngine.logging = True
        
            self.base_msg = None
            self.func_name = None
            self.parameters = None
            self.args = None
            self.rctx = None
            self.error = False
            self.executed = False
            self.user = None
            self.command = None
            self.channel = None
            self.base_msg = None
            self.user_beid = -1
        
        async def say(self, msg):
            if(int(self.user_beid) > 0):
                if(RconCommandEngine.logging==True):
                    print(msg)
                await RconCommandEngine.cogs.CommandRcon.arma_rcon.sayPlayer(self.user_beid, msg)
            else:
                self.error = "Invalid BEID"
                raise Exception(self.error)
    
        def __repr__(self):
            return "RconContext<[{}], {}>".format(self.user_beid, self.base_msg)
            
        def __str__(self):
            return "{} [beid: {}, executed: {}, error: {}]".format(self.base_msg, self.user_beid, self.executed, self.error)
    
    logging = True
    commands = []
    channels = ["Side", "Global", "Vehicle", "Direct", "Group", "Command"]
    command_prefix = "?"
    cogs = None
    users = {}
    rate_limit_commands = []
    rate_limit = 900 #15min
    admins = []
    
    
    def log(self, msg):
        if(RconCommandEngine.logging==True):
            now = datetime.datetime.now()
            print(now.strftime("%m/%d/%Y, %H:%M:%S"), ctx)    
            
    @staticmethod
    async def getPlayerBEID(player: str):
        #get updated player list, only if player not found
        #if(not player in Tools.column(self.playerList,4)):   
        playerList = await RconCommandEngine.cogs.CommandRcon.arma_rcon.getPlayersArray()
        for id, ip, ping, guid, name  in playerList:
            if(name.endswith(" (Lobby)")): #Strip lobby from name
                name = name[:-8]
            if(player == name):
                return id
        raise LookupError("Player '{}' not found".format(player))
        
    @staticmethod
    def isChannel(msg):
        for channel in RconCommandEngine.channels:
            if(channel in msg):
                return channel
        return False
    
    @staticmethod
    async def parseCommand(message: str):
        try:
            if(": " in message):
                header, body = message.split(": ", 1)
                channel = RconCommandEngine.isChannel(header)
                if(channel): #was written in a channel
                    ctx = RconCommandEngine.context()
                    ctx.base_msg = message
                    ctx.user = header.split(") ")[1]
                    
                    ctx.args = body.split(" ")
                    ctx.command = ctx.args[0]
                    ctx.args = ctx.args[1:]
                    
                    ctx.channel = channel
                    if(len(ctx.command) > 0 and RconCommandEngine.command_prefix==ctx.command[0]):
                        ctx.command = ctx.command[1:]
                        return await RconCommandEngine.processCommand(ctx)
        except Exception as e:
            self.log(traceback.format_exc())
            self.log(e)
                        
    async def processCommand(ctx):
        ctx.user_beid = await RconCommandEngine.getPlayerBEID(ctx.user)
        for func_name, func, parameters in RconCommandEngine.commands:
            ctx.func_name = func_name 
            ctx.parameters = parameters 
            try:
                if(func_name==ctx.command):
                    self.log(ctx)
                    if( ctx.user  not in RconCommandEngine.admins):
                        #Create Rate limit
                        if( ctx.user  not in RconCommandEngine.users):
                            RconCommandEngine.users[ctx.user] = RateBucketLimit(True, RconCommandEngine.rate_limit)
                        if(func_name in RconCommandEngine.rate_limit_commands):
                            check_data = RconCommandEngine.users[ctx.user].check(func_name)
                            if(check_data != True):
                                ctx.executed = False
                                await ctx.say("Error: '{}'".format(check_data))
                                return ctx
                    
                    if(len(parameters) > 0):
                        await func(ctx, *ctx.args)
                    else:
                        await func(ctx)
                    ctx.executed = True
                    return ctx
            except TypeError as e:
                ctx.error = "Invalid arguments: Given {}, expected {}".format(len(ctx.args), len(parameters)-2)
                ctx.executed = False
                self.log(traceback.format_exc())
                self.log("Error in: {}".format(ctx))
                return ctx
            except Exception as e:
                if(ctx.command == "afk"):
                    self.afkLock = False
                self.log(traceback.format_exc())
                ctx.error = "Error: '{}'".format(e)
                ctx.executed = False
                self.log("Error in: {}".format(ctx))
                return ctx
        #Command not found
        ctx.error = "Command '{}' not found".format(ctx.command)
        ctx.executed = False
        self.log(ctx)
        return ctx
            
    @staticmethod
    def command(*args, **kwargs):
        def arguments(function):
            if("name" in kwargs):
                name = kwargs["name"]
            else:
                name =  function.__name__

            if(name in Tools.column(RconCommandEngine.commands, 0)):
                raise Exception("Command '{}' already exists".format(name))
            #init
            async def wrapper(*args, **kwargs):
                return await function(RconCommandEngine.cogs, *args, **kwargs)
            t = wrapper
            RconCommandEngine.commands.append([name, t, inspect.getfullargspec(function)[0]])
            return t
        return arguments


# Registering functions, and interacting with the discord bot.
class CommandRconIngameComs(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.path = os.path.dirname(os.path.realpath(__file__))
        
        self.afkLock = False
        self.afkTime = -1
        asyncio.ensure_future(self.on_ready())
        RconCommandEngine.cogs = self
        RconCommandEngine.rate_limit_commands.append("afk")
        RconCommandEngine.admins.append("Yoshi_E")
        RconCommandEngine.admins.append("[H] Tom")
        RconCommandEngine.admins.append("zerty")
        
    async def on_ready(self):
        await self.bot.wait_until_ready()
        self.CommandRcon = self.bot.cogs["CommandRcon"]
    
        
    @RconCommandEngine.command(name="ping")  
    async def ping(self, rctx):
        await rctx.say("Pong!")    

    @RconCommandEngine.command(name="help")  
    async def ping(self, rctx):
        for func_name, func, parameters in RconCommandEngine.commands:
            if(len(parameters) > 2):
                await rctx.say("{} {}".format(func_name, parameters[2:]))   
            else:
                await rctx.say("{}".format(func_name))    
        
    @RconCommandEngine.command(name="players")  
    async def players(self, rctx):
        playerList = await self.CommandRcon.arma_rcon.getPlayersArray()
        msg = ""
        for id, ip, ping, guid, name in playerList:
            msg += "\n{} | {}".format(id, name[:22]) #.ljust(20, " ") #.rjust(3, " ")
            if(len(msg)>200):
                await rctx.say(msg)
                msg = "\n"
        if(msg != ""):
            await rctx.say(msg)    
            
    @RconCommandEngine.command(name="afk")  
    async def check_afk(self, rctx, beid):
        time_to_respond = 300 #checks for 5min (10*30s), gives a warning every 30s
        channel = rctx.channel
        user = rctx.user
        ctx_beid = rctx.user_beid
        
        
        if(self.afkLock == True):
            await rctx.say("An AFK check is already in progess, please wait {}s.".format(self.afkTime))
            return False
        self.afkLock = True
        
        players = await self.CommandRcon.arma_rcon.getPlayersArray()
        player_name = None
        for player in players:
            if(int(player[0]) == int(beid)):
                player_name = player[4]
        if(player_name!=None and player_name.endswith(" (Lobby)")): #Strip lobby from name
            player_name = player_name[:-8]
        
        if(player_name==None):
            await rctx.say("Failed to find player with that ID")
            self.afkLock = False
            return False
        msg= "Starting AFK check for: {} - {}".format(player_name, beid)
        await rctx.say(msg)
        
        already_active = False
        for i in range(0, time_to_respond): 
            self.afkTime = time_to_respond-i
            if(self.CommandRcon.playerTypesMessage(player_name)):
                if(i==0):
                    already_active = True
                    await rctx.say("Player was recently active. Canceling AFK check.")  
                else:
                    await rctx.say("Player responded in chat. Canceling AFK check.")  
                if(already_active == False):
                    await self.CommandRcon.arma_rcon.sayPlayer(beid,  "Thank you for responding in chat.")
                self.afkLock = False
                return True
            if((i % 30) == 0):
                try:
                    for k in range(0, 3):
                        await self.CommandRcon.arma_rcon.sayPlayer(beid, "Type something in chat or you will be kicked for being AFK. ("+str(round(i/30)+1)+"/10)")
                except: 
                    print("Failed to send command sayPlayer (checkAFK)")
            await asyncio.sleep(1)
        if(self.CommandRcon.playerTypesMessage(player_name)):
            if(i==0):
                already_active = True
            await rctx.say("Player responded in chat. Canceling AFK check.")  
            if(already_active == False):
                try:
                    await self.CommandRcon.arma_rcon.sayPlayer(beid, "Thank you for responding in chat.")
                except:
                    print("Failed to send command sayPlayer")
            self.afkLock = False        
            return False
        else:
            await self.CommandRcon.arma_rcon.kickPlayer(beid, "AFK too long (user_check by {})".format(user))
            await rctx.say("``{}`` did not respond and was kicked for being AFK".format(player_name))
        self.afkLock = False
            
def setup(bot):
    bot.add_cog(CommandRcon(bot))
    bot.add_cog(CommandRconTaskScheduler(bot))
    bot.add_cog(CommandRconIngameComs(bot))
    bot.add_cog(CommandRconSettings(bot))