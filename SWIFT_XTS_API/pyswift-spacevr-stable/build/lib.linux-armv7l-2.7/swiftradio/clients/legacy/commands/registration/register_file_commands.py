import os
from ...utils import stringconversions

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__company__ = "Tethers Unlimited Inc."
__status__ = "Development"
__date__ = "Late Updated: 1/30/15"

def register_file_commands(Command_Table, filename):
	"""
	Description: 
	Parameters: 
	Return: 
	"""	
	new_entry = False
	new_metadata = False
	new_command = False
	new_parmeter = False
	command_name = ""
	parameter_name = ""
	file_object = None

	# check if file exists
	if os.path.isfile(filename):

		# open file
		file_object = open(filename, 'r')

		# iterate through each line of text in file object
		for line in file_object:

			# check for a new field tag in file...
			if "[META]" in line:
				new_metadata = True
				metadata_info = dict()

			elif "[ENTRY]" in line:
				new_entry = True

			elif "[COMMAND]" in line:
				new_command = True
				command_info = dict()

			elif "[PARAMETER]" in line:
				new_parameter = True
				parameter_info = dict()

			# check if this is a field name/value line...
			elif "=" in line:
				fieldname = ""
				fieldval = ""

				# extract field name and value from line of text
				line = line.rstrip('\n')
				fieldname, fieldval = split_field(line, "=")

				# convert the field value to the appropriate data type (i.e. int, float, hex, string)
				fieldval = get_true_field_value(fieldval)

				# store data in correct info dictionary
				if new_metadata == True:
					metadata_info[fieldname] = fieldval
				elif new_command == True:
					command_info[fieldname] = fieldval
				elif new_parameter == True:
					parameter_info[fieldname] = fieldval

			# check for a end of field tag in file
			elif "[/META]" in line:
				# store meta data in table (not yet implemented)
				pass
				# indicate end of field
				new_metadata = False

			elif "[/COMMAND]" in line:
				# register new command
				# check that command is not already registered before registering
				if Command_Table.verify_command_registered(command_info["cname"]) != 1:
					Command_Table.register_command_by_name(command_info["cname"])
				# indicate end of field
				new_command = False

			elif "[/PARAMETER]" in line:
				# register parameter to associated command
				# check that command is registered before adding parameter
				if Command_Table.verify_command_registered(command_info["cname"]) == 1:
					# make sure this parameter is not already registered to this command
					if Command_Table.verify_parameter_registered(command_info["cname"], parameter_info["pname"]) != 1:
						Command_Table.register_parameter(command_info["cname"], parameter_info["pname"], parameter_info["popt"], 
													 	 parameter_info["ptype"], parameter_info["pdefault"], parameter_info["parg"])
				# indicate end of field
				new_parameter = False

			elif "[/ENTRY]" in line:
				new_entry = False
				new_parameter = False
				new_command = False
				new_metadata = False

			# otherwise, line is blank or contains other text layout formatting characters
			else:
				pass

	# file has not yet been created, return error code
	else:
		Command_Table = -1
	
	# return new command table and file error check
	return Command_Table

def split_field(field_str, separator = "="):
	"""
	Description: 
	Parameters: 
	Return: 
	"""		
	
	# split field
	field_str = field_str.split(separator)
	
	# read in the field name and value (which will be in string format for now)
	fieldname = str(field_str[0])
	fieldval = str(field_str[1])

	# return tuple with both values
	return fieldname, fieldval	

def get_true_field_value(field_val):
	"""
	Description: 
	Parameters: 
	Return: 
	"""		
	true_val = None

	if len(field_val) > 0:
		# determine if this string represents a numerical value (int, float or hex)
		if stringconversions.is_number(field_val):
			true_val = stringconversions.return_num(field_val)
		# if not, leave as a string	
		else:
			true_val = field_val
	else:
		true_val = "NONE"

	# print true_val
	return true_val
	
	
if __name__ == "__main__":
	from CMD_Host_Utilities.Packet_Translator import text_to_swiftbytelist
	from CMD_Host_Utilities.Message_Framer import wrap_swiftmsg_data
	from Program.Utilities.System import Get_System_Date
	
	CMDHost_CmdTable = register_cmds()
	CMDHost_CmdTable.print_command_table()
	raw_input("Press Enter to Continue...")
	bytelist = text_to_swiftbytelist("bintest --num1 23", Command_Table = CMDHost_CmdTable)
	# print bytelist
	frame_buffer = wrap_swiftmsg_data(bytelist)
	print frame_buffer