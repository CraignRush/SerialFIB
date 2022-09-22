
import pickle
with open('pickle.tmp','rb') as pickle_in:
    infile=pickle.load(pickle_in)
    stagepositions=infile[0]
    images=infile[1]
    patterns=infile[2]

from src.AquilosDriver import fibsem

fibsem=fibsem()
import math
from time import sleep
pos = fibsem.getStagePosition()
pos['x'] = -2.1915e-3
pos['y'] = -4.3908e-3
pos['z'] = 6.9725e-3
pos['t'] = 0.0
rotation = 0.0 # radians!
pos['r'] = rotation


newPos = fibsem.getStagePosition()
while round(rotation,3) != round(newPos['r'],3):
    pos['r'] = rotation + 2/180 * math.pi    
    fibsem.moveStageAbsolute(pos) 
    sleep(1)   
    pos['r'] = rotation  
    fibsem.moveStageAbsolute(pos)
    sleep(1)   
    newPos = fibsem.getStagePosition()



