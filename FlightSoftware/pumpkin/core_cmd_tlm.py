################################################################################
#(C) Copyright Pumpkin, Inc. All Rights Reserved.
#
#This file may be distributed under the terms of the License
#Agreement provided with this software.
#
#THIS FILE IS PROVIDED AS IS WITH NO WARRANTY OF ANY KIND,
#INCLUDING THE WARRANTY OF DESIGN, MERCHANTABILITY AND
#FITNESS FOR A PARTICULAR PURPOSE.
################################################################################

"""
Interfaces with Core FSW database files to generate and parse Bus
command and telemetry objects.

core_cmd_telem.py - Public API v0.2
===================================

### CONSTANTS

    CMD
    TLM
    ENUMS

### FUNCTIONS

    unpack_telemetry(packet_obj)

### CLASSES

    Command
    Telemetry

"""

import struct, os, logging
from csv import DictReader

#from supernova_apps import core_packets
#from supernova_apps.settings import Settings
from _utils import verify_range

# LOGGING:
#    LOG.debug() is called when a telemetry packet_obj is unpacked
LOG = logging.getLogger(__name__)

_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
_FOLDER = os.path.join(_SCRIPT_PATH, "core_definitions")

_CMD_CSV_PATH = os.path.join(_FOLDER, "qry_icd_cmd_definitions_full.csv")
_TLM_CSV_PATH = os.path.join(_FOLDER, "qry_icd_tlm_pkt_definitions.csv")
_ENUM_CSV_PATH = os.path.join(_FOLDER, "enum_entry.csv")

# --- Format char lookup table
_FORMAT_TABLE = {
    'Character': 'c',
    'UInt8': 'B',
    'UInt16': 'H',
    'UInt32': 'I',
    'UInt64': 'Q',
    'Int8': 'b',
    'Int16': 'h',
    'Int32': 'i',
    'Int64': 'q',
    'Ieee32': 'f',
    'Ieee64': 'd'
# --- {x}BitUInt{y} handled separately
}

_ENDIAN_SYMBOLS = {
    'little_endian': '<',
    'big_endian': '>'
}

def unpack_telemetry(packet_obj):
    """
    Parse a TelemetryPacket, returning a Telemetry object.

    Args:
        packet_obj (TelemetryPacket): a packet object containing telemetry

    Returns:
        (Telemetry)

    """
    # --- Find the telemetry packet name corresponding to packet_id.
    packet_name = TLM.name_by_id[packet_obj.packet_id]
    bytes_recd = len(packet_obj.packet_data)
    bytes_expected = TLM.get_packet_len_bytes(packet_name)
    if bytes_recd < bytes_expected:
        raise ValueError('{}: expected {} got {} bytes.'.format(packet_name,
            bytes_expected, bytes_recd))
    # --- Definitions describe the data items in a packet & their types.
    definitions = TLM.table[packet_name]
    telemetry_obj = Telemetry(
        tlm_pkt_name=TLM.name_by_id[packet_obj.packet_id],
        values=_bytes_to_dict(packet_obj.packet_data, definitions),
        source_node=packet_obj.source_node,
        packet_subid=packet_obj.packet_subid
        )
    LOG.debug('Telemetry unpacked.')
    return telemetry_obj

class Telemetry(object):
    """
    Represent a telemetry message and associated metadata.

    Attributes:
        source_node (int): origin of telemetry packet.
        packet_id (int): telemetry packet identifier.
        packet_subid (int): secondary packet identifier.
        values (dict): values keyed by data_item_name.
    """
    def __init__(self,
        tlm_pkt_name,
        values=None,
        source_node=0, # Settings.PL_NODE,
        packet_subid=0
        ):

        verify_range(0, 0x3F, 'source_node', source_node)
        verify_range(0, 0xFF, 'packet_subid', packet_subid)
        self._name = tlm_pkt_name
        self._packet_id = TLM.id_by_name[tlm_pkt_name]
        self.packet_subid = packet_subid
        self.source_node = source_node
        self.definitions = TLM.table[tlm_pkt_name]
        if values is None:
            self.values = TLM.create_empty_dict(tlm_pkt_name)
        else:
            self.values = values

    @property
    def name(self):
        """
        Command packet name.

        """
        return self._name

    @property
    def packet_id(self):
        """
        Command packet ID.

        """
        return self._packet_id

    @property
    def data(self):
        """
        Return telemetry data in packed byte format.

        """
        return _dict_to_bytes(self.values, self.definitions)

class Command(object):
    """
    Represent a Bus command and associated metadata.

    Attributes:
        data (dict): values keyed by data_item_name.
        source_node (int): origin of command.
        arguments (dict): command arguments keyed by data_item_name.
    """
    def __init__(self,
        cmd_pkt_name,
        arguments=None,
        source_node=0, # Settings.PL_NODE,
        packet_subid=0
        ):
        verify_range(0, 0x3F, 'source_node', source_node)
        verify_range(0, 0xFF, 'packet_subid', packet_subid)
        self._name = cmd_pkt_name
        self._packet_id = CMD.id_by_name[cmd_pkt_name]
        self.packet_subid = packet_subid
        self.source_node = source_node
        self.definitions = CMD.table[cmd_pkt_name]
        if arguments is None:
            self.arguments = CMD.create_empty_dict(cmd_pkt_name)
        else:
            self.arguments = arguments

    @property
    def name(self):
        """
        Command packet name.

        """
        return self._name

    @property
    def packet_id(self):
        """
        Command packet ID.

        """
        return self._packet_id

    @property
    def data(self):
        """
        Return command data in packed byte format.

        """
        return _dict_to_bytes(self.arguments, self.definitions)

class _DefinitionTable(object):
    """
    Holds a command or telemetry table and associated methods.

    """
    def __init__(self, path, primary_id, secondary_id, packet_id):
        self.table = _group_items(_load_csv(path), primary_id, secondary_id)
        self.name_by_id, self.id_by_name = _make_lookups(self.table, packet_id)

    def create_empty_dict(self, packet_name):
        """
        Create a dictionary with all of the keys set to empty values.

        Args:
            packet_name (str): Name of the packet to create the dictionary from.

        """
        dictionary = {}
        definitions = self.table[packet_name]
        for sequence_count in definitions:
            item = definitions[sequence_count]
            data_type = item['DATA_TYPE_NAME']
            if data_type is None:
                # --- Sometimes there are no arguments
                return {}
            else:
                # --- Check type
                if data_type == 'Character':
                    # --- Use lower case x as default, could be anything though.
                    value = 'x'
                elif 'Ieee' in data_type:
                    value = float(0)
                else:
                    value = int(0)
                # --- Check for array
                if item['ARRAY_NAME']:
                    dim1_size = item['DIM_1_SIZE']
                    dim2_size = item['DIM_2_SIZE']
                    value = tuple(dim1_size * [value])
                    if dim2_size:
                        value = tuple(dim2_size * [value])
                    elif data_type == 'Character':
                        # --- Change from list to string if it's characters
                        value = ''.join(value)
                dictionary[item['DATA_ITEM_NAME']] = value
        return dictionary

    def get_packet_len_bytes(self, packet_name):
        """
        Returns the total packet length of a packet in Bytes.

        """
        items = self.table[packet_name].iteritems()
        total_bits = 0
        for item in items:
            item_bits = item[1]['NUM_BITS']
            if item_bits is None:
                # --- handle case where there are no values or arguments
                item_bits = 0
            if item[1]['DIM_1_SIZE']:
                item_bits = item_bits * item[1]['DIM_1_SIZE']
                if item[1]['DIM_2_SIZE']:
                    item_bits = item_bits * item[1]['DIM_2_SIZE']
            total_bits += item_bits
        extra_bits = total_bits % 8
        bytes = total_bits // 8 + bool(extra_bits)
        return bytes

    def get_item_names(self, packet_name):
        """
        Return list of items (telemetry fields or arguments) for given packet.

        """
        items = self.table[packet_name].iteritems()
        names = []
        for item in items:
            names.append(item[1]['DATA_ITEM_NAME'])
        return names

def _bytes_to_dict(bytes, definitions):
    """
    Turn bytearray structure into python dictionary acording to `definitions`.

    """
    # --- Dictionary of name/values to return
    dictionary = {}
    # --- start_byte: describes where we are in the `bytes` packet as we parse
    start_byte = 0
    # --- Create iterator from ordered list of sequence counts
    sequence_counts = iter(sorted(definitions.keys()))
    while True:
        try:
            sequence_count = sequence_counts.next()
        except StopIteration:
            # --- Finished going through all items
            break
        else:
            definition = definitions[sequence_count]
            # ---
            # --- STEP 1: Determine if item is a packed or array special case.
            data_type = definition['DATA_TYPE_NAME']
            if data_type is None:
                # --- ASSUMPTION: if there is no data_type than then
                # ---   this command has no arguments.
                return {}
            ARRAY_ITEM, PACKED_ITEM = _determine_item_type(definition)
            # ---
            # --- STEP 2: Get `fmt_string` and `num_bytes`
            fmt_string = _ENDIAN_SYMBOLS[definition['ENDIAN_NAME']]
            if PACKED_ITEM:
                num_bytes, fmt_char = _lookup_packed_datatype(data_type)
            else: #STANDARD_ITEM or ARRAY_ITEM
                num_bytes = definition['NUM_BITS'] // 8
                fmt_char = _FORMAT_TABLE[data_type]
                if ARRAY_ITEM:
                    # --- Add number to fmt_string indicating series (eg. '<3I')
                    dim1_size = definition['DIM_1_SIZE']
                    dim2_size = definition['DIM_2_SIZE']
                    num_elements = dim1_size
                    if dim2_size:
                        num_elements = num_elements * dim2_size
                    num_bytes = num_bytes * num_elements
                    fmt_string += str(num_elements)
            fmt_string += fmt_char
            # ---
            # --- STEP 3: Unpack data & update start_byte
            end_byte = start_byte + num_bytes
            chunk = bytes[start_byte:end_byte]
            value = struct.unpack(fmt_string, str(chunk))
            start_byte += num_bytes
            # ---
            # --- STEP 4: Post-process unpacked value & add to dictionary
            if PACKED_ITEM:
                bit_count = definition['NUM_BITS']
                parts = []
                total_bits = bit_count
                # --- Add this item to a list of (name, bit_count) tuples
                parts.append((definition['DATA_ITEM_NAME'], bit_count))
                while total_bits < (num_bytes * 8):
                    # --- Iterate through all items in packed datatype
                    definition = definitions[sequence_counts.next()]
                    bit_count = definition['NUM_BITS']
                    total_bits += bit_count
                    # --- Add this item to a list of (name, bit_count) tuples
                    parts.append((definition['DATA_ITEM_NAME'], bit_count))
                # --- Unpack the parts into a dict of integer values.
                parts_dict = _unpack_parts(value[0], parts)
                for name in parts_dict:
                    dictionary[name] = parts_dict[name]
            elif ARRAY_ITEM:
                if dim2_size:
                    # --- Split up into 2d array.
                    value = tuple([value[i:i+dim1_size] for i in
                        xrange(0, len(value), dim1_size)])
                elif data_type == 'Character':
                    # --- Change from list to string if it's characters
                    value = ''.join(value)
                # --- Add array (1d or 2d) to dictionary
                dictionary[definition['DATA_ITEM_NAME']] = value
            else: #STANDARD_ITEM
                # --- Add first element of struct.unpack to dictionary
                dictionary[definition['DATA_ITEM_NAME']] = value[0]
        # --- END WHILE LOOP
    # --- Return from _bytes_to_dict()
    return dictionary

def _dict_to_bytes(dictionary, definitions):
    """
    Pack a dictionary of data items according to definitions.

    """
    packet_data = bytearray()
    # --- Create iterator from ordered list of sequence counts
    sequence_counts = iter(sorted(definitions.keys()))
    while True:
        try:
            sequence_count = sequence_counts.next()
        except StopIteration:
            # --- Finished going through all items
            break
        else:
            definition = definitions[sequence_count]
            # ---
            # --- STEP 1: Determine if item is a packed or array special case.
            data_type = definition['DATA_TYPE_NAME']
            if data_type is None:
                # --- ASSUMPTION: if there is no data_type than then
                # ---   this command has no arguments.
                return bytearray()
            ARRAY_ITEM, PACKED_ITEM = _determine_item_type(definition)
            # ---
            # --- STEP 2: Get `fmt_char` and `num_bytes`
            fmt_string = _ENDIAN_SYMBOLS[definition['ENDIAN_NAME']]
            if PACKED_ITEM:
                num_bytes, fmt_char = _lookup_packed_datatype(data_type)
            else: #STANDARD_ITEM or ARRAY_ITEM
                num_bytes = definition['NUM_BITS'] // 8
                fmt_char = _FORMAT_TABLE[data_type]
            fmt_string += fmt_char
            # ---
            # --- STEP 3: Process & pack dictionary values
            if PACKED_ITEM:
                bit_count = definition['NUM_BITS']
                parts = []
                total_bits = bit_count
                value = dictionary[definition['DATA_ITEM_NAME']]
                # --- Add this item to a list of (value, bit_count) tuples
                parts.append((value, bit_count))
                while total_bits < (num_bytes * 8):
                    # --- Iterate through all items in packed datatype
                    definition = definitions[sequence_counts.next()]
                    bit_count = definition['NUM_BITS']
                    total_bits += bit_count
                    value = dictionary[definition['DATA_ITEM_NAME']]
                    # --- Add this item to a list of (value, bit_count) tuples
                    parts.append((value, bit_count))
                # --- Pack the parts into a bytearray
                packet_part = _pack_parts(parts, fmt_string, num_bytes)
            elif ARRAY_ITEM:
                values = dictionary[definition['DATA_ITEM_NAME']]
                packet_part = _pack_array(values, definition, fmt_string,
                    num_bytes)
            else: #STANDARD_ITEM
                # --- Pack dictionary value into bytearray
                value = dictionary[definition['DATA_ITEM_NAME']]
                packet_part = bytearray(num_bytes)
                struct.pack_into(fmt_string, packet_part, 0, value)
            # --- Add part to return array before looping
            packet_data += packet_part
        # --- END WHILE LOOP
    # --- Return from _dict_to_bytes()
    return packet_data

def _determine_item_type(definition):
    """
    Determine if the item is an ARRAY or PACKED item.

    Args:
        definition (dict): Describes the item in question.

    """
    data_type = definition['DATA_TYPE_NAME']
    ARRAY_ITEM = False
    PACKED_ITEM = False
    if definition['ARRAY_NAME']:
        ARRAY_ITEM = True
    elif 'BitUInt' in data_type:
        PACKED_ITEM = True
    return ARRAY_ITEM, PACKED_ITEM

def _lookup_packed_datatype(data_type):
    """
    Return unpack fmt_char & bit length for a given data_type

    Args:
        data_type (str): Data type in format in format {x}BitUInt{y}

    Returns:
        (bit_length (int), fmt_char (str))

    Raises:
        ValueError: when data_type is not of corrrect format.

    """
    if 'UInt8' in data_type:
        return 1, 'B'
    elif 'UInt16' in data_type:
        return 2, 'H'
    elif 'UInt32' in data_type:
        return 4, 'I'
    elif 'UInt64' in data_type:
        return 8, 'Q'
    else:
        raise ValueError

def _pack_array(values, definition, fmt_string, num_bytes):
    """
    Pack an array item defined by a dictionary entry into a bytearray

    Args:
        values (tuple): 1d or 2d tuple of values to pack
        definition (dict): definition of the data item
        fmt_string (str): struct.unpack format string for an element
        num_bytes (int): number of bytes of each element

    """
    packet_part = bytearray()
    if definition['DIM_2_SIZE']:
        for dim1 in values:
            for value in dim1:
                buff = bytearray(num_bytes)
                struct.pack_into(fmt_string, buff, 0, value)
                packet_part += buff
    else:
        for value in values:
            buff = bytearray(num_bytes)
            struct.pack_into(fmt_string, buff, 0, value)
            packet_part += buff
    return packet_part

def _unpack_parts(packed_value, parts):
    """
    Create a dictionary of UInt values.

    This unpacks data that is stored in fractional UInt sizes, eg. 1 byte split
    into a 3BitUint8 and a 5BitUint8.

    Args:
        packed_value (int): A number representing packed integers of various bit sizes
        parts (list): List of tuples like: (part name (str), bit size (int))

    Returns:
        Dictionary of names/part_values

    """
    dictionary = {}
    total_bits = sum([parts[x][1] for x in xrange(len(parts))])
    parsed_bits = 0
    for part in parts:
        num_bits = part[1]
        parsed_bits += num_bits
        shift = total_bits - parsed_bits
        mask = sum([1 << x for x in xrange(num_bits)]) << shift
        value = (packed_value & mask) >> shift
        dictionary[part[0]] = value
    return dictionary

def _pack_parts(parts, fmt_string, num_bytes):
    """
    Combine a list of integers of different bit sizes & pack into bytearray.

    This packs data that is stored in fractional UInt sizes, eg. 1 byte split
    into a 3BitUint8 and a 5BitUint8.

    Args:
        parts (list): List of tuples like: (value (int), bit_count (int))
        fmt_string (str): struct.unpack format string to use
        num_bytes (int): Number of bytes long the datatype to pack into is

    Returns:
        Packed bytearray of the values in `parts`

    """
    pack_value = 0
    shift = (num_bytes * 8)
    for part in parts:
        value = part[0]
        num_bits = part[1]
        shift = shift - num_bits
        pack_value += (value << shift)
    packet_part = bytearray(num_bytes)
    struct.pack_into(fmt_string, packet_part, 0, pack_value)
    return packet_part

def _make_lookups(table, id_key):
    """
    Create lookup tables by `id_key` & name for top level keys in grouped dict.

    Telemetry example:

    {
        1: 'NAME_OF_TELEM_PKT_1',
        2: 'NAME_OF_TELEM_PKT_2',
        etc.
    }
    {
        'NAME_OF_TELEM_PKT_1': 1,
        'NAME_OF_TELEM_PKT_2': 2,
        etc.
    }
    """
    name_by_id = {}
    id_by_name = {}
    for name in table:
        # --- Choose any data item in the packet to get the packet_id
        item = table[name].iteritems().next()[1]
        packet_id = item[id_key]
        # --- Create lookup table as {'packet_id': 'packet_name'}
        name_by_id[packet_id] = name
        id_by_name[name] = packet_id
    return name_by_id, id_by_name

def _load_csv(path):
    """
    Load csv returning dictionaries with standardized & converted field types.

    """
    table = []
    with open(path, "rb") as csv_file:
        reader = DictReader(csv_file)
        for row in reader:
            # --- Convert fields to uppercase & copy
            row = dict((k.upper(), v) for k,v in row.iteritems())
            for key in row:
                # --- Convert to int if it's a number field
                try:
                    row[key] = int(row[key])
                except:
                    pass
                # --- Convert to 'None' if it's an empty string
                if row[key] == '':
                    row[key] = None
            table.append(row)
    return table

def _group_items(table, key1, key2):
    """
    Take list of dictionaries & group into dictionary with 2-level heirarchy.

    table = {
        key1-value1 (packet_name): {
            key2-value1 (sequence_number): {
                <additional fields in associated with (key1-value1,key2-value1)>
                ...
            },
            key2-value2 (sequence_number): {
                ...
            },
            ...
        },
        key1-value2 (packet_name): {
            ...
        },
        ...
    }

    """
    grouping = {}
    for row in table:
        val1 = row.pop(key1)
        val2 = row.pop(key2)
        if val1 not in grouping:
            # --- Add new key1 value
            grouping[val1] = dict()
        if val2 in grouping[val1]:
            # --- Check for duplicates of val2 within any val1 group
            raise KeyError
        else:
            # --- Add remainder of 'row' dictionary under val1
            grouping[val1][val2] = row
    return grouping

#------------------------------------------------
# --- Initialize TABLE constants on module import
CMD = _DefinitionTable(_CMD_CSV_PATH, 'CMD_PKT_NAME', 'SEQUENCE_NUMBER',
    'CMD_ID')
TLM = _DefinitionTable(_TLM_CSV_PATH, 'TLM_PKT_NAME', 'SEQUENCE_NUMBER',
    'PKT_ID')
ENUMS = _group_items(_load_csv(_ENUM_CSV_PATH), 'ENUM_RELID', 'DISPLAY_NAME')
