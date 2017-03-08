from ...utils.error import SwiftRadioError
from ...utils import stringconversions
from ...utils.dataconversions import int_to_bytelist, float_to_bytelist, uint_to_bytelist, format_bytelist_endianess
from ...utils.algorithms import fletcher16

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__company__ = "Tethers Unlimited Inc."
__status__ = "Development"
__date__ = "Late Updated: 11/14/14"
 
def text_to_swiftbytelist(text_input, CMDHost_Table, control_code = 0x01, transid = 0x0000, packet_endianess = "big"):	
	"""
	Description: 
	Parameters: 
	Return: 
	"""			
	swiftbytelist = list()
	Command_Table = CMDHost_Table
	escape_code = 0xFF00

	# [1] - Parse out Command name and Parameter name/value information from text input
	command_name, params_info_dict = parse_cmdline_input(text_input, CMDHost_Table)

	# [2] - Construct Swift Packet Buffer
	swiftbytelist = construct_swiftmsg_buffer(Command_Table, command_name, params_info_dict, escape_code, transid, control_code, packet_endianess)
	
	# [3] - Return Packet Buffer
	return swiftbytelist

def construct_swiftmsg_buffer(Command_Table, command_name, params_info_dict, escape_code, transid, control_code, buffer_endianess):
	"""
	Description: 
	Parameters: 
	Return: fully populated list of bytes containing Swift Message information
	"""	
	swift_msg_buffer = list()
	params_inserted = 0
	if transid == 0x0000:
		code_len = 2		#code length
	else:
		code_len = 4		#code length, when transid is included

	# get the name of the command in hash format	
	command_hash = Command_Table.get_command_fletcher(command_name, buffer_endianess)
	if command_hash == -1:
		raise SwiftRadioError("Packet Translator: '" + str(command_name) + "' command name not recognized.")		
		swift_msg_buffer = -1

	# [1] Insert Header Field Information
	swift_msg_buffer = insert_header_field(swift_msg_buffer, escape_code, control_code, code_len, buffer_endianess)

	# [2] Insert Command Field Information
	swift_msg_buffer = insert_command_field_info(swift_msg_buffer, command_hash, transid, buffer_endianess)

	# [3] Insert Parameter Field Information for Each Parameter Stored in Dictionary
	if params_info_dict != None:
		for param_name in params_info_dict:

			# get parameter fletcher
			parameter_hash = Command_Table.get_param_fletcher(command_name, param_name, endianess = buffer_endianess)
			if parameter_hash == -1:
				raise SwiftRadioError("Packet Translator: '" + str(param_name) + "' parameter name not recognized.")
				swift_msg_buffer = -1

			# get parameter type
			param_type = str(Command_Table.get_param_type(command_name, param_name)).lower()	

			# get parameter payload value in raw byte form
			payload_val, size = get_param_raw_val(param_type, params_info_dict[param_name], buffer_endianess)

			# get parameter size
			payload_size = size

			# insert parameter field into outgoing buffer
			swift_msg_buffer = insert_parameter_field_info(swift_msg_buffer, parameter_hash, payload_size, payload_val, buffer_endianess)

	return swift_msg_buffer	


def parse_cmdline_input(commandline_input, command_table):
	"""
	Description: 
	Parameters: commandline_input - a command line text string (in GNU/POSIX format) containing the command/parameter information to be converted
									to a swiftradio packet
				command_table - command table instance used to extract command/parameter parsing information
	Return: a tuple (command_name, param_info)
			command_name - the name of the command, as a string 
			param_info - a dictionaries, each key corresponds to the parsed parameter name, is entry is the parsed parameter value
	"""
	command_name = None
	param_info = None

	arglist = commandline_input.split(" ")

	# extract the name of the command from text string
	command_name = str(arglist[0])

	# verify that this command name is registered in command table
	if command_table.verify_command_registered(command_name):
		# text has parameter information, use the command's internal command line processor to parse any parameters
		param_args = arglist[1:]
		# note: the command line parser accepts list arguments only
		param_info = command_table.parse_parameter_text(command_name, param_args)
	else:
		param_info = None

	return command_name, param_info	

def insert_parameter_field_info(swift_msg_buffer, parameter_hash, payload_size, payload_buf, field_endianess="little"):
	"""
	Description: 
	Parameters: 
	Return: 
	"""	
	param_hash = uint_to_bytelist(int(parameter_hash), bytelist_size=2, endianess=field_endianess)
	param_size = uint_to_bytelist(int(payload_size), bytelist_size=2, endianess=field_endianess)

	# insert 16-bit parameter hash id
	swift_msg_buffer += param_hash
	# insert 16-bit parameter size value
	swift_msg_buffer += param_size
	# insert payload buffer (note: this is already in a list format)
	swift_msg_buffer += payload_buf

	# return byte list
	return swift_msg_buffer			

def insert_command_field_info(swift_msg_buffer, command_hash_uint16, transid, field_endianess="little"):
	"""
	Description: 
	Parameters: 
	Return: 
	"""			

	command_hash = uint_to_bytelist(int(command_hash_uint16), bytelist_size=2, endianess=field_endianess)
	transid = uint_to_bytelist(int(transid), bytelist_size=2, endianess=field_endianess)
	
	# insert 16-bit command hash id
	swift_msg_buffer += command_hash
	# insert 16-bit transaction identifier
	swift_msg_buffer += transid

	# return byte list
	return swift_msg_buffer	

def insert_header_field(swift_msg_buffer, escape_code, cntrl_code, code_len, field_endianess = "little"):
	"""
	Description: 
	Parameters: 
	Return: 
	"""			
	# --Header Word[1]--
	escape_code = uint_to_bytelist(int(escape_code), bytelist_size=2, endianess=field_endianess)
	control_code = uint_to_bytelist(int(cntrl_code), bytelist_size=1, endianess=field_endianess) 
	code_length = uint_to_bytelist(int(code_len), bytelist_size=1, endianess=field_endianess) 

	# place into outgoing buffer
	#insert escape code
	swift_msg_buffer += escape_code
	#insert control code
	swift_msg_buffer += control_code
	#insert command field offset
	swift_msg_buffer += code_length

	return swift_msg_buffer	

def get_param_raw_val(param_type, param_val, field_endianess="little"):
	"""
	Description: 
	Parameters: 
	Return: 
	"""	
	raw_param_val = list()
	payload_size = 0

	# INT type
	if param_type == "int":
		payload_size = 4
		raw_param_val = int_to_bytelist(param_val, field_endianess, bytelist_size=payload_size)
		
	# FLOAT Type
	elif param_type == "float":
		payload_size = 8
		# insert payload data into byte list
		raw_param_val = float_to_bytelist(param_val, field_endianess, bytelist_size=payload_size)

	# HEX Type
	elif param_type == "hex":
		payload_size = 4
		param_val = hex(param_val)

		if len(param_val) > 10:
			param_val = param_val[:10]

		# convert string to hex list
		hex_list = list(stringconversions.return_num(param_val))

		# zero pad if necessary
		if len(hex_list) < payload_size:
			for i in range(payload_size-len(hex_list)):
				# left pad hex value
				raw_param_val.append('\x00')

		# insert payload data into byte list
		raw_param_val += hex_list[:payload_size]	# Note: hex value concatenated if longer than 4 bytes
		raw_param_val = format_bytelist_endianess(raw_param_val, len(raw_param_val), endianess=field_endianess)		

	# BOOL Type		
	elif param_type == "bool":
		# set size of a bool param type (4 bytes)
		payload_size = 4

		# insert value into raw parameter list (note: True == int(1), False == int(0))
		raw_param_val = uint_to_bytelist(param_val, field_endianess, bytelist_size=payload_size)		

	# STROPT Type		
	elif param_type == "stropt":
		# set size of a stropt param type (4 bytes)
		payload_size = 4
		
		# hash the stropt string into a integer value
		stropt_hash = fletcher16(str(param_val))

		# convert integer to a 4 item hex list
		raw_param_val = uint_to_bytelist(stropt_hash, bytelist_size=payload_size, endianess=field_endianess)

	# STR Type		
	elif param_type == "str":
		# insert null byte into string
		param_val += '\x00'

		# find size of string val
		payload_size = len(param_val)
		
		# place each character in rawbuffer
		for data_byte in param_val:
			raw_param_val.append(data_byte)	

		# set endianess of raw buffer
		raw_param_val = format_bytelist_endianess(raw_param_val, len(raw_param_val), endianess=field_endianess)

		# zero pad check
		if (payload_size % 4) != 0:
			for i in range(4 - (payload_size % 4)):
				raw_param_val.append('\x00')

	# BIN Type		
	elif param_type == "bin":
		# find size of bin val for zero pad check
		payload_size = len(param_val)

		# place each character in rawbuffer
		for data_byte in param_val:
			raw_param_val.append(data_byte)	

		# set endianess of raw buffer
		raw_param_val = format_bytelist_endianess(raw_param_val, len(raw_param_val), endianess=field_endianess)
			
		# zero pad check
		if (payload_size % 4) != 0:
			# zero pad
			for i in range(4 - (payload_size % 4)):
				raw_param_val.append('\x00')

	# IP4ADX Type		
	elif param_type == "ip4adx":
		# insert null byte into string
		param_val += '\x00'

		# find size of string val for zero pad check
		payload_size = len(param_val)

		# place each character in rawbuffer
		for data_byte in param_val:
			raw_param_val.append(data_byte)	

		# set endianess of raw buffer
		raw_param_val = format_bytelist_endianess(raw_param_val, len(raw_param_val), endianess=field_endianess)
			
		# zero pad check
		if (payload_size % 4) != 0:
			# zero pad
			for i in range(4 - (payload_size % 4)):
				raw_param_val.append('\x00')

	return raw_param_val, payload_size			

if __name__ == '__main__':
	pass
