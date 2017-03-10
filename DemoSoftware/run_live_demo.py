#!/usr/bin/env python2.7

"""
Main entry point for mid-March-2017 live demonstration.

The goals of this demonstation:

   1.  Wait for any GPIO input to go high.
   2.  Trigger the capture of ~5 still images from
       4 cameras at ~1080p resolution each.
   3.  Send the images to the S-band radio.
   4.  Repeat.

Copyright SpaceVR, 2017.  All rights reserved.
"""

# Suppress print statement in favor of print method
from __future__ import print_function

import re
import sys, os.path
import subprocess

# Determine project root directory
import os,sys,inspect
MY_DIR   = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
ROOT_DIR = os.path.dirname(MY_DIR)
# Add the UVCStill folder to the sys.path
sys.path.append(os.path.join(ROOT_DIR, 'UVCstill'))
sys.path.append(os.path.join(ROOT_DIR, 'SWIFT_XTS_API'))

import uvcstill
import SpaceVR_Configuration_Connection_Telemetry
import TransferFile

# Assert Python 2.7
assert sys.version_info[0:2] == (2,7)

def wait_for_gpio():
    exit_code = subprocess.call([os.path.join(ROOT_DIR, 'GPIOControl', 'WaitForPinApp')])
    if exit_code != 0:
        raise Exception("Error when running WaitForPinApp")
    return

def init_cameras():
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
    code = subprocess.call(["sudo", "insmod", 
                           os.path.join(ROOT_DIR, "UVCstill", "uvcstill.ko")])
    if code == 0:
        print("OK")
    else:
        print("***FAILED***")
        sys.exit(1)

def trigger_cameras():
    read_all_cameras(numCams=4, width=1920, height=1080, iter=1)
    read_all_cameras(numCams=4, width=1920, height=1080, iter=2)
    read_all_cameras(numCams=4, width=1920, height=1080, iter=3)
    read_all_cameras(numCams=4, width=1920, height=1080, iter=4)
    read_all_cameras(numCams=4, width=1920, height=1080, iter=5)
    return
 
def transmit_images():
   #TODO 
   SpaceVR_Configuration_Connection_Telemetry.InitializeRadio(???, DEV_MODEL, "192.168.1.42", "192.168.1.50", 30000, 30100,30200)
   for camNum in range(4) 
     for image in range (5)
       filename = "/media/ubuntu/EVO8501TB/test_output/cam%d.%d.yuyv" % (camNum, image)
       TransmitFile.ToSWIFT("192.168.1.42", TBD, filename, False)

    TransmitFile.DownlinkToGroundStation(???, ???, ???)
    return

def main():
    print("Initializing cameras...")
    init_cameras()

    while True:
        print("Waiting for a GPIO pin to go high...")
        wait_for_gpio()

        print("Triggered.  Capturing images...")
        trigger_cameras()

        print("Transmitting...")
        transmit_images()

if __name__ == "__main__":
    main()
