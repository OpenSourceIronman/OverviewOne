#!/usr/bin/env python3.4

import re, os, os.path, subprocess, sys
import unity

print("-------------------------------------------");
print("SpaceVR Camera Tests");
print("-------------------------------------------");
print("")


print("* Querying number of cameras...", end="")
numCams = unity.get_num_cameras()
print(numCams)

for j in range(0,999):
    # Testing small image
    print("\n* Retrieving a small (1280x720) image...")
    unity.test_all_cameras(numCams, 1280, 720)

    # Testing medium image
    print("\n* Retrieving a medium (2592x1944) image...")
    unity.test_all_cameras(numCams, 2592, 1944)

    # Testing full image
    print("\n* Retrieving a full (4192x3104) image...")
    unity.test_all_cameras(numCams, 4192, 3104)

    # Testing full image, again
    print("\n* Retrieving a full (4192x3104) image again...")
    unity.test_all_cameras(numCams, 4192, 3104)
