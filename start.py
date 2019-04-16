import subprocess

while True:
    lines = None
    try:
        print(subprocess.check_output(['python', 'bot.py']))
    except KeyboardInterrupt:
        break
        