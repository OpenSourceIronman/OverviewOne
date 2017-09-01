"""
Hardware layer implementation for flight software.

Copyright SpaceVR, 2017.  All rights reserved.
"""

import time
import sys

from send import Send
from payload_cmd_defs import PayloadCommandId
from supernova import BusCommands

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

    def time(self):
        return time.time() - self.start_time

    # --- BEGIN Hardware API
    #
    # Implementing a method here means that a corresponding version should be added
    # to hardware_mock.py (and of course a test written, too).

    def deploy_solar_panels(self):
        """
        Send a command to the bus to trigger solar panel deployment.

        TODO: should the burns happen sequentially or at once?
        """

        burn_time = 10 #seconds

        for num in range(1,5):
            Send.send_bus_cmd(BusCommands.PRM_CMD,
                              bytearray([0x05, num, 0x00]) )
            Send.send_bus_cmd(BusCommands.PRM_CMD,
                              bytearray([0x07, num, 0x00]) )
            Send.send_bus_cmd(BusCommands.PRM_CMD,
                              bytearray([0x09, num, burn_time]) )

            # XXX: On the simulator, a small delay is required or the
            # XXX: fourth wire fails to fire.
            time.sleep(0.1)


    def power_cpm(self, enable):
        """
        Power on/off the TK1 payload computer.

        Send a command to the power manager.
        """

        # Maybe...
        if (enable):
            # Send.send_bus_cmd(BusCommands.PIM_POWER_ON,                          
            #                   bytearray([0x01]) )  # <--- This is the port ID
            None
        else:
            # Send.send_bus_cmd(BusCommands.PIM_POWER_OFF,                          
            #                   bytearray([0x01]) )  # <--- This is the port ID
            None
    
        raise NotImplementedError()


    def power_gps(self, enable):
        """
        Power on/off the GPSRM1.
        """

        if (enable):
            None # TODO
        else:
            None # TODO

        raise NotImplementedError()


    def power_cameras(self, enable):
        """
        Power on/off the camera hardware.
        """

        if (enable):
            Send.send_payload_cmd(Hardware.PAYLOAD_BUS_ID,
                                  PayloadCommandId.CAMERA_POWER_ON,
                                  None )
        else:
            Send.send_payload_cmd(Hardware.PAYLOAD_BUS_ID,
                                  PayloadCommandId.CAMERA_POWER_OFF,                     
                                  None )


    def power_eyestar(self, enable):
        """
        Power on/off the L-band globalstar radio.

        Usage: 0.8 W
        """

        if (enable):
            None # TODO
        else:
            None # TODO

        raise NotImplementedError()

    def run_capture_360(self, num_frames):
        """
        Send a command to the payload to run a 360-degree (eight camera) capture
        for the specified number of frames.
        """

        Send.send_payload_cmd(Hardware.PAYLOAD_BUS_ID,
                              PayloadCommandId.CAPTURE_360,
                              bytearray([num_frames]) ) # no data

    def run_capture_180(self, num_frames):
        """
        Send a command to the payload to run a 180-degree (four camera) capture
        for the specified number of frames.
        """

        Send.send_payload_cmd(Hardware.PAYLOAD_BUS_ID,
                              PayloadCommandId.CAPTURE_180,
                              bytearray([num_frames]) ) # no data


    def abort_capture(self):
        """
        Send a command to the payload computer to abort any image capture operation.
        """
        Send.send_payload_cmd(Hardware.PAYLOAD_BUS_ID,
                              PayloadCommandId.ABORT_CAPTURE,
                              None) # no data

    def point_cells_to_sun(self):
        """
        Turn the spacecraft.
        Point the solar cells toward the sun.

        Turn on the MAI-400. (?)
        """
        raise NotImplementedError()

    def point_cameras_to_ground(self):
        """
        Turn the spacecraft.
        Point the cameras toward the -Z nadir.
        """
        raise NotImplementedError()

    def point_antenna_to_transmit(self):
        """
        Turn the spacecraft.
        Point the X-band antennas toward the ground station.
        """
        raise NotImplementedError()

    def transmit_health_data(self):
        """
        Transmit a health overview packet over GlobalStar network.
        """
        raise NotImplementedError()

    # --- BEGIN Testing API

    def flash_pim_led(self):
        """
        Flash the LED on the PIM module.
        """

        # Maybe...
        # Send.send_bus_cmd(BusCommands.PIM_CTRL,                          
        #                   bytearray([0x07, 0x00]) )  # LED_FLASH

        raise NotImplementedError()


    def run_payload_noop(self):
        """
        Send a no-op command to the payload.
        """
        Send.send_payload_cmd(Hardware.PAYLOAD_BUS_ID,
                              PayloadCommandId.NO_OP,
                              None) # no data        

