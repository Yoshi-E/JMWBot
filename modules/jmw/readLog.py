#pip install matplotlib

import matplotlib.pyplot as plt
import ast
import os
from datetime import datetime
import json

class readLog:
    def __init__(self, cfg):
        self.cfg = cfg
        self.path = os.path.dirname(os.path.realpath(__file__))
                
    #get the log files from folder and sort them by oldest first
    def getLogs(self):
        if(os.path.exists(self.cfg.get('logs_path'))):
            files = []
            for file in os.listdir(self.cfg.get('logs_path')):
                if file.endswith(".log"):
                    files.append(file)
            return sorted(files)
        else:
            return []

    #preconditon: GameOver was called at least once
    def readData(self, admin, gameindex):
        logindex = -1
        logs = self.getLogs()
        if(len(logs)>0):
            name = logs[logindex] #fetch last log file
            #print("scanning: "+name)
            collected_rows = self.scanfile(name)
            #if data is also in previous logs, search there, until 2 game ends are found
            #that way we cen be sure if found a complete game from start till the end
            while((logindex*-1) < 10 and (logindex*-1) < len(logs) and (gameindex+1) >= len(collected_rows)): 
                logindex -= 1
                name = self.getLogs()[logindex] #fetch previous log file
                #print("next scan: "+name)
                p = self.scanfile(name)
                if(len(p[-1][0]) > 0): #incase p is empty
                    for data in collected_rows[0][0]:
                        #adds the time from last session onto the current game to have consistent timeline
                        data["time"] = data["time"]+p[-1][0][-1]["time"] 
                    collected_rows[0][0] = (p[-1][0]) + (collected_rows[0][0]) #combine data from previous 
                    collected_rows = p[:-1] + collected_rows  
            #last element in collected_rows is the current game, 2nd last the the last finished game
            if((gameindex+1) <= len(collected_rows)):
                data = collected_rows[-(gameindex+1)]
                return self.dataToGraph(data[0], data[1], data[2], data[3], data[4], admin)
        return None

        
    def scanfile(self, name):
        collected_rows = []
        rows = []
        lastwinner = "????"
        lastmap = "unkown"
        timestamp = "??:??:?? "
        date = os.path.getmtime(self.cfg.get('logs_path')+name)
        with open(self.cfg.get('logs_path')+name) as fp: 
            databuilder = {}
            try:
                line = fp.readline()
            except:
                line = "Error"
            while line:
                
                if(line.find("BattlEye") ==-1 and line.find("[") > 0 and "CTI_DataPacket" in line and line.rstrip()[-2:] == "]]"):
                #if("CTI_Mission_Performance: GameOver" in line):
                    splitat = line.find("[")
                    r = line[splitat:]  #remove timestamp
                    timestamp = line[:splitat]
                    r = r.rstrip() #remove /n
                    #converting arma3 boolen working with python +converting rawnames to strings:
                    r = r.replace(",WEST]", ',"WEST"]')
                    r = r.replace(",EAST]", ',"EAST"]') #this still needs working
                    r = r.replace("true", "True")
                    r = r.replace("false", "False")
                    try:
                        datarow = ast.literal_eval(r) #convert string into array object
                        datarow = dict(datarow)
                        if(datarow["CTI_DataPacket"] == "Header"):
                            #print("Map starting: "+datarow["Map"])
                            #rows.append(datarow)
                            lastmap = datarow["Map"]
                        if("Data_" in datarow["CTI_DataPacket"]):
                            if(len(databuilder)>0):
                                #check if previous 'Data_x' is present
                                if(int(databuilder["CTI_DataPacket"][-1])+1 == int(datarow["CTI_DataPacket"][-1])):
                                    databuilder.update(datarow)
                                    #If last element "Data_3" is present, 
                                    if(datarow["CTI_DataPacket"] == "Data_3"):
                                        databuilder["CTI_DataPacket"] = "Data"
                                        rows.append(databuilder)
                                        databuilder = {}
                            elif(datarow["CTI_DataPacket"] == "Data_1"):
                                #add first element
                                databuilder.update(datarow)

                        if(datarow["CTI_DataPacket"] == "EOF"):
                            lastmap = datarow["Map"]
                            
                        if(datarow["CTI_DataPacket"] == "GameOver"):
                            lastmap = datarow["Map"]
                            if(datarow["Lost"]):
                                if(datarow["Side"] == "WEST"):
                                    lastwinner = "EAST"
                                else:
                                    lastwinner = "WEST"
                            else:
                                if(datarow["Side"] == "WEST"):
                                    lastwinner = "WEST"
                                else:
                                    lastwinner = "EAST"
                                #rows.append(datarow)
                            collected_rows.append([rows.copy(),  lastwinner, lastmap, timestamp[:-1], date])
                            timestamp = "??:??:?? "
                            rows = []
                            #seeks forward until a new mission start was found, to ensure entries between end - start will be skipped
                            while line:
                                try:
                                    line = fp.readline()
                                    if(line.find("BattlEye") ==-1 and "CTI_DataPacket" in line):
                                        break
                                except:
                                    line = "Error"
                    except:
                        line = "Error" #failed to convert to dict  
                    
                try:
                    line = fp.readline()
                except:
                    line = "Error"
            collected_rows.append([rows.copy(),  "::currentGame::", lastmap,timestamp[:-1], date]) #get rows from current game
        return collected_rows.copy()
    
    def featchValues(self, data,field):
        if(len(data)>0 and field in data[0]):
            return [item[field] for item in data]
        else:
            return []
        
            
    # this is an exmaple place holder fuction for other plot types
    # ignore for now
    def stackedBarchart(self):
        # Set the vertical dimension to be smaller.. 
        # 3.5 seems to work after a bit of experimenting.
        plt.rcParams["figure.figsize"] = [10, 3.5]
        fig, chart_ax = plt.subplots()
        plt.rcdefaults()

        # Sample Data
        # -------------------

        segment_values = [ {'value': 12, 'label': 'A', 'color': '#FF0000'},
         {'value': 8, 'label': 'B', 'color': '#00FF00'},
         {'value': 5, 'label': 'C', 'color': '#0000FF'},
         {'value': 5, 'label': 'D', 'color': '#33A6CC'},
         {'value': 16, 'label': 'E', 'color': '#A82279'}
         ]

        # Sum up the value total.
        outer_bar_length = 0
        for segitem in segment_values:
            outer_bar_length += segitem['value']
        outer_bar_label = 'Total Time'

        # In this case we expect only 1 item in the entries list.
        y_pos = [0]
        width = 0.05

        # Set the 'empty' bar .. this is here to coerce Matplotlib
        # to keep the size of the bar smaller on our actual data.
        # Otherwise the bar will use all available space.

        chart_ax.barh(y_pos, 0, 1.0, align='center', color='white', ecolor='black', label=None)

        # Is there an 'outer' or container bar?
        if outer_bar_length != -1:
            chart_ax.barh(y_pos, outer_bar_length, 0.12,
            align='center', color='#D9DCDE', label=outer_bar_label, left=0)


        # Now go through and add in the actual segments of data.
        left_pos = 0
        for idx in range(len(segment_values)):
            segdata = segment_values[idx]
            seglabel = segdata['label']
            segval = segdata['value']
            segcol = segdata['color']

            chart_ax.barh(y_pos, [segval], width, align='center', color=segcol, label=seglabel, left=left_pos, edgecolor=['black', 'black'], linewidth=0.5)
            left_pos += segval

        chart_ax.set_yticks([1])
        chart_ax.invert_yaxis()
        chart_ax.set_xlabel('Time')
        chart_ax.set_title('Single Stacked Bar Chart')
        plt.tight_layout()

        # Set up the legend so it is arranged across the top of the chart.
        anchor_vals = (0.01, 0.6, 0.95, 0.2)
        plt.legend(bbox_to_anchor=anchor_vals, loc=4, ncol=4, mode="expand", borderaxespad=0.0)

        plt.show() 
        
    def dataToGraph(self, data, lastwinner, lastmap, timestamp, date, admin):
        #register plots
        plots = []
        v1 = self.featchValues(data, "score_east")
        v2 = self.featchValues(data, "score_west")
        #data: [[data, color_String],....]
        if(len(v1) > 0):
            plots.append({
                "data": [[v1, "r"],
                        [v2, "b"]],
                "xlabel": "Time in min",
                "ylabel": "Team Score",
                "title": "Team Score"
                })
     
        v1 = self.featchValues(data, "town_count_east")
        v2 = self.featchValues(data, "town_count_west")
        if(len(v1) > 0):
            plots.append({
                "data": [[v1, "r"],
                        [v2, "b"]],
                "xlabel": "Time in min",
                "ylabel": "Towns owned",
                "title": "Towns owned"
                })
                
        v1 = self.featchValues(data, "player_count_east")
        v2 = self.featchValues(data, "player_count_west")
        if(len(v1) > 0):
            plots.append({
                "data": [[v1, "r"],
                        [v2, "b"]],
                "xlabel": "Time in min",
                "ylabel": "Players",
                "title": "Players on Server"
                })  
                
        if(admin == True):
            v1 = self.featchValues(data, "fps")
            if(len(v1) > 0):
                plots.append({
                    "data": [[v1, "g"]],
                    "xlabel": "Time in min",
                    "ylabel": "Server FPS",
                    "title": "Server FPS"
                    }) 
                    
        if(admin == True):       
            v1 = self.featchValues(data, "active_SQF_count")
            if(len(v1) > 0):
                plots.append({
                    "data": [[v1, "g"]],
                    "xlabel": "Time in min",
                    "ylabel": "Active SQF",
                    "title": "Active Server SQF"
                    })  
                    
        if(admin == True):       
            v1 = self.featchValues(data, "active_towns")
            if(len(v1) > 0):
                plots.append({
                    "data": [[v1, "g"]],
                    "xlabel": "Time in min",
                    "ylabel": "Active Towns",
                    "title": "Active Towns"
                    }) 
                    
        if(admin == True):       
            v1 = self.featchValues(data, "active_AI")
            if(len(v1) > 0):
                plots.append({
                    "data": [[v1, "g"]],
                    "xlabel": "Time in min",
                    "ylabel": "Units",
                    "title": "Total Playable units count"
                    })  
                    
        if(admin == True):       
            v1 = self.featchValues(data, "total_objects")
            if(len(v1) > 0):
                plots.append({
                    "data": [[v1, "g"]],
                    "xlabel": "Time in min",
                    "ylabel": "Objects",
                    "title": "Total Objects count"
                    })  

        fdate = datetime.utcfromtimestamp(date).strftime('%Y-%m-%d')
        #Calculate time in min
        time = self.featchValues(data, "time")
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

        fig.suptitle("Game end: "+fdate+" "+timestamp+", "+str(gameduration)+"min. Map: "+lastmap+" Winner: "+lastwinner, fontsize=14)
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
        if not os.path.exists(self.path+"/"+self.cfg.get('data_path')):
            os.makedirs(self.path+"/"+self.cfg.get('data_path'))
        if not os.path.exists(self.path+"/"+self.cfg.get('image_path')):
            os.makedirs(self.path+"/"+self.cfg.get('image_path'))
        
        t=""
        if(lastwinner=="::currentGame::"):
            lastwinner="currentGame"
            t = "-CUR"
        if(admin==True):
            t +="-ADV"
                        #path / date # time # duration # winner # addtional_tags
        filename_pic =(self.path+"/"+self.cfg.get('image_path')+fdate+"#"+timestamp.replace(":","-")+"#"+str(gameduration)+"#"+lastwinner+"#"+lastmap+"#"+t+'.png').replace("\\","/")
        filename =    (self.path+"/"+self.cfg.get('data_path')+ fdate+"#"+timestamp.replace(":","-")+"#"+str(gameduration)+"#"+lastwinner+"#"+lastmap+"#"+t+'.json').replace("\\","/")
        
        #save image
        fig.savefig(filename_pic, dpi=100, pad_inches=3)
        #save rawdata
        with open(filename, 'w') as outfile:
            json.dump(data, outfile)
        
        return {"date": fdate, "time": timestamp, "lastwinner": lastwinner, "gameduration": gameduration, "picname": filename_pic, "dataname": filename, "data": data}

    
#readData()

