#!/usr/bin/env python2.7

# Copyright SpaceVR, 2017.  All rights reserved.

import sys
import socket
from supernova import Supernova
from spacepacket import Packet
from collections import deque

# Assert Python 2.7
assert sys.version_info[0:2] == (2,7)

class Send(object):
    """ Basic packet transmission features.
    """

    # For debugging purposes, we keep a trace of all serialized packets
    # that were transmitted.
    ENABLE_TRACE = False
    TRACE_QUEUE  = deque() # append on left, pop on right

    def __init__(self):
        """Construct object
        """

    @staticmethod
    def send(packet):
        """Transmit a packet

        Args:
            packet : a ready-to-send Packet instance.

        Returns:
            Nothing
        """

        if not isinstance(packet, Packet):
            raise TypeError("Expected a Packet object")

        # If the packet were too large, we'd need to split it.  TODO.
        assert packet.data_len <= Packet.MAX_DATA_SIZE

        # Serialize the packet (including all headers and data) into a buffer of raw bytes
        buf = packet.serialize()

        if Send.ENABLE_TRACE:
            Send.TRACE_QUEUE.appendleft(buf)

        # Configure UDP socket to send to the bus
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # OK, send it!!!
        service_name = Supernova.SERVICES[packet.service-1]
        sock.sendto(buf, (Supernova.controller_ip(packet.src_node),
                          Supernova.service_send_port(service_name, packet.src_node)))
        # Close socket
        sock.close()

    @staticmethod
    def send_to_self(packet):
        """
        Transmit a packet to self.
        This is for testing purposes.

        Args:
            packet : a ready-to-send Packet instance.

        Returns:
            Nothing
        """

        # Serialize the packet (including all headers and data) into a buffer of raw bytes
        buf = packet.serialize()
        
        # Configure UDP socket to send to the bus
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # OK, send it!!!
        service_name = Supernova.SERVICES[packet.service-1]
        sock.sendto(buf, ('127.0.0.1',
                          Supernova.service_recv_port(service_name, packet.dest_node)))
        # Close socket
        sock.close()


    @staticmethod
    def send_payload_cmd(dest_payload_id, command, data):

        if isinstance(data, bytes) or isinstance(data, bytearray):
            data_len = len(data)
        elif data == None:
            data_len = 0
        else:
            raise TypeError("Data argument is not an array of bytes")

        if data_len > Packet.MAX_DATA_SIZE:
            raise ValueError("Data length too long.  TODO")

        p = Packet() # empty packet

        # --- Primary header
        # This is a bus command
        p.service = Supernova.service_id("Payload Command")
        p.dst_node = dest_payload_id
        p.pkt_type = 1 # 0: telemetry, 1: command
        # It's a single packet, so set the sequence flags appropriately.
        # TODO: support packet sequences
        p.seq_count = 0x00  # first (and last) packet
        p.seq_flags = 0x03  # first and last packet
        p.pkt_id    = command

        # --- Secondary header
        p.scid        = 0       # Spacecraft ID
        p.checksum_valid = 0x01 # Yes, valid (of course)
        p.ack         = 0       # No, not an ACK
        p.auth_count  = 0       # ???
        p.pkt_subtype = 0x00    # Unused
        p.src_node    = Supernova.get_my_id()
        p.pkt_subid   = 0x00    # Unused
        p.byp_auth    = 0x01    # Bypass authentication

        # --- Data
        p.data_len = data_len
        p.data     = data

        Send.send(p)


    @staticmethod
    def send_bus_cmd(command, data):

        if isinstance(data, bytes) or isinstance(data, bytearray):
            data_len = len(data)
        elif data == None:
            data_len = 0
        else:
            raise TypeError("Data argument is not an array of bytes")

        if data_len > Packet.MAX_DATA_SIZE:
            raise ValueError("Data length too long.  TODO")

        p = Packet() # empty packet

        # --- Primary header
        # This is a bus command
        p.service = Supernova.service_id("Bus Command")
        p.dst_node = Supernova.BUS_CONTROLLER_PAYLOAD_ID
        p.pkt_type = 1 # 0: telemetry, 1: command
        # It's a single packet, so set the sequence flags appropriately.
        # TODO: support packet sequences
        p.seq_count = 0x00  # first (and last) packet
        p.seq_flags = 0x03  # first and last packet
        p.pkt_id    = command

        # --- Secondary header
        p.scid        = 0       # Spacecraft ID
        p.checksum_valid = 0x01 # Yes, valid (of course)
        p.ack         = 0       # No, not an ACK
        p.auth_count  = 0       # ???
        p.pkt_subtype = 0x00    # Unused
        p.src_node    = Supernova.get_my_id()
        p.pkt_subid   = 0x00    # Unused
        p.byp_auth    = 0x01    # Bypass authentication

        # --- Data
        p.data_len = data_len
        p.data     = data

        Send.send(p)