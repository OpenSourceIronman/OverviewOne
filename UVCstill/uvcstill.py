#!/usr/bin/env python2

# Suppress print statement in favor of print method
from __future__ import print_function

import re, os, os.path, subprocess, sys

# Returns the number of cameras (as seen by the uvcstill driver);
def get_num_cameras():
    n = 0
    for f in os.listdir("/dev"):
        if re.match("still.*", f):
            n += 1
    return n

# Return the last 'numLines' from /var/log/kern.log.
def get_kern_log(numLines):
    p = subprocess.Popen(
        ["tail", "-n", str(numLines), "/var/log/kern.log"],
        stdout=subprocess.PIPE)
    (output, err) = p.communicate(timeout=3)
    return output.decode("utf-8")


# Read an image from each camera.  Do not save it.
def test_all_cameras(numCams, width, height):
    for i in range(0, numCams):

        print("  cam %d : " % i, end="")
        p = subprocess.Popen(
            ["sudo", "./snapshot", "/dev/null", "--dev", ("/dev/still%d" % i), "--format", "none", "--size", str(width), str(height), "--suspend", "--resume"],
            stdout=subprocess.PIPE)
        try:
            (output, err) = p.communicate(timeout=30)
            output_str = output.decode("utf-8")

            if re.search(r"\*FULL\*", output_str, flags=re.MULTILINE):
                print("OK")
            elif re.search(r"\*INCOMPLETE\*", output_str, flags=re.MULTILINE):
                print("INCOMPLETE")
            else:
                print("*** FAILED ***")
                print("Kernel log:")
                print(get_kern_log(10))

        except subprocess.TimeoutExpired:
            print("TIMEOUT")


# Read an image from each camera and save it to disk.
def read_all_cameras(numCams, width, height, iter):
    outputFiles = list()
    for i in range(0, numCams):
        filename = "/media/ubuntu/VRcameraSSD/tmp/cam%d.%d.yuyv" % (i, iter)

        print("  cam %d : " % i, end="")
        p = subprocess.Popen(
            ["sudo", "./snapshot", filename, "--dev", ("/dev/still%d" % i), "--format", "yuyv", "--size", str(width), str(height), "--suspend", "--resume"],
            stdout=subprocess.PIPE)
        try:
            (output, err) = p.communicate(timeout=30)
            output_str = output.decode("utf-8")

            if re.search(r"\*FULL\*", output_str, flags=re.MULTILINE):
                print("OK")
                outputFiles.append(filename)
            elif re.search(r"\*INCOMPLETE\*", output_str, flags=re.MULTILINE):
                print("INCOMPLETE")
            else:
                print("*** FAILED ***")
                print("Kernel log:")
                print(get_kern_log(10))

        except subprocess.TimeoutExpired:
            print("TIMEOUT")

    # If all were not captured correctly, delete the remaining image files.
    if len(outputFiles) != numCams:
        for f in outputFiles:
            try:
                os.remove(f)
            except FileNotFoundError:
                1+1 # Ignore
        print("    Deleted %d files because of a failure" % len(outputFiles))
