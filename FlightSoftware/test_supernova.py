import pytest
import sys, os

from supernova import Supernova

# Assert Python 2.7
assert sys.version_info[0:2] == (2,7)

def test_ips():
    # Payloads 3 and 4 run on the BBB but communicate via loopback
    assert Supernova.controller_ip(3) == '127.0.0.1'
    assert Supernova.controller_ip(4) == '127.0.0.1'
    assert Supernova.payload_ip(3) == '127.0.0.1'
    assert Supernova.payload_ip(4) == '127.0.0.1'

    # Payloads 1 and 2 (and others) communicate with controller via eth
    assert Supernova.controller_ip(1) == '192.168.1.70'
    assert Supernova.controller_ip(2) == '192.168.1.70'
    assert Supernova.controller_ip(9) == '192.168.1.70'

    # Check the known two payload IDs
    assert Supernova.payload_ip(1) == '192.168.1.71'
    assert Supernova.payload_ip(2) == '192.168.1.72'

    # Exceptional: Unexpected IP
    with pytest.raises(ValueError) as ex:
        Supernova.payload_ip(9)

def test_service_ids():
    # The service names should be ordered from service ID 1
    id = 1
    for service in Supernova.SERVICES:
        assert(Supernova.service_id(service) == id)
        id = id +1

    # Exceptional: Unexpected service name
    with pytest.raises(ValueError) as ex:
        Supernova.service_id("Blah blah blah")

def test_ports():
    # Test a known value
    assert(Supernova.service_recv_port("Time", 4) == 0x8412)

    for service in Supernova.SERVICES:
        # Test adjacency of send and receive ports
        assert(Supernova.service_recv_port(service, 1) + 1 ==
               Supernova.service_send_port(service, 1))

