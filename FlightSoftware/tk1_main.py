#!/usr/bin/env python2.7

"""
Main entry point for TK1 flight software.

Copyright SpaceVR, 2017.  All rights reserved.
"""

import sys

from agent import Agent
from payload_cmd_handler import PayloadCommandHandler
from payload_cmd_defs import PayloadCommandId

# Assert Python 2.7
assert sys.version_info[0:2] == (2,7)

class Tk1Software:

    def __init__(self):
        """ Constructor """

        self.cmds = self.create_payload_cmd_handler()
        self.agent = Agent()
        self.agent.service_handler["Payload Command"] = self.cmds.dispatch


    def create_payload_cmd_handler(self):
        """
        Create the payload command handler.

        This establishes the mapping of our command IDs to the
        code that handles them.  Adding a new payload command
        requires linking to it here.
        """
        handler = PayloadCommandHandler()

        handler.handlers.update( {
            PayloadCommandId.ABORT_CAPTURE.value : self.do_abort_capture,
            PayloadCommandId.CAPTURE_360.value   : self.do_capture_360,
            PayloadCommandId.CAPTURE_180.value   : self.do_capture_180,
        } )
        return handler

    def main(self):
        """
        Start up the Pumpkin Supernova agent and wait for commands.
        """

        print("Binding UDP sockets")
        self.agent.bind_udp_sockets()
        print("Waiting for bus")
        self.agent.run()

    @staticmethod
    def do_abort_capture(packet):
        """
        Immediately terminate any camera captures that are in progress.
        """
        raise NotImplementedError()

    @staticmethod
    def do_capture_180(packet):
        """
        Capture a 360-degree sequence.
        """
        raise NotImplementedError()

    @staticmethod
    def do_capture_360(packet):
        """
        Capture a 180-degree sequence.
        """
        raise NotImplementedError()

if __name__ == "__main__":
    Tk1Software().main()
