#!/usr/bin/env python2.7

"""
Run Agent for testing/development purposes.

This is used to expose and test common payload commands.

Copyright SpaceVR, 2017.  All rights reserved.
"""

# --- Import standard modules ---

# System-specific functions.  Used to check Python version.
import sys

# --- Import custom modules ---

# Agent: manages incoming network traffic from the Supernova bus.
from agent import Agent
# Supernova: defines Supernova helpers and constants.
from supernova import Supernova
# Supernova: defines format of Supernova packet data.
from spacepacket import Packet
# PayloadCommandHandler: manages payload-specific commands.
from payload_cmd_handler import PayloadCommandHandler

# Assert Python 2.7
assert sys.version_info[0:2] == (2,7)

def main():
    """ Main entry point for executable. """

    a = Agent()

    cmd_handler = PayloadCommandHandler()

    # Register some callbacks
    a.service_handler["Payload Command"] = cmd_handler.dispatch;
    #a.service_handler["Bus Telemetry"] = cmd_handler.print_it;

    print("Binding UDP sockets")
    a.bind_udp_sockets()

    print("Waiting for bus")
    a.run()

if __name__ == "__main__":
    main()
