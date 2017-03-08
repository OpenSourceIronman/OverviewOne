import os
import time
import struct
from ..utils.algorithms import fletcher16
from ..utils import cmdlinesyntax
from ..utils.error import SwiftRadioError

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__status__ = "Development"

class SwiftCmdhostCommandTable:
	"""
	Description:
	Parameters:
	Return:
	"""
	def __init__(self, cname='default'):
		"""
		Description:
		Parameters:
		Return:
		"""
		self.table_name = cname
		self.command_list = list()
		self.command_name_dict = dict()
		self.command_fletcher_dict = dict()

	def get_command(self, cname = None, cfletcher = None):
		"""
		Description:
		Parameters:
		Return:
		"""
		if cname != None:
			if str(cname).lower() in self.command_name_dict:
				return self.command_name_dict[str(cname).lower()]
			else:
				print "command name not in name dict"
				return -1
		elif cfletcher != None:
			if cfletcher in self.command_fletcher_dict:
				return self.command_fletcher_dict[cfletcher]
			else:
				print "command fletcher not in fletcher dict"
				return -1
		else:
			return -1

	def get_command_fletcher(self, cname=None, endianess = "little"):
		"""
		Description:
		Parameters:
		Return:
		"""
		if str(cname).lower() in self.command_name_dict:
			little_endian_fletcher = self.command_name_dict[cname].get_command_fletcher()
			if endianess == "little":
				return little_endian_fletcher
			elif endianess == "big":
				temp_fletcher = struct.pack('<H', little_endian_fletcher)
				hex_fletcher = temp_fletcher.encode('hex')
				big_endian_fletcher = int(hex_fletcher, 16)

				return big_endian_fletcher
			else:
				print "invalid endianess type '{}'".format(endianess)
		else:
			print "'" + str(cname) + "' unrecognized cmdhost command.\n"
			return -1

	def get_command_name(self, cfletcher = None):
		"""
		Description:
		Parameters:
		Return:
		"""
		if cfletcher in self.command_fletcher_dict:
			return self.command_fletcher_dict[cfletcher].get_command_name()
		else:
			return -1

	def get_num_cmds_registered(self):
		"""
		Description:
		Parameters:
		Return:
		"""
		return len(self.command_list)

	def get_num_params_registered(self):
		"""
		Description:
		Parameters:
		Return:
		"""
		total_params_registered = 0

		# iterate through registered commands list
		for command in self.command_list:
			# get all parameters for this command
			param_list = command.get_param_list()
			# iterate through registered parameters list
			for param in param_list:
				# increment parameter counter
				total_params_registered += 1

		return total_params_registered

	def get_param_fletcher(self, cname, pname=None, pprefix=None, endianess = "little"):
		"""
		Description:
		Parameters:
		Return:
		"""
		command = self.command_name_dict[cname]
		little_endian_fletcher = command.get_param_fletcher(pname, pprefix)
		if endianess == "little":
			return little_endian_fletcher
		elif endianess == "big":
			temp_fletcher = struct.pack('<H', little_endian_fletcher)
			hex_fletcher = temp_fletcher.encode('hex')
			big_endian_fletcher = int(hex_fletcher, 16)
			return big_endian_fletcher
		else:
			print "invalid endianess type '{}'".format(endianess)

	def get_param_type(self, cname, pname):
		"""
		Description:
		Parameters:
		Return:
		"""
		command = self.command_name_dict[cname]
		return command.get_param_type(pname)

	def get_output_list(self, cname):
		"""
		Description:
		Parameters:
		Return:
		"""
		command = self.command_name_dict[cname]
		return command.output_list

	def get_table_name(self):
		"""
		Description:
		Parameters:
		Return:
		"""
		return self.cmdname

	def parse_parameter_text(self, command_name, arglist):
		"""
		Description:
		Parameters:
		Return:
		"""
		parsed_param_info = dict()
		# get command cmdline parser
		parser = self.command_name_dict[command_name].get_cmdline_parser()
		num_params = self.command_name_dict[command_name].get_param_num()
		try:
			# use parser to parse (convert to namespace) the argument list
			parser_namespace = parser.parse_args(arglist)
			# convert namespace to dictionary for easier handling
			parser_dict = vars(parser_namespace)
			# note: this dictionary contains every parameter associated with this command,
			# command parameters that were not specified in the command line text will have an
			# assigned value of None. Remove these extra parameters for convenience, store
			# in our return dictionary
			for paramname in parser_dict:
				if parser_dict[paramname] != None:
					parsed_param_info[paramname] = parser_dict[paramname]

			# if (len(parsed_param_info) == 0) and (num_params > 0):
			# 	raise cmdlinesyntax.CommandParserError("command '{}' requires at least one argument.".format(command_name))

			return parsed_param_info

		except cmdlinesyntax.CommandParserError, error:
			parser_error = error.get_error_msg(added_info = parser.format_help())
			raise SwiftRadioError(parser_error)
			return None

	def print_command_table(self):
		"""
		Description:
		Parameters:
		Return:
		"""
		print ""
		for command in self.command_list:
			print "---------------------------------------------"
			print " " + str(command.get_command_name())
			print "---------------------------------------------"
			print "[Command]"
			print "    Description: {}".format( command.cmdhelp )
			print "    Fletcher: 0x{}".format( hex(command.get_command_fletcher())[2:].upper().zfill(4) )
			param_list = command.get_param_list()
			output_list = command.get_output_list()
			print "    Inputs: {}".format( len(param_list) )
			print "    Outputs: {}".format( len(output_list) )
			print ""
			for i, param in enumerate(param_list):
				print "[Input]"
				print "    Name: {}".format(param.param_name)
				print "    Description: {}".format(param.param_desc)
				print "    Fletcher: 0x" + hex(param.param_fletcher)[2:].upper().zfill(4)
				print "    num: {}".format(i+1)
				print "    arg: {}".format(param.param_arg)
				print "    opt: {}".format(param.param_prefix)
				print "    type: {}".format(param.param_type)
				print "    units: {}".format(param.param_units)
				print "    default: {}".format(param.param_val)
				print "    min: {}".format(param.param_min)
				print "    max: {}".format(param.param_max)
				if len(param.param_stropts) > 0:
					print "    stropts:".format(param.param_max)
					for enum_name in param.param_stropts:
						print "    - {}".format(enum_name)
				print ""

			for i, output in enumerate( output_list ):
				print "[Output]"
				print "    Name: {}".format( output.name )
				print "    Description: {}".format( output.desc )
				print "    Fletcher: 0x" + hex( output.name_hash )[2:].upper( ).zfill( 4 )
				print "    num: {}".format( i+1 )
				print "    type: {}".format( output.type )
				print "    units: {}".format( output.units)
				print "    default: {}".format( output.default )
				print "    min: {}".format( output.min )
				print "    max: {}".format( output.max )
				print ""

	def register_command(self, command):
		"""
		Description:
		Parameters:
		Return:
		"""
		command_name = command.get_command_name()
		command_fletcher = command.get_command_fletcher()

		self.command_list.append(command)
		self.command_name_dict[command_name] = command
		self.command_fletcher_dict[command_fletcher] = command

	def register_command_by_name(self, command_name, description=""):
		"""
		Description:
		Parameters:
		Return:
		"""
		# check that command is not already registered
		if self.verify_command_registered(command_name) == 0:
			# create new command instance using command name
			new_command_instance = Command(command_name, description)
			# create new parser
			new_command_instance.create_cmdline_parser()
			# add command to table's command_list and dict
			self.command_list.append(new_command_instance)
			self.command_name_dict[command_name] = new_command_instance
			# store fletcher value
			command_fletcher = new_command_instance.get_command_fletcher()
			self.command_fletcher_dict[command_fletcher] = new_command_instance
			return 1
		else:
			raise SwiftRadioError("command '%s' is already registered"%(command_name))
			return -1

	def register_parameter(self, command_name, pname=None, optprefix="", ptype=None, pdefault=None,
		                   argument=False, desc=None, min_val=None, max_val=None, units=None, stropts=None):
		"""
		Description:
		Parameters:
		Return:
		"""
		# check if the command that the parameter will be registered to exists
		if self.verify_command_registered(command_name) == 1:
			# verify that this parameter is not already registered
			if self.verify_parameter_registered(command_name, pname) != 1:
				# get command instance using provided command name
				command = self.command_name_dict[command_name]
				# register the parameter
				registration_complete = command.add_param(pname, optprefix, ptype, pdefault, argument, desc, min_val, max_val, units, stropts)
				# raise exception if parameter could not be registered
				if registration_complete != 1:
					raise SwiftRadioError("parameter registration failure")
					return -3
			else:
				raise SwiftRadioError("register_parameter->parameter '%s' is already registered"%(pname))
				return -2
		else:
			raise SwiftRadioError("register_parameter->command '%s' does not exist"%(command_name))
			return -1
		return 1

	def register_output(self, command_name, pname=None, ptype=None, pdefault=None, pdesc=None, min_val=None, max_val=None, units=None):
		"""
		Description:
		Parameters:
		Return:
		"""
		# check if the command that the parameter will be registered to exists
		if self.verify_command_registered(command_name) == 1:

			# verify that this parameter is not already registered
			if self.verify_output_registered(command_name, pname) != 1:
				# get command instance using provided command name
				command = self.command_name_dict[command_name]
				# register the parameter
				registration_complete = command.add_output(pname, ptype, pdesc, pdefault, min_val, max_val, units)
				# raise exception if parameter could not be registered
				if registration_complete != 1:
					raise SwiftRadioError("output registration failure")

			else:
				raise SwiftRadioError("register_output->output '%s' is already registered"%(pname))

		else:
			raise SwiftRadioError("register_output->command '%s' does not exist"%(command_name))

		return 1

	def verify_command_registered(self, command_name):
		"""
		Description:
		Parameters:
		Return:
		"""
		# check if command name is in table's command dictionary
		if command_name in self.command_name_dict:
			return 1
		else:
			return 0

	def verify_parameter_registered(self, command_name, parameter_name):
		"""
		Description:
		Parameters:
		Return:

		.. todo:: return either 0 or 1, as in verify_command_registered()!!!
		"""
		# check if command name is in table's command dictionary
		if command_name in self.command_name_dict:
			command = self.command_name_dict[command_name]
			# check if parameter name is in this command's parameter table
			if command.verify_param_registered(parameter_name) == 1:
				return 1
			else:
				return -1
		else:
			return -2

	def verify_output_registered(self, command_name, output_name):
		"""
		Description:
		Parameters:

		:returns: 0 if not registered, 1 if registered
		"""
		registered = 0
		# check if command name is in table's command dictionary
		if command_name in self.command_name_dict:
			command = self.command_name_dict[command_name]
			# check if parameter name is in this command's parameter table
			if command.verify_output_registered(output_name) == 1:
				registered = 1
			else:
				registered = 0
		else:
			registered = 0

		return registered

	def write_table_to_file(self, filename):
		"""
		Description:
		Parameters:
		Return:
		"""
		file_object = None
		time_stamp = time.time()

		# open file
		file_object = open(filename, 'w')

		# write metadata to file
		file_object.write("[META]\n")
		file_object.write(str(self.time_stamp_file()) + "\n")
		file_object.write("table=" + str(self.table_name) + "\n")
		file_object.write("entries=" + str(len(self.command_list)) + "\n")
		file_object.write("[/META]\n")
		file_object.write("---------------------------------------------\n")
		# file_object.write("params=" + str(self.table_name) + "\n")

		# write table commands to
		for command in self.command_list:
			file_object.write("---------------------------------------------\n")
			file_object.write("[ENTRY]" + "\n\n")
			file_object.write("[COMMAND]" + "\n")
			file_object.write("cname=%s" % (str(command.get_command_name())) + "\n")
			file_object.write("cfletcher=%d" % (command.get_command_fletcher()) + "\n")
			param_list = command.get_param_list()
			file_object.write("cparams=" + str(len(param_list)) + "\n")
			file_object.write("[/COMMAND]" + "\n\n")

			param_num = 1
			for param in param_list:
				file_object.write("[PARAMETER]" + "\n")
				file_object.write("pname=" + str(param.param_name) + "\n")
				file_object.write("pfletcher=%d" % (param.param_fletcher)  + "\n")
				file_object.write("pnum=" + str(param_num) + "\n")
				file_object.write("parg=" + str(param.param_arg) + "\n")
				file_object.write("popt=" + str(param.param_prefix) + "\n")
				file_object.write("ptype={}".format(param.param_type) + "\n")
				file_object.write("pdefault=" + str(param.param_val) + "\n")
				file_object.write("pmin=" + "\n")
				file_object.write("pmax=" + "\n")
				file_object.write("pcmd=" + str(str(command.get_command_name())) + "\n")
				file_object.write("[/PARAMETER]" + "\n\n")
				param_num += 1
			file_object.write("[/ENTRY]" + "\n")
			file_object.write("---------------------------------------------\n")

	def time_stamp_file(self):
		"""
		Description:
		Parameters:
		Return:
		"""
		#update system time
		time_secs = time.time()
		t = time.localtime(time_secs)
		date = time.strftime("%b %d, %Y", t)
		hours = time.strftime("%H", t)
		min = time.strftime("%M", t)
		sec = time.strftime("%S", t)
		return "date={}\nsystem time={}:{}:{}".format(date, hours, min, sec)

class Command:
	"""
	Description:
	Parameters:
	Return:
	"""
	def __init__(self, cname, desc=""):
		"""
		Description:
		Parameters:
		Return:
		"""
		#command information
		self.cmdname = str(cname).lower()
		self.cmdfletcher = fletcher16(self.cmdname)
		self.cmdparams = 0
		self.cmdhelp = desc
		# associated parameter containers/identifiers
		self.param_list = list()
		self.command_argument = None
		self.param_name_dict = dict()
		self.param_fletcher_dict = dict()
		self.param_prefix_dict = dict()
		# associated output containers/identifiers
		self.output_list = list()
		self.output_name_dict = dict()
		self.output_fletcher_dict = dict()
		#command line parsing mechanism for parsing command line strings, provides numerous other error checking/reporting functionality
		# create new parser
		self.cmdline_parser = None
		self.create_cmdline_parser()

	def add_output(self, name, dtype, desc=None, default=None, min_val=None, max_val=None, units=None):
		"""
		Description:
		Parameters:
		Return:
		"""
		output_obj = Output(name, dtype, desc, default, min_val, max_val, units)
		self.output_list.append(output_obj)
		self.output_name_dict[output_obj.name] = output_obj
		self.output_fletcher_dict[output_obj.name_hash] = output_obj
		return 1

	def add_param(self, pname, optprefix, ptype, pdefault=None, argument=False, desc=None, min_val=None, max_val=None, units=None, stropts=None):
		"""
		Description:
		Parameters:
		Return:
		"""
		if optprefix == "":
			optprefix = "NONE"
		param_name = str(pname).lower()
		param_type = str(ptype).lower()
		param_val = pdefault
		param_prefix = str(optprefix).lower()
		param_instance = Parameter(param_name, param_type, param_val, optprefix, argument, min_val, max_val, desc, units, stropts)
		param_fletcher = param_instance.get_param_fletcher()
		if argument == True:
			self.command_argument = param_name
		self.param_list.append(param_instance)
		self.param_name_dict[param_name] = param_instance
		self.param_fletcher_dict[param_fletcher] = param_instance
		self.param_prefix_dict[optprefix] = param_name
		if self.cmdline_parser != None:
			self.__add_param_to_parser(param_name, param_type, optprefix, pdefault, help=None, arg=argument)
		return 1

	def __add_param_to_parser(self, param_name, text_paramtype, opt=None, default=None, help=None, arg=False):
		"""
		Description:
		Parameters:
		Return:
		"""
		if arg == True:
			self.cmdline_parser = cmdlinesyntax.add_required_parameter_to_parser(self.cmdline_parser, param_name, text_paramtype, help)
		else:
			self.cmdline_parser = cmdlinesyntax.add_optional_parameter_to_parser(self.cmdline_parser, param_name, opt, text_paramtype, default, help)
		return 1


	def create_cmdline_parser(self):
		"""
		Description:
		Parameters:
		Return:
		"""
		self.cmdline_parser = cmdlinesyntax.SwiftRadioCommandParser(prog=self.cmdname, description=self.cmdhelp, add_help=False)
		return 1

	def get_command_fletcher(self):
		"""
		Description:
		Parameters:
		Return:
		"""
		return self.cmdfletcher

	def get_cmdline_parser(self):
		"""
		Description:
		Parameters:
		Return:
		"""
		return self.cmdline_parser

	def get_command_name(self):
		"""
		Description:
		Parameters:
		Return:
		"""
		return self.cmdname

	def get_param_fletcher(self, pname=None, pprefix=None):
		"""
		Description:
		Parameters:
		Return:
		"""
		if pname != None:
			if pname == "#arg":
				if self.command_argument != None:
					pname = self.command_argument
				else:
					print "This command has no 'argument' parameter. Please include the parameter name or prefix."
					return -1
			elif "-" in pname:
				prefix = pname.replace("-","")
				if prefix in self.param_prefix_dict:
					pname = self.param_prefix_dict[prefix]
				else:
					print "unrecognized Option Prefix."
					return -1
			if str(pname).lower() in self.param_name_dict:
				param = self.param_name_dict[str(pname).lower()]
				return param.param_fletcher
			else:
				print "'" + str(pname) + "' unrecognized parameter for '" + str(self.cmdname) + "' command.\n"
				return -1

	def get_param_list(self):
		"""
		Description:
		Parameters:
		Return:
		"""
		return self.param_list

	def get_output_list(self):
		"""
		Description:
		Parameters:
		Return:
		"""
		return self.output_list

	def get_param_num(self):
		"""
		Description:
		Parameters:
		Return:
		"""
		return len(self.param_list)

	def get_param_type(self, pname):
		"""
		Description:
		Parameters:
		Return:
		"""
		if pname == "#arg":
			if self.command_argument != None:
				pname = self.command_argument
			else:
				print "This command has no 'argument' parameter. Please include the parameter name or prefix."
		elif "-" in pname:
			prefix = pname.replace("-","")
			if prefix in self.param_prefix_dict:
				pname = self.param_prefix_dict[prefix]
			else:
				print "unrecognized Option Prefix."
				return -1
		param = self.param_name_dict[str(pname).lower()]
		return param.param_type

	def verify_param_registered(self, param_name):
		"""
		Description:
		Parameters:
		Return:
		"""
		# check if command name is in table's command dictionary
		if param_name in self.param_name_dict:
			return 1
		else:
			return 0

	def verify_output_registered(self, output_name):
		"""
		Description:
		Parameters:
		Return:
		"""
		# check if command name is in table's command dictionary
		if output_name in self.output_name_dict:
			return 1
		else:
			return 0

class Parameter:
	"""
	Description:
	Parameters:
	Return:
	"""
	def __init__(self, pname, ptype, pdefault, pprefix, parg=False, pmin=None, pmax=None, desc=None, units=None, stropts=None):
		"""
		Description:
		Parameters:
		Return:
		"""
		self.param_fletcher = 0x0000
		self.param_name = str(pname).lower()
		self.param_arg = parg
		self.param_desc = desc
		# self.param_num = pnum
		self.param_prefix = pprefix
		self.param_fletcher = fletcher16(self.param_name)
		self.param_type = ptype
		self.param_val = pdefault
		self.param_min = pmin
		self.param_max = pmax
		self.param_units = units
		self.param_stropts = stropts or list()
		self.param_entry = [self.param_name, self.param_fletcher, self.param_type, self.param_val]


	def get_param_name(self):
		"""
		Description:
		Parameters:
		Return:
		"""
		return self.param_name

	def get_param_fletcher(self):
		"""
		Description:
		Parameters:
		Return:
		"""
		return self.param_fletcher


class Output:
	"""
	Description:
	Parameters:
	Return:
	"""
	def __init__(self, name, dtype, desc=None, default=None, min_val=None, max_val=None, units=None):
		"""
		.. todo:: add error checking for each value
		"""
		self.name = name
		self.name_hash =  fletcher16(self.name)
		self.type = dtype
		self.units = units
		self.desc = desc
		self.default = default
		self.min = min_val
		self.max = max_val


if __name__ == "__main__":
	from Register_Commands import register_cmds
	CMDHost_CmdTable = register_cmds()
	CMDHost_CmdTable.print_command_table()
	raw_input("Press Enter to Continue...")
