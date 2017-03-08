#!/usr/bin/env python

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__company__ = "Tethers Unlimited Inc."
__status__ = "Development"
__date__ = "Late Updated: 12/9/14"

class SwiftBoardDefinition:
	""" 
	Description: 
	"""	
	def __init__(self):
		""" 
		Description:
		"""
		self.name = None				# unofficial name of board (i.e. "BASE2")
		self.board = None				# board index number (i.e. "128A-401")
		self.assembly_variant = None	# assembly variant (i.e. "901" for board "128A-401")
		self.assembly_board = None		# assembly board number (i.e. "20A") 
		self.revision = None			# board revision number
		self.type = None				# type of board (i.e. "baseband", "frontend", "breakout")

	def get_name(self):
		"""
		Description:
		Parameters:
		Return:
		"""		
		return self.name

	def get_type(self):
		"""
		Description:
		Parameters:
		Return:
		"""		
		return self.type

	def get_board_index(self):
		"""
		Description:
		Parameters:
		Return:
		"""		
		return self.board

	def get_board_index_with_variant(self):
		"""
		Description:
		Parameters: 
		Return:
		"""
		# get board index
		bindex = self.get_board_index()

		# get assembly variant
		avariant = self.get_assembly_variant()

		# get full board number
		full_bnumber = "{}-{}".format(bindex, avariant)

		return full_bnumber

	def get_assembly_variant(self):
		"""
		Description:
		Parameters:
		Return:
		"""		
		return self.assembly_variant

	def get_assembly_board(self):
		"""
		Description:
		Parameters:
		Return:
		"""		
		return self.assembly_board	

	def get_revision(self):
		"""
		Description:
		Parameters:
		Return:
		"""		
		return self.revision		

	def set_type(self, boardtype):
		"""
		Description:
		Parameters:
		Return:
		"""		
		self.type = boardtype		
		
	def set_name(self, name):
		"""
		Description:
		Parameters:
		Return:
		"""
		# make sure that given name is a string object
		if type(name) is str:

			# set name
			self.name = name

		# otherwise, report error
		else:
			raise SwiftBoardDefinitionError("invalid pcb board unit name '{}'. name must be a string".format(name))		

	def set_board_index(self, index):
		"""
		Description:
		Parameters:
		Return:
		"""
		# make sure information is a string
		if type(index) is str:

			# check that variant is in XXX-XXX format
			pass

			# set variant number
			self.board = index

		# otherwise, report error
		else:
			raise SwiftBoardDefinitionError("{} board index must be a alphanumeric string (i.e. '128A-401')".format(self.name))

	def set_assembly_variant(self, variant):
		"""
		Description:
		Parameters:
		Return:
		"""
		# make sure information is a string
		if type(variant) is str:

			# set variant number
			self.assembly_variant = variant

		# otherwise, report error
		else:
			raise SwiftBoardDefinitionError("{} assembly variant must be a alphanumeric string (i.e. '05')".format(self.name))

	def set_assembly_board(self, board):
		"""
		Description:
		Parameters:
		Return:
		"""
		# make sure information is a string
		if type(board) is str:

			# set variant number
			self.assembly_board = board

		# otherwise, report error
		else:
			raise SwiftBoardDefinitionError("{} assembly board number must be a alphanumeric string (i.e. '5-7' or '20A')".format(self.name))			

	def set_revision(self, revision_num):
		"""
		Description:
		Parameters:
		Return:
		"""
		# make sure information is a string
		if type(revision_num) is str:

			# set variant number
			self.revision = revision_num

		# otherwise, report error
		else:
			raise SwiftBoardDefinitionError("revision number value '' must be a string (i.e. '2'). not {}".format(revision_num, type(revision_num)))	


			
class SwiftBasebandBoard(SwiftBoardDefinition):
	""" 
	Description: 
	"""	
	def __init__(self):
		""" 
		Description:
		"""
		SwiftBoardDefinition.__init__(self)
		self.devid = None

	def get_devid(self):
		"""
		Description: 
		Parameters: 
		Return: 
		"""	
		return self.devid

	def set_devid(self, id):
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
		# make sure that given device id is a string object
		if type(id) is str:

			# make sure it is at least 16 digits
			if len(id) == 16:

				# make sure all characters are alphanumeric
				if id.isalnum() == True:

					# make sure all characters are capitalized
					for character in id:
						if character.isalpha() == True:
							if character.isupper() == False:
								raise SwiftBoardDefinitionError("could not set devid {}. all characters must be upper case.".format(id))

					# set device id
					self.devid = id

					return 1

				# raise error if not
				else:
					raise SwiftBoardDefinitionError("could not set devid '{}'. one or more characters in given string is non-alphanumeric.".format(id))
					
			# raise error if not
			else:
				raise SwiftBoardDefinitionError("could not set devid '{}'. string must be at least 16 characters in length.".format(id))
		
		# raise error if not	
		else:
			raise SwiftBoardDefinitionError("could not set devid {}. given value is not a string.".format(id))

		# if here, return an error code
		return -1							



class SwiftFrontendBoard(SwiftBoardDefinition):
	""" 
	Description: 
	"""	
	pass


class SwiftBreakoutBoard(SwiftBoardDefinition):
	""" 
	Description: 
	"""	
	pass

class SwiftBoardDefinitionError(RuntimeError):
	pass		