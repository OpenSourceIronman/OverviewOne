#!/usr/bin/env python2.7

"""
Main entry point for TK1 flight software.

Copyright SpaceVR, 2017.  All rights reserved.
"""

import sys
import subprocess

from agent import Agent
from payload_cmd_handler import PayloadCommandHandler
from payload_cmd_defs import PayloadCommandId

# Assert Python 2.7
assert sys.version_info[0:2] == (2,7)

class Tk1Main:

    DEBUG = False

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
            PayloadCommandId.ABORT_CAPTURE.value : Tk1Main.do_abort_capture,
            PayloadCommandId.CAPTURE_360.value   : Tk1Main.do_capture_360,
            PayloadCommandId.CAPTURE_180.value   : Tk1Main.do_capture_180,
            PayloadCommandId.CAMERA_POWER_ON.value  : Tk1Main.do_cameras_on,
            PayloadCommandId.CAMERA_POWER_OFF.value : Tk1Main.do_cameras_off,
        } )

        if Tk1Main.DEBUG: PayloadCommandHandler.DEBUG = True

        return handler

    def main(self):
        """
        Start up the Pumpkin Supernova agent and wait for commands.
        """

        if Tk1Main.DEBUG: print("Binding UDP sockets")
        self.agent.bind_udp_sockets()
        if Tk1Main.DEBUG: print("Waiting for bus")
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

    @staticmethod
    def do_cameras_on(packet):
        """
        Power on the cameras.
        """

        if Tk1Main.DEBUG: print("Powering on cameras")

        try:
           # Maybe:
           # subprocess.check_call(["../GPIOControl", "1"])
           # XXX: Do we even have a program to turn on/off the pins?
           None
        except Exception as e:
           # TODO: log error somewhere appropriate
           None

        raise NotImplementedError()

    @staticmethod
    def do_cameras_off(packet):
        """
        Power off the cameras.
        """

        if Tk1Main.DEBUG: print("Powering off cameras")

        try:
           # Maybe:
           # subprocess.check_call(["../GPIOControl", "1"])
           # XXX: Do we even have a program to turn on/off the pins?
           None
        except Exception as e:
           # TODO: log error somewhere appropriate
           None

        raise NotImplementedError()

if __name__ == "__main__":
    Tk1Main().main()
