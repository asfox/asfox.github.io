#!/usr/bin/env python

# import alot of libraries... 
# If these aren't installed, you will have to install them. :-/
import sys
import os
import nibabel as nib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import subprocess

def main(argv):
    sliceNum = argv[1]
    dim = int(argv[2])
    outf = argv[3]
    rate = int(argv[4])
    in_files = argv[5:]

    # Prepare to pipe to ffmpeg
    cmdstring = ('ffmpeg',
        '-y',
        '-f','image2pipe',
        '-r', '%d' % rate,
        '-vcodec', 'png',
        '-s', '320x280',
        '-i', 'pipe:', outf
        )
    # setup a ffmpeg pipe... 
    p = subprocess.Popen(cmdstring, stdin=subprocess.PIPE)

    # setup a the fig and main axis to plot on
    fig = plt.figure(facecolor='black', figsize=(4, 3), dpi=80)
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)

    # for each image in the input list
    for i, f in enumerate(in_files):
        # read the image
        img = nib.load(f)
        img_data = img.get_data()
        # find the right slice to draw
        if dim==1:
            toDraw = img_data[:,sliceNum,:];
        elif dim==2:
            toDraw = img_data[sliceNum,:,:];
        elif dim==3:
            toDraw = img_data[:,:,sliceNum];
        # orient appropriately?
        toDraw=np.rot90(toDraw)
        
        # show the image 
        im = ax.imshow(toDraw, cmap = cm.Greys_r, interpolation='nearest')
        plt.show()
        # write to the pipe...
        plt.savefig(p.stdin, format='png', facecolor=fig.get_facecolor(), edgecolor='none', dpi=(80) )

if __name__ == '__main__':
    main(sys.argv)


