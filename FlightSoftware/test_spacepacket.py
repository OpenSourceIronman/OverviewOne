import pytest
import sys, os
from spacepacket import Packet, TelemetryPacket, AckPacket

# Assert Python 2.7
assert sys.version_info[0:2] == (2,7)

def test_dummy():
    assert True == True
    assert True != False

def roundtrip(p):
    buf = p.serialize()
    p_copy = Packet()
    p_copy.deserialize(buf)
    buf_copy = p_copy.serialize()
    assert buf == buf_copy

def test_roundtrip():
    ''' Test the combined serialization + deserialization.

    It's easy to compare byte buffers (at least versus the data structure).  
    Therefore, we take various packets and compare the serialized
    version against another roundtrip of that data.  If anything is lost or
    mutated along the way, the final result will differ
    '''

    # Empty packet
    p = Packet()
    roundtrip(p)

    # Packet with some data as 'bytearray'
    p.data_len = 6;
    p.data = bytearray([0xA0, 0x13, 0xFF, 0x00, 0xFF, 0x8C])
    assert len(p.data) == p.data_len
    roundtrip(p)

    # Packet with some data as 'str'
    p.data_len = 6;
    p.data = str("hello!")
    assert len(p.data) == p.data_len
    roundtrip(p)

def test_seq0():
    ''' Test the breakdown of (large packets) into a sequence of smaller ones.
    
    This variant tests a packet with zero data.
    We should still return a sequence containing the empty packet.
    '''

    p = Packet()
    p.data_len = 0
    p.data = None

    seq = p.make_seq()

    assert len(seq) == 1
    assert seq[0].data_len == 0

def test_seq1():
    ''' Test the breakdown of (large packets) into a sequence of smaller ones.
    
    This variant tests a packet with zero data.
    We should still return a sequence containing the empty packet.
    '''

    p = Packet()
    p.data_len = 1
    p.data = bytearray([0xAA])

    seq = p.make_seq()

    assert len(seq) == 1
    assert seq[0].data_len == 1
    assert seq[0].data == bytearray([0xAA])

def test_seq2():
    ''' Test the breakdown of (large packets) into a sequence of smaller ones.
    
    This variant tests a sequence of 2 packets.
    '''

    p = Packet()
    p.data_len = 2 * p.MAX_DATA_SIZE
    p.data = bytearray(p.data_len)

    seq = p.make_seq()

    assert len(seq) == 2
    assert seq[0].data_len == p.MAX_DATA_SIZE
    assert seq[1].data_len == p.MAX_DATA_SIZE

def test_telemetry_deserialize():
    ''' Test the deserialization of a telemetry packet.
    '''

    p = Packet()
    p.data_len = 266
    p.data = bytearray(266)

    tp = TelemetryPacket(p)
    tp.deserialize()

def test_packet_seriailize():
    ''' Test the serialization of a packet headers.
    '''

    p = Packet()

    # Exceptional: data that isn't a buffer
    with pytest.raises(ValueError) as ex:
        p.data_len = 1
        p.data     = 0x00
        p.serialize()

    # Exceptional: data buffer doesn't match length
    with pytest.raises(ValueError) as ex:
        p.data_len = 2
        p.data     = bytearray(1)
        p.serialize()

def test_debug_output():
    ''' Test operations with DEBUG flags enabled.
    '''

    Packet.DEBUG = True
    TelemetryPacket.DEBUG = True

    buf = bytearray(6+6+2)

    # Deserialize all 0's
    for i in range(0, 14):
        buf[i] = 0x00
    p = Packet( buf )
    p.data_len = 0
    p.serialize()

    # Deserialize all 1's
    for i in range(0, 14):
        buf[i] = 0xFF
    p = Packet( buf )
    p.data_len = 0
    p.serialize()

    # Insert telemetry data
    p.data_len = 266
    p.data = bytearray(266)
    tp = TelemetryPacket(p)
    tp.deserialize()

    # Insert ack data
    p.data_len = 4
    p.data = bytearray(4)
    ack = AckPacket(p)
    ack.deserialize()

    Packet.DEBUG = False
    TelemetryPacket.DEBUG = False
