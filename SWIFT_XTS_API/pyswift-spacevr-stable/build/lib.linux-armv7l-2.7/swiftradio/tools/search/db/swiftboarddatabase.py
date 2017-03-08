#!/usr/bin/env python
from defs import swiftboarddef

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__company__ = "Tethers Unlimited Inc."
__status__ = "Development"
__date__ = "Late Updated: 12/9/14"

class SwiftBoardDatabase:
	"""
	Description:
	"""
	def __init__(self, name = None):
		"""
		Description:
		Parameters:
		"""
		self.name = name
		self.board_db = list()
		self.baseband_db = list()
		self.frontend_db = list()
		self.breakout_db = list()

	# ===========================================================================================================================
	# 	Public Methods
	# ===========================================================================================================================
	def add_baseband_board(self, name, board, assembly_variant, assembly_board, revision = None, fpga_devid = None):
		"""
		Description:
		Parameters:
		Return:
		"""
		new_board = swiftboarddef.SwiftBasebandBoard()

		# define new board with general board attributes (board name, index, assembly variant, assembly board and revision num)
		new_board = self._create_new_board(new_board, name, board, assembly_variant, assembly_board, revision)

		# don't add new board if it already exists in database
		if new_board != -1:

			# define the baseband's device ID
			if fpga_devid != None:

				# make sure another board does not already share this device ID!!!!
				for baseband in self.baseband_db:
					if baseband.get_devid() == fpga_devid:
						raise SwiftBoardDatabaseError("cannot register baseband unit {}-{}-{} with device id {} ".format(board, assembly_variant, assembly_board, fpga_devid) +
													"in board database because this device ID is already assigned to baseband {}-{}-{}".format(baseband.get_board_index(), baseband.get_assembly_variant(), baseband.get_assembly_board()) )

				new_board.set_devid(fpga_devid)

			# save board type
			new_board.set_type("baseband")

			# add board to database
			self.board_db.append(new_board)
			self.baseband_db.append(new_board)

	def add_frontend_board(self, name, board, assembly_variant, assembly_board, revision = None):
		"""
		Description:
		Parameters:
		Return:
		"""
		new_board = swiftboarddef.SwiftFrontendBoard()

		# define new board with general board attributes (board name, index, assembly variant, assembly board and revision num)
		new_board = self._create_new_board(new_board, name, board, assembly_variant, assembly_board, revision)

		# don't add new board if it already exists in database
		if new_board != -1:

			# save board type
			new_board.set_type("frontend")

			# add board to database
			self.board_db.append(new_board)
			self.frontend_db.append(new_board)

	def add_breakout_board(self, name, board, assembly_variant, assembly_board, revision = None):
		"""
		Description:
		Parameters:
		Return:
		"""
		new_board = swiftboarddef.SwiftBreakoutBoard()

		# define new board with general board attributes (board name, index, assembly variant, assembly board and revision num)
		new_board = self._create_new_board(new_board, name, board, assembly_variant, assembly_board, revision)

		# don't add new board if it already exists in database
		if new_board != -1:

			# save board type
			new_board.set_type("breakout")

			# add board to database
			self.board_db.append(new_board)
			self.breakout_db.append(new_board)

	def get_board(self, board_index, assembly_variant, assembly_board):
		"""
		Description:
		Parameters:
		Return: - SwiftBoardDefinition instance if board with matching parameters was found
		  		- a None object if no matching board could be found.
		"""
		# iterate through the board database
		for board in self.board_db:

			# first, check for matching board index
			if board.get_board_index() == board_index:

				# second, check for matching assembly variant
				if board.get_assembly_variant() == assembly_variant:

					# finally, check for matching assembly board number
					if board.get_assembly_board() == assembly_board:

						return board

		# if no board with matching parameters was found return None object
		return None

	def get_database_boards(self):
		"""
		Description:
		Parameters:
		Return: - a list of all SwiftBoardDefinition instances in database
		  		- a None object if no instances are in database.
		"""
		return self.board_db

	def get_database_baseband_boards(self):
		"""
		Description:
		Parameters:
		Return: - a list of all SwiftBoardDefinition instances in database
		  		- a None object if no instances are in database.
		"""
		return self.baseband_db

	def get_database_frontend_boards(self):
		"""
		Description:
		Parameters:
		Return: - a list of all SwiftBoardDefinition instances in database
		  		- a None object if no instances are in database.
		"""
		return self.frontend_db

	def get_database_breakout_boards(self):
		"""
		Description:
		Parameters:
		Return: - a list of all SwiftBoardDefinition instances in database
		  		- a None object if no instances are in database.
		"""
		return self.breakout_db

	# ==============================================================================================================
	# 	Private Methods
	# ==============================================================================================================
	def _create_new_board(self, board, name, index, assembly_variant, assembly_board, revision = None):
		"""
		Description: generic create board method, all board types (baseband, breakout, frontend) should
					share the listed parameter board attributes (assembly variant, board index, ect.) and
					therefore all board types will also need to set them when being created. this function
					has been created to consolidate that processs for all boards.
		Parameters:
		Return:
		"""

		# make sure a board with the same assembly values does not already exist in database
		board_check = self._check_new_board_assembly(name, index, assembly_variant, assembly_board)

		# if it doesn't exist in database, create a new board
		if board_check == 1:

			# set board name
			board.set_name(name)

			# set board index number
			board.set_board_index(index)

			# set board assembly variant number
			board.set_assembly_variant(assembly_variant)

			# set board assembly board number
			board.set_assembly_board(assembly_board)

			# set revision number, if provided
			if revision != None:
				board.set_revision(revision)

			return board

		# if this exact board already exists in database, skip add
		elif board_check == -1:
			return -1

		# if the board exists, but is trying to be defined (i.e. under a different name) raise error
		else:
			board_serial = "{}-{}-{}".format(index, assembly_variant, assembly_board)
			raise SwiftBoardDatabaseError("cannot add '{}' board {} to database. A different '{}' board with index {}, assembly variation {}, and assembly board number {} already exists!".format(name, board_serial, board_check, index, assembly_variant, assembly_board) )

	def _check_new_board_assembly(self, name, board_index, assembly_variant, assembly_board):
		"""
		Description:
		Parameters:
		Return:
		"""
		board_db = self.board_db

		# make sure that no board in current database has the same exact assembly values
		for board in board_db:

			# check if the board indexes match
			if board.get_board_index() == board_index:

				# check if the board assembly variants match
				if board.get_assembly_variant() == assembly_variant:

					# check if the board assembly board numbers match
					if board.get_assembly_board() == assembly_board:

						# this board already exists, return error code
						if board.get_name() == name:
							return -1
						else:
							return board.get_name()

		# if program is here, no board errors were found
		return 1

class SwiftBoardDatabaseError(RuntimeError):
	pass
