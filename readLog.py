#pip install matplotlib

import matplotlib.pyplot as plt
import ast
import os
from datetime import datetime
#import matplotlib.patches as mpatches


path = "images/"
log_path = "logs/"

def getLogs():
    global log_path
    files = sorted(os.listdir(log_path))
    return files

#preconditon: GameOver was called
def readData():
    global log_path

    logindex = -1
    logs = getLogs()
    name = logs[logindex] #fetch last log file
    collected_rows = scanfile(name)
    #if data is also in previous logs, search there, until 2 game ends are found
    while((logindex*-1) < len(logs) and len(collected_rows)<=1): 
        logindex = logindex -1
        name = getLogs()[logindex] #fetch previous log file
        p = scanfile(name)
        collected_rows[0][0].insert(0,p[-1][0]) #combine data from previous 

    gamemetadata = []
    #for data in collected_rows:
    #    #generate image and store metadata
    #    gamemetadata.append(dataToGraph(data[0], data[1], data[2], data[3]))  
    data = collected_rows[-1] #fetch last game
    gamemetadata.append(dataToGraph(data[0], data[1], data[2], data[3]))  
    
    
    return gamemetadata

    
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
                    r = r[-5:-1]
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

    return collected_rows
    
def featchValues(data,field):
    return [item[field] for item in data]
    
def dataToGraph(data, lastwinner, timestamp, date):
    global path
    
    fdate = datetime.utcfromtimestamp(date).strftime('%Y-%m-%d')
    #Team Scores
    time = featchValues(data, "time")
    for i in range(len(time)):
        if(time[i] > 0):
            time[i] = time[i]/60 #seconds->min
    gameduration = round(time[-1])
    print(timestamp+","+lastwinner+","+str(gameduration))
    fig = plt.figure(figsize = (10,10))
    fig.suptitle("Game end: "+fdate+" "+timestamp+", "+str(gameduration)+"min. Winner: "+lastwinner, fontsize=14)
    #red_patch = mpatches.Patch(color='red', label='The red data')
    #plt.legend(bbox_to_anchor=(0, 0), handles=[red_patch])
    fig.subplots_adjust(hspace=0.3)
    
    p1 = fig.add_subplot(3,2,1)
    score_east = featchValues(data, "score_east")
    score_west = featchValues(data, "score_west")
    p1.plot(time, score_east, color='r')
    p1.plot(time, score_west, color='b')
    p1.set_xlabel('Time in min')
    p1.set_ylabel('Team Score')
    p1.set_title('Team Score')

    p2 = fig.add_subplot(3,2,2)
    fps = featchValues(data, "fps")
    p2.plot(time, fps, color='g')
    p2.set_xlabel('Time in min')
    p2.set_ylabel('Server FPS')
    p2.set_title('Server FPS')

    p3 = fig.add_subplot(3,2,3)
    town_count_west = featchValues(data, "town_count_west")
    town_count_east = featchValues(data, "town_count_east")
    p3.plot(time, town_count_west, color='b')
    p3.plot(time, town_count_east, color='r')
    p3.set_xlabel('Time in min')
    p3.set_ylabel('Towns owned')
    p3.set_title('Towns owned')

    p4 = fig.add_subplot(3,2,4)
    active_SQF_count = featchValues(data, "active_SQF_count")
    p4.plot(time, active_SQF_count, color='g')
    p4.set_xlabel('Time in min')
    p4.set_ylabel('Active SQF')
    p4.set_title('Active Server SQF')

    
    p5 = fig.add_subplot(3,2,5)
    player_count_east = featchValues(data, "player_count_east")
    player_count_west = featchValues(data, "player_count_west")
    p5.plot(time, player_count_east, color='r')
    p5.plot(time, player_count_west, color='b')
    p5.set_xlabel('Time in min')
    p5.set_ylabel('Players')
    p5.set_title('Players on Server')
    
    if not os.path.exists(path):
        os.makedirs(path)
    
    filename = path+fdate+" "+timestamp.replace(":","-")+"("+str(gameduration)+")"+'.png'
    fig.savefig(filename, dpi=300, pad_inches=3)
    
    return {"date": fdate, "time": timestamp, "lastwinner": lastwinner, "gameduration": gameduration, "filename": filename, "data": data}

    
#readData()

