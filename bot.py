
# Work with Python 3.6
import discord
from discord.ext.commands import Bot
import readLog
import asyncio
TOKEN = ''
BOT_PREFIX = ("?", "!")

#client = discord.Client()
client = Bot(command_prefix=BOT_PREFIX)


@client.command()
async def square(number):
    squared_value = int(number) * int(number)
    await client.say(str(number) + " squared is " + str(squared_value))


@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    if message.content.startswith('!help'):
        msg = 'Only commands are: \n !hello and !lastgame'.format(message)
        await client.send_message(message.channel, msg)
        
    if message.content.startswith('!hello'):
        msg = 'Hello {0.author.mention}'.format(message)
        await client.send_message(message.channel, msg)
     
    if message.content.startswith('!lastgame'):
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
            await client.send_message(message.channel, msg)
        else:
            msg="["+timestamp+"] Congratulation, "+game["lastwinner"]+"! You beat the other team after "+str(game["gameduration"])+"min of intense fighting. A new game is about to start, time to join!"
            filename = game["filename"]
            log_graph = filename
            await client.send_file(message.channel, log_graph, 
            content=msg)

        
#this will be used for watching for a game end     
async def watch_Log():
    await client.wait_until_ready()
    current_log = readLog.getLogs()[-1]
    print("current log: "+current_log)
    while not client.is_closed:
        where = file.tell()
        line = file.readline()
        if not line:
            await asyncio.sleep(1)  
            file.seek(where)
        else:
            print line, # already has newline
   
async def list_servers():
    await client.wait_until_ready()
    while not client.is_closed:
        print("Current servers:")
        for server in client.servers:
            print(server.name)
        await asyncio.sleep(600)        
        
        
@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

client.loop.create_task(list_servers())
client.run(TOKEN)