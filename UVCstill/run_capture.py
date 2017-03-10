#!/usr/bin/env python3.4

import re, os, os.path, subprocess, sys, time
import uvcstill

print("-------------------------------------------");
print("SpaceVR Capture");
print("-------------------------------------------");
print("")

print("* Querying number of cameras...", end="")
numCams = uvcstill.get_num_cameras()
print(numCams)

all_start = time.time()
for j in range(1):
    # Testing full image
    frame_start = time.time()
    print("\n* Retrieving a full (4192x3104) image...")
    uvcstill.read_all_cameras(numCams, 4192, 3104, j)
    print("    frame rate : cur=%0.3f overall=%0.3f" %
          ( 1.0/(time.time()-frame_start) ,
            1.0*(j+1)/(time.time()-all_start) ) )
