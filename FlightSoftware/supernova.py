# Copyright SpaceVR, 2017.  All rights reserved.

import sys, os

# Assert Python 2.7
assert sys.version_info[0:2] == (2,7)

class Supernova:
    ''' Information about supernova service names and port mappings
    '''

    SUPERNOVA_ID_ENV_VAR = "SUPERNOVA_ID"

    # Ordered list of Supernova bus services
    SERVICES = [
        "Payload Command",
        "Payload Telemetry",
        "Bus Command",
        "Telemetry Packet",
        "Telemetry Stream",
        "Data Storage",
        "Data Downlink",
        "Data Upload",
        "Time"
    ]

    # Payload ID to use to direct commands at the bus controller itself
    BUS_CONTROLLER_PAYLOAD_ID = 0x30

    # Cached map of service names to numeric IDs
    _service_id = None

    @staticmethod
    def controller_ip(payload_id):
        """ Return the IP address of the Supernova bus controller.

        It's unclear what the Supernova software expects.
        At least when the packet originates from the same
        machine, it throws an error UDP_ERR_MSG_IP if the IP is
        192.168.1.70 but accepts the loopback address 127.0.0.1 ok.

        TBD what is appropriate when the packet originates from
        a different IP (.... but presumably the IP).

        Args:
            payload_id : an integer from 1..4

        Returns:
            An IP address string.
        """
        if payload_id == 3:
            return '127.0.0.1'
        elif payload_id == 4:
            return '127.0.0.1'

        return '192.168.1.70' # I presume

    @staticmethod
    def payload_ip(payload_id):
        """ Get the IP address of a payload by its ID.

        The Supernova spec defines specific IPs for each payload ID.

        Args:
            payload_id : an integer from 1..4

        Returns:
            An IP address string.

        Exceptions:
            ValueError : if unexpected payload ID value.
        """

        if payload_id == 1:
            return '192.168.1.71'
        elif payload_id == 2:
            return '192.168.1.72'
        elif payload_id == 3:
            return '127.0.0.1'
        elif payload_id == 4:
            return '127.0.0.1'

        raise ValueError("Unexpected payload ID.  No known IP mapping")

    @staticmethod
    def service_id(name):
        if not Supernova._service_id:
            Supernova._service_id = {}
            id = 1
            for n in Supernova.SERVICES:
                Supernova._service_id[n] = id
                id = id + 1

        if name not in Supernova._service_id:
            raise ValueError("Unrecognized service")

        return Supernova._service_id[name]

    @staticmethod
    def service_recv_port(name, payload_id):
        return 0x8000 + 0x0100*payload_id + 2*Supernova.service_id(name)

    @staticmethod
    def service_send_port(name, payload_id):
        return 0x8000 + 0x0100*payload_id + 2*Supernova.service_id(name) + 1

    @staticmethod
    def get_my_id():
        """ 
        Returns the Supernova bus ID of this process.

        Read value from an environment variable, and exit with error if it is not set.
        """

        try:
            payload_id = int(os.getenv(Supernova.SUPERNOVA_ID_ENV_VAR)) # The Supernova ID of this process.
            if payload_id < 1 or payload_id > 4:
                raise ValueError()
        except Exception as e:
            print("Must set the "+Supernova.SUPERNOVA_ID_ENV_VAR+" environment variable to the bus ID.\n")
            print("Valid values are between 1 and 4.\n")
            sys.exit(1)

        return payload_id


class BusCommands(object):
    """ Send commands to the Supernova bus
    """

    # --- Command Definitions ------------------------

    NO_OP = 0x10
    """
    Summary:     No operation
    Description: This command does nothing except update the command execution statistics.

    Data:
        None
    """

    PIM_PWR_ON = 88
    """
    Summary:     PIM Power On
    Description: Power on the selected PIM channel by sending MCU commands to the PIM.

    Data:
        UInt8 - channel
    """

    PIM_PWR_ON = 89
    """
    Summary:     PIM Power Off
    Description: Power off the selected PIM channel by sending MCU commands to the PIM.

    Data:
        UInt8 - channel
    """

    PIM_CTRL = 90
    """
    Summary:     PIM Control
    Description: Send control commands to the PIM MCU based on the action specified in the
                 PIM_ACTION parameter. Some actions require an additional parameter value
                 provided in PIM_PARAM.

    Data:
        UInt8 - action
        UInt8 - param
    """

    PRM_CMD = 0xAB
    """
    Summary:     PRM Control
    Description: Burn wires for solar panels.

    Data:
        UInt8 - command
           * 0x05 = ENABLE
           * 0x07 = ARM
           * 0x09 = FIRE
        UInt8 - prm number
        UInt8 - time (seconds)
    """
