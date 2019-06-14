
# Work with Python 3.6
import asyncio
from collections import Counter
import json
import os
from modules.rcon import rcon
import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, CheckFailure
import ast
import builtins as __builtin__
import logging
import prettytable
from difflib import get_close_matches 
import textwrap

logging.basicConfig(filename='error.log',
                    level=logging.INFO, 
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

def print(*args, **kwargs):
    if(len(args)>0):
        logging.info(args[0])
    return __builtin__.print(*args, **kwargs)

class CommandRcon:
    def __init__(self, bot):
        self.bot = bot
        self.path = os.path.dirname(os.path.realpath(__file__))
        
        
        #checking depencies 
        if("Commandconfig" in bot.cogs.keys()):
            self.cfg = bot.cogs["Commandconfig"]
        else: 
            sys.exit("Module 'Commandconfig' not loaded, but required")
        
        self.rcon_settings = {}
        if(os.path.isfile(self.path+"/rcon_cfg.json")):
            self.rcon_settings = json.load(open(self.path+"/rcon_cfg.json","r"))
        else:
            self.creatcfg() #make empty cfg file
            raise Exception("Error: You have to configure the rcon_cfg first!")
        
        self.epm_rcon = rcon.ARC(self.rcon_settings["ip"], 
                                 self.rcon_settings["password"], 
                                 self.rcon_settings["port"], 
                                 {'timeoutSec' : self.rcon_settings["timeoutSec"]}
                                )


        #array = self.epm_rcon.getPlayersArray()
        #print(array)
        #rcon.sayGlobal("No humans here, just bots")
    
        
        
###################################################################################################
#####                                  common functions                                        ####
###################################################################################################
    def creatcfg(self):
        self.rcon_settings["ip"] = "000.000.000.000"
        self.rcon_settings["password"] = "<Enter Rcon Password here>"
        self.rcon_settings["port"] = 3302
        self.rcon_settings["timeoutSec"] = 1
        #save data
        with open(self.path+"/rcon_cfg.json", 'w') as outfile:
            json.dump(self.rcon_settings, outfile, sort_keys=True, indent=4, separators=(',', ': '))
            
    def hasPermission(self, author, lvl=1):
        roles = self.cfg.get('Roles')
        if(roles['Default'] >= lvl):
            return True
            
        if hasattr(author, 'roles'):
            for role in roles:
                if (roles[role] >= lvl and role.lower() in [y.name.lower() for y in author.roles]):
                    return True
        return False

    ###################################################################################################
    #####                                   Bot commands                                           ####
    ###################################################################################################   
    def isAdmin(ctx):
        admin_ids = ["165810842972061697"] #Yoshi
        return ctx.message.author.id in admin_ids

    def canUseCmds(ctx):
        aroles = ["Admin", "Developer"]
        admin_ids = ["165810842972061697"] #Yoshi
        self = local_module #fecthing cog from outside class
        if(ctx.message.author.id in admin_ids):
            return True
        msg = ctx.message.author.name+"#"+str(ctx.message.author.id)+": "+ctx.message.content
        print(msg)
        # is server: ctx.message.server==None
        for server in self.bot.servers:
            for member in server.members:
                if(member.id == ctx.message.author.id): #locate user
                    for role in member.roles:           #check if role is valid
                        if(role.name.lower() in [x.lower() for x in aroles]):
                            return True
        return False
        
        
    @commands.check(canUseCmds)   
    @commands.command(name='command',
        brief="Sends a custom command to the server",
        pass_context=True)
    async def command(self, ctx, *message): 
        message = " ".join(message)
        self.epm_rcon.command(message)
        msg = "Executed command: ``"+message+"``"
        await self.bot.send_message(ctx.message.channel, msg)    
        
    @commands.check(canUseCmds)   
    @commands.command(name='kickPlayer',
        brief="Kicks a player who is currently on the server",
        pass_context=True)
    async def kickPlayer(self, ctx, in_player, *message): 
        message = " ".join(message)
        print("kickPlayer", in_player, message)
        matches = ["?"]
        if(len(in_player) >3 and in_player.isdigit()==False):
            #find player
            players = {}
            players_list = self.epm_rcon.getPlayersArray()
            for cplayer in players_list:
                players[cplayer[4]] = cplayer[0] 
                
            matches = get_close_matches(in_player, players.keys(), cutoff = 0.5, n = 3)   
            if(len(matches) > 0):
                player = players[matches[0]]
            else:
                matches = ["?"]
                player = in_player
        else:
            player = in_player
        if(len(message)<2):
            self.epm_rcon.kickPlayer(player)
        else:
            self.epm_rcon.kickPlayer(player, message)
            
        msg = "kicked player: ``"+player+" - "+matches[0]+"``"
        await self.bot.send_message(ctx.message.channel, msg)
            
    @commands.check(canUseCmds)   
    @commands.command(name='say',
        brief="Sends a global message",
        pass_context=True)
    async def sayGlobal(self, ctx, *message): 
        name = ctx.message.author.name
        message = " ".join(message)
        self.epm_rcon.sayGlobal(name+": "+message)
        msg = "Send: ``"+message+"``"
        await self.bot.send_message(ctx.message.channel, msg)    
        
    @commands.check(canUseCmds)   
    @commands.command(name='sayPlayer',
        brief="Sends a message to a specific player",
        pass_context=True)
    async def sayPlayer(self, ctx, in_player, *message): 
        message = " ".join(message)
        name = ctx.message.author.name
        print("sayPlayer", in_player, message)
        matches = ["?"]
        if(len(in_player) >3 and in_player.isdigit()==False):
            #find player
            players = {}
            players_list = self.epm_rcon.getPlayersArray()
            for cplayer in players_list:
                players[cplayer[4]] = cplayer[0] 
                
            matches = get_close_matches(in_player, players.keys(), cutoff = 0.5, n = 3)   
            if(len(matches) > 0):
                player = players[matches[0]]
            else:
                matches = ["?"]
                player = in_player
        else:
            player = in_player
        if(len(message)<2):
            self.epm_rcon.sayPlayer(player, name+": Ping")
        else:
            self.epm_rcon.sayPlayer(player, name+": "+message)
            
        msg = "Send msg: ``"+player+" - "+matches[0]+"``"+message
        await self.bot.send_message(ctx.message.channel, msg)
    
    @commands.check(canUseCmds)   
    @commands.command(name='loadScripts',
        brief="Loads the 'scripts.txt' file without the need to restart the server",
        pass_context=True)
    async def loadScripts(self, ctx): 
        self.epm_rcon.loadScripts()
        msg = "Loaded Scripts!"
        await self.bot.send_message(ctx.message.channel, msg)    
            
            
    @commands.check(canUseCmds)   
    @commands.command(name='maxPing',
        brief="Changes the MaxPing value. If a player has a higher ping, he will be kicked from the server",
        pass_context=True)
    async def maxPing(self, ctx, ping): 
        self.epm_rcon.maxPing(ping)
        msg = "Set maxPing to: "+ping
        await self.bot.send_message(ctx.message.channel, msg)       

    @commands.check(canUseCmds)   
    @commands.command(name='changePassword',
        brief="Changes the RCon password",
        pass_context=True)
    async def changePassword(self, ctx, *password): 
        password = " ".join(password)
        self.epm_rcon.changePassword(password)
        msg = "Set Password to: "+password
        await self.bot.send_message(ctx.message.channel, msg)        
        
    @commands.check(canUseCmds)   
    @commands.command(name='loadBans',
        brief="(Re)load the BE ban list from bans.txt",
        pass_context=True)
    async def loadBans(self, ctx): 
        self.epm_rcon.loadBans()
        msg = "Loaded Bans!"
        await self.bot.send_message(ctx.message.channel, msg)    
        
    @commands.check(canUseCmds)   
    @commands.command(name='players',
        brief="lists current players on the server",
        pass_context=True)
    async def players(self, ctx):
        players = self.epm_rcon.getPlayersArray()
        msgtable = prettytable.PrettyTable()
        msgtable.field_names = ["ID", "Name", "IP"]
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
                if(len(str(msgtable)) < 1800):
                    msgtable.add_row([player[0], player[4], player[1],player[3]])
                    i += 1
                    new = False
                else:
                    msg += "```"
                    msg += str(msgtable)
                    msg += "```"
                    await self.bot.send_message(ctx.message.channel, msg)
                    msgtable.clear_rows()
                    msg = ""
                    new = True
        if(new==False):
            msg += "```"
            msg += str(msgtable)
            msg += "```"
            await self.bot.send_message(ctx.message.channel, msg)    
              
    @commands.check(canUseCmds)   
    @commands.command(name='getMissions',
        brief="Gets a list of all Missions",
        pass_context=True)
    async def getMissions(self, ctx):
        missions = self.epm_rcon.getMissions()
        while(len(missions)>0):
            if(len(missions)>1800):
                await self.bot.send_message(ctx.message.channel, missions[:1800])
                missions = missions[1800:]
            else:
                await self.bot.send_message(ctx.message.channel, missions)
                missions = ""
                
    @commands.check(canUseCmds)   
    @commands.command(name='banPlayer',
        brief="Ban a player's BE GUID from the server. If time is not specified or 0, the ban will be permanent.",
        pass_context=True)
    async def banPlayer(self, ctx, in_player, time=0, *message): 
        message = " ".join(message)
        print("banPlayer", in_player, message)
        matches = ["?"]
        if(len(in_player) >3 and in_player.isdigit()==False):
            #find player
            players = {}
            players_list = self.epm_rcon.getPlayersArray()
            for cplayer in players_list:
                players[cplayer[4]] = cplayer[0] 
                
            matches = get_close_matches(in_player, players.keys(), cutoff = 0.5, n = 3)   
            if(len(matches) > 0):
                player = players[matches[0]]
            else:
                matches = ["?"]
                player = in_player
        else:
            player = in_player
        if(len(message)<2):
            self.epm_rcon.banPlayer(player=player, time=time)
        else:
            self.epm_rcon.banPlayer(player, message, time)
            
        msg = "Banned player: ``"+player+" - "+matches[0]+"`` with reason: "+message
        await self.bot.send_message(ctx.message.channel, msg)    
        
        
    @commands.check(canUseCmds)   
    @commands.command(name='addBan',
        brief="Same as 'banPlayer', but allows to ban a player that is not currently on the server",
        pass_context=True)
    async def addBan(self, ctx, in_player, time=0, *message): 
        message = " ".join(message)
        print("addBan", in_player, message)
        matches = ["?"]
        if(len(in_player) >3 and in_player.isdigit()==False):
            #find player
            players = {}
            players_list = self.epm_rcon.getPlayersArray()
            for cplayer in players_list:
                players[cplayer[4]] = cplayer[0] 
                
            matches = get_close_matches(in_player, players.keys(), cutoff = 0.5, n = 3)   
            if(len(matches) > 0):
                player = players[matches[0]]
            else:
                matches = ["?"]
                player = in_player
        else:
            player = in_player
        if(len(message)<2):
            self.epm_rcon.addBan(player=player, time=time)
        else:
            self.epm_rcon.addBan(player, message, time)
            
        msg = "Banned player: ``"+player+" - "+matches[0]+"`` with reason: "+message
        await self.bot.send_message(ctx.message.channel, msg)   

    @commands.check(canUseCmds)   
    @commands.command(name='removeBan',
        brief="Removes a ban",
        pass_context=True)
    async def removeBan(self, ctx, banID): 
        self.epm_rcon.removeBan(banID)
            
        msg = "Removed ban: ``"+banID+"``"
        await self.bot.send_message(ctx.message.channel, msg)    
        
    @commands.check(canUseCmds)   
    @commands.command(name='getBans',
        brief="Removes a ban",
        pass_context=True)
    async def getBans(self, ctx): 
        bans = self.epm_rcon.getBansArray()
        bans.reverse() #news bans first
        msgtable = prettytable.PrettyTable()
        msgtable.field_names = ["ID", "GUID", "Time", "Reason"]
        msgtable.align["ID"] = "r"
        msgtable.align["Name"] = "l"
        msgtable.align["IP"] = "l"
        msgtable.align["GUID"] = "l"

        limit = 50
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
                    await self.bot.send_message(ctx.message.channel, msg)
                    msgtable.clear_rows()
                    msg = ""
                    new = True
        if(new==False):
            msg += "```"
            msg += str(msgtable)
            msg += "```"
            await self.bot.send_message(ctx.message.channel, msg)   
        if(i>=limit):
            msg = "Limit of "+str(limit)+" reached. There are still "+str(len(bans)-i)+" more bans"
            await self.bot.send_message(ctx.message.channel, msg)   
            
    @commands.check(canUseCmds)   
    @commands.command(name='getBEServerVersion',
        brief="Gets the current version of the BE server",
        pass_context=True)
    async def getBEServerVersion(self, ctx): 
        version = self.epm_rcon.getBEServerVersion()
        msg = "BE version: ``"+version+"``"
        await self.bot.send_message(ctx.message.channel, msg)  

    @commands.check(isAdmin)    
    @commands.command(name='restart',
        brief="terminates the bot and auto restarts",
        pass_context=True)
    async def setRestart(self, ctx):
        await self.bot.send_message(ctx.message.channel, "Restarting...")
        sys.exit()          
        
    ###################################################################################################
    #####                                  Debug Commands                                          ####
    ###################################################################################################
       
local_module = None
def setup(bot):
    global local_module
    module = CommandRcon(bot)
    local_module = module #access for @check decorators
    bot.add_cog(module)      