import sys
import struct
NATIVEA = '@'                   # native        native
NATIVE = '='                    # native        standard
LITTLEENDIAN = '<'              # little        standard
BIGENDIAN = '>'                 # big           standard
NETWORK = '!'                   # network       standard

VALID_ENDIANESS_TYPES = [ NATIVEA, NATIVE, LITTLEENDIAN, BIGENDIAN, NETWORK ]

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__status__ = "Development"
__date__ = "Late Updated: 10/30/14"

def bytelist_to_uint(bytelist, endianess='little', lsize = None):
	"""
	Author: S. Alvarado
	Updated: 5/8/15 (SRA)
	Description: convert a list of bytes (string objects) into a Python unsigned integer
	Parameters: bytelist - a list of bytes
				lsize - length of list. If not included, len() function used to determine length.
				endianess - Endianess (https://en.wikipedia.org/wiki/Endianness) of the list of bytes
	Return: unsigned integer converted from byte list
	"""
	if(lsize == 1):
		return struct.unpack_from("<B", "".join(bytelist))[0]
	if(lsize == 2):
		return struct.unpack_from("<H", "".join(bytelist))[0]
	if(lsize == 4):
		return struct.unpack_from("<I", "".join(bytelist))[0]

def bytelist_to_int(bytelist, endianess='little', lsize = None):
	"""
	Author: S. Alvarado
	Updated: 5/8/15 (SRA)
	Description: convert a list of bytes (string objects) into a Python integer
	Parameters: bytelist - a list of bytes
				lsize - length of list. If not included, len() function used to determine length.
				endianess - Endianess (https://en.wikipedia.org/wiki/Endianness) of the list of bytes
	Return: integer converted from byte list
	"""
	if(lsize == 1):
		return struct.unpack_from("<b", "".join(bytelist))[0]
	if(lsize == 2):
		return struct.unpack_from("<h", "".join(bytelist))[0]
	if(lsize == 4):
		return struct.unpack_from("<i", "".join(bytelist))[0]
		

def bytelist_to_float(bytelist, endianess='little', lsize = None):
	"""
	Author: S. Alvarado
	Updated: 5/8/15 (SRA)
	Description: convert a list of bytes (string objects) into a Python float
	Parameters: bytelist - a list of bytes
				lsize - length of list. If not included, len() function used to determine length.
				endianess - Endianess (https://en.wikipedia.org/wiki/Endianness) of the list of bytes
	Return: float converted from byte list
	"""
	return struct.unpack_from("<d", "".join(bytelist))[0]

def bytelist_to_fixedfloat(bytelist, endianess='little', lsize = None):
	"""
	Author: S. Alvarado
	Updated: 5/8/15 (SRA)
	Description: convert a list of bytes (string objects) into a Python fixed float
	Parameters: bytelist - a list of bytes
				lsize - length of list. If not included, len() function used to determine length.
				endianess - Endianess (https://en.wikipedia.org/wiki/Endianness) of the list of bytes
	Return: fixed float converted from byte list
	"""
	fixedfloat = 0x0000
	castedint = bytelist_to_uint(bytelist, endianess='big', lsize = 2)

	if(castedint >= 2**15):
		castedint = -2**16 + castedint

	fixedfloat = (float(castedint)/(2**15))
	return fixedfloat

def float_to_bytelist(value, endianess='big', bytelist_size=8):
	"""
	Author: S. Alvarado
	Updated: 5/8/15 (SRA)
	Description: convert a python float object into a list of bytes (string objects) in the specified Endianess
	Parameters: value - float value to convert to list
				bytelist_size - byte-width of float value
				endianess - Endianess (https://en.wikipedia.org/wiki/Endianness) of the list of bytes
	Return: list of bytes representing float value
	"""
	if bytelist_size > 8:
		bytelist_size = 8

	if endianess == 'big' or endianess == 'network':
		bytelist = list(struct.pack("!d",value))
		bytelist = bytelist[:bytelist_size]
	elif endianess == 'little':
		bytelist = list(struct.pack("<d",value))
		bytelist = bytelist[(8-bytelist_size):]
	else:
		return -1

	return bytelist

def uint_to_bytelist(value, endianess='big', bytelist_size=4):
	"""
	Author: S. Alvarado
	Updated: 5/8/15 (SRA)
	Description: convert a python unsigned integer object into a list of bytes (string objects) in the specified Endianess
	Parameters: value - unsigned integer value to convert to list
				bytelist_size - byte-width of unsigned integer value
				endianess - Endianess (https://en.wikipedia.org/wiki/Endianness) of the list of bytes
	Return: list of bytes representing unsigned integer value
	"""
	if endianess == 'big' or endianess == 'network':
		bytelist = list(struct.pack("!I",value))
		if bytelist_size > 4:
			bytelist_size = 4
		bytelist = bytelist[(4-bytelist_size):]
	elif endianess == 'little':
		bytelist = list(struct.pack("<I",value))
		if bytelist_size > 4:
			bytelist_size = 4
		bytelist = bytelist[:bytelist_size]
	else:
		return -1

	return bytelist

def int_to_bytelist(value, endianess='big', bytelist_size=4):
	"""
	Author: S. Alvarado
	Updated: 5/8/15 (SRA)
	Description: convert a python integer object into a list of bytes (string objects) in the specified Endianess
	Parameters: value - integer value to convert to list
				bytelist_size - byte-width of integer value
				endianess - Endianess (https://en.wikipedia.org/wiki/Endianness) of the list of bytes
	Return: list of bytes representing integer value
	"""
	if endianess == 'big' or endianess == 'network':
		bytelist = list(struct.pack("!i",value))
		if bytelist_size > 4:
			bytelist_size = 4
		bytelist = bytelist[(4-bytelist_size):]
	elif endianess == 'little':
		bytelist = list(struct.pack("<i",value))
		if bytelist_size > 4:
			bytelist_size = 4
		bytelist = bytelist[:bytelist_size]
	else:
		return -1

	return bytelist

def format_bytelist_endianess(bytelist, bytelist_size=4, endianess='big'):
	"""
	Author: S. Alvarado
	Updated: 5/8/15 (SRA)
	Description:
	Parameters:
	Return:
	"""
	system_endianess = sys.byteorder

	if endianess == system_endianess:
		bytelist = bytelist[::-1]

	return bytelist

def convert_raw_bytelist(bytelist, data_type):
	"""
	Author: S. Alvarado
	Updated: 5/8/15 (SRA)
	Description:
	Parameters:
	Return:
	"""
	parsed_val = None
	data_length = None
	# for numeric values of fixed length, set the length for subsequent conversions
	if data_type in ["uint", "int", "float"]:
		if "uint" in data_type:
			data_length = 4
		elif "int" in data_type:
			data_length = 4
		elif "float" in data_type:
			data_length = 8

		# make sure the bytelist has a matching length before performing the conversions
		if (len(bytelist) != data_length):
			# print "***input bytelist length ({}) does not match input data type length ({})***".format(len(bytelist), data_length)
			return None

	# using given data type, call correct conversion function
	if "uint" in data_type:
		parsed_val = bytelist_to_uint(bytelist, lsize = data_length)
	elif "int" in data_type:
		parsed_val = bytelist_to_int(bytelist, lsize = data_length)
	elif "float" in data_type:
		parsed_val = bytelist_to_float(bytelist, lsize = data_length)
	elif "str" in data_type:
		# remove any NULL bytes before forming string!
		if bytelist[len(bytelist)-1] == '\x00':
			del bytelist[len(bytelist)-1]

		# convert list to string
		parsed_val = "".join(bytelist)
	elif "raw" in data_type:
		pass
	else:
		# print "***invalid '{}' data type. only 'uint', 'int', 'float' or 'str' types are valid***".format(data_type)
		parsed_val = None
	return parsed_val

def convert_raw(buf, data_type, order=NETWORK):
	"""
	Author: S. Alvarado
	Updated: 5/8/15 (SRA)
	Description:
	Parameters:
	Return:
	"""
	parsed_val = None
	data_length = None

	if type(buf) is not str:
		raise SwiftConversionsError("buf must be string data type, not {}".format(type(buf).__name__))

	# error check order!
	if order not in VALID_ENDIANESS_TYPES:
		raise SwiftConversionsError("invalid order '{}'. valid orders: {}".format(order, ",".join(VALID_ENDIANESS_TYPES) ))

	# for numeric values of fixed length, set the length for subsequent conversions
	if data_type in ["uint", "int", "float"]:
		if "uint" in data_type:
			data_length = 4
		elif "int" in data_type:
			data_length = 4
		elif "float" in data_type:
			data_length = 8

		# make sure the bytelist has a matching length before performing the conversions
		if (len(buf) != data_length):
			# print "***input bytelist length ({}) does not match input data type length ({})***".format(len(bytelist), data_length)
			data_type = "raw"
	
	order=LITTLEENDIAN
	# using given data type, call correct conversion function
	if "uint" in data_type:
		parsed_val = struct.unpack(order+"I", buf)[0]
	elif "int" in data_type:
		parsed_val = struct.unpack(order+"i", buf)[0]
	elif "float" in data_type:
		parsed_val = struct.unpack(order+"d", buf)[0]
	elif "str" in data_type:
		# remove any NULL bytes before forming string!
		parsed_val = buf.replace("\x00", "")

	elif "raw" in data_type:
		parsed_val = list(buf)

	else:
		# print "***invalid '{}' data type. only 'uint', 'int', 'float' or 'str' types are valid***".format(data_type)
		parsed_val = list(buf)

	return parsed_val

class SwiftConversionsError(RuntimeError):
	pass

if __name__ == '__main__':
	uint_val = 63907
	float_val = float("1315e6")
	uint_bytelist = ['\xF9','\xA3','\x00','\x00']
	float_bytelist = ['\x40','\x25','\x00','\x00',
					  '\x00','\x00','\x00','\x00']

	print "\nuint conversions:"
	cmd_fletcher = uint_to_bytelist(uint_val, bytelist_size=4)
	print cmd_fletcher
	cmd_fletcher = uint_to_bytelist(uint_val, endianess='little',bytelist_size=4)
	print cmd_fletcher
	cmd_fletcher = uint_to_bytelist(uint_val, endianess='big',bytelist_size=2)
	print cmd_fletcher
	cmd_fletcher = uint_to_bytelist(uint_val, endianess='little',bytelist_size=2)
	print cmd_fletcher
	print "\n"

	print "float conversions:"
	cmd_fletcher = float_to_bytelist(float_val, bytelist_size=8)
	print cmd_fletcher
	float_bytelist = float_to_bytelist(float_val, endianess='little',bytelist_size=8)
	print float_bytelist
	print "\n"

	print "bytelist to uint conversion:"
	cmd_fletcher = bytelist_to_uint(uint_bytelist, endianess='little')
	print cmd_fletcher
	cmd_fletcher = bytelist_to_uint(uint_bytelist, endianess='big')
	print cmd_fletcher

	print ""
	print "bytelist to float conversion:"
	cmd_fletcher = bytelist_to_float(float_bytelist, endianess='big')
	print cmd_fletcher
	cmd_fletcher = bytelist_to_float(float_bytelist, endianess='little')
	print cmd_fletcher
