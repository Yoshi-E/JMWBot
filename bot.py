import asyncio
import discord
import traceback
import os
from discord.ext import commands
import time
import builtins as __builtin__
import logging
import sys

logging.basicConfig(filename='error.log',
                    level=logging.INFO, 
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

def print(*args, **kwargs):
    if(len(args)>0):
        logging.info(args[0])
    return __builtin__.print(*args, **kwargs)

modules = ["core", "errorhandle", "jmw"] #, "rcon"
bot = commands.Bot(command_prefix="!", pm_help=True)
 
def load_modules():
    for extension in modules:
        try:
            bot.load_extension("modules."+extension+".module")
        except (discord.ClientException, ModuleNotFoundError):
            print(f'Failed to load extension {extension}.')
            traceback.print_exc()

###################################################################################################
#####                                  Initialization                                          ####
###################################################################################################     


@bot.event
async def on_ready():

    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------------')
    

@bot.event
async def on_disconnect():
    #await asyncio.sleep(60)
    print("Connection to discord API lost...")
    
    
@bot.event
async def on_error(event, args, kwargs):
    print("Discord Error at '{}' {} - {}".format(event, args, kwargs))

def main():
    load_modules()

    #checking depencies 
    if("Commandconfig" in bot.cogs.keys()):
        cfg = bot.cogs["Commandconfig"].cfg
        #bot.is_closed()
    else: 
        sys.exit("Module 'Commandconfig' not loaded, but required")
    bot.run(cfg["TOKEN"], reconnect=True)
    #while True:
    #    try:
    #        bot.loop.run_until_complete(bot.run(cfg["TOKEN"]))
    #    except Exception as e:
    #        print(e)
    #        time.sleep(5)
            
if __name__ == '__main__':
    print("Starting...")
    main() 
    #print("The bot has crashed. Attemping to restart it...")
        
            
#make bot join server:
# https://discordapp.com/oauth2/authorize?client_id=xxxxxx&scope=bot

#https://discordpy.readthedocs.io/en/rewrite/ext/commands/api.html#event-reference

