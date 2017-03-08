import os
import time
import argparse
from .error import SwiftRadioError
from . import stringconversions

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__status__ = "Development"


class SwiftRadioCommandParser(argparse.ArgumentParser):
	"""
	Description: A subclass of the argparse ArgumentParser module modified
				 to provide services specific to the swiftradio Library

	Parameters: 
	Return: 
	"""		
	def error(self, message):
		raise CommandParserError(message) 


class CommandParserError(Exception):
	"""
	Description: 
	Parameters: 
	Return: 
	"""		 
	def __init__(self, message):
		self.message = message

	def get_error_msg(self, added_info = None):
		# stack_trace = traceback.format_stack()
		# stack_trace = " ".join(stack_trace)
		# self.message += "\n"
		# self.message += stack_trace
		error_msg = "CommandParserError: " + str(self.message)
		if added_info != None:
			error_msg += "\n\n-Additional Info- \n\n" + str(added_info)

		return error_msg

class boolAction(argparse.Action):
	"""
	Description: 
	Parameters: 
	Return: 
	"""		
	def __call__(self, parser, namespace, values, option_string=None):
		new_val = None
		if values == None:
			new_val = True 		# set to true if no val was given
		else:
			new_val = values
		setattr(namespace, self.dest, new_val) 

class strAction(argparse.Action):
	"""
	Description: 
	Parameters: 
	Return: 
	"""		
	def __call__(self, parser, namespace, values, option_string=None):
		new_val = None
		if type(values) is list:
			new_val = " ".join(values)
		else:
			new_val = values

		setattr(namespace, self.dest, new_val) 

class binAction(argparse.Action):
	"""
	Description: 
	Parameters: 
	Return: 
	"""		
	def __call__(self, parser, namespace, values, option_string=None):
		new_val = None
		if type(values) is list:
			new_val = " ".join(values)
		else:
			new_val = values

		setattr(namespace, self.dest, new_val) 

def get_parser_settings(paramtype):
	"""
	Description: 
	Parameters: 
	Return: 
	"""				
	parser_paramtype = None
	action = "store"
	nargs_mod = None

	if paramtype == "int":
		parser_paramtype = int_parsetype	

	elif paramtype == "bool":
		parser_paramtype = bool_parsetype
		action = boolAction
		nargs_mod = '?'

	elif paramtype == "float":
		parser_paramtype = float_parsetype

	elif paramtype == "hex":
		parser_paramtype = hex_parsetype

	elif paramtype == "str": 
		parser_paramtype = str_parsetype
		action = strAction
		nargs_mod = '+'

	elif paramtype == "stropt":
		parser_paramtype = stropt_parsetype

	elif paramtype == "ip4adx":
		parser_paramtype = ip4adx_parsetype

	elif paramtype == "bin":
		parser_paramtype = bin_parsetype
		action = binAction
		nargs_mod = argparse.REMAINDER
		
	else:
		try:
			raise CommandParserError("cannot register unrecognized parameter type '%s'"%(paramtype))
		except CommandParserError, error:
			parser_error = error.get_error_msg()
			raise SwiftRadioError(parser_error)

	return parser_paramtype, action, nargs_mod		


def add_optional_parameter_to_parser(parser, param_name, opt, text_paramtype, default=None, help=None):
	"""
	Description: 
	Parameters: 
	Return: 
	"""			
	paramtype = None
	action = "store"
	nargs_mod = None

	# get parser settings based on the parameter type
	paramtype, action, nargs_mod = get_parser_settings(text_paramtype)

	# construct default help string if help parameter has not been provided
	if help == None:
		help = "type {}. defaults to {}".format(text_paramtype, default) 

	# create new parser parameter
	if opt == "NONE":
		parser.add_argument("--%s"%(param_name), type=paramtype,
	                   	help=help, default=None, action=action, nargs=nargs_mod)
	else:
		parser.add_argument("-%s"%(opt), "--%s"%(param_name), type=paramtype,
	                   	help=help, default=None, action=action, nargs=nargs_mod)

	return parser		


def add_required_parameter_to_parser(parser, param_name, text_paramtype, help=None):
	"""
	Description: 
	Parameters: 
	Return: 
	"""				
	paramtype = None
	action = "store"
	nargs_mod = None

	# get parser settings based on the parameter type
	paramtype, action, nargs_mod = get_parser_settings(text_paramtype)

	# construct default help string if help parameter has not been provided
	if help == None:
		help = "type {}".format(text_paramtype) 

	# create a new parser argument
	parser.add_argument(param_name, type=paramtype, help=help, action=action, nargs=nargs_mod)
	
	return parser		

def int_parsetype(text):
	# check that the text strin can be converted to paramtype, raise CommandParserError if not
	if verify_paramtype_textformat(text, "int", 1) == True:
		# convert string to int value
		int_val = int(float(text))			# to allow BASEeEXP syntax (i.e. 1315e6), 
											# convert to float before int
		# return if no error
		return int_val

def float_parsetype(text):
	# check that the text strin can be converted to paramtype, raise CommandParserError if not
	if verify_paramtype_textformat(text, ["float", "int"], 1) == True:		# an text int value is also acceptable
		# convert string to float values 								
		float_val = float(text)
		# return if no error
		return float_val

def hex_parsetype(text):
	# error check here, raise CommandParserError if error
	if verify_paramtype_textformat(text, "hex", 1) == True:

		# convert string to 'hex' value
		hex_val = text
		if len(hex_val)%2 != 0:
			# left pad any odd character hex values (i.e 0x8->0x08)
			prepadded_char = hex_val[len(hex_val)-1]
			postpadded_char = "0" + prepadded_char
			hex_val = hex_val[:len(hex_val)-1] + postpadded_char
		
		# return hex_Val if no error
		return int(hex_val, 16)

def bool_parsetype(text):
	if text != None:
		if text == 'True' or text == 'False':
			bool_val = bool(text)
		elif verify_paramtype_textformat(text, "int", 1) == True:
			bool_val = bool(int(text))
	else:
		bool_val = True	

	return bool_val	

def str_parsetype(text):
	return text

def stropt_parsetype(text):
	return text

def ip4adx_parsetype(text):
	return text

def bin_parsetype(text):
	return text

def verify_paramtype_textformat(text, expected_param_type, raise_exception=0):
	param_type = stringconversions.determine_datatype_from_text(str(text))

	if param_type in expected_param_type:
		return True
	else:
		if raise_exception == 1:
			raise TypeError
		return False
