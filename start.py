import subprocess

while True:
    lines = None
    try:
        print(subprocess.check_output(['python', 'bot.py']))
    except Exception as e:
        print(e)
        print("Restarting...")