#pip install matplotlib

import matplotlib.pyplot as plt
import os
from datetime import datetime
from PIL import Image
from PIL import ImageDraw


TownsAltis = {
"Town0": [20826.033,36.789253,6824.6987],
"Town1": [16820.996,26.518801,12713.124],
"Town2": [19407.914,42.663628,13262.551],
"Town3": [18089.914,26.811056,15200.277],
"Town4": [18810.496,35.676094,16633.451],
"Town5": [20945.688,47.213638,16965.613],
"Town7": [27018.002,25.26956,23167.574],
"Town8": [16640.928,19.293343,16056.638],
"Town9": [16244.04,29.379099,17314.234],
"Town12": [14032.271,30.131212,18737],
"Town13": [11745.446,57.814919,18331.873],
"Town16": [10292.485,134.56599,19118.633],
"Town21": [4588.5151,303.55054,21381.932],
"Town17": [8649.4277,184.71611,18285.018],
"Town18": [9298.0059,119.61528,15932.003],
"Town14": [12362.523,25.348881,15765.438],
"Town15": [12608.428,16.056833,14320.253],
"Town19": [9038.1826,26.646751,11954.574],
"Town20": [3507.7151,12.373648,12996.904],
"Town11": [14181.469,23.505833,16286.399],
"Town10": [15191.061,21.902496,17301.797],
"Town22": [20274.463,52.501724,11714.725],
"Town23": [12842.514,46.522461,19633.301],
"Town24": [4864.3594,82.693581,16151.614],
"Town25": [25623.484,22.950079,21285.391],
"Town26": [20516.811,38.253426,8883.252],
"Town27": [7118.8721,116.19866,16439.533],
"Town28": [22950.141,9.1006737,18859.719],
"Town29": [13587.634,19.314034,12209.913],
"Town30": [14964.189,10.588233,11105.679],
"Town32": [17745.547,6.3756104,18107.686],
"Town33": [11574.771,23.315058,9442.752],
"Town31": [17077.311,23.238556,10059.891],
"Town34": [14651.969,49.779419,20758.879],
"Town35": [16854.336,14.130496,21871.979],
"Town36": [20113.703,22.211153,20032.137],
"Town37": [20943.436,17.919567,19257.873],
"Town38": [9220.6602,19.509701,21622.859],
"Town39": [23199.52,18.140114,19971.23],
"Town40": [11623.219,27.020689,11943.426],
"Town41": [26851.094,30.606556,24466.365],
"Town42": [5068.5044,56.909691,11306.087],
"Town43": [21895.934,26.782196,21010.182],
"Town44": [5475.6577,31.276804,14999.543],
"Town45": [21091.016,5.8291836,14768.472],
"Town46": [3853.6687,19.174381,17472.664],
"Town47": [21752.174,19.689096,7520.2725],
"Town48": [5853.1182,229.927,20094.025],
"Town49": [23236.664,38.75779,21794.523]
}
class readLog:
    def __init__(self, cfg):
        self.cfg = cfg
        self.path = os.path.dirname(os.path.realpath(__file__))
                
    #get the log files from folder and sort them by oldest first
    def getLogs(self):
       pass 


def coordTransform(Map, img, x, y):
    #Bottom-Left to Top-Right
    Maps = {"Altis": 30720,
            "Malden": 12800,
            "Stratis": 8192,
            "Tanoa": 15360}
    width, height = img.size
    if(x > Maps[Map]):
        x = Maps[Map]
    if(y > Maps[Map]):
        y = Maps[Map]
    
    return [width*(x/Maps[Map]),height-(height*(y/Maps[Map]))]

def loadMap(Map):
    Maps = {"Altis": "Altis_sat_s.jpg",
            "Malden": "",
            "Stratis": "",
            "Tanoa": ""}
    img = Image.open("mapTemplates/"+Maps[Map])
    return [ImageDraw.Draw(img, "RGBA"), img]
    
def drawTown(canvas, p_x, p_y, side):
    sides = {   "neutral": [0,0.8,0,0.3],
                "east": [0.5,0,0,0.3],
                "west": [0,0.3,0.6,0.3]
    }
    radius = 5
    # Now I draw the circle:
    canvas.ellipse((p_x - radius, p_y - radius, p_x + radius, p_y + radius), fill=(round(255*sides[side][0]), round(255*sides[side][1]), round(255*sides[side][2]), round(255*sides[side][3])))
    
def drawBase(canvas, p_x, p_y, side):
    sides = {   "neutral": [0,0.8,0,0.6],
                "east": [0.5,0,0,0.6],
                "west": [0,0.3,0.6,0.6]
    }
    radius = 5
    # Now I draw the circle:
    canvas.rectangle((p_x - radius, p_y - radius, p_x + radius, p_y + radius), fill=(round(255*sides[side][0]), round(255*sides[side][1]), round(255*sides[side][2]), round(255*sides[side][3])))
    



Map = "Altis" 
canvas, img = loadMap(Map)   
for key, value in TownsAltis.items():
    Town = TownsAltis[key]
    Town = coordTransform(Map, img, Town[0],Town[2])
    drawTown(canvas, Town[0],Town[1], "neutral")  

Town = coordTransform(Map, img, 13000,15000)
drawBase(canvas,Town[0],Town[1], "east")
#img = Image.new('RGBA', size = (1000, 1000), color = (128, 128, 128, 255))


  
# now save and close
del canvas
img.save("test.png", 'PNG')