import pytest
import sys, os
import subprocess

from spacepacket import Packet
from payload_cmd_handler import PayloadCommandHandler
from send import Send

# Assert Python 2.7
assert sys.version_info[0:2] == (2,7)

# Test the payload command to simply echo data
def test_echo():
    payload = PayloadCommandHandler()

    p = Packet()
    p.data = b"echoed data"
    p.data_len = len(p.data)
    p.pkt_id = PayloadCommandHandler.ECHO_CMD

    payload.dispatch(p)


# Test the payload command to run a shell command
def test_shell():
    payload = PayloadCommandHandler()

    PayloadCommandHandler.DEBUG = True
    Send.ENABLE_TRACE = True

    # Send a single-packet command
    p = Packet()
    p.data = b"uname"
    p.data_len = len(p.data)
    p.seq_flags |= Packet.SEQ_FLAG_FIRST | Packet.SEQ_FLAG_LAST
    p.pkt_id = PayloadCommandHandler.SHELL_CMD
    payload.dispatch(p)

    # Check output
    assert len(Send.TRACE_QUEUE) == 1
    rsl = Packet(Send.TRACE_QUEUE.pop())
    assert rsl.data == b"Linux\n"

    # Send a multi-packet command
    # Test options
    p = Packet()
    p.data = b"uname" + (" "*300) + "-o"
    p.data_len = len(p.data)
    p.pkt_id = PayloadCommandHandler.SHELL_CMD

    seq = p.make_seq()

    for s in seq:
        payload.dispatch(s)

    # Check output
    assert len(Send.TRACE_QUEUE) == 1
    rsl = Packet(Send.TRACE_QUEUE.pop())
    assert rsl.data == b"GNU/Linux\n"

# Test error or invalid inputs
def test_error_cases():
    payload = PayloadCommandHandler()

    # Exceptional: Invalid parameter type
    with pytest.raises(TypeError) as ex:
        payload.dispatch(bytearray(266))

    p = Packet()
    p.data_len = 1234
    p.data = bytearray(1234)
    p.pkt_id = 0xDEADBEEF # unknown command ID
    p.seq_flags |= Packet.SEQ_FLAG_FIRST | Packet.SEQ_FLAG_LAST
    payload.dispatch(p)

def test_bad_command():
    payload = PayloadCommandHandler()

    Send.ENABLE_TRACE = True

    # Run a bad shell command
    p = Packet()
    p.data = b"asdf;;"
    p.data_len = len(p.data)
    p.seq_flags |= Packet.SEQ_FLAG_FIRST | Packet.SEQ_FLAG_LAST
    p.pkt_id = PayloadCommandHandler.SHELL_CMD

    # Test: no exception
    payload.dispatch(p)

    # Test: the error message is in the result
    rsl = Packet(Send.TRACE_QUEUE.pop())
    assert "ERROR" in rsl.data
    assert "Syntax error" in rsl.data
