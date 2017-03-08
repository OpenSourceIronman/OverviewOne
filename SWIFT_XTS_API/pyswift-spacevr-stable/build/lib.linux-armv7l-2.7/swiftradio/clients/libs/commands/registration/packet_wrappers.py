__author__ = 'Phil Budne <phil@ultimate.com>'
__credits__ = ['Steve Alvarado']
__date__ = "Created: 5/1/16"
__version__ = '0.4'

import struct
import sys

                                # ORDER         ALIGNMENT
NATIVEA = '@'                   # native        native
NATIVE = '='                    # native        standard
LITTLEENDIAN = '<'              # little        standard
BIGENDIAN = '>'                 # big           standard
NETWORK = '!'                   # network       standard

# IDEAS:
# pass "dump" format into "add" methods, keep in a dict
class Prototype(object):
    """
    Prototype objects are used to construct new packet type classes.

    After Prototype instantiation, add fields, with add_xxx() methods,
    then create a new class with the klass() method.
    """

    def __init__(self):
        self.fields = []
        self.format = ""
        self.len = 0

    def add_pad(self, flen=1):
        """add a pad field (ignored bytes)"""
        self.format += "%dx" % flen
        self.len += flen

    def _add(self, name, fmt, flen):
        """field-maker helper"""
        self.fields.append(name)
        self.format += fmt
        self.len += flen

    def add_int8(self, name):
        """add a signed 8-bit integer (byte) field"""
        self._add(name, 'b', 1)

    def add_uint8(self, name):
        """add an unsigned 8-bit integer (byte) field"""
        self._add(name, 'B', 1)

    def add_int16(self, name):
        """add a signed 16-bit integer field"""
        self._add(name, 'h', 2)

    def add_uint16(self, name):
        """add an unsigned 16-bit integer field"""
        self._add(name, 'H', 2)

    def add_int32(self, name):
        """add a signed 32-bit integer field"""
        self._add(name, 'i', 4)

    def add_uint32(self, name):
        """add an unsigned 32-bit integer field"""
        self._add(name, 'I', 4)

    def add_float(self, name):
        """add an unsigned 32-bit integer field"""
        self._add(name, 'f', 4)

    def add_double(self, name):
        """add an unsigned 32-bit integer field"""
        self._add(name, 'd', 8)

    def add_string(self, name, flen):
        """add a fixed-length string (or sub-structre) field"""
        self._add(name, "%ds" % flen, flen)

    def add_sub_struct(self, name, obj):
        """add a fixed-length string (or sub-structre) field"""
        # check for an object that is of type Packet
        if isinstance(obj, Packet):
            pass
            # # iterate through fields and add to
            # for field in self.__class__._fields:
            #     value = getattr(self, field)
            #     if show_all or value != 0:
            #         if type(value) is not str:
            #             out.write("{}: 0x{:x}\n".format(field, value) )
            #         else:
            #             out.write("{}: {}\n".format(field, value) )
            #
            # self._add(name, "%ds" % flen, flen)
        else:
            PacketWrapperError("sub struct field must be a Packet Object")

    def klass(self, name, order=NETWORK):
        """
        Returns a new class for this packet type:
        `name' is the name for the class,
        `order' is one of:
                                        # ORDER         ALIGNMENT
        packet.NATIVEA = '@'            # native        native
        packet.NATIVE = '='             # native        standard
        packet.LITTLEENDIAN = '<'       # little        standard
        packet.BIGENDIAN = '>'          # big           standard
        packet.NETWORK = '!'            # network       standar

        The returned class' constructor takes a string to unpack,
        or None to construct an empty packet
        (all fields initialized to zeroes).

        Each class has a value attribute for each defined field,
        and a pack() method to pack up the current packet contents.
        """
        self._order = order
        new = type(name, (Packet,), {
                '__doc__': "%s packet" % name,
                '_fields': self.fields,
                '_format': order + self.format,
                '_len': self.len })
        return new

class Packet(object):
    """
    base class for all packet classes
    """

    # keep pylint quiet:
    _format = ''
    _len = 0
    _fields = []

    def __init__(self, data=None):
        if data is None:
            data = "\0" * self._len
        values = struct.unpack(self._format, data)
        for i in xrange(0, len(values)):
            setattr(self, self._fields[i], values[i])

    def __len__(self):
        return self._len

    def pack(self):
        """return packed string with packet contents"""
        values = [ getattr(self, fld) for fld in self._fields ]

        return struct.pack(self._format, *values)

    def dump(self, out=sys.stdout, show_all=False):
        """dump field values to `out'"""
        for field in self.__class__._fields:
            value = getattr(self, field)
            if show_all or value != 0:
                # if type(value) is int:
                #     out.write("{}: 0x{}\n".format(field, value) )
                # else:
                out.write("{}: {}\n".format(field, value) )

# "%s: %x\n" % (field, value)

class PacketWrapperError(RuntimeError):
    pass

if __name__ == '__main__':
    # demo: make an IP packet packer/unpacker

    # IP Prototype
    ipp = Prototype()
    ipp.add_uint8('vhl')
    ipp.add_uint8('tos')
    ipp.add_uint16('len')
    ipp.add_uint16('id')
    ipp.add_uint16('off')
    ipp.add_uint8('ttl')
    ipp.add_uint8('p')
    ipp.add_uint16('sum')
    ipp.add_uint32('src')
    ipp.add_uint32('dst')
    IP = ipp.klass('IP', NETWORK)
    del ipp

    print IP
    print IP.__name__
    print IP.__doc__
    print IP._len
    print IP._format

    sample = struct.pack("20B",
                         0x45, 0x00, 0x00, 0x34,
                         0x43, 0x42, 0x40, 0x00,
                         0x40, 0x06, 0x30, 0xbd,
                         0xc0, 0xa8, 0x0f, 0x1c,
                         0x52, 0x5e, 0xa4, 0xa2)
    x = ['\x45', '\x00', '\x00','\x34',
        '\x43','\x42','\x40','\x00',
        '\x40','\x06','\x30','\xBD',
        '\xC0','\xA8','\x0F', '\x1C',
        '\x52','\x5E','\xA4','\xA2']

    # sample = struct.pack("20p", x)
    print len(sample), len(x)
    # load sample bytestring into an IP packet
    packet = IP("".join(x))
    print "packet len:", len(packet)

    # dump fields
    packet.dump()

    # repack, and check if same
    repacked = packet.pack()
    print len(repacked)
    for repacked_byte, sample_byte in zip(repacked, sample):
        print hex( ord(repacked_byte) ), hex( ord(sample_byte) )

    assert sample == repacked
