#!/usr/bin/env python2.7

# Copyright SpaceVR, 2017.  All rights reserved.

import sys
from send import BusCommands, send_payload_cmd

# Assert Python 2.7
assert sys.version_info[0:2] == (2,7)

def main():
    # My payload ID
    my_id = 4

    print("Sending no-op command to bus...")
    bc = BusCommands(my_id)
    bc.noop()

    print("Sending shell command to self...")
    send_payload_cmd(my_id, my_id, 0x00, "ls")

if __name__ == "__main__":
    main()
