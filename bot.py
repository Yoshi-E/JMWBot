
# Work with Python 3.6
import discord
from discord.ext.commands import Bot
import readLog
import asyncio
TOKEN = ''
BOT_PREFIX = ("?", "!")

client = Bot(command_prefix=BOT_PREFIX)


#@client.command()
#async def square(number):
#    squared_value = int(number) * int(number)
#    await client.say(str(number) + " squared is " + str(squared_value))


@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    #if message.content.startswith('!help'):
    #    msg = 'Only commands are: \n !hello and !lastgame'.format(message)
    #    await client.send_message(message.channel, msg)
        
async def processGame(channel):
    
    games = readLog.readData()
    game = games[-1] #most recent game
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
                    msg="["+timestamp+"] "+"Let the game go on! Server is continuing the mission."
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

client.loop.create_task(watch_Log())
client.run(TOKEN)