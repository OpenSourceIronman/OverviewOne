import pytest
import sys, os
import threading
import socket
import time

from agent import Agent
from spacepacket import Packet
from supernova import Supernova
from send import Send

# Assert Python 2.7
assert sys.version_info[0:2] == (2,7)

def test_handlers():
    p = Packet()

    Agent.do_nothing(None)

    Agent.print_it(p)
    p.service = Supernova.service_id("Telemetry Packet")
    p.data_len = 266
    p.data = bytearray(266)
    Agent.print_it(p)

def test_socket_bind_error():
    # Block socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((Supernova.payload_ip(Supernova.get_my_id()),
               Supernova.service_recv_port("Payload Command", Supernova.get_my_id())) )

    a = Agent()
    a.bind_udp_sockets() # will fail gracefully
    a.close()

    sock.close()

def test_startup_and_shutdown():
    # Create an agent that throws an exception when it receives
    # a payload command packet.
    a = Agent()
    a.bind_udp_sockets()
    a.service_handler["Payload Command"] = Agent.raise_exception

    # Run agent.
    t = threading.Thread(target=Agent.run, args=(a,))
    t.daemon = True
    t.start()

    # Send an ACK packet
    p = Packet()
    p.service = Supernova.service_id("Payload Command")
    p.dest_node = Supernova.get_my_id()
    p.ack = 1
    Send.send_to_self(p)   

    # Wait for and then assert that thread has *not* exited.
    t.join(0.01)
    assert t.is_alive()

    # Send a payload command packet -- SHUTDOWN
    p = Packet()
    p.service = Supernova.service_id("Payload Command")
    p.dest_node = Supernova.get_my_id()
    Send.send_to_self(p)   

    # Wait for and then assert that thread has exited.
    t.join(0.01)
    assert not t.is_alive()


def test_timeout():
    # Create an agent that throws an exception when it receives
    # a payload command packet.
    a = Agent()
    a.bind_udp_sockets()
    a.service_handler["Payload Command"] = Agent.raise_exception

    # Set a timeout that is << delay.
    Agent.TIMEOUT = 0.005

    # Run agent.
    t = threading.Thread(target=Agent.run, args=(a,))
    t.daemon = True
    t.start()

    # Delay
    time.sleep(0.02)

    # Send a payload command packet -- SHUTDOWN
    p = Packet()
    p.service = Supernova.service_id("Payload Command")
    p.dest_node = Supernova.get_my_id()
    Send.send_to_self(p)   

    # Wait for and then assert that thread has exited.
    t.join(0.01)
    assert not t.is_alive()
