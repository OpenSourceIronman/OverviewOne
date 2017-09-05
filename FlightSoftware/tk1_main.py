#!/usr/bin/env python2.7

"""
Main entry point for TK1 flight software.

Copyright SpaceVR, 2017.  All rights reserved.
"""


import time
import sys
import os
import subprocess
import signal

from capture_main import CaptureMain
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

        self.capture_proc = None


    def create_payload_cmd_handler(self):
        """
        Create the payload command handler.

        This establishes the mapping of our command IDs to the
        code that handles them.  Adding a new payload command
        requires linking to it here.
        """
        handler = PayloadCommandHandler()

        handler.handlers.update( {
            PayloadCommandId.ABORT_CAPTURE : self.do_abort_capture,
            PayloadCommandId.CAPTURE_360   : self.do_capture_360,
            PayloadCommandId.CAPTURE_180   : self.do_capture_180,
            PayloadCommandId.CAPTURE_CUSTOM: self.do_capture_custom,
            PayloadCommandId.CAMERA_POWER_ON  : self.do_cameras_on,
            PayloadCommandId.CAMERA_POWER_OFF : self.do_cameras_off,
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


    def do_abort_capture(self, packet):
        """
        Immediately terminate any camera captures that are in progress.
        """

        if self.capture_proc and not self.capture_proc.poll():
            if Tk1Main.DEBUG: print("Aborting capture")
            # Send a SIGTERM to capture process
            self.capture_proc.send_signal(signal.SIGTERM)
        else:
            if Tk1Main.DEBUG: print("No capture to abort")



    def do_capture_180(self, packet):
        """
        Capture a 180-degree sequence.
        """

        if (packet.data_len <= 8):
            # Ignore bad packets.
            return

        (num_frames, start_time) = struct.unpack("ll", packet.data)

        self.capture(4, num_frames, start_time)


    def do_capture_360(self, packet):
        """
        Capture a 360-degree sequence.
        """

        if (packet.data_len <= 8):
            # Ignore bad packets.
            return

        (num_frames, start_time) = struct.unpack("ll", packet.data)

        self.capture(8, num_frames, start_time)


    def do_capture_custom(self, packet):
        """
        Capture a custom sequence.
        """

        if (packet.data_len <= 14):
            # Ignore bad packets.
            return

        (num_cameras, num_frames,  start_time, width, height) 
             = struct.unpack("hhlll", packet.data)

        self.capture(num_cameras, num_frames, start_time, widht, height)


    def do_cameras_on(self, packet):
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


    def do_cameras_off(self, packet):
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

    # -------------------------------------------------------

    def capture(self, num_cameras, num_frames, start_time,
                      width=None, height=None):

        if self.capture_proc and not self.capture_proc.poll():
            # Previous capture process is still running.

            # TODO: Need to consider what the behavior should be here.
            if Tk1Main.DEBUG: print("Previous capture still in progress.")
            return

        if Tk1Main.DEBUG:
            print("Starting new capture.  Cameras=%d, Frames=%d" %
                  (num_cameras, num_frames))

        cmdline = ['./capture_main.py',
                   '--frames', str(num_frames),
                   '--cameras', str(num_cameras)
                  ]

        if start_time:
            cmdline.extend(['--timestamp', str(start_time)])

        if width and height:
            cmdline.extend(['--size', str(width), str(height)])

        # Run capture in the background
        self.capture_proc = subprocess.Popen(cmdline)


    def delete_all(self):
        """
        Delete all files in the CaptureMain.FILE_ROOT directory.
        """

        num_deleted = 0
        for filename in os.listdir(CaptureMain.FILE_ROOT):
            os.delete(filename)
            num_deleted += 1

        if Tk1Main.DEBUG: print("Deleted %d files" % num_deleted)


if __name__ == "__main__":
    # Was --debug passed on the command line?
    if "--debug" in sys.argv:
	Tk1Main.DEBUG = True

    Tk1Main().main()
