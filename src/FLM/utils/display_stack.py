import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import cv2
import tkinter as tk
from tkinter import filedialog
import tifffile as tif
import time

root = tk.Tk()
root.withdraw()

input_file = filedialog.askopenfilename()
stack =tif.imread(input_file)



### Plottin stuff
fig = plt.figure()

idx0 = 0
l = plt.imshow(stack[:,:,idx0])

axidx = plt.axes([0.25, 0.15, 0.65, 0.03])
slidx = Slider(axidx, 'Slice', 0, stack.shape[2]-1, valinit=idx0, valfmt='%d')

def update(val):
    idx = slidx.val
    l.set_data(stack[:,:,int(idx)])
    fig.canvas.draw()
    time.sleep(0.5)
slidx.on_changed(update)
plt.show()
input()