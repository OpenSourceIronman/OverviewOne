import pytest
import sys, os

from spacepacket import Packet
from payload_cmd_handler import PayloadCommandHandler

# Assert Python 2.7
assert sys.version_info[0:2] == (2,7)

def test_echo():
    payload = PayloadCommandHandler()

    p = Packet()
    p.data = b"echoed data"
    p.data_len = len(p.data)
    p.pkt_id = PayloadCommandHandler.ECHO_CMD

    payload.dispatch(p)


def test_shell():
    payload = PayloadCommandHandler()

    PayloadCommandHandler.DEBUG = True

    # Send a single-packet command
    p = Packet()
    p.data = b"uname"
    p.data_len = len(p.data)
    p.seq_flags |= Packet.SEQ_FLAG_LAST 
    p.pkt_id = PayloadCommandHandler.SHELL_CMD
    payload.dispatch(p)

    # Send a multi-packet command
    p = Packet()
    p.data = b"uname" + (" "*300) + "-a"
    p.data_len = len(p.data)
    p.pkt_id = PayloadCommandHandler.SHELL_CMD

    seq = p.make_seq()

    for s in seq:
        payload.dispatch(s)

def test_error_cases():
    payload = PayloadCommandHandler()

    # Exceptional: Invalid parameter type
    with pytest.raises(TypeError) as ex:
        payload.dispatch(bytearray(266))

    p = Packet()
    p.data_len = 1234
    p.data = bytearray(1234)
    p.pkt_id = 0xDEADBEEF # unknown command ID
    payload.dispatch(p)