__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__company__ = "Tethers Unlimited Inc."
__status__ = "Development"
__date__ = "Late Updated: 5/3/16"

import struct
import sys
try:
    import packet_wrappers
except ImportError:
    from commands import packet_wrappers

                                                # ORDER         ALIGNMENT
NATIVEA = packet_wrappers.NATIVEA               # native        native
NATIVE = packet_wrappers.NATIVE                 # native        standard
LITTLEENDIAN = packet_wrappers.LITTLEENDIAN     # little        standard
BIGENDIAN = packet_wrappers.BIGENDIAN           # big           standard
NETWORK = packet_wrappers.NETWORK               # network       standard

# param types
CMDTABLE_DTYPE_UNKNOWN	= 0
CMDTABLE_DTYPE_STR		= 1	# Null-terminated strings of arbitrary length.
CMDTABLE_DTYPE_ENUM		= 2	# Enumerated strings where the strings are hashed.
CMDTABLE_DTYPE_INT		= 3	# Signed integers.
CMDTABLE_DTYPE_FLOAT	= 4	# Double-precision floating point numbers.
CMDTABLE_DTYPE_HEX		= 5
CMDTABLE_DTYPE_BOOL		= 6	# Zero/one/true/false booleans represented by a signed integer.
CMDTABLE_DTYPE_IP4ADX	= 7	# Four-byte IPv4 address.
CMDTABLE_DTYPE_BIN		= 8	# Unspecified and arbitrary length binary data.

# number byte sizes
DTYPE_SIZE_INT          = 4
DTYPE_SIZE_FLOAT        = 8
DTYPE_SIZE_BOOL         = 4

# Packet Definitions
CMDTABLE_MAX_COMMAND_NAME_LENGTH = 32
CMDTABLE_MAX_INPUT_OUTPUT_NAME_LENGTH = 32
CMDTABLE_MAX_STROPT_NAME_LENGTH	= 32
CMDTABLE_MAX_UNITS_LENGTH = 32
CMDTABLE_MAX_DESCRIPTION_LENGTH	= 248

DTYPE_NAMES = {
	CMDTABLE_DTYPE_UNKNOWN: "UNKNOWN",
	CMDTABLE_DTYPE_STR: "STR",
	CMDTABLE_DTYPE_ENUM: "STROPT",
	CMDTABLE_DTYPE_INT: "INT",
	CMDTABLE_DTYPE_FLOAT: "FLOAT",
	CMDTABLE_DTYPE_HEX: "HEX",
	CMDTABLE_DTYPE_BOOL: "BOOL",
	CMDTABLE_DTYPE_IP4ADX: "IP4ADX",
	CMDTABLE_DTYPE_BIN: "BIN"
}

#########################################################
# Help Command Packet Prototype
#########################################################
help_command_packet = packet_wrappers.Prototype()
help_command_packet.add_uint16('command_name_hash')
help_command_packet.add_pad(6)
help_command_packet.add_uint16('num_inputs')
help_command_packet.add_uint16('num_outputs')
help_command_packet.add_int32('level')
help_command_packet.add_string('command_name', CMDTABLE_MAX_COMMAND_NAME_LENGTH)
HelpCommandPacket = help_command_packet.klass('HelpCommandPacket', order=packet_wrappers.LITTLEENDIAN)
del help_command_packet

#########################################################
# Help Input/Output Command Prototype
#########################################################
help_io_packet = packet_wrappers.Prototype()
help_io_packet.add_uint16('command_name_hash')
help_io_packet.add_uint16('input_output_name_hash')
help_io_packet.add_pad(4)
help_io_packet.add_uint8('optopt')
help_io_packet.add_uint8('num_enums')
help_io_packet.add_uint16('type')
help_io_packet.add_string('units', CMDTABLE_MAX_UNITS_LENGTH)
help_io_packet.add_string('min', 16)
help_io_packet.add_string('max', 16)
help_io_packet.add_string('default', 16)
help_io_packet.add_string('input_output_name', CMDTABLE_MAX_INPUT_OUTPUT_NAME_LENGTH)
HelpIOPacket = help_io_packet.klass('HelpIOPacket', order=packet_wrappers.LITTLEENDIAN)

del help_io_packet

#########################################################
# Help Description Packet
#########################################################
help_desc_packet = packet_wrappers.Prototype()
help_desc_packet.add_uint16( 'command_name_hash' )
help_desc_packet.add_uint16( 'input_output_name_hash' )
help_desc_packet.add_uint16( 'enum_name_hash' )
help_desc_packet.add_pad( 2 )
help_desc_packet.add_string( 'description', CMDTABLE_MAX_DESCRIPTION_LENGTH )
HelpDescriptionPacket = help_desc_packet.klass( 'HelpDescriptionPacket', order=packet_wrappers.LITTLEENDIAN )

del help_desc_packet

#########################################################
# Help stropt Enum Packet
#########################################################
help_stropt_enum_packet = packet_wrappers.Prototype()
help_stropt_enum_packet.add_uint16( 'command_name_hash' )
help_stropt_enum_packet.add_uint16( 'input_output_name_hash' )
help_stropt_enum_packet.add_uint16( 'enum_name_hash' )
help_stropt_enum_packet.add_pad( 2 )
help_stropt_enum_packet.add_string( 'enum_name', CMDTABLE_MAX_STROPT_NAME_LENGTH )
HelpStroptEnumPacket = help_stropt_enum_packet.klass( 'HelpStroptEnumPacket', order=packet_wrappers.LITTLEENDIAN )
del help_stropt_enum_packet

#
if __name__ == '__main__':

    # command packet
    cmd_pkt =  [
        '\x11', '\x90', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00',
        '\x03', '\x00', '\x05', '\x00',
        '\x00', '\x00', '\x00', '\x00',
        's', 'y', 's', 't',
        'i', 'm', 'e', '\x00',
        '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00']

    command_input1 = [
        # command[2], parameter[2]
        '\x11', '\x90', '\xf1', '\xbe',
        # pad[4]
        '\x00', '\x00', '\x00', '\x00',
        # optopt, num enums, type[2]
        '\x00', '\x08', '\x03', '\x00',
        # units[32]
        '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00',
        # min[16]
        '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00',
        # max[16]
        '\xff', '\xff', '\xff', '\x7f',
        '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00',
        # def[16]
        '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00',
        # input/output name[32]
        's', 'e', 'c', 'o',
        'n', 'd', 's', '\x00',
        '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00']

    command_output1 = ['\x11', '\x90', '\xf1', '\xbe', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x03', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\xff', '\xff', '\xff', '\x7f', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00', 's', 'e', 'c', 'o', 'n', 'd', 's', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00']
		
    command_description = ['\x11', '\x90', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', 'O', 'p', 't', 'i', 'o', 'n',
        'a', 'l', 'l', 'y', ' ', 'u', 'p', 'd', 'a', 't', 'e', 's', ',', ' ', 'c', 'o', 'n', 'f', 'i', 'g', 'u', 'r', 'e',
        's', ' ', 's', 'y', 'n', 'c', 'h', 'r', 'o', 'n', 'i', 'z', 'a', 't', 'i', 'o', 'n', ',', ' ', 'a', 'n', 'd', ' ',
        't', 'h', 'e', 'n', ' ', 'r', 'e', 't', 'u', 'r', 'n', 's', ' ', 't', 'h', 'e', ' ', 'c', 'u', 'r', 'r', 'e', 'n',
        't', ' ', 's', 'y', 's', 't', 'e', 'm', ' ', 't', 'i', 'm', 'e', ' ', 'a', 'n', 'd', ' ', 't', 'i', 'm', 'e', ' ',
        's', 'y', 'n', 'c', 'h', 'r', 'o', 'n', 'i', 'z', 'a', 't', 'i', 'o', 'n', ' ', 's', 't', 'a', 't', 'u', 's', '.',
        '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
        '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00']

    command_enum1 = ['\xfb', '\xae', '\x11', '\x19', '\xb1', 'J', '\x00', '\x00', 'n', 'o', 'n', 'e',
    	'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
    	'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
    	'\x00', '\x00', '\x00', '\x00', '\x00', '\x00']

    # sample = struct.pack("20p", x)
    # print len(cmd_pkt)
    # print len("".join(cmd_pkt))
    # load sample bytestring into an IP packet
    cmd_packet = get_command_packet(cmd_pkt)
    print "\nCommand Packet for '{}':".format( cmd_packet.command_name )
    cmd_packet.dump()

    # print len(command_input1)
    # print len(command_input2)
    # print len(command_input3)

    print "\nInput Packets:"
    input_packets = list()
    input_packets.append( get_input_packet(command_input1) )
    input_packets.append( get_input_packet(command_input2) )
    input_packets.append( get_input_packet(command_input3) )
    for input_packet in input_packets:
        print "\n{} ".format(input_packet.input_output_name)
        input_packet.dump(show_all=True)

    print "\nOutput Packets:"
    output_packets = list()
    output_packets.append( get_output_packet(command_output1) )
    output_packets.append( get_output_packet(command_output2) )
    output_packets.append( get_output_packet(command_output3) )
    output_packets.append( get_output_packet(command_output4) )
    output_packets.append( get_output_packet(command_output5) )
    for output_packet in output_packets:
        print "\n{} ".format(output_packet.input_output_name)
        output_packet.dump(show_all=True)

    print "\nDescription Packet:"
    desc_packet = get_description_packet(command_description)
    desc_packet.dump()

    print "\nEnum Packet:"
    enum_packets = list()
    enum_packets.append( get_enum_packet(command_enum1) )
    enum_packets.append( get_enum_packet(command_enum2) )
    enum_packets.append( get_enum_packet(command_enum3) )
    enum_packets.append( get_enum_packet(command_enum4) )
    for enum_packet in enum_packets:
        print "\n{} ".format(enum_packet.enum_name)
        enum_packet.dump(show_all=True)
