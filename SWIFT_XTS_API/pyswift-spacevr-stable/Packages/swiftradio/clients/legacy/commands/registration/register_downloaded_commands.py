from ...utils import stringconversions

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__company__ = "Tethers Unlimited Inc."
__status__ = "Development"
__date__ = "Late Updated: 9/10/14"


def register_dlcmdinfo_command_pkts(Command_Table, dlcmdinfo_pkts, error_check = True):
	"""
	Description: processes packets received after a dlcmdinfo command and adds command information to table
	Parameters: packet list containing all the packets received from dlcmdinfo command
	Return: updated command table with new commands
	"""	
	registration_complete = False
	trans_packet_rcvd = False
	expected_cmds = None
	expected_params = None
	total_cmds_received = 0
	total_params_received = 0
	received_cmds_dict = dict()
	
	# [1] iterate through packet list, search for received cmdhost command information
	for packet in dlcmdinfo_pkts:

		# get this rpc packet's data field contents (note: some packets do not have a data field--i.e. DESYNC packets)
		param_contents = packet.get_command_data("string")	# note: data chosen to be returned as string instead of a list

		# if data contents were found, process the dlcmdinfo info
		if param_contents != None:

			# check if this is a command information packet
			if "[command]" in param_contents:

				# this packet contains info about a parameter and it's associated command
				# get command info
				cmd_name = get_field_value("cmd", param_contents)
				cmd_nparams = int(get_field_value("nparams", param_contents))

				# get parameter info
				param_name = get_field_value("param", param_contents)
				param_num = get_field_value("num", param_contents)
				param_arg = int(get_field_value("arg", param_contents))
				param_opt = get_field_value("opt", param_contents)
				param_type = get_field_value("type", param_contents)
				param_default = get_true_default_val(get_field_value("default", param_contents), param_type)
				
				# add this received command to list	
				if cmd_name not in received_cmds_dict:
					# add cmd name as dictionary key, add an empty list for any parameters
					received_cmds_dict[cmd_name] = list()
					total_cmds_received += 1

				# if parameter info is included, add to command's parameter list
				if param_name != "0":

					# check if parameter is not already included
					if param_name not in received_cmds_dict[cmd_name]:

						# add to command's parameter list
						received_cmds_dict[cmd_name].append(param_name)
						total_params_received += 1

				# check if command associated with this packet exists
				if Command_Table.verify_command_registered(cmd_name) != 1:

					# if not, register new command
					Command_Table.register_command_by_name(cmd_name)
					
				# check if this command packet has any parameter data
				if cmd_nparams != 0:				
					# make sure this parameter is not already registered to this command
					if Command_Table.verify_parameter_registered(cmd_name, param_name) != 1:
						# if param not registered, use parsed info to register parameter to command
						Command_Table.register_parameter(cmd_name, 
												param_name, param_opt, param_type, param_default, param_arg)
					else:
						# parameter already exists, ignore
						pass
				else:
					# otherwise, this command has no parameters
					pass

			# check if this is a transaction information packet
			elif "[trans]" in param_contents:
				# this packet contains data transaction info 
				# store number of commands and parameters that should have been downloaded
				expected_cmds = int(get_field_value("cmds", param_contents))
				expected_params = int(get_field_value("params", param_contents))
				trans_packet_rcvd = True

			# otherwise, this is an unknown packet, ignore
			else:
				pass
		
	# [2] error check transaction if option is set to True
	if error_check == True:
		# verify that transaction packet was received
		if trans_packet_rcvd == True:
			# verify that the number of commands registered matches expected value
			if total_cmds_received == expected_cmds:
				# verify that number of params registered matched expected
				if total_params_received == expected_params:
					# verification complete!
					registration_complete = 1
				else:
					registration_complete = -3
			else:
				registration_complete = -2
		else:
			registration_complete = -1
	# if error check option is false, registration is complete		
	else:
		registration_complete = 1

	# [4] finally, return populated table, verification code, and number of new table entries
	return Command_Table, registration_complete, (total_cmds_received, expected_cmds), (total_params_received, expected_params)


def get_field_value(field_name, field_val_str, field_val_delimiter = ":"):
	"""
	Description: searches a string containing the desired field name/value info and returns 
				 the field value as a string.
	Parameters: 
	Return: 
	"""		
	text_lines = list()
	field_val = None
	found = False


	# split string into a list of text lines (\n delimited)	
	text_lines = field_val_str.split("\n")
	
	# check each line for a matching field name 
	for line in text_lines:
		# split line into field name/value, but first check if there is a 
		# field name/value delimiter
		if field_val_delimiter in line:

			# read in the field name from the line of text
			lfield_name = line.split(field_val_delimiter)[0]

			# check if this is the desired field name
			if lfield_name == field_name:

				# extract the field value
				field_val = line.replace(field_name+field_val_delimiter,"")
				found = True

	if found == False:
		field_val = ""

	return field_val

def get_true_default_val(default_val_str, param_type):	
	"""
	Description: 
	Parameters: 
	Return: 
	"""		
	true_default_val = None

	# check if default string evaluates to a numerical value 
	# note (int, float, and hex param types are classified as numerical values)
	if stringconversions.is_number(default_val_str):
		true_default_val = stringconversions.return_num(default_val_str)
	else:
		true_default_val = default_val_str

	return true_default_val


def get_command_info_from_packets(packets):
	"""
	Description: 
	Parameters: 
	Return: 
	"""	
	pass

def add_new_command_info(newcmdinfo, cmdinfo):
	"""
	Description: 
	Parameters: 
	Return: 
	"""	
	pass	

def verify_all_commands_downloaded(cmdinfo, transinfo):
	"""
	Description: 
	Parameters: 
	Return: 
	"""	
	pass

def register_downloaded_commands(packets, transinfo):
	"""
	Description: 
	Parameters: 
	Return: 
	"""	
	pass	

