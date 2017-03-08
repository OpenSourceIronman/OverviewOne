import dataconversions
import algorithms

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__status__ = "Development"
__date__ = "Late Updated: 05/05/16"

def find_command_data_by_name(command_data, output_name, output_dtype='raw', all_matches=False):
	"""
	Description:
	Parameters: command_data - must be raw byte string
	Return: - a list of one or more items containing the command data requested in the
			  data format specified.
			- a None object if no packet data could be found
	Note: this method is intended to work with SwiftPacket Objects only. A None object will always
			be returned for any other instance contained in the SwiftPacketList
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
