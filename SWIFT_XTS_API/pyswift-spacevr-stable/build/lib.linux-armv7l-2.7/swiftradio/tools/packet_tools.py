import dataconversions
import algorithms

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__status__ = "Development"
__date__ = "Late Updated: 05/05/16"

def find_command_data_by_name(command_data, output_name, output_dtype='raw', all_matches=False):
	"""
	Searches a dictionary for command data with the specified output name (in hash integer form). \
	This can be useful if a particular radio command has unregistered outputs, which will result \
	in a swiftradio client returning dictionary of raw data with the hash integer value of the \
	returned data as the dictionary keys.

	Found data can be returned as a particular data type by specifying a dtype value using the \
	output_dtype parameter. See below for a list of dtype values to choose from.

	:param dict command_data: Dictionary containing the command data to be searched.
	:param str output_name: Name of the response data.
	:param bool all_matches: Return data as a list. Can be useful if a command returns multiple data \
	packets with the same output name.
	:param str output_dtype: Return data type. See below for valid values.

		- "uint" : converts a raw string of length 4, into a unsigned int object.
		- "int" : converts a raw string of length 4, into a signed int object.
		- "float" : converts a raw string of length 8, into a float object.
		- "str" : returns string. Note that if the raw string has padded null values, these will \
		be stripped from the return value
		- "raw" : returns the raw string, unmodified.

	:returns: The value in the specified data format or a list of one or more items if all_matches \
	is True. If no data with given name could be found, a NoneType object is returned.


	**Example**:

	.. code-block:: python
		:linenos:

		cmdinfo = radio.execute("sysstat")

		uptime = find_command_data_by_name(cmdinfo, "uptime", "int")
		temp = find_command_data_by_name(cmdinfo, "temp", "float")

	.. note:: If command data is found in the frame but cannot be converted according to specified \
	data_type, the raw string will be returned instead.

	Last Updated: 05/09/16 (SRA)
	"""
	output_found = False
	return_data = list()

	if type(output_name) is not str:
		raise SwiftUtilsError("output_name parameter must be a string. Not {}".format(type(output_name).__name__))

	# check if data names need to be hashed.
	if output_name not in command_data.keys():

		output_hash = algorithms.fletcher16(output_name)

		# iterate through each output and search for matching
		for name, data in command_data.items():

			# extract packet from list
			if name != "_error":

				# check if matching hash
				if name == output_hash:
					key = output_hash
					output_found = True
	else:
		output_found = True
		key = output_name

	# convert data
	if output_found:

		# get data associated with this output name
		val = command_data[key]

		# use convert_raw from dataconversions file

		# multiple values
		if type(val) is list:
			for sub_val in val:
				return_data.append( dataconversions.convert_raw(sub_val, output_dtype) )
		# single value
		else:
			return_data.append( dataconversions.convert_raw(val, output_dtype) )

		# check if data was recovered
		if len(return_data) > 0:

			if all_matches == False:
				# only get the first data in list
				return_data = return_data[0]

	# otherwise, return None object
	else:
		return_data = None

	return return_data

class SwiftUtilsError(RuntimeError):
	pass
