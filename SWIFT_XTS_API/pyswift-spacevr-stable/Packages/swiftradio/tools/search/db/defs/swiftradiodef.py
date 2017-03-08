#!/usr/bin/env python

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__company__ = "Tethers Unlimited Inc."
__status__ = "Development"
__date__ = "Late Updated: 12/9/14"

class SwiftRadioDefinition:
	""" 
	Description: Information about a assembled radio unit. Including the baseband board and any additional frontend or
				 breakout board information.
	"""	
	def __init__(self):
		""" 
		Description:
		"""
		self.name = None				# arbitrary radio name for referencing this unit
		self.stackup = None				# optional stackup number unique to each radio
		self.devid = None				# device id, this value is pulled from the baseband board information
		self.firmware_info = None		# firmware information
		self.connection = None			# pc to radio data interface (i.e. "ethernet")
		self.connection_info = None		# information about this connection
		self.baseband = None			# baseband unit
		self.frontends = list()			# frontend unit
		self.breakout = None			# breakout unit

	def add_baseband_board(self, board):
		"""
		Description:
		Parameters:
		Return:
		"""
		# set baseband instance and device id
		self.baseband = board
		self.devid = self.baseband.get_devid()

	def add_frontend_board(self, board):
		"""
		Description:
		Parameters:
		Return:
		"""		
		self.frontends.append(board)

	def add_breakout_board(self, board):
		"""
		Description:
		Parameters:
		Return:
		"""		
		self.breakout = board				

	def get_stackup(self):
		"""
		Description:
		Parameters:
		Return:
		"""	
		return self.stackup

	def get_name(self):
		"""
		Description:
		Parameters:
		Return:
		"""		
		return self.name

	def get_devid(self):
		"""
		Description:
		Parameters:
		Return:
		"""		
		return self.devid

	def get_firmware_info(self):
		"""
		Description:
		Parameters:
		Return:
		"""		
		return self.firmware_info

	def set_firmware_info(self, fwinfo):
		"""
		Description:
		Parameters:
		Return:
		"""		
		self.firmware_info = fwinfo

	def get_baseband_info(self, return_as_dict = False):
		"""
		Description:
		Parameters:
		Return:
		"""
		if return_as_dict == True:		
			info = self._get_board_info(self.baseband)

			if info != None:
				info["devid"] = self.baseband.get_devid()

			return info

		else:
			return self.baseband

	def get_frontend_info(self, return_as_dict = False):
		"""
		Description:
		Parameters:
		Return:
		"""
		frontend_list = list()
		if return_as_dict == True:		

			# get info about each frontend as a dictionary, store in list
			for frontend in self.frontends:

				# place frontend information into a dictionary
				frontend_list.append(self._get_board_info(frontend))

			return frontend_list
		else:
			return self.frontends

	def get_breakout_info(self, return_as_dict = False):
		"""
		Description:
		Parameters:
		Return:
		"""		
		if return_as_dict == True:	
			return self._get_board_info(self.breakout)
		else:
			return self.breakout

	def get_connection_type(self):
		"""
		Description:
		Parameters:
		Return:
		"""		
		return self.connection

	def get_connection_info(self):
		"""
		Description:
		Parameters:
		Return:
		"""		
		return self.connection_info

	def set_name(self, name=None):
		"""
		Description:
		Parameters:
		Return:
		"""		
		if name != None:

			# make sure that given name is a string object
			if type(name) is str:

				# set name
				self.name = name

			# otherwise, report error 
			else:
				raise SwiftRadioDefinitionError("invalid radio unit name '{}'. name must be a string".format(name))

	def set_stackup(self, stackup):
		"""
		Description:
		Parameters:
		Return:
		"""		
		if stackup != None:

			# make sure that given name is a string object
			if type(stackup) is str:

				# set name
				self.stackup = stackup

			# otherwise, report error 
			else:
				raise SwiftRadioDefinitionError("invalid radio unit stackup '{}'. stackup must be a string".format(stackup))

	def set_connection_info(self, connection_type, connection_info=None):
		"""
		Description:
		Parameters:
		Return:
		"""		
		if type(connection_type) is str:
			self.connection = connection_type
			self.connection_info = connection_info

	def set_connection_type(self, connection_type):
		"""
		Description:
		Parameters:
		Return:
		"""		
		if type(connection_type) is str:
			self.connection = connection_type
			
	def set_devid(self, device_identifier):
		"""
		Description: sets the current instance device identification string
		Parameters: device_identifier - 16 digit device identifier as a string
		Return: status integer indicating if the device id was successfully set
		   		1 - device id was successfully set
				-1 - device could not be set to given value
		Note: device identifier must be a 16 character python string object
		Note: all string characters must be alphanumeric (i.e. letter or string)
		Note: all alphanumeric characters in string must be capitalized
		"""	
		# make sure that given device id if a string object
		if type(device_identifier) is str:

			# make sure it is at least 16 digits
			if len(device_identifier) == 16:

				# make sure all characters are alphanumeric
				if device_identifier.isalnum() == True:

					# make sure all characters are capitalized
					for character in device_identifier:
						if character.isalpha() == True:
							if character.isupper() == False:
								raise SwiftRadioDefinitionError("could not set devid. all characters must be upper case.")

					# set device id
					self.devid = device_identifier

					return 1

				# raise error if not
				else:
					raise SwiftRadioDefinitionError("could not set devid. one or more characters in given string is non-alphanumeric.")
					
			# raise error if not
			else:
				raise SwiftRadioDefinitionError("could not set devid. string must be at least 16 characters in length.")

		# raise error if not	
		else:
			raise SwiftRadioDefinitionError("could not set devid. given value is not a string.")

		# if here, return an error code
		return -1	

	def _get_board_info(self, board = None):
		"""
		Description:
		Parameters:
		Return:
		"""
		info = dict()
		if board != None:		
			info["name"] = board.get_name()
			info["board"] = board.get_board_index()
			info["variant"] = board.get_assembly_variant()
			info["number"] = board.get_assembly_board()
			info["revision"] = board.get_revision()
			info["serial"] = "{}-{}-{}".format(info["board"], info["variant"], info["number"])
			return info

		else:
			return None

class SwiftRadioDefinitionCli(SwiftRadioDefinition):
	""" 
	Description: 
	"""	
	def print_info(self):
		"""
		Description:
		Parameters:
		Return:
		"""
		name = self.get_name()
		connection_type = self.get_connection_type()
		baseband_info = ("baseband", [self.get_baseband_info()])
		frontend_info = ("frontend", self.get_frontend_info())
		breakout_info = ("breakout", [self.get_breakout_info()])
		radio_boards = [baseband_info, frontend_info, breakout_info]
		devid = (baseband_info[1])[0].get_devid()

		# print basic radio info
		print " name: {}".format(name)
		print " device id: {}".format(devid)
		print " connection: {}".format(connection_type)

		# print daughter board info
		for board_type, board_info_list in radio_boards:
			for board_info in board_info_list:
				if board_info != None:
					print "     {}: {} {}-{}-{}".format(board_type, board_info.get_name(), board_info.get_board_index(), board_info.get_assembly_variant(), board_info.get_assembly_board())

class SwiftRadioDefinitionError(RuntimeError):
	pass		