import json
from os import listdir
from os.path import isfile, join
import numpy as np
import numpy.random
from PIL import Image
import sys


# Usage: image = generateMap(self, player_name="all", bins=50)

class playerMapGenerator():
    def __init__(self, path):
        self.MAP_SIZE = 30720
        self.mypath = path
        
    def getPlayers(self, data, player_name="all"):
        p = []
        if(not "players" in data):
            return []
        players = data["players"]
        for player in players:
            if(player_name != "all" and player[0]!=player_name):
                continue
            
            if(player[3][0] >= 0 and player[3][0] <= MAP_SIZE and player[3][1] >= 0 and player[3][1] <= MAP_SIZE):
                p.append([player[3][0],player[3][1]])
            
            #if(player[3][0] > 50000 or player[3][1] > 50000):
            #    print(player)
        return p

    def generateData(self, player_name="all"):
        files = [f for f in listdir(mypath) if isfile(join(mypath, f))]

        players=[] #[[0,0],[MAP_SIZE,MAP_SIZE]]  
        for file in files:
            if("CUR" not in file and "ADV" in file and "Altis" in file):
                with open('jmw2/'+file) as f:
                    data = json.load(f)
                    if(len(data) > 0):
                        for row in data:
                            if(row["CTI_DataPacket"] == "Data"):
                                players += self.getPlayers(row, player_name)
        return np.array(players)

    def drawheatmap(self, data, image):
        TINT_COLOR = (0, 0, 0)  # Black
        TRANSPARENCY = .25  # Degree of transparency, 0-100%
        OPACITY = int(255 * TRANSPARENCY)
        
        data = np.rot90(data)
        overlay = image.copy()

        height, width, channels = image.shape
        bins = len(data)
        
        x_size = int(height/bins)
        y_size = int(width/bins)
        for y,row in enumerate(data):
            for x,val in enumerate(row):
                color = self.colvF1(val)
                
                x_pos = int(x_size * x)
                y_pos = int(y_size * y)

                overlay = Image.new('RGBA', img.size, color+(0,))
                draw = ImageDraw.Draw(overlay)  # Create a context for drawing things on it.
                draw.rectangle(((x_pos, y_pos),(x_pos + x_size, y_pos + y_size)), fill=color+(OPACITY,))

                # Alpha composite these two images together to obtain the desired result.
                img = Image.alpha_composite(img, overlay)
                img = img.conve
                

    def colvF1(self, val):
        color = (0,0,0)        
        if(val > 0 and val < 10): 
            color = (0,50+val*10,0)
        if(val >= 10 and val <100): 
            norm = (val - 10)/(100-10) * 10
            color = (50+norm*10,0,0)       
        if(val >= 100): 
            norm = (val - 100)/(300-100) * 10
            color = (0,0,50+norm*10)     
        return (255-color[0], 255-color[1], 255-color[2])

    def generateMap(self, player_name="all", bins=50):
        image = Image.open('Altis_sat_s.jpg').convert('LA')
        image = cv2.cvtColor(image,cv2.COLOR_GRAY2RGB)
        players = self.generateData(player_name)
        print("Cords Count:", len(players))

        # Generate data
        x = players[:,0]
        y = players[:,1]
        
        heatmapD, xedges, yedges = np.histogram2d(x, y, bins=bins, range=[[0,MAP_SIZE],[0,MAP_SIZE]])
        self.drawheatmap(heatmapD, image)
        
        byteImgIO = io.BytesIO()
        image.save(byteImgIO, "JPG")

        return byteImgIO

# image = generateMap("Yoshi_E", 100)
# cv2.imshow('image',image)
# cv2.waitKey(0)
# cv2.destroyAllWindows()