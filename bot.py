import asyncio
import discord
import traceback
import os
from discord.ext import commands

modules = ["errorhandle", "config", "jmw"]
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

if __name__ == '__main__':
    while True:
        try:
            load_modules()
            bot.loop.create_task(bot.cogs["CommandJMW"].watch_Log())
            
            #checking depencies 
            if("Commandconfig" in bot.cogs.keys()):
                cfg = bot.cogs["Commandconfig"].cfg
            else: 
                sys.exit("Module 'Commandconfig' not loaded, but required")
            bot.run(cfg["TOKEN"])
        except Exception as e:
            bot.logout()
            print(e)
            print("The bot has crashed. Attemping to restart it...")
            
#make bot join server:
# https://discordapp.com/oauth2/authorize?client_id=xxxxxx&scope=bot

#https://discordpy.readthedocs.io/en/rewrite/ext/commands/api.html#event-reference

