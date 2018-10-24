#pip install matplotlib

import matplotlib.pyplot as plt
import ast
import os
from datetime import datetime
#import matplotlib.patches as mpatches
import config
import json
image_path = config.image_path
log_path = config.log_path
data_path = config.data_path

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
        if(len(p[-1][0]) > 0): #incase p is empty
            for data in collected_rows[0][0]:
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
                    if("losse" in line): #if loser is found
                        if(r == "EAST"):
                            r = "WEST"
                        else:
                            r = "EAST"
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
    if(len(data)>0 and field in data[0]):
        return [item[field] for item in data]
    else:
        return []
    
def dataToGraph(data, lastwinner, timestamp, date, admin):
    global image_path  
    
    #register plots
    plots = []
    
    v1 = featchValues(data, "score_east")
    v2 = featchValues(data, "score_west")
    #data: [[data, color_String],....]
    if(len(v1) > 0):
        plots.append({
            "data": [[v1, "r"],
                    [v2, "b"]],
            "xlabel": "Time in min",
            "ylabel": "Team Score",
            "title": "Team Score"
            })
 
    v1 = featchValues(data, "town_count_east")
    v2 = featchValues(data, "town_count_west")
    if(len(v1) > 0):
        plots.append({
            "data": [[v1, "r"],
                    [v2, "b"]],
            "xlabel": "Time in min",
            "ylabel": "Towns owned",
            "title": "Towns owned"
            })
            
    v1 = featchValues(data, "player_count_east")
    v2 = featchValues(data, "player_count_west")
    if(len(v1) > 0):
        plots.append({
            "data": [[v1, "r"],
                    [v2, "b"]],
            "xlabel": "Time in min",
            "ylabel": "Players",
            "title": "Players on Server"
            })            
    if(admin == True):
        v1 = featchValues(data, "fps")
        if(len(v1) > 0):
            plots.append({
                "data": [[v1, "g"]],
                "xlabel": "Time in min",
                "ylabel": "Server FPS",
                "title": "Server FPS"
                }) 
    if(admin == True):       
        v1 = featchValues(data, "active_SQF_count")
        if(len(v1) > 0):
            plots.append({
                "data": [[v1, "g"]],
                "xlabel": "Time in min",
                "ylabel": "Active SQF",
                "title": "Active Server SQF"
                })  

    fdate = datetime.utcfromtimestamp(date).strftime('%Y-%m-%d')
    #Calculate time in min
    time = featchValues(data, "time")
    for i in range(len(time)):
        if(time[i] > 0):
            time[i] = time[i]/60 #seconds->min
    if (len(time) > 0):
        gameduration = round(time[-1])
    else:
        gameduration = 0
    print(timestamp+","+lastwinner+","+str(gameduration))
    
    #maps plot count to image size
    #plot_count: image_size
    hight={ 12: 22,
            11: 22,
            10: 18,
            9: 18,
            8: 14,
            7: 14,
            6: 10,
            5: 10,
            4: 6,
            3: 6,
            2: 3,
            1: 3}
    phight = 10
    if(len(plots) in hight):
        phight = hight[len(plots)]
    fig = plt.figure(figsize = (10,phight)) 

    fig.suptitle("Game end: "+fdate+" "+timestamp+", "+str(gameduration)+"min. Winner: "+lastwinner, fontsize=14)
    #red_patch = mpatches.Patch(color='red', label='The red data')
    #plt.legend(bbox_to_anchor=(0, 0), handles=[red_patch])
    fig.subplots_adjust(hspace=0.3)
    zplots = []
    #writes data to plot
    for pdata in plots:
        if(len(pdata["data"][0])>0):
            zplots.append(fig.add_subplot( int(round((len(plots)+1)/2)), 2 ,len(zplots)+1))
            for row in pdata["data"]:
                zplots[-1].plot(time, row[0], color=row[1])
            zplots[-1].set_xlabel(pdata["xlabel"])
            zplots[-1].set_ylabel(pdata["ylabel"])
            zplots[-1].set_title(pdata["title"])
    
    #create folders to for images / raw data
    if not os.path.exists(data_path):
        os.makedirs(data_path)
    if not os.path.exists(image_path):
        os.makedirs(image_path)
    
    t=""
    if(lastwinner=="::currentGame::"):
        t = "-CUR"
    if(admin==True):
        t +="-ADV"
        
    filename = image_path+fdate+" "+timestamp.replace(":","-")+"("+str(gameduration)+")"+t
    #save image
    fig.savefig(filename+'.png', dpi=100, pad_inches=3)
    #save rawdata
    with open(filename+".json", 'w') as outfile:
        json.dump(data, outfile)
    
    return {"date": fdate, "time": timestamp, "lastwinner": lastwinner, "gameduration": gameduration, "picname": filename+'.png', "dataname": filename+'.txt', "data": data}

    
#readData()

