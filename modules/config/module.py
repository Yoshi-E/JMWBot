import traceback
import sys
from discord.ext import commands
from discord.ext.commands import has_permissions, CheckFailure
import discord
import os
import json

class Commandconfig:
    def __init__(self, bot):
        self.bot = bot
        
        self.path = os.path.dirname(os.path.realpath(__file__))
        self.config_name = self.path+"/config.json" 
        self.config_default_name = self.path+"/config_default.json" 
        
        self.cfg = {}
        self.config_load()
        
    def config_load(self):
        if(os.path.isfile(self.config_name)):
            self.cfg = json.load(open(self.config_name,"r"))
        else:
            self.cfg = json.load(open(self.config_default_name,"r"))
            with open(self.config_name, 'w') as outfile:
                json.dump(self.cfg, outfile, indent=4, separators=(',', ': '))   
                
    def set(self, field, value):
        self.cfg[field] = value
        with open(self.config_name, 'w') as outfile:
            json.dump(self.cfg, outfile, indent=4, separators=(',', ': '))     
            
    def get(self, field):
        if(field in self.cfg):
            return self.cfg[field]
        else:
            _cfg_default = json.load(open(self.config_default_name,"r"))
            if(field in _cfg_default):
                self.cfg.update({field: _cfg_default[field]})
                with open(self.config_name, 'w') as outfile:
                    json.dump(self.cfg, outfile, indent=4, separators=(',', ': '))
                return _cfg_default[field]
            else:
                print("Error, cound not find config value for: "+str(field))
        return None

    @commands.command(  name='config_reload',
                        brief="reloads the config",
                        description="reloads the config from disk")
    @has_permissions(administrator=True)
    async def config_reload(self):
        self.config_load()
        await ctx.send("Reloaded!")
                

def setup(bot):
    bot.add_cog(Commandconfig(bot))
    
   
    
#Load Config
