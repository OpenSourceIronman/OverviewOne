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

import sys

# Assert Python 2.7
assert sys.version_info[0:2] == (2,7)

def wait_for_gpio():
    #TODO
    return

def trigger_cameras():
    #TODO
    return

def transmit_images():
    #TODO
    return

def main():
    while True:
        print("Waiting for a GPIO pin to go high...")
        wait_for_gpio()

        print("Triggered.  Capturing images...")
        trigger_cameras()

        print("Transmitting...")
        transmit_images()

main()
