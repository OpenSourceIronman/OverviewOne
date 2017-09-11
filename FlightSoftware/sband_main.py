#!/usr/bin/env python2.7

"""
Main entry point for BBB flight software.

Copyright SpaceVR, 2017.  All rights reserved.
"""

import sys
# sys.path.insert(1, "../../Packages")
from swiftradio.clients import SwiftRadioEthernet
from swiftradio.clients import SwiftUDPClient
import swiftradio

from send import Send

# Assert Python 2.7
assert sys.version_info[0:2] == (2,7)

class SbandMain:

    def __init__(self):
        None

    def main(self):
        # Instantiate a UDP connection to the uplink port.

        # TODO: Need to utilize telemetry command framing
        try:
            udp = SwiftUDPClient(args.ip_addr, args.bind_port, args.port)
            udp.connect()
        except:
            print "Could not open a udp client for the provided IPv4 address and port."
            sys.exit(1)
        
        # Buffer in which to accumulate incoming data
        buf = bytearray(0)

        # How many bytes are we expecting to read?
        # If this below zero, then we haven't synchronized. 
        expect = 0

        while True:
            data = udp.read(SRX_PKTSIZE)

            # TODO: This should be a self-contained packet.
            # Verify.
        
        udp.disconnect()

if __name__ == "__main__":
    SbandMain().main()
