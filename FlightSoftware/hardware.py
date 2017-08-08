#!/usr/bin/env python2.7

"""
Hardware layer implementation for BBB flight software.

Copyright SpaceVR, 2017.  All rights reserved.
"""

import time
import sys

from send import Send

# Assert Python 2.7
assert sys.version_info[0:2] == (2,7)

class Hardware:
    """
    Hardware implementation layer.

    This class encapsulates "how" to perform any hardware activies.
    A typical activity consists of constructing and sending a bus or payload
    command to the Supernova software.

    It also stores the latest telemetry summary packet, as received from the
    Supernova bus.
    """

    # There is a singleton instance of this class, set when it is constructed
    # during the initialization of the top-level software.
    # (And for testing purposes, a hardware mock instance can be injected.)
    SINGLETON = None

    @staticmethod
    def get():
        """ Return the global singleton instance. """
        return Hardware.SINGLETON

    def __init__(self):
        Hardware.SINGLETON = self

        self.telemetry = None
        self.start_time = time.time() # Seconds since epoch when the flight software started.

    # --- BEGIN Hardware API
    #
    # Implementing a method here means that a corresponding version should be added
    # to hardware_mock.py (and of course a test written, too).

    def turn_on_cpm(self):
        """
        Send a command to the power manager to power-up the TK1 payload computer.
        """
        None # TODO


    def turn_off_cpm(self):
        """
        Send a command to the power manager to power-up the TK1 payload computer.
        """
        None # TODO


    def turn_on_cameras(self):
        """
        Send a command to the power manager to power-up the camera hardware.
        """
        None # TODO


    def turn_on_cameras(self):
        """
        Send a command to the power manager to power-up the camera hardware.
        """
        None # TODO


    def run_capture_360(self, num_frames):
        """
        Send a command to the payload to run a 360-degree (eight camera) capture
        for the specified number of frames.
        """
        None # TODO


    def run_capture_180(self, num_frames):
        """
        Send a command to the payload to run a 180-degree (four camera) capture
        for the specified number of frames.
        """
        None # TODO


    def abort_capture(self):
        """
        Send a command to the payload computer to abort any image capture operation.
        """
        Send.send_payload_command()
