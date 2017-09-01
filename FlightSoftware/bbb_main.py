#!/usr/bin/env python2.7

"""
Main entry point for BBB flight software.

Copyright SpaceVR, 2017.  All rights reserved.
"""

import sys
import time
import threading
from local_enum import Enum

from agent import Agent
from payload_cmd_handler import PayloadCommandHandler
from hardware import Hardware
from flight_sm import State,Transitions
from stats import Stats

# Assert Python 2.7
assert sys.version_info[0:2] == (2,7)

class BbbSoftware:

    # Timeout after waiting for any network event
    MAIN_LOOP_TIMEOUT = 1.0 # seconds

    def __init__(self):
        self.agent = None
        self.payload_cmds = None

        # Event object to wake the flight control loop
        self.event = threading.Event()

        # Initialize components of state machine
        self.hardware = Hardware()

        # Initialize state
        self.state = State.INITIAL

        # Initialize stats
        self.stats = Stats()

    def on_telemetry(self, packet):
        # Decode as telemetry packet
        tp = TelemetryPacket(packet)
        tp.deserialize()
        # Update newest data
        self.hardware.telemetry = tp
        # Wake the main control thread
        self.event.set()

    def thread_agent(self):
        """
        This is the entry point for the thread that handles
        all communication with the Supernova bus.
        It communicates back to the main ConnOps loop via
        multithreaded Event objects.
        """
        while True:
            try:
                # Set up the command handlers
                self.agent = Agent()
                self.agent.service_handler["Telemetry Packet"] = self.on_telemetry

                # Run
                self.agent.bind_udp_sockets()
                self.agent.run() # should never exit

            except Exception as ex:
                # NOTE: It is an error to ever reach this line.
                # Catch and swallow all exceptions.
                1 + 1

            # NOTE: It is an error to ever reach this line.
            self.agent_errors = self.agent_errors + 1

    def main(self):
        # Launch the thread that communicates with the Supernova bus.
        agent_thread = threading.Thread(target=self.thread_agent)
        agent_thread.daemon = True
        agent_thread.start()

        # Run the flight state machine program
        while True:
            self.event.wait(BbbSoftware.MAIN_LOOP_TIMEOUT)
            self.state = Transitions.next(self.state)


if __name__ == "__main__":
    BbbSoftware().main()
