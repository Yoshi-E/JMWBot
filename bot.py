
# Work with Python 3.6
import discord
from discord.ext import commands
import readLog
import asyncio
import config
from collections import Counter
from tempfile import TemporaryFile
import numpy as np
import os

TOKEN = config.discord_token
user_data_path = config.user_data_path
BOT_PREFIX = ("?", "!")

client = commands.Bot(command_prefix=BOT_PREFIX)

#load data
user_data = []
if(os.path.isfile(user_data_path)):
    user_data = np.loadtxt(user_data_path)
    
async def set_user_data(user, field, data):
    global user_data
    #check user id
    user_data[user] = {field: data}
    #save data
    np.savetxt(user_data_path+"userdata.txt", user_data)

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
    
    if message.content.startswith('!help'):
        msg="JMWBot commands that are available to you: \n"
        cmd =       [   ["help", "Displays this message."],
                        ["ping", "returns Pong!"] 
                    ]
        
        cmdAdmin =  [   ["lastgame [index]", "Displays a datasheet for a game, where index=0 is the current game."],
                        ["lastdata [index]", "Returns the raw data for a game, where index=0 is the current game."]]
        msg+="```"
        for command in cmd:
            msg+=command[0].ljust(20)+command[1]+"\n"
        if "admin" in [y.name.lower() for y in message.author.roles]:
            msg+="Admin commands: \n"
            for command in cmdAdmin:
                msg+=command[0].ljust(20)+command[1]+"\n"
        msg+="```"
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
            
    if message.content.startswith('!lastdata'):
        if(" " in message.content):
            val = message.content.split(" ")[1]
            if(val.isdigit()):
                val = int(val)
            else:
                val = 1
        else:
            val = 1
        if "admin" in [y.name.lower() for y in message.author.roles]:
            await processGame(message.channel, True, val, True)
        
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
            await client.send_file(channel, log_graph, content=msg)
            com_east = "EAST_com:"+str(Counter(readLog.featchValues(game["data"], "commander_east")))
            com_west = "WEST_com:"+str(Counter(readLog.featchValues(game["data"], "commander_west")))
            await client.send_message(channel, com_east)
            await client.send_message(channel, com_west)
        else: #normal dislay
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
                filename = game["picname"]
                log_graph = filename
                await client.send_file(channel, log_graph, content=msg)

    else:
        await client.send_message(channel, "Invalid Index. has to be >0 and <10")

            
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

