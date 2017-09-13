"""
Hardware layer implementation for flight software.

Copyright SpaceVR, 2017.  All rights reserved.
"""

import time
import sys
import struct

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

        # TODO: Does the sun-pointing mode need an offset to for our solar panel angle?
        self.mai_set_mode(7)

    def point_cameras_to_ground(self):
        """
        Turn the spacecraft.
        Point the cameras toward the -Z nadir.
        """
        # TODO: Does this actually point the antenna to ground?
        self.mai_set_mode(3)

    def point_antenna_to_transmit(self):
        """
        Turn the spacecraft.
        Point the X-band antennas toward the ground station.
        """

        # XXX: Presumable we've stored the latest ground station coordinates.
        # self.mai_set_latlong(longitude, latitude, start_time, stop_time):

        # XXX: Example
        self.mai_set_latlong(75, 50, 0, 999999999)

        self.mai_set_mode(4)

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

    def mai_set_mode(self, mode):
        """
        Sets the ACDACS operational mode.

        Arguments:
            mode - integer between 0 and 9, inclusive

        More details:
            Mode 0: Test mode. The system receives and executes wheel torque and speed commands, and
                dipole commands manually from the user. The magnetometer and sun sensors are sampled and
                attitude is computed. No closed loop control is performed. This is intended for ground test and
                system check-out on-orbit.

            Mode 1: Acquisition mode. The system computes magnetic coil commands to reduce spacecraft
                rate as measured by the magnetometer (or external magnetometer readings). Note only torques
                perpendicular to the current magnetic field can be produced. Over an orbit, spacecraft rates are
                ground general maintained to 2x orbit rate (average inertial rate of magnetic field). The magnetometer and
                sun sensors are sampled and attitude is computed. Any reaction wheel speeds from normal
                operation or bias operation will be commanded to zero, inducing spacecraft speeds if acquisition
                mode is commanded (note that this does not apply acquisition/Bdot operation temporarily applied
                due to temporary loss of 3-axis attitude from other modes below. When power is initially
                applied, the system enters Acquisition Mode.

            Mode 3: Normal Mode. A zero momentum, magnetic momentum management mode. The
                system endeavors to maintain a nadir pointing attitude based on Earth sensor/magnetometer or sun
                sensor/magnetometer attitude determination. An offset quaternion may also be commanded with
                the Qbo command. ADACS firmware will be set to maintain the desired LVLH attitude (spacecraft
                axes can be selected based on desired mounting of the ADACS and sensor orientations if
                communicated to MAI). The system computes reaction wheel torque commands by a quaternion
                feedback control law. Momentum is managed magnetically to maintain offset reaction wheel
                speeds. As reaction wheel speeds cannot be maintained at very low speeds (<20-40 RPM), if
                normal mode is planned as a full-time operational mode, offset reaction wheel speeds are
                recommended (requires magnetic torqueing to maintain offset wheel speeds).
                If a valid 3-axis attitude is not available, normal mode will revert to b-dot mode, as with acquisition
                mode, with the exception that reaction wheel speeds are maintained at the last
                commanded/integrated speed (not commanded to zero speed as with the commanded acquisition
                mode). As with other closed loop control modes, if the magnetic field is not valid, closed loop
                control is disabled.

            Mode 4: Lat/Long Mode. This mode allows the user to select a fixed latitude and longitude at
                some time in the future (defined as a start and stop GPS time) loaded with a separate lat/long
                command. Valid 3-axis attitude is required to perform pointing, either with Sun/Mag or
                Earth/Mag. The offset pointing from nadir, except for short duration lat/long modes will generally
                violate nadir pointing requirements for Earth/Mag, thus, care should be taken to command lat/long
                outside of eclipse periods.
                When this ACS mode is selected, the current attitude is used until the start time (which is expected
                to be normal mode to limit slew times to the lat/long). Thus, the selected lat/long point on the
                Earth surface should be in view of the satellite as it flies over during the start/stop time period. The
                control system maintains nominal pointing to the lat/long point, which can also be offset with the
                Qbo offset quaternion, if commanded. After the stop time occurs, control is automatically
                transitioned to normal mode.

            Mode 5: QbX Mode. A momentum biased, Bdot damping mode for the QbX satellite. The X
                axis wheel is command to a constant speed. Aerodynamic stabilization points the satellite into the
                ram. Bdot damping orients the pitch axis to the orbit normal.

            Mode 7: Normal-Sun Mode. This mode provides nadir pointing for the primary axis, and rotates
                about the nadir axis to optimize solar pointing for a secondary axis (currently an axis 45 degrees
                between the X and Y axes, although this can be modified in firmware based on selected
                configuration). Rotation about the nadir axis is controlled from +/-30 degrees of the sun projected
                onto the orbit plane to prevent high rates due to singularity or near singularities.

            Mode 8: Lat/Long-Sun Mode. This mode operates similar to normal Lat/Long mode, with the
                exception of rotation about the primary axis, which uses the normal-Sun mode logic to optimize
                solar pointing. As with normal Lat/Long, the ACS mode used prior to the start time is maintained,
                and control is autonomously switched to Normal-Sun mode after the stop time. This mode shares
                the same Lat/Long configuration command with normal Lat/Long.

            Mode 9: Qinertial Mode. This mode provides inertial pointing using a commanded quaternion
                as part of the mode parameters and the current 3-axis attitude knowledge quaternion. As the
                requirements for Earth/mag 3-axis attitude moves at orbit rate, it is likely this mode will be used
                with Sun/mag and thus will lose inertial pointing during eclipse.
        """

        DATA_LEN = 40 #always
        data = bytearray(DATA_LEN)

        syncbyte    = 0xEB90 # TODO: the Pumpkin comments contain some confusing statements about endianness
        commandID   = 0x00   # SET_MODE

        # Create data
        struct.pack_into('<HBB', data, 0, syncbyte, commandID, mode) 

        # Add data checksum.  (This is different than the packet checksum.)
        checksum = 0xFFFF & sum(data[0:DATA_LEN]) 
        struct.pack_into('<H', data, 38, checksum) 

        Send.send_bus_cmd(BusCommands.MAI_CMD, data)


    def mai_set_latlong(self, longitude, latitude, start_time, stop_time):
        """
        Sets the programmed latitude and logitude mode.

        Description: Loads an Earth latitude and longitude target and start and stop time (in GPS seconds)
            in which to operate. This command is shared with both normal Lat/Long and Lat/Long sun (i.e.
            either ACS mode will use the Lat/Long start/stop time loaded to perform it's pointing).
            The Lat//Long or Lat/Long-Sun ACS mode needs to be commanded to use this data. The ACS
            mode does not change until the start time is reached. The selected Lat/Long ACS mode will then
            start. When the stop time is reached, the ACS mode automatically returns to either normal (nadir)
            or normal-Sun ACS mode.

        TODO: what if the start time is before the current time?

        Arguments:
            longitude: Geodetic Longitude in ECEF +180:-180 deg = +32767:-32767 0.005493332 deg/lsb
            latitude:  Geodetic Latitude in ECEF +90:-90 deg = +16384:-16384 0.005493332 deg/lsb
            start_time: gul_GPStime_LLstart (sec)
            stop_time:  gul_GPStime_LLend (sec)
        """

        DATA_LEN = 40 #always
        data = bytearray(DATA_LEN)

        syncbyte    = 0xEB90 # TODO: the Pumpkin comments contain some confusing statements about endianness
        commandID   = 0x51   # "torque command" (says manual)

        # Create data
        struct.pack_into('<HBhhLL', data, 0, syncbyte, commandID, 
                         longitude, latitude,
                         start_time, stop_time)

        # Add data checksum.  (This is different than the packet checksum.)
        checksum = 0xFFFF & sum(data[0:DATA_LEN]) 
        struct.pack_into('<H', data, 38, checksum) 

        Send.send_bus_cmd(BusCommands.MAI_CMD, data)


    def mai_set_time(self, gpstime):
        """
        Sets the ADACS clock.

        Arguments:
            gpstime - GPS time is a linear count of seconds elapsed since 0h Jan 6, 1980.
        """

        DATA_LEN = 40 #always
        data = bytearray(DATA_LEN)

        syncbyte    = 0xEB90 # TODO: the Pumpkin comments contain some confusing statements about endianness
        commandID   = 0x44   # set GPS time

        # Create data
        struct.pack_into('<HBL', data, 0, syncbyte, commandID, 
                         gpstime)

        # Add data checksum.  (This is different than the packet checksum.)
        checksum = 0xFFFF & sum(data[0:DATA_LEN]) 
        struct.pack_into('<H', data, 38, checksum) 

        Send.send_bus_cmd(BusCommands.MAI_CMD, data)



    def mai_reset(self):
        """
        Resets the ADACS.
        """

        DATA_LEN = 40 #always
        data = bytearray(DATA_LEN)

        # --- First command

        syncbyte    = 0xEB90 # TODO: the Pumpkin comments contain some confusing statements about endianness
        commandID   = 0x5A   # Reset step 1

        # Create data
        struct.pack_into('<HB', data, 0, syncbyte, commandID)

        # Add data checksum.  (This is different than the packet checksum.)
        checksum = 0xFFFF & sum(data[0:DATA_LEN]) 
        struct.pack_into('<H', data, 38, checksum) 

        Send.send_bus_cmd(BusCommands.MAI_CMD, data)

        # --- Second command

        commandID   = 0xF1   # Reset step 2

        # Create data
        struct.pack_into('<HB', data, 0, syncbyte, commandID)

        # Add data checksum.  (This is different than the packet checksum.)
        checksum = 0xFFFF & sum(data[0:DATA_LEN]) 
        struct.pack_into('<H', data, 38, checksum) 

        Send.send_bus_cmd(BusCommands.MAI_CMD, data)

