__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__company__ = "Tethers Unlimited Inc."
__status__ = "Development"
__date__ = "Late Updated: 1/30/15"

def register_default_cmds(cmds_table):
	"""
	Description: this function registers basic radio commands that every SwiftRadioInterface instance will
				 have access to upon creation.
	Parameters: cmds_table - Command_Table object that the new commands will be registered to
	Return: Command_Table object
	"""
	# Register default set of commands
	cmds_table = register_packet_cmds(cmds_table)
	cmds_table = register_swift_bsp_base_cmds(cmds_table)
	cmds_table = register_swift_bsp_clock_cmds(cmds_table)
	cmds_table = register_help_cmds(cmds_table)

	return cmds_table

def register_default_cmds_v2(cmds_table):
	"""
	Description: this function registers basic radio commands that every SwiftRadioInterface instance will
				 have access to upon creation.
	Parameters: cmds_table - Command_Table object that the new commands will be registered to
	Return: Command_Table object
	"""
	# Register default set of commands
	cmds_table = register_help_cmds(cmds_table)

	return cmds_table

def register_packet_cmds(cmds_table):
	"""
	Description:
	Parameters:
	Return:
	"""
	cmds_table.register_command_by_name("dlcmdinfo")
	cmds_table.register_parameter("dlcmdinfo", "command", 'c', "str", "all", argument=True)
	cmds_table.register_parameter("dlcmdinfo", "transinfo", 't', "bool", 0)

	return cmds_table

def register_swift_bsp_base_cmds(cmds_table):
	"""
	Description:
	Parameters:
	Return:
	"""
	cmds_table.register_command_by_name("baserst")
	cmds_table.register_parameter("baserst", "type", 't', 'stropt', "")

	cmds_table.register_command_by_name("loglevel")
	cmds_table.register_parameter("loglevel", "level", 'l', 'str', "", argument=True)

	cmds_table.register_command_by_name("devid")

	cmds_table.register_command_by_name("sysinfo")

	# return Command Table
	return cmds_table

def register_swift_bsp_clock_cmds(cmds_table):
	"""
	Description:
	Parameters:
	Return:
	"""
	cmds_table.register_command_by_name("time")

	return cmds_table

def register_help_cmds(cmds_table):
	"""
	Description:
	Parameters:
	Return:
	"""
	cmds_table.register_command_by_name("help")
	cmds_table.register_parameter("help", "command", 'c', "str", "")
	cmds_table.register_parameter("help", "description", 'd', "bool", False)

	cmds_table.register_output("help", "command", "bin")
	cmds_table.register_output("help", "command_description", "bin")
	cmds_table.register_output("help", "command_input", "bin")
	cmds_table.register_output("help", "command_input_description", "bin")
	cmds_table.register_output("help", "command_input_enum", "bin")
	cmds_table.register_output("help", "command_input_enum_description", "bin")
	cmds_table.register_output("help", "command_output", "bin")
	cmds_table.register_output("help", "command_output_description", "bin")

	return cmds_table
