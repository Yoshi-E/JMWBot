#pip install matplotlib

import matplotlib.pyplot as plt
import ast
import os
from datetime import datetime
#import matplotlib.patches as mpatches
import config

image_path = config.image_path
log_path = config.log_path

def getLogs():
    global log_path
    files = sorted(os.listdir(log_path))
    return files

#preconditon: GameOver was called
def readData(admin, gameindex):
    global log_path
    logindex = -1
    logs = getLogs()
    name = logs[logindex] #fetch last log file
    print("scanning: "+name)
    collected_rows = scanfile(name)
    for row in collected_rows:
        print(row[2])
    #if data is also in previous logs, search there, until 2 game ends are found

    while((logindex*-1) < 10 and (logindex*-1) < len(logs) and (gameindex+1) >= len(collected_rows)): 
        logindex -= 1
        name = getLogs()[logindex] #fetch previous log file
        print("next scan: "+name)
        p = scanfile(name)
        #if(p[-1][0][-1]["time"] > collected_rows[-1][0][-1]["time"]): #add time from before crash onto new log
        for data in collected_rows[-1][0]:
            data["time"] = data["time"]+p[-1][0][-1]["time"]
        collected_rows[0][0] = (p[-1][0]) + (collected_rows[0][0]) #combine data from previous 
        collected_rows = p[:-1] + collected_rows  
    
    #collected_rows.append(collected_rows.pop(0)) #append current game to the end of list
    for row in collected_rows:
        print(row[2])
    gameindex += 1
    data = collected_rows[-gameindex]
    return dataToGraph(data[0], data[1], data[2], data[3], admin)

    
def scanfile(name):
    global log_path
    collected_rows = []
    rows = []
    lastwinner = "????"
    timestamp = "??:??:??"
    date = os.path.getmtime(log_path+name)
    with open(log_path+name) as fp: 
        try:
            line = fp.readline()
        except:
            line = "Error"
        while line:
            if(line.find("BattlEye") ==-1 and line.find("[") > 0 and "CTI_Mission_Performance" in line):
                if("CTI_Mission_Performance: GameOver" in line):
                    splitat = line.find("[")
                    r = line[splitat:]  #remove timestamp
                    timestamp = line[:splitat] #time stamp of game end
                    r = r.rstrip() #remove \n
                    r = r[-5:-1] #get winner
                    lastwinner = r
                    collected_rows.append([rows.copy(),  lastwinner, timestamp[:-1], date])
                    rows = []
                else:
                    splitat = line.find("[")
                    r = line[splitat:]  #remove timestamp
                    r = r.rstrip() #remove \n
                    p = ast.literal_eval(r) #convert string into array object
                    p = p[1:] #remove first element
                    d = dict(p)
                    rows.append(d)
            try:
                line = fp.readline()
            except:
                line = "Error"
        collected_rows.append([rows.copy(),  "::currentGame::", timestamp[:-1], date]) #get rows from current game
    return collected_rows.copy()
    
def featchValues(data,field):
    return [item[field] for item in data]
    
def dataToGraph(data, lastwinner, timestamp, date, admin):
    global image_path
    
    fdate = datetime.utcfromtimestamp(date).strftime('%Y-%m-%d')
    #Team Scores
    time = featchValues(data, "time")
    for i in range(len(time)):
        if(time[i] > 0):
            time[i] = time[i]/60 #seconds->min
    if (len(time) > 0):
        gameduration = round(time[-1])
    else:
        gameduration = 0
    print(timestamp+","+lastwinner+","+str(gameduration))
    fig = plt.figure(figsize = (10,10))
    fig.suptitle("Game end: "+fdate+" "+timestamp+", "+str(gameduration)+"min. Winner: "+lastwinner, fontsize=14)
    #red_patch = mpatches.Patch(color='red', label='The red data')
    #plt.legend(bbox_to_anchor=(0, 0), handles=[red_patch])
    fig.subplots_adjust(hspace=0.3)
    
    
    if(admin==True):
        p1 = fig.add_subplot(3,2,1)
    else:
        p1 = fig.add_subplot(2,2,1)
    score_east = featchValues(data, "score_east")
    score_west = featchValues(data, "score_west")
    p1.plot(time, score_east, color='r')
    p1.plot(time, score_west, color='b')
    p1.set_xlabel('Time in min')
    p1.set_ylabel('Team Score')
    p1.set_title('Team Score')

    if(admin==True):
        p2 = fig.add_subplot(3,2,2)
    else:
        p2 = fig.add_subplot(2,2,2)
    town_count_east = featchValues(data, "town_count_east")
    town_count_west = featchValues(data, "town_count_west")
    p2.plot(time, town_count_east, color='r')
    p2.plot(time, town_count_west, color='b')
    p2.set_xlabel('Time in min')
    p2.set_ylabel('Towns owned')
    p2.set_title('Towns owned')

    if(admin==True):
        p3 = fig.add_subplot(3,2,3)
    else:
        p3 = fig.add_subplot(2,2,3)
    player_count_east = featchValues(data, "player_count_east")
    player_count_west = featchValues(data, "player_count_west")
    p3.plot(time, player_count_east, color='r')
    p3.plot(time, player_count_west, color='b')
    p3.set_xlabel('Time in min')
    p3.set_ylabel('Players')
    p3.set_title('Players on Server')
    
    
    if(admin==True):
        p4 = fig.add_subplot(3,2,4)
        fps = featchValues(data, "fps")
        p4.plot(time, fps, color='g')
        p4.set_xlabel('Time in min')
        p4.set_ylabel('Server FPS')
        p4.set_title('Server FPS')
    
        p5 = fig.add_subplot(3,2,5)
        active_SQF_count = featchValues(data, "active_SQF_count")
        p5.plot(time, active_SQF_count, color='g')
        p5.set_xlabel('Time in min')
        p5.set_ylabel('Active SQF')
        p5.set_title('Active Server SQF')

    if not os.path.exists(image_path):
        os.makedirs(image_path)
    
    if(lastwinner=="::currentGame::"):
        filename = image_path+fdate+" "+timestamp.replace(":","-")+"("+str(gameduration)+")ADV"+'.png'
    else:
        filename = image_path+fdate+" "+timestamp.replace(":","-")+"("+str(gameduration)+")"+'.png'
    fig.savefig(filename, dpi=100, pad_inches=3)
    
    return {"date": fdate, "time": timestamp, "lastwinner": lastwinner, "gameduration": gameduration, "filename": filename, "data": data}

    
#readData()

