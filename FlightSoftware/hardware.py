"""
Hardware layer implementation for flight software.

Copyright SpaceVR, 2017.  All rights reserved.
"""

import time
import sys

from send import Send
from payload_cmd_defs import PayloadCommandId

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

    def __init__(self):
        self.telemetry = None
        self.start_time = time.time() # Seconds since epoch when the flight software started.

    # --- Helpers and other stuff

    PAYLOAD_BUS_ID = 1

    # --- BEGIN Hardware API
    #
    # Implementing a method here means that a corresponding version should be added
    # to hardware_mock.py (and of course a test written, too).

    def deploy_solar_panels(self):
        """
        Send a command to the bus to trigger solar panel deployment.
        """
        raise NotImplementedError()


    def turn_on_cpm(self):
        """
        Send a command to the power manager to power-up the TK1 payload computer.
        """
        raise NotImplementedError()


    def turn_off_cpm(self):
        """
        Send a command to the power manager to power-up the TK1 payload computer.
        """
        raise NotImplementedError()


    def turn_on_cameras(self):
        """
        Send a command to the power manager to power-up the camera hardware.
        """
        raise NotImplementedError()


    def turn_on_cameras(self):
        """
        Send a command to the power manager to power-up the camera hardware.
        """
        raise NotImplementedError()


    def run_capture_360(self, num_frames):
        """
        Send a command to the payload to run a 360-degree (eight camera) capture
        for the specified number of frames.
        """
        raise NotImplementedError()


    def run_capture_180(self, num_frames):
        """
        Send a command to the payload to run a 180-degree (four camera) capture
        for the specified number of frames.
        """
        raise NotImplementedError()


    def send_payload_noop(self):
        """
        Send a no-op command to the payload.
        """
        Send.send_payload_cmd(Hardware.PAYLOAD_BUS_ID,
                              PayloadCommandId.NO_OP.value,
                              None) # no data        

    def abort_capture(self):
        """
        Send a command to the payload computer to abort any image capture operation.
        """
        Send.send_payload_cmd(Hardware.PAYLOAD_BUS_ID,
                              PayloadCommandId.ABORT_CAPTURE.value,
                              None) # no data
