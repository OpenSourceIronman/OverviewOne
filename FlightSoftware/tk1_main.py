#!/usr/bin/env python2.7

"""
Main entry point for TK1 flight software.

Copyright SpaceVR, 2017.  All rights reserved.
"""

import sys

from agent import Agent
from payload_cmd_handler import PayloadCommandHandler

# Assert Python 2.7
assert sys.version_info[0:2] == (2,7)

class Tk1Software:

    def __init__(self):
        self.cmds = PayloadCommandHandler()

        self.agent = Agent()
        self.agent.service_handler["Payload Command"] = self.cmds.dispatch

    def main(self):
        print("Binding UDP sockets")
        self.agent.bind_udp_sockets()
        print("Waiting for bus")
        self.agent.run()


if __name__ == "__main__":
    Tk1Software().main()
