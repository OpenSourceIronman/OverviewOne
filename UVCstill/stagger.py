#!/usr/bin/env python3.4

import time
from threading import Thread
import re, os, os.path, subprocess, sys
#import unity

# The 'schedule' dictionary is a map from the
# camera ID to the millisecond offset.
#schedule = {
#   0: 1000,
#   1: 1500,
#   2: 2000,
#   3: 2500,
#   4: 3000,
#   5: 3500,
#   6: 4000,
#   7: 4500
#}

schedule = [(300*x + 200) for x in range(8)]

# This is the multi-thread function.
# Several will run simultaneously, one for each camera.
def do_onecam(i, offset_ms,iterator):
    time.sleep(offset_ms/1000.0)
    print("Time = %f ms : Capturing camera num %d" % (offset_ms, i))
    # TODO: run the camera capture code
    filename = "/media/ubuntu/VRcameraSSD/tmp/cam%d.%d" % (i,iterator)
    p = subprocess.Popen(
            ["sudo", "./snapshot", filename, "--dev", ("/dev/still%d" % i), "--format", "jpg", "--size", str(4192), str(3104), "--suspend", "--resume"],
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
                #print(get_kern_log(10))

    except subprocess.TimeoutExpired:
    	print("TIMEOUT")

	



print("Starting")

# Launch a thread for each camera
for j in range(100):
    cur_threads = []
    for cam_num in range(0, 8):
        t = Thread(target=do_onecam, args=(cam_num,schedule[cam_num],j))
        cur_threads.append(t)
        t.start()

# Wait for all threads to finish
    for t in cur_threads:
        t.join()

    print("Finished")

# -------------------------
