import pytest
import sys, os

from spacepacket import Packet
from send import Send
from supernova import BusCommands

# Assert Python 2.7
assert sys.version_info[0:2] == (2,7)

# Tests sending a payload command
def test_send_payload_command():
    Send.send_payload_cmd(4, 0x00, None)
    Send.send_payload_cmd(4, 0x00, b"Command string")

    # Exceptional: Packet too long
    with pytest.raises(ValueError) as ex:
        Send.send_payload_cmd(4, 0x00, bytearray(1000))

# Tests sending a bus command
def test_send_bus_command():
    Send.send_bus_cmd(BusCommands.NO_OP, None)
    Send.send_bus_cmd(BusCommands.NO_OP, b"Foo")

    # Exceptional: Packet too long
    with pytest.raises(ValueError) as ex:
        Send.send_bus_cmd(0x00, bytearray(1000))

# Test error or invalid inputs
def test_error_cases():

    # Exceptional: Invalid parameter type
    with pytest.raises(TypeError) as ex:
        Send.send(bytearray(266))

    # Exceptional: Invalid parameter type
    with pytest.raises(TypeError) as ex:
        Send.send_payload_cmd(4, 0x00, 0x00)

    # Exceptional: Invalid parameter type
    with pytest.raises(TypeError) as ex:
        Send.send_bus_cmd(0x00, 0x00)
