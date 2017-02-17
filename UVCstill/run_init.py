#!/usr/bin/env python3.4

import re, os, os.path, subprocess, sys, time
import unity

print("-------------------------------------------");
print("SpaceVR Camera Tests");
print("-------------------------------------------");
print("")

# Clean
print("Cleaning directory... ", end="")
try:
    os.remove("uvcstill.ko")
    os.remove("snapshot")
except:
    pass
    # Didn't exist

print("OK")

# Build code
print("Building code... ", end="")
p = subprocess.Popen(
    ["make", "clean"],
    stdout=subprocess.PIPE, shell=True)
(output, err) = p.communicate()

if (os.path.isfile("uvcstill.ko") and os.path.isfile("snapshot")):
    print("OK")
else:
    print("***FAILED***")
    print(err)
    sys.exit(1)

# Unbinding uvcvideo
print("Unbinding uvcvideo... ", end="")
numOldDevs = 0
for f in os.listdir("/sys/bus/usb/drivers/uvcvideo/"):
    if re.match(".*:1.0", f):
        numOldDevs +=1
        subprocess.call("sudo sh -c 'echo %s > /sys/bus/usb/drivers/uvcvideo/unbind'" % f, shell=True)

print("%d devices" % numOldDevs)

# Remove existing uvcstill module
print("Unloading uvcstill module... ", end="")
try:
    code = subprocess.call(["sudo", "rmmod", "uvcstill"])
except:
    code = code
if code == 0:
    print("OK")
else:
    print("NO")

# Install module
print("Loading uvcstill module... ", end="")
code = subprocess.call(["sudo", "insmod", "uvcstill.ko"])
if code == 0:
    print("OK")
else:
    print("***FAILED***")
    sys.exit(1)

# Searching for /dev/stillX drivers
print("Checking for /dev/still devices... ", end="")
numDevs = unity.get_num_cameras()
print(numDevs)

print("Waiting 2 seconds...")
time.sleep(2);

# Testing small image
print("")
print("Retrieving a 1280 720 image...")
unity.test_all_cameras(numDevs, 1280, 720)

# Testing full image
print("")
print("Retrieving a 4192 x 3104 image...")
unity.test_all_cameras(numDevs, 4192, 3104)
