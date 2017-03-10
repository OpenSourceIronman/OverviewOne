#!/usr/bin/env python2.7

"""
run_terminal.py

This executable implements an interactive terminal, that
sends a line at a time to be executed in the target's
bash shell.  The responses will be printed.

Copyright SpaceVR, 2017.  All rights reserved.
"""

import sys

from agent import Agent
from payload_cmd_handler import PayloadCommandHandler
from send import send_payload_cmd

# Assert Python 2.7
assert sys.version_info[0:2] == (2,7)

def main():
    # My payload ID
    MY_ID = 3
    # Destination ID
    DEST_ID = 4

    # Initialize an Agent to print out all command responses
    cmd_handler = PayloadCommandHandler()
    cmd_handler.handlers[PayloadCommandHandler.SHELL_RESP] = Agent.print_it

    a = Agent()
    a.payload_id = MY_ID
    a.service_handler["Payload Command"] = cmd_handler.dispatch

    # Send user input, one line at a time
    while(True):
        cmd = raw_input()
        send_payload_cmd(MY_ID, DEST_ID, PayloadCommandHandler.SHELL_CMD, cmd)

if __name__ == "__main__":
    main()
