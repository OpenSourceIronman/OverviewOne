#!/usr/bin/env python2.7

"""
run_terminal.py

This executable implements an interactive terminal, that
sends a line at a time to be executed in the target's
bash shell.  The responses will be printed.

Copyright SpaceVR, 2017.  All rights reserved.
"""

from __future__ import print_function
import sys
import threading

from agent import Agent
from payload_cmd_handler import PayloadCommandHandler
from send import Send

# Assert Python 2.7
assert sys.version_info[0:2] == (2,7)

# Destination ID
DEST_ID = 1

def main():
    # Initialize an Agent to print out all command responses
    cmd_handler = PayloadCommandHandler()
    cmd_handler.handlers[PayloadCommandHandler.SHELL_RESP] = Agent.print_it

    a = Agent()
    a.service_handler["Payload Command"] = cmd_handler.dispatch

    # Thread 1: Wait for keyboard events and send packages
    t = threading.Thread(target=thread1_keyboard)
    t.daemon = True
    t.start()

    # Thread 2: Wait for replies and print output
    thread2_network(a)


def thread1_keyboard():
    # Send user input, one line at a time
    print("----- Remote terminal ----- \n")
    while(True):
        cmd = raw_input()
        Send.send_payload_cmd(Agent.get_my_id(), DEST_ID, PayloadCommandHandler.SHELL_CMD, cmd)


def thread2_network(a):
    # Listen for incoming network packets
    a.bind_udp_sockets()
    a.run()


if __name__ == "__main__":
    main()
