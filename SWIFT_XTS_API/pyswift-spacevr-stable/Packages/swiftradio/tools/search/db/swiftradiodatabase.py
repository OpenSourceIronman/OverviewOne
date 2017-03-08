#!/usr/bin/env python
from defs import swiftradiodef
import swiftboarddatabase

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__company__ = "Tethers Unlimited Inc."
__status__ = "Development"
__date__ = "Late Updated: 12/9/14"

class SwiftRadioDefinitionDatabase:
	"""
	Description:
	"""
	def __init__(self, board_db = None, name = None):
		"""
		Description:
		Parameters:
		"""
		self.name = name 				# optional database name
		self.radio_db = list()			# database containing info on each radio unit
		if board_db != None:
			self.board_db = board_db	# swift board database, used to define board information
										# for each radio in radio database
		else:
			self.board_db = swiftboarddatabase.SwiftBoardDatabase()

	# =============================================================================================================
	# 	Public Methods
	# =============================================================================================================
	def add_radio_info(self, name, baseband, frontend = None, breakout = None, connection = None, stackup = None):
		"""
		Description:
		Parameters:
		"""
		# create radio info object to store in database
		radio_info = swiftradiodef.SwiftRadioDefinitionCli()

		# set radio unit name (i.e. 'EM1')
		for radio in self.radio_db:
			# make sure a radio of the same name does not already exist
			if radio.get_name() == name:
				raise SwiftRadioDatabaseError("a radio with name '{}' already exists in radio database".format(radio.get_name()))

			# make sure this baseband is not already being used by another radio in database
			basebandinfo = radio.get_baseband_info(return_as_dict=True)
			baseband_num = "{}-{}-{}".format(basebandinfo["board"], basebandinfo["variant"], basebandinfo["number"])

			if baseband_num == baseband:
				raise SwiftRadioDatabaseError("cannot register baseband unit '{}' to radio '{}' because this baseband is already registered to radio '{}'".format(baseband, name, radio.get_name()))


		radio_info.set_name(name)

		# set board information
		radio_info = self._set_radio_board_info(radio_info, baseband, frontend, breakout)

		# set connection information
		radio_info.set_connection_info(connection)

		# set connection information
		radio_info.set_stackup(stackup)

		# place info in radio_db list
		self.radio_db.append(radio_info)


	def _set_radio_board_info(self, radio_unit, baseband, frontend=None, breakout=None):
		"""
		Description:
		Parameters:
		Return:
		"""
		board_info_strings = [("baseband", baseband), ("frontend" , frontend), ("breakout", breakout)]

		# get board information for each board
		for board_type, board_info in board_info_strings:

			# some radios can have multiple frontends, in this case board_info_strings will be a
			# list and the following process will need to be repeated appropriately
			daughterboard_strings = list()

			if type(board_info) is not list:
				daughterboard_strings.append(board_info)
			else:
				daughterboard_strings = board_info

			for daughterboard_assembly_string in daughterboard_strings:
				# first, parse combined board string into separate board index, assembly variant and board number values
				if daughterboard_assembly_string != None:
					index, variant, number = self._split_combined_board_string(daughterboard_assembly_string)

					# now, use separated board info to extract board from database, throw exception if it couldn't be found
					board = self.board_db.get_board(index, variant, number)

					# store board info
					if board != None:
						if board_type == "baseband":
							radio_unit.add_baseband_board(board)
						elif board_type == "frontend":
							radio_unit.add_frontend_board(board)
						elif board_type == "breakout":
							radio_unit.add_breakout_board(board)
						else:
							raise SwiftRadioDatabaseError("invalid board type '{}'".format(board_type))

					# raise error if board info could not be found in board database
					else:
						raise SwiftRadioDatabaseError("cannot add {} board with the index {}, assembly variation {}, and assembly board number {} because it could not be found in board database.".format(board_type, index, variant, number) )

		# return radio_unit object with newly saved board information
		return radio_unit

	def get_radio_info_by_name(self, name):
		"""
		Description:
		Parameters:
		Return:
		"""
		for radio_unit in self.radio_db:

			if name == radio_unit.get_name():

				return radio_unit

		return -1

	def get_radio_by_name(self, name):
		"""
		Description:
		Parameters:
		Return:
		"""
		return self.get_radio_info_by_name(name)

	def get_radio_by_devid(self, devid):
		"""
		Description:
		Parameters:
		Return:
		"""
		for radio_unit in self.radio_db:

			if devid == radio_unit.get_devid():

				return radio_unit

		return -1

	def get_database_radios(self):
		"""
		Description:
		Parameters:
		Return:
		"""
		return self.radio_db

	def get_database_radio_names(self):
		"""
		Description:
		Parameters:
		Return:
		"""
		name_list = list()

		for radio in self.radio_db:
			name_list.append(radio.get_name())

		return name_list

	def get_board_database(self):
		"""
		Description:
		Parameters:
		Return:
		"""
		return self.board_db

	def set_board_database(self, new_board_db):
		"""
		Description:
		Parameters:
		Return:
		"""
		# check if this is a SwiftBoardDatabase instance
		if 1:
			self.board_db = new_board_db
		else:
			raise SwiftRadioDatabaseError("**cannot set board database. database must be a SwiftBoardDatabase object**")

	def update_board_database(self, new_board_db):
		"""
		Description:
		Parameters:
		Return:
		"""
		# check if this is a SwiftBoardDatabase instance
		if 1:
			self.board_db = new_board_db
		else:
			raise SwiftRadioDatabaseError("**cannot set board database. database must be a SwiftBoardDatabase object**")

	# ==============================================================================================================
	# 	Private Methods
	# ==============================================================================================================
	def _split_combined_board_string(self, board_combined_string):
		"""
		Description:
		Parameters:
		Return:
		Note: combined string format:
			  BBB-BBB-AAA-CC
			  where,
			  BBB-BBB is the board number or index as a string (i.e. "128A-401")
			  AAA is the assembly variation as a string (i.e. "901")
			  CCC is the assembly board number as a string (i.e. "20A")
			  example: "128A-510-901-20E" (slx frontend)
		"""
		bad_string_format = False

		# check combined string format
		if ('-' in board_combined_string) and ( len(board_combined_string.split("-") ) > 3):

			# split string
			bstring = board_combined_string.split("-")

			# get index number
			index = "{}-{}".format(str(bstring[0]), str(bstring[1]))

			# get assembly variation
			variant = str(bstring[2])

			# get assembly board number
			temp = bstring[3:]
			number = "-".join(temp)		# this recombines a assembly board numbers that have '-' characters (i.e. 5-7)

			# return board info values
			return index, variant, number

		# otherwise, raise error and show correct format
		else:
			raise SwiftRadioDatabaseError("board information format incorrect. correct string format:\n" +
										  "BBB-BBB-AAA-CC\n" +
			  							  "where,\n" +
			  							  'BBB-BBB is the board number or index as a string (i.e. "128A-401")\n' +
			  							  'AAA is the assembly variant as a string (i.e. "901")\n' +
			  							  'CCC is the assembly board number as a string (i.e. "20A")\n' +
			  							  'example: "128A-510-901-20E" (slx frontend)\n')

		# indicate error if program reaches here (it shouldn't in current form)
		return -1

class RadioDatabase(SwiftRadioDefinitionDatabase):
	pass

class SwiftRadioDatabase(SwiftRadioDefinitionDatabase):
	pass

class SwiftRadioDatabaseError(RuntimeError):
	pass
