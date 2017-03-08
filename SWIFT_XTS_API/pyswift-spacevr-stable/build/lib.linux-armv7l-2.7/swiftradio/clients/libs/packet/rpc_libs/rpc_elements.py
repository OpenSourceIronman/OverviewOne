from ...utils import dataconversions

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__company__ = "Tethers Unlimited Inc."
__status__ = "Development"
__date__ = "Late Updated: 10/29/14"


# ========================================================================================================================
# RPC Control Sequence and Named Parameters/Response Base Classes
# ========================================================================================================================

class RPCControlSequence:
	"""
	Description:
	Parameters: 
	Return: 
	"""
	def __init__(self, endianess="little"):
		"""
		Description:
		Parameters: 
		Return: 
		"""
		# used to pack/unpack fields according to this endianess
		self.endianess = endianess

		# header field
		self.header = RPCControlSequenceHeader()

		# these info fields will vary for each control sequence
		self.info_fields = list()
		self.info_fields = self._define_info_fields()	

	# Public:	
	def generate_default_tag(self):
		"""
		Description: 
		Parameters: 
		Return: 
		"""
		return self.header.get_ctrl_code_str()

	def get_element_type(self):
		"""
		Description: 
		Parameters: 
		Return: 
		"""
		return self.element_type

	def set_header(self, header):
		"""
		Description: 
		Parameters: 
		Return: 
		"""
		if header.__class__.__name__ == "RPCControlSequenceHeader":
			self.header = header
		else:
			print "header object not a RPCControlSequenceHeader class"

	def	get_control_code(self):
		"""
		Description: 
		Parameters: 
		Return: 
		"""
		return self.header.get_ctrl_code()

	def	get_control_code_str(self):
		"""
		Description: 
		Parameters: 
		Return: 
		"""
		return self.header.get_ctrl_code_str()			
	
	def parse_raw_header_fields(self, buffer, buffer_length, buffer_endianess="little"):
		"""
		Description: 
		Parameters: 
		Return: 
		"""
		return self.header.parse_raw_header(buffer, buffer_length, buffer_endianess)

	def get_info_fields(self):
		"""
		Description: 
		Parameters: 
		Return: 
		"""
		return self.info_fields

	def get_header_fields(self):
		"""
		Description: 
		Parameters: 
		Return: 
		"""
		return self.header.get_fields()

	def get_fields(self):
		"""
		Description: 
		Parameters: 
		Return: 
		"""
		# get header fields 
		all_fields = self.header.get_fields()
		# get info fields
		all_fields += self.info_fields
		# return combined list
		return all_fields

	def get_field_val(self, field_name, field_target=None):
		"""
		Description: 
		Parameters: 
		Return: 
		"""
		# search header for matching field name
		if field_target == None or field_target == "header":
			for field in self.header.get_fields():
				if field_name == field[0]:
					# return current value stored in this field
					return field[1]

		# search info fields for matching field name
		if field_target == None or field_target == "info":
			for field in self.info_fields:
				if field_name == field[0]:
					# return current value stored in this field
					return field[1]

		return None

	def parse_raw_info_fields(self, buffer, buffer_length, buffer_endianess="little"):
		"""
		Description: 
		Parameters: 
		Return: 
		"""
		parse_result = 1
		byte_ctr = 0
		
		# set the endianess that buffer data will be converted to
		if buffer_endianess == "little":
			conversion_endianess = "big"
		else:
			conversion_endianess = "little"

		# for every info field, parse the buffer and store the value in the info field
		for field in self.info_fields:
			parsed_field_val = None

			# parse raw buffer
			data_type = field[2]
			field_size = field[3]
			parsed_field_val = self._parse_raw_field(buffer[byte_ctr:byte_ctr+field_size], field_size, data_type, conversion_endianess)
			# store parsed value
			field[1] = parsed_field_val
			# increment buffer byte counter
			byte_ctr += field_size

		# return status (not used at this point)
		return parse_result

	def print_fields(self):
		"""
		Description: 
		Parameters: 
		Return: 
		"""		
		self.header.print_fields_info()
		for field in self.info_fields:
			print "{}: {}".format(field[0], field[1])

	# Private:
	def _define_info_fields(self):	
		pass	

	def _parse_raw_field(self, field_buffer, field_length, data_type, endianess="little"):
		"""
		Description: 
		Parameters: 
		Return: 
		"""
		parsed_val = None

		# using data type, call correct conversion function
		if "uint" in data_type:
			parsed_val = dataconversions.bytelist_to_uint(field_buffer, endianess, field_length)
		elif "int" in data_type:
			parsed_val = dataconversions.bytelist_to_int(field_buffer, endianess, field_length)
		elif "float" in data_type:
			parsed_val = dataconversions.bytelist_to_int(field_buffer, endianess, field_length)
		else:
			print "***invalid '{}' data type. only 'uint', 'int' or 'float' types are valid***".format(data_type)
			return -1

		return parsed_val

	def _get_field_size(self, data_type):
		"""
		Description: 
		Parameters: 
		Return: 
		"""
		data_length = None
		# get data length based on data type
		if "8" in data_type:
			data_length == 1
		elif "16" in data_type:
			data_length == 2
		elif "32" in data_type:
			data_length == 4
		elif "64" in data_type:
			data_length == 8
		else:
			print "***invalid '{}' data type. cannot interpret data length in bytes***".format(data_length)
			return -1

		return data_length

class RPCControlSequenceHeader:
	"""
	Description: 
	Parameters: 
	Return:
	"""	
	def __init__(self, endianess="little"):
		"""
		Description:
		Parameters: 
		Return: 
		"""
		self.endianess = endianess
		self.HEADER_LENGTH = 4
		self.MAX_DATA_LENGTH = 4
		# header fields
		self.ESCAPE = ["escape", 0xFF00, "uint16", 2]	# frame escape sequence 2 byte constant
		self.ctrl_code = ["code", None, "int8", 1]
		self.data_length = ["length", None, "uint8", 1]

		# miscellaneous info
		self.rpc_ctrl_codes_dict = self.get_control_codes()	

	def	get_control_codes(self):
		"""
		Description: 
		Parameters: 
		Return: 
		"""	
		control_codes =	{32:"EXECTIME",
						16:"THROTTLE",
						8:"CMDERR",
						2:"DESYNC",
						1:"SYNC",
						0:"NOOP",
						-1:"INVSYNC",
						-2:"INVCMD",
						-3:"NOARG",
						-4:"INVPARAM"}

		return control_codes				

	def	parse_raw_header(self, buffer, buffer_length, buffer_endianess="little"):
		"""
		Description: 
		Parameters: 
		Return: 1 if parse was successful or negative value if the buffer is not a valid header
		"""
		return_int = 1
		esc = 0
		ctrl = 0
		len = 0

		# set the endianess that buffer data will be converted to
		if buffer_endianess == "little":
			conversion_endianess = "big"
		else:
			conversion_endianess = "little"

		# parse escape value 
		esc = dataconversions.bytelist_to_uint([buffer[0], buffer[1]], conversion_endianess, 2)

		# escape value constant, error check received value
		if esc != self.ESCAPE[1]:
			# print "invalid escape code '{}'".format(esc)
			return_int = -1

		# parse control code
		ctrl = dataconversions.bytelist_to_int([buffer[2]], conversion_endianess, 1)
		if ctrl not in self.rpc_ctrl_codes_dict:
			# print "control code '{}' not recognized.".format(ctrl)
			return_int = -2
			self.ctrl_code[1] = None
		else:
			self.ctrl_code[1] = ctrl

		# parse length
		len = dataconversions.bytelist_to_uint([buffer[3]], conversion_endianess, 1)
		if len > self.MAX_DATA_LENGTH:
			return_int = -3
			self.data_length[1] = None
			# print "control code '{}' not recognized.".format(len)
		else:
			self.data_length[1] = len
		
		return return_int	

	def	get_fields(self):
		"""
		Description: 
		Parameters: 
		Return: 
		"""
		return [self.ESCAPE, self.ctrl_code, self.data_length]
	
	def	get_ctrl_code_str(self):
		"""
		Description: 
		Parameters: 
		Return: 
		"""
		code_int = self.ctrl_code[1]
		named_ctrl_code = ""

		if code_int in self.rpc_ctrl_codes_dict:
			named_ctrl_code = self.rpc_ctrl_codes_dict[code_int]
		else:
			named_ctrl_code = "UNKNOWN"

		return named_ctrl_code

	def	get_ctrl_code(self):
		"""
		Description: 
		Parameters: 
		Return: 
		"""
		return self.ctrl_code[1]

	def print_fields_info(self):
		"""
		Description: 
		Parameters: 
		Return: 
		"""	
		print "escape: {}".format(self.ESCAPE[1])
		print "code: {}".format(self.ctrl_code[1])
		print "length: {}".format(self.data_length[1])


class RPCParameterAndResponse:
	"""
	Description:
	Parameters: 
	Return: 
	"""
	def __init__(self, endianess="little"):
		"""
		Description:
		Parameters: 
		Return: 
		"""
		# used to pack/unpack fields according to this endianess
		self.endianess = endianess

		# header field
		self.header = RPCParameterAndResponseHeader()

		# info fields
		self.info_fields = list()
		self.info_fields.append(["data", list(), "uint8", None])

	def generate_default_tag(self):
		"""
		Description: 
		Parameters: 
		Return: 
		"""
		return "COMMAND DATA"

	def set_header(self, header):
		"""
		Description: 
		Parameters: 
		Return: 
		"""
		if header.__class__.__name__ == "RPCParameterAndResponseHeader":
			self.header = header
		else:
			print "header object not a RPCParameterAndResponseHeader class"
			return -1

	def get_info_fields(self):
		"""
		Description: 
		Parameters: 
		Return: 
		"""
		return self.info_fields

	def get_header_fields(self):
		"""
		Description: 
		Parameters: 
		Return: 
		"""
		return self.header.get_fields()

	def get_fields(self):
		"""
		Description: 
		Parameters: 
		Return: 
		"""
		# get header fields 
		all_fields = self.header.get_fields()
		# get info fields
		all_fields += self.info_fields
		# return combined list
		return all_fields

	def get_field_val(self, field_name, field_type=None):
		"""
		Description: 
		Parameters: 
		Return: 
		"""
		# search header for matching field name
		if field_type == None or field_type == "header":
			for field in self.header.get_fields():
				if field_name == field[0]:
					# return current value stored in this field
					return field[1]
					
		# search info fields for matching field name
		if field_type == None or field_type == "info":
			for field in self.info_fields:
				if field_name == field[0]:
					# return current value stored in this field
					return field[1]

		return None

	def	parse_raw_header(self, buffer, buffer_length, buffer_endianess="little"):		
		"""
		Description: 
		Parameters: 
		Return: 
		"""
		return self.header.parse_raw_header()

	def parse_raw_data_fields(self, buffer, buffer_length, buffer_endianess="little"):
		"""
		Description: 
		Parameters: 
		Return: 
		"""
		# format the raw data in the proper endianess
		#raw_data = dataconversions.format_bytelist_endianess(buffer, buffer_length, buffer_endianess)	
		raw_data = buffer
		# make sure to store only the data (and no zero padding that was previously added for word alignment)
		if len(raw_data) != buffer_length:
			raw_data = raw_data[:buffer_length]

		# store the data and length information
		self.info_fields[0][1] = raw_data
		self.info_fields[0][3] = len(raw_data)

	def print_fields(self):
		"""
		Description: 
		Parameters: 
		Return: 
		"""		
		byte_ctr = 0
		raw_data = self.info_fields[0][1]
		self.header.print_fields_info()
		print "data: {}".format(raw_data)


class RPCParameterAndResponseHeader:
	"""
	Description: 
	Parameters: 
	Return:
	"""	
	def __init__(self, endianess="little"):
		"""
		Description:
		Parameters: 
		Return: 
		"""
		self.endianess = endianess
		self.HEADER_LENGTH = 4
		self.MAX_DATA_LENGTH = 0xFFFF
		self.INVALID_NAMES = [0xFFFF, 0xFF00, 0x00FF]

		# header fields
		self.name = ["name", None, "uint16", 2]	
		self.data_length = ["length", None, "uint16", 2]	

	def	get_fields(self):
		"""
		Description: 
		Parameters: 
		Return: 
		"""
		return [self.name, self.data_length]

	def	parse_raw_header(self, buffer, buffer_length, buffer_endianess="little"):
		"""
		Description: 
		Parameters: 
		Return: 1 if parse was successful or -1 if the buffer was not a valid header
		"""
		return_int = 1
		name = 0
		len = 0

		# set the endianess that buffer data will be converted to
		if buffer_endianess == "little":
			conversion_endianess = "big"
		else:
			conversion_endianess = "little"

		# parse the hash name
		name = dataconversions.bytelist_to_uint([buffer[0], buffer[1]], conversion_endianess, 2)

		# error check hash name
		if name in self.INVALID_NAMES:
			return_int = -1
			self.name[1] = None
		else:
			self.name[1] = name

		# parse the data field length
		len = dataconversions.bytelist_to_uint([buffer[2], buffer[3]], conversion_endianess, 2)

		# error check length value
		if len > self.MAX_DATA_LENGTH:
			return_int = -1
			self.data_length[1] = None
		else:
			self.data_length[1] = len
		
		return return_int	

	def print_fields_info(self):
		"""
		Description: 
		Parameters: 
		Return: 
		"""	
		print "name: {}".format(self.name[1])
		print "length: {}".format(self.data_length[1])	

# ========================================================================================================================
# Daughter Control Sequence Classes 
# ========================================================================================================================

class Exectime(RPCControlSequence):
	"""
	Description:
	Parameters: 
	Return: 
	"""

	def _define_info_fields(self):	
		"""
		Description:
		Parameters: 
		Return: 
		"""	
		info_field = list()

		info_field.append(["duration", None, "uint32", 4])
		
		return info_field

class Throttle(RPCControlSequence):
	"""
	Description:
	Parameters: 
	Return: 
	"""

	def _define_info_fields(self):	
		"""
		Description:
		Parameters: 
		Return: 
		"""	
		info_field = list()

		info_field.append(["duration", None, "uint32", 4])
		
		return info_field

class Cmderr(RPCControlSequence):
	"""
	Description:
	Parameters: 
	Return: 
	"""

	def _define_info_fields(self):	
		"""
		Description:
		Parameters: 
		Return: 
		"""	
		info_field = list()

		info_field.append(["value", None, "int32", 4])

		return info_field

class Sync(RPCControlSequence):
	"""
	Description:
	Parameters: 
	Return: 
	"""

	def _define_info_fields(self):	
		"""
		Description:
		Parameters: 
		Return: 
		"""	
		info_field = list()

		info_field.append(["name", None, "uint16", 2])
		info_field.append(["transid", None, "uint16", 2])

		return info_field

class Desync(RPCControlSequence):
	"""
	Description:
	Parameters: 
	Return: 
	"""

	def _define_info_fields(self):	
		"""
		Description:
		Parameters: 
		Return: 
		"""	
		info_field = list()

		info_field.append(["name", None, "uint16", 2])
		info_field.append(["transid", None, "uint16", 2])

		return info_field		

class Noop(RPCControlSequence):
	"""
	Description:
	Parameters: 
	Return: 
	"""
	def _define_info_fields(self):	
		"""
		Description:
		Parameters: 
		Return: 
		"""	
		info_field = list()

		return info_field

class Invsync(RPCControlSequence):
	"""
	Description:
	Parameters: 
	Return: 
	"""

	def _define_info_fields(self):	
		"""
		Description:
		Parameters: 
		Return: 
		"""	
		info_field = list()

		info_field.append(["name", None, "uint16", 2])
		info_field.append(["transid", None, "uint16", 2])

		return info_field

class Invcmd(RPCControlSequence):
	"""
	Description:
	Parameters: 
	Return: 
	"""

	def _define_info_fields(self):	
		"""
		Description:
		Parameters: 
		Return: 
		"""	
		info_field = list()

		return info_field

class Noarg(RPCControlSequence):
	"""
	Description:
	Parameters: 
	Return: 
	"""

	def _define_info_fields(self):	
		"""
		Description:
		Parameters: 
		Return: 
		"""	
		info_field = list()

		info_field.append(["param", None, "uint16", 2])
		
		return info_field

class Invparam(RPCControlSequence):
	"""
	Description:
	Parameters: 
	Return: 
	"""

	def _define_info_fields(self):	
		"""
		Description:
		Parameters: 
		Return: 
		"""	
		info_field = list()

		info_field.append(["param", None, "uint16", 2])
		info_field.append(["error", None, "uint16", 2])
		
		return info_field
