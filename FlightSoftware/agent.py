"""
Agent module

Copyright SpaceVR, 2017.  All rights reserved.
"""

import socket
import time
import select
import sys

from spacepacket import Packet,TelemetryPacket,AckPacket
from supernova import Supernova

# Assert Python 2.7
assert sys.version_info[0:2] == (2,7)

class Agent:
    """ Receive and process traffic on Supernova bus.

    This class exists to abstract out the generic parts of receiving,
    processing, and handling command packets.  It avoids any code
    that is specific to a particular payload.

    Properties:
        payload_id : The payload ID for this agent.
                Each payload ID has a very specific role.  See the Supernova spec.
                This should be set appropriately by the caller.
    """

    TIMEOUT = 300 # seconds
    DEBUG = False

    def __init__(self):
        """ Initialize an Agent object

        All service handlers are initially set to do nothing.
        """

        self.payload_id = Supernova.get_my_id()
        self.service_sock = {}

        # Service handler functions.
        # Map of service name to method.
        self.service_handler = {
            "Payload Command"   : Agent.do_nothing,
            "Payload Telemetry" : Agent.do_nothing,
            "Bus Command"       : Agent.do_nothing,
            "Telemetry Packet"  : Agent.do_nothing,
            "Telemetry Stream"  : Agent.do_nothing,
            "Data Storage"      : Agent.do_nothing,
            "Data Downlink"     : Agent.do_nothing,
            "Data Upload"       : Agent.do_nothing,
            "Time"              : Agent.do_nothing,
        }


    @staticmethod
    def do_nothing(packet):
      """ Do nothing and return

      This exists as a default handler for services that this agent can ignore.

      Args:
          packet : A Packet instance

      Returns:
          Nothing.
      """

      return

    @staticmethod
    def raise_exception(packet):
      """ Raise an exception.

      This is for testing purposes.

      Args:
          packet : A Packet instance

      Returns:
          Nothing.
      """

      if Agent.DEBUG: print("Raising an exception")
      raise Exception()

    @staticmethod
    def print_it(packet):
        if packet.service == Supernova.service_id("Telemetry Packet"):
            tp = TelemetryPacket(packet)
            tp.deserialize()
            tp.printout()
        else:
            print("=== Begin ===")
            print(packet.data)
            print("===  End  ===")

    def bind_udp_sockets(self):
        """ Bind UDP sockets to appropriate ports

        Effects:
            self.supernova_sock : set to a dict of interface names -> socket instances
        """

        for i in Supernova.SERVICES:
            self.service_sock[i] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            try:
                self.service_sock[i].bind((Supernova.payload_ip(self.payload_id),
                                           Supernova.service_recv_port(i, self.payload_id)))
            except Exception as e:
                print("Error binding socket for %s service: %s\n" % (i, repr(e)))
                # TODO: (failsafe) wait and retry


    def close(self):
        """ Close associated resources.

        In production, this isn't generally needed (for the continuously-running agent),
        but it's very useful for testing.
        """

        for i in Supernova.SERVICES:
            self.service_sock[i].close()


    def run(self):
        """ Receive and process incoming packets

        As each UDP packet is received, it is deserialized as a space packet.  Based on
            the destination service (as determined by which port it was sent to), look
            up a method in the self.service_handler map and pass it to that method.

        This method will continue forever.

        Precondition:
            self.supernova_sock should contain a set of bound sockets (e.g. by
                calling bind_udp_sockets first)
        """

        if Agent.DEBUG: print("Running main loop")

        while True:
            # Select function monitors all inputs and waits the specified timeoue period. Once a port is readable (has data to read) it is returned in the readable array.
            readable, writable, exceptional = select.select(self.service_sock.values(), [], [], Agent.TIMEOUT)
            if readable != []:
                # Read each port with data available
                for sock in readable:
                    data, addr = sock.recvfrom(Packet.PACKET_SIZE)

                    # Deconstruct packets to retrieve header data and packet data
                    packet = Packet()
                    packet.deserialize(data)

                    # Parse data based on packet type and service
                    if packet.ack == 1:
                        # If packet is an ACK packet, data is parsed the same regardless of port
                        ack = AckPacket(packet)
                        if Agent.DEBUG: print("Received an ack")
                    else:
                        if Agent.DEBUG: print("Received a packet!")

                        for i in Supernova.SERVICES:
                            if sock == self.service_sock[i]:
                                self.service_handler[i](packet)

            # Timeout condition
            if readable == []:
                print('\nTimed out at ' + str(timeout) + ' seconds')
