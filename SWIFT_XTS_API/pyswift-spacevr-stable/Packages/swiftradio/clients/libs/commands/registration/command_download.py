__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__company__ = "Tethers Unlimited Inc."
__status__ = "Development"
__date__ = "Late Updated: 9/10/14"

# from ...utils import stringconversions
import struct
import collections
if __name__ == "__main__":
	import help_packets_def
else:
	import help_packets_def

def register_help_commands(help_commands, cmdtable, endianess = None):
	"""
	Description: processes packets received after a dlcmdinfo command and adds command information to table
	Parameters: packet list containing all the packets received from dlcmdinfo command
	Return: updated command table with new commands
	"""

	for command_entry in help_commands.values():
		# check if command has been registered
		if cmdtable.verify_command_registered(command_entry["name"]):
		# do nothing if already registered
			pass
		else:
			# if not, register new command
			cmdtable.register_command_by_name(command_entry["name"], command_entry["description"])
			# print command_entry["inputs"]
			# register inputs
			for input_entry in command_entry["inputs"]:
				# print cmdtable.verify_parameter_registered(command_entry["name"], input_entry["name"])
				# check if input has been registered
				if cmdtable.verify_parameter_registered(command_entry["name"], input_entry["name"]) == 1:
					# do nothing if already registered
					pass
				# if not, register new command
				else:
					# determine if this is an optional input or required
					if input_entry["optopt"] is None:
						arg = True
						input_entry["optopt"] = ""
					else:
						arg = False

					# get the stropt enumerations for registration
					enums = None
					if input_entry["num_enums"] > 0:
						enums = list()
						for enum_entry in input_entry["enums"]:
							enums.append(enum_entry["name"])

					# get the parameter type as a string
					input_type = (help_packets_def.DTYPE_NAMES[input_entry["type"]]).lower()
					cmdtable.register_parameter(command_entry["name"], input_entry["name"], input_entry["optopt"],
												input_type, input_entry["default"], arg, input_entry["description"],
												input_entry["min"], input_entry["max"], input_entry["units"], enums)

			# register outputs
			for output_entry in command_entry["outputs"]:
				# print cmdtable.verify_parameter_registered(command_entry["name"], output_entry["name"])
				# check if output has been registered
				if cmdtable.verify_output_registered(command_entry["name"], output_entry["name"]) == 1:
					# do nothing if already registered
					pass
				# if not, register new command
				else:

					# get the output type as a string
					output_type = (help_packets_def.DTYPE_NAMES[output_entry["type"]]).lower()
					cmdtable.register_output(command_entry["name"], output_entry["name"], output_type,
											output_entry["default"], output_entry["description"],
											output_entry["min"], output_entry["max"], output_entry["units"])


	return cmdtable

def parse_returned_help_packets(pkts, endianess = None):
	"""
	Processes the packets received from execting the 'help' command.

	:param SwiftPacketList pkts: Packet wrapper objects containing packet info returned by radio
	after executing "help".


	Parameters: packet list containing all the packets received from dlcmdinfo command
	Return: updated command table with new commands
	"""
	parsed_commands_info = dict()
	parsed_command_packets = list()
	parsed_input_packets = list()
	parsed_input_enum_packets = list()
	parsed_output_packets = list()
	parsed_command_descriptions = list()
	parsed_command_input_descriptions = list()
	parsed_command_input_enum_descriptions = list()
	parsed_command_output_descriptions = list()

	###########################################
	# [1] parsed all received help packets
	###########################################

	# parse all command packets
	command_pkts = pkts.find_command_data_by_name("command", all_matches=True)
	if command_pkts is not None:
		# parse and store each packet
		for packet in command_pkts:
			parsed_packet = parse_help_command_packet( packet )
			if parsed_packet is not None:
				parsed_command_packets.append( parsed_packet )
	else:
		raise SwiftHelpParseError("Did not receive any 'command' packets after executing 'help'.") 

	# parse all input packets
	input_pkts = pkts.find_command_data_by_name("command_input", all_matches=True)
	if input_pkts is not None:
		# parse every help input packet found
		for packet in input_pkts:
			parsed_packet = parse_help_input_packet( packet )
			if parsed_packet is not None:
				parsed_input_packets.append( parsed_packet )

	# parse all stropt enum input packets
	enum_pkts = pkts.find_command_data_by_name("command_input_enum", all_matches=True)
	if enum_pkts is not None:
		# parse each found packet
		for packet in enum_pkts:
			parsed_packet = parse_help_enum_packet( packet )
			if parsed_packet is not None:
				parsed_input_enum_packets.append( parsed_packet )

	# parse all output packets
	output_pkts = pkts.find_command_data_by_name("command_output", all_matches=True)
	if output_pkts is not None:
		for packet in output_pkts:
			parsed_packet = parse_help_output_packet( packet )
			if parsed_packet is not None:
				parsed_output_packets.append( parsed_packet )

	# parse all description packets
	command_desc_pkts = pkts.find_command_data_by_name("command_description", all_matches=True)
	input_desc_pkts = pkts.find_command_data_by_name("command_input_description", all_matches=True)
	input_enum_desc_pkts = pkts.find_command_data_by_name("command_input_enum_description", all_matches=True)
	output_desc_pkts = pkts.find_command_data_by_name("command_output_description", all_matches=True)
	# to shorten parsing code, zip the packets and storage lists so we can parse with just 2 nested for loops
	desc_pkts_list = [command_desc_pkts, input_desc_pkts, input_enum_desc_pkts, output_desc_pkts]
	desc_storage_lists = [parsed_command_descriptions, parsed_command_input_descriptions, parsed_command_input_enum_descriptions, parsed_command_output_descriptions]
	# for each type of desciption packets, parse and store in separate lists
	for packets, storage_list in zip(desc_pkts_list, desc_storage_lists):
		if packets is not None:
			for packet in packets:
				parsed_packet = parse_help_description_packet( packet )
				if parsed_packet is not None:
					storage_list.append( parsed_packet )

	###########################################
	# Organize parsed data into dict
	###########################################

	# create an entry for each parsed command, use name of command as key
	# entries should be dictionary that look like the following:
	for parsed_command_pkt in parsed_command_packets:

		# [1] create command entry
		command_entry = {
			"name": parsed_command_pkt.command_name,
			"name_hash": parsed_command_pkt.command_name_hash,
			"num_inputs": parsed_command_pkt.num_inputs,
			"num_outputs": parsed_command_pkt.num_outputs,
			"level": parsed_command_pkt.level,
			"description": None,
			"inputs": [],
			"outputs": []
		}

		# [2] get description string (if any)
		for parsed_cmd_desc_pkt in parsed_command_descriptions:
			if parsed_cmd_desc_pkt.command_name_hash == command_entry["name_hash"]:
				# store description in command entry
				command_entry["description"] = parsed_cmd_desc_pkt.description

		# [3] get command inputs (if any)
		if command_entry["num_inputs"] > 0:

			# from parsed input list, store all inputs associated with this command (if any)
			for parsed_input_pkt in parsed_input_packets:
				if parsed_input_pkt.command_name_hash == command_entry["name_hash"]:
					# create input entry
					input_entry = {
						"name": parsed_input_pkt.input_output_name,
						"name_hash": parsed_input_pkt.input_output_name_hash,
						"command_name_hash": parsed_input_pkt.command_name_hash,
						"optopt": parsed_input_pkt.optopt,
						"num_enums": parsed_input_pkt.num_enums,
						"type": parsed_input_pkt.type,
						"units": parsed_input_pkt.units,
						"min": parsed_input_pkt.min,
						"max": parsed_input_pkt.max,
						"default": parsed_input_pkt.default,
						"description": None,
						"enums": []
					}

					# check if input has a description
					for parsed_input_desc_pkt in parsed_command_input_descriptions:
						if parsed_input_desc_pkt.command_name_hash == command_entry["name_hash"]:
							if parsed_input_desc_pkt.input_output_name_hash == input_entry["name_hash"]:
								# store description in command entry
								input_entry["description"] = parsed_input_desc_pkt.description

					# check if input has any enums
					if input_entry["num_enums"] > 0:
						for parsed_enum_pkt in parsed_input_enum_packets:
							if parsed_enum_pkt.command_name_hash == command_entry["name_hash"]:
								if parsed_enum_pkt.input_output_name_hash == input_entry["name_hash"]:
									# create enum entry
									enum_entry = {
										"name": parsed_enum_pkt.enum_name,
										"name_hash": parsed_enum_pkt.enum_name_hash,
										"command_name_hash": parsed_enum_pkt.command_name_hash,
										"input_output_name_hash": parsed_enum_pkt.input_output_name_hash,
										"description": None
									}
									# check if enum has a description
									for parsed_enum_desc_pkt in parsed_command_input_enum_descriptions:
										if parsed_enum_desc_pkt.command_name_hash == command_entry["name_hash"]:
											if parsed_enum_desc_pkt.input_output_name_hash == input_entry["name_hash"]:
												if parsed_enum_desc_pkt.enum_name_hash == enum_entry["name_hash"]:
													# store description in command entry
													enum_entry["description"] = parsed_enum_desc_pkt.description

									# store entry in input enum list
									input_entry["enums"].append(enum_entry)

						# make sure all the enums have been parsed
						if input_entry["num_enums"] != len(input_entry["enums"]):
							raise SwiftHelpParseError("missing {} enums from {} command input {}".format( input_entry["num_enums"] - len(input_entry["enums"]),
							 																			command_entry["name"],
																										input_entry["name"] ) )

					# store input entry in command inputs list
					command_entry["inputs"].append( input_entry )

			# make sure all the enums have been parsed
			if command_entry["num_inputs"] != len(command_entry["inputs"]):
				raise SwiftHelpParseError("missing {} inputs for {} command".format( command_entry["num_inputs"] - len(command_entry["inputs"]),
				 																			command_entry["name"] ) )

		# [4] get command outputs (if any)
		if command_entry["num_outputs"] > 0:

			# from parsed output list, store all outputs associated with this command (if any)
			for parsed_output_pkt in parsed_output_packets:
				if parsed_output_pkt.command_name_hash == command_entry["name_hash"]:
					# create output entry
					output_entry = {
						"name": parsed_output_pkt.input_output_name,
						"name_hash": parsed_output_pkt.input_output_name_hash,
						"command_name_hash": parsed_output_pkt.command_name_hash,
						"optopt": parsed_output_pkt.optopt,
						"type": parsed_output_pkt.type,
						"units": parsed_output_pkt.units,
						"min": parsed_output_pkt.min,
						"max": parsed_output_pkt.max,
						"default": parsed_output_pkt.default,
						"description": None
					}

					# check if output has a description
					for parsed_output_desc_pkt in parsed_command_output_descriptions:
						if parsed_output_desc_pkt.command_name_hash == command_entry["name_hash"]:
							if parsed_output_desc_pkt.input_output_name_hash == output_entry["name_hash"]:
								# store description in command entry
								output_entry["description"] = parsed_output_desc_pkt.description

					# store input entry in command inputs list
					command_entry["outputs"].append( output_entry )

			# make sure all the outputs have been parsed
			if command_entry["num_outputs"] != len(command_entry["outputs"]):
				raise SwiftHelpParseError("missing {} outputs for {} command".format( command_entry["num_outputs"] - len(command_entry["outputs"]),
				 																			command_entry["name"] ) )

		# [5] store final command entry (Use name as key)
		parsed_commands_info[command_entry["name"]] = command_entry

	# [4] finally, return populated table, verification code, and number of new table entries
	return parsed_commands_info


def register_downloaded_commands(packets, transinfo):
	"""
	Description:

	Last Updated: 5/4/16

	"""
	pass

def get_io_field_val(val, dtype, order=help_packets_def.LITTLEENDIAN):
	"""
	Convert the min, max, and default values of the help i/o packets from a binary string into the
	proper data type for more convenient handling.

	Last Updated: 5/4/16

	:param str val: raw byte string value to convert.
	:param int dtype: the value data type, as defined in help_packets_def.
	:param str order: Endianess of the raw string, as defined in help_packets_def.
	"""
	return_val = None
	if dtype == help_packets_def.CMDTABLE_DTYPE_STR:
		return_val = val.replace("\x00", "")
	elif (dtype == help_packets_def.CMDTABLE_DTYPE_INT) or (dtype == help_packets_def.CMDTABLE_DTYPE_ENUM) or (dtype == help_packets_def.CMDTABLE_DTYPE_HEX):
		return_val = struct.unpack("{}i".format(order), val[:help_packets_def.DTYPE_SIZE_INT])[0]
	elif (dtype == help_packets_def.CMDTABLE_DTYPE_BOOL):
		return_val = bool(struct.unpack("{}i".format(order), val[:help_packets_def.DTYPE_SIZE_INT])[0])
	elif dtype == help_packets_def.CMDTABLE_DTYPE_FLOAT:
		return_val = struct.unpack("{}d".format(order), val[:help_packets_def.DTYPE_SIZE_FLOAT])[0]
	elif dtype == help_packets_def.CMDTABLE_DTYPE_BIN:
		return_val = val
	else:
		return_val = val

	return return_val

def parse_help_command_packet(buf, order=help_packets_def.LITTLEENDIAN):
	"""
	parse the raw list of bytes into a HelpCommandPacket object.

	Last Updated: 5/4/16

	:param list buf: raw byte string value to convert.
	:param str order: Endianess of the raw string, as defined in help_packets_def.

	.. note:: order parameter is currently unused.
	"""
	if type(buf) is not list:
		raise SwiftHelpParseError("buffer must be a list type. not {}".format(type(buf).__name__))

	cmd_packet = help_packets_def.HelpCommandPacket( "".join(buf) )

	# remove null and zero pads from name
	cmd_packet.command_name = str(cmd_packet.command_name).replace("\x00", "")
	# print "\nCommand Packet for '{}':".format(str(cmd_packet.command_name).replace("\x00", ""))
	# cmd_packet.dump()
	return cmd_packet

def parse_help_io_packet(buf, order=help_packets_def.LITTLEENDIAN):
	"""
	parse the raw list of bytes into a HelpIOPacket object.

	Last Updated: 5/4/16

	:param list buf: raw byte string value to convert.
	:param str order: Endianess of the raw string, as defined in help_packets_def.

	.. note:: order parameter is currently unused.
	"""
	if type(buf) is not list:
		raise SwiftHelpParseError("buffer must be a list type. not {}".format(type(buf).__name__))

	io_packet = help_packets_def.HelpIOPacket( "".join(buf) )

	# remove null and zero pads from name
	io_packet.input_output_name = str(io_packet.input_output_name).replace("\x00", "")
	io_packet.units = str(io_packet.units).replace("\x00", "")
	if io_packet.optopt != 0:
		io_packet.optopt = chr(io_packet.optopt)
	else:
		io_packet.optopt = None

	io_packet.min = get_io_field_val(io_packet.min, io_packet.type)
	io_packet.max = get_io_field_val(io_packet.max, io_packet.type)
	io_packet.default = get_io_field_val(io_packet.default, io_packet.type)
	if io_packet.min == '':
		io_packet.min = None
	if io_packet.max == '':
		io_packet.max = None
	if io_packet.default == '':
		io_packet.default = None

	# add a field that contains any enumerations (this will be left empty for now)
	if io_packet.num_enums == 0:
		io_packet.enums = None
	else:
		io_packet.enums = []

	return io_packet

def parse_help_output_packet(buf, order=help_packets_def.LITTLEENDIAN):
	"""
	parse the raw list of bytes into a HelpIOPacket object.

	Last Updated: 5/4/16

	:param list buf: raw byte string value to convert.
	:param str order: Endianess of the raw string, as defined in help_packets_def.

	.. note:: order parameter is currently unused.
	"""
	return parse_help_io_packet(buf)

def parse_help_input_packet(buf, order=help_packets_def.LITTLEENDIAN):
	"""
	parse the raw list of bytes into a HelpIOPacket object.

	Last Updated: 5/4/16

	:param list buf: raw byte string value to convert.
	:param str order: Endianess of the raw string, as defined in help_packets_def.

	.. note:: order parameter is currently unused.
	"""
	return parse_help_io_packet(buf)

def parse_help_description_packet(buf, order=help_packets_def.LITTLEENDIAN):
	"""
	parse the raw list of bytes into a HelpDescriptionPacket object.

	Last Updated: 5/4/16

	:param list buf: raw byte string value to convert.
	:param str order: Endianess of the raw string, as defined in help_packets_def.

	.. note:: order parameter is currently unused.
	"""
	if type(buf) is not list:
		raise SwiftHelpParseError("buffer must be a list type. not {}".format(type(buf).__name__))

	desc_packet = help_packets_def.HelpDescriptionPacket( "".join(buf) )
	desc_packet.description = str(desc_packet.description).replace("\x00", "")
	return desc_packet

def parse_help_enum_packet(buf, order=help_packets_def.LITTLEENDIAN):
	"""
	parse the raw list of bytes into a HelpStroptEnumPacket object.

	Last Updated: 5/4/16

	:param list buf: raw byte string value to convert.
	:param str order: Endianess of the raw string, as defined in help_packets_def.

	.. note:: order parameter is currently unused.
	"""
	if type(buf) is not list:
		raise SwiftHelpParseError("buffer must be a list type. not {}".format(type(buf).__name__))

	enum_packet = help_packets_def.HelpStroptEnumPacket( "".join(buf) )

	enum_packet.enum_name = str(enum_packet.enum_name).replace("\x00", "")
	return enum_packet

class SwiftHelpParseError(RuntimeError):
	pass

if __name__ == '__main__':

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

	command_input2 = [
		'\x11', '\x90', '\xf4', '\xec',

		'\x00', '\x00', '\x00', '\x00',

		'\x00', '\x00', '\x03', '\x00',

		'\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00',
		'\x01', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00',
		'd', 'i', 's', 'a',
		'b', 'l', 'e', '_',
		's', 'y', 'n', 'c',
		'\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00']

	command_input3 = ['\x11', '\x90', '\xbe', '\r', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x04',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\xf0', '\xbf', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\xf0', '?', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', 's', 'y', 'n', 'c', '_', 'b', 'i', 'a', 's', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00']

	command_output1 = ['\x11', '\x90', '\xf1', '\xbe', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x03', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\xff', '\xff', '\xff', '\x7f', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', 's', 'e', 'c', 'o', 'n', 'd', 's', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00']
	command_output2 = ['\x11', '\x90', '\x9c', '\xbb', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x04', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\xf0', '?', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', 's', 'u', 'b', '_', 's', 'e', 'c', 'o', 'n', 'd', 's', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00']
	command_output3 = ['\x11', '\x90', 'A', '\xb4', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x01', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', 's', 'y', 'n', 'c', '_', 's', 't', 'a', 't', 'e', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00']
	command_output4 = ['\x11', '\x90', '\xbe', '\r', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x04', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\xf0', '\xbf', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\xf0', '?', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', 's', 'y', 'n', 'c', '_', 'b', 'i', 'a', 's', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00']
	command_output5 = ['\x11', '\x90', 'J', '\x9c', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x04', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\xf0', '\xbf', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\xf0', '?', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', 's', 'y', 'n', 'c', '_',
		 'e', 'r', 'r', 'o', 'r', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		 '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00']

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
	command_enum2 = ['\xfb', '\xae', '\x11', '\x19', 'C', '\x90', '\x00', '\x00', 'o', 'n', 'e', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00']
	command_enum3 = ['\xfb', '\xae', '\x11', '\x19', '[', '\xbb', '\x00', '\x00', 't', 'w', 'o', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00']
	command_enum4 = ['\xfb', '\xae', '\x11', '\x19', '\x1a', 'o', '\x00', '\x00', 't', 'h', 'r', 'e', 'e',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00', '\x00',
		'\x00', '\x00', '\x00', '\x00', '\x00']

	# sample = struct.pack("20p", x)
	# print len(cmd_pkt)
	# print len("".join(cmd_pkt))
	# load sample bytestring into an IP packet
	cmd_packet = parse_help_command_packet(cmd_pkt)
	print "\nCommand Packet for '{}':".format( cmd_packet.command_name )
	cmd_packet.dump()

	# print len(command_input1)
	# print len(command_input2)
	# print len(command_input3)

	print "\nInput Packets:"
	input_packets = list()
	input_packets.append( parse_help_input_packet(command_input1) )
	input_packets.append( parse_help_input_packet(command_input2) )
	input_packets.append( parse_help_input_packet(command_input3) )
	for input_packet in input_packets:
		print "\n{} ".format(input_packet.input_output_name)
		input_packet.dump(show_all=True)

	print "\nOutput Packets:"
	output_packets = list()
	output_packets.append( parse_help_output_packet(command_output1) )
	output_packets.append( parse_help_output_packet(command_output2) )
	output_packets.append( parse_help_output_packet(command_output3) )
	output_packets.append( parse_help_output_packet(command_output4) )
	output_packets.append( parse_help_output_packet(command_output5) )
	for output_packet in output_packets:
		print "\n{} ".format(output_packet.input_output_name)
		output_packet.dump(show_all=True)

	print "\nDescription Packet:"
	desc_packet = parse_help_description_packet(command_description)
	desc_packet.dump()

	print "\nEnum Packet:"
	enum_packets = list()
	enum_packets.append( parse_help_enum_packet(command_enum1) )
	enum_packets.append( parse_help_enum_packet(command_enum2) )
	enum_packets.append( parse_help_enum_packet(command_enum3) )
	enum_packets.append( parse_help_enum_packet(command_enum4) )
	for enum_packet in enum_packets:
		print "\n{} ".format(enum_packet.enum_name)
		enum_packet.dump(show_all=True)
