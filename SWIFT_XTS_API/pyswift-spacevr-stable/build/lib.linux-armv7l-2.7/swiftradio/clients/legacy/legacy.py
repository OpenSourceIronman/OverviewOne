import os
import sys
import time
import warnings
import logging
from commands import command_table
from commands.registration import register_default_commands, register_file_commands, register_downloaded_commands
from packet import Packet_Classes
from packet.Packet_Utilities import Packet_Translator, Message_Framer
from threads import swift_threads
from utils import stringconversions
from utils.error import SwiftRadioError
from connections.settings import executecmd

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__company__ = "Tethers Unlimited Inc."
__status__ = "Development"
__date__ = "Created: 8/30/14"

class SwiftRadioInterface:
	"""
	Author: S. Alvarado
	Created: 8/30/14
	Description: main class used for commanding and controlling a SWIFT-SDR device over a variety
				 of physical connection types.
	"""
	def __init__(self, name=None, devid = None, text_translator = "on", trace=0, commands_file=None,
				register_file_cmds = False, nofile_warn = True, logfile=None):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description: General class constructor for instantiating a SwiftRadioInterface object.
		Parameters: name - arbitrary name of the SwiftRadioInterface object. defaults to 'SwiftRadioInterface'.
					devid - unique device identifier as a 16-character hex string (i.e.'013C4F2AC427C20B')
					trace - trace level for automatic log outputs to stdout.
					commands_file  - name of the commands .txt file to register from. By default, the SwiftRadioInterface
									 object will use the swiftradio_cmds.txt file unless otherwise specified.
					register_file_cmds - If set to True, the SwiftRadioInterface object will automatically search for a commands
										text file from which to register command information. If False, no command file is used to
										register command information.
					nofile_warn - If True, a warning will be issued if a commands .txt file has not been downloaded and saved in the default directory
								 within the swiftradio package. Setting to False will turn off warnings.
					logfile - name of file to write automatic log outputs. defaults to stdout if not provided.
		Return: SwiftRadioInterface instance
		"""
		self._radio_name = name 					# arbitrary name that can be assigned to instances
		self._devid = devid 						# radio device identifier
		self._connection_list = list() 				# list of connections created
		self._tracelevel = trace 					# verbosity trace level for automatic logging
		self._commands_filename = commands_file 	# name of the commands file for registering command information
		self._logger = None 						# file object used to write log outputs
		self._command_table = None 					# command table object for storing command information

		# set default radio name if none provided
		if self._radio_name == None:
			self._radio_name = self.__class__.__name__

		# if provided, set device ID string	using set_devid method
		if self._devid != None:
			self.set_devid(devid)

		# create logger, if no logger provided, use stdout as default
		if logfile == None:
			self._logger = sys.stdout
		else:
			self._logger = open( logfile, "w" )

		# create radio commands table
		self._command_table = command_table.SwiftCmdhostCommandTable()

		# register basic radio commands that every SwiftRadioInterface has access to
		self._command_table = self._register_default_cmds(self._command_table)

		# register commands from downloaded commands file
		if register_file_cmds:
			self._command_table = self._register_download_file_cmds(self._command_table, self._commands_filename, nofile_warn)

	# ===========================================================================================================================
	# 	Public Methods
	# ===========================================================================================================================
	def add_ethernet_connection(self, host, name = None, port=12345, discovery_port=802, bind_port = 40000, protocol = "IPv4",
								data_endianess="little", transport_layer="UDP", cmd_text_translator = "on", packet_type = "swiftpacket",
								timeout=0):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description: adds a "ethernet" connection to instance connection list. Supports UDP and TCP protocols
		Parameters: host - a string representing the ip address of the radio to connect (i.e. '198.22.43.8'). format depends on 'protocol' parameter
		Optional Parameters: name - caller can assign a connection an arbitrary name (as a string) which can then be referenced for other operations
									involving a connection (i.e. connecting/disconnecting). useful if multiple connections are assigned to a single SwiftRadioInstance
		 					 port - radio service port number. defaults to 12345--which is the packet interface port.
		 					 cmd_text_translator - 	allows radio commands to be executed in "command-line text format" (i.e. 'bintest -n 1 -p 128').
							 						options include 'on' or 'off'.
		Return: status integer value.
				 1 - successful connection established
				-1 - unsuccessful connect attempt
		Example:
				radio = SwiftRadioInstance(trace = 1)
				radio.add_ethernet_connection("123.456.789.123", name = "packet_interface", cmd_text_translator = 'on')
				...
		"""
		# import Swift Ethernet libraries
		from io.Ethernet.SwiftEthernetInterface import SwiftEthernetInterface

		connection_type = "ethernet"
		info_dict = dict()
		self._trace_output("adding {} connection... ".format(connection_type), newline=0, msg_tracelevel=2)

		# define object that represents physical interface (ethernet socket).
		connection_instance = SwiftEthernetInterface(host=host, port=port, discovery_port=discovery_port, bind_port = bind_port,
											  protocol=protocol, transport_layer=transport_layer, timeout=timeout)

		# assign a receive thread to this connection. the thread assigned will differ depending on transport layer specified (UDP or TCP)
		if str(packet_type).lower() == 'swiftpacket':
			connection_thread = swift_threads.UdpSwiftPacketRxThread(DataInterface = connection_instance, endianess = data_endianess)
		elif str(packet_type).lower() == 'raw_dgram':
			connection_thread = swift_threads.RawUdpPacketRxThread(DataInterface = connection_instance, endianess = data_endianess)
		else:
			raise SwiftRadioError("add_ethernet_connection: invalid packet type ('swiftpacket', 'raw_dgram')")
			return -1

		# assign a default connection name if not given
		if name == None:
			name = connection_type + str(len(self._connection_list))

		# create an information dictionary describing this connection protocol attributes
		info_dict = {"host":host, "port":port, "bind_port":bind_port,"discovery_port":discovery_port, "protocol":protocol, "transport_layer":transport_layer,"timeout":timeout}

		# create default execute command settings dict
		command_settings = self._create_default_execute_settings()
		command_settings.cmdline_syntax = cmd_text_translator

		# create an information dictionary describing the connection and store in this instances connection list
		self._connection_list.append({"name":name, "instance":connection_instance, "type":connection_type, "packet_list":list(), "isopen":False,
									"thread":connection_thread, "translator":cmd_text_translator, "endianess":data_endianess,
									"execute_settings":command_settings,
									"spacewire": None, "ethernet":info_dict, "uart": None})

		self._trace_output("done.", msg_tracelevel=2, radioname=0)

		return 1

	def add_spacewire_connection(self, device = 65536, name = None, rx_channel = 1, tx_channel = 1, end_of_packet = 1, mode = "interface",
								cmd_text_translator = "on", data_endianess = "little", timeout=0):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description:
		Parameters:
		Return: status integer value.
				 1 - successful connection established
				-1 - unsuccessful connect attempt
		Example:
				...
				spacewire_device_id = 65536
				radio = SwiftRadioInstance(trace = 1)
				radio.add_spacewire_connection(spacewire_device_id)
				...
		"""
		# import Swift Spacewire libraries
		from io.SpaceWire.SwiftSpaceWireInterface import SwiftSpaceWireInterface

		connection_type = "spacewire"
		info_dict = dict()
		self._trace_output("adding {} connection... ".format(connection_type), newline=0, msg_tracelevel=2)

		# create a spacewire interface (an instance representing the radio's spacewire interface)
		connection_instance = SwiftSpaceWireInterface(identifier = device, rx_channel = rx_channel, tx_channel = tx_channel, end_of_packet = end_of_packet, mode = mode)

		# assign a receive thread to this connection.
		connection_thread = swift_threads.SwiftSpaceWireRxThread(DataInterface = connection_instance, endianess = data_endianess)

		# assign a default connection name if not given
		if name == None:
			name = connection_type + str(len(self._connection_list))

		# create an information dictionary describing the attributes of this connection type's attributes
		info_dict = {"identifier": device, "rx_channel": rx_channel, "tx_channel": tx_channel, "end_of_packet":end_of_packet, "mode":mode, "timeout":timeout}

		# create default execute command settings dict
		command_settings = self._create_default_execute_settings()
		command_settings.cmdline_syntax = cmd_text_translator

		# create an information dictionary describing the connection attributes and store in this instances connection list
		self._connection_list.append({"name":name, "instance":connection_instance, "type":connection_type, "packet_list":list(), "isopen":False,
									"thread":connection_thread, "translator":cmd_text_translator, "endianess":data_endianess,
									"execute_settings":command_settings,
									"spacewire":info_dict, "ethernet":None, "uart":None})

		self._trace_output("done.", msg_tracelevel=2, radioname=0)
		return 1

	def add_uart_connection(self, port, name = None, baud=115200, timeout=0, framing="HDLC", cmd_text_translator = "on", data_endianess = "little"):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description: adds a new uart connection to radio instance's connection list.
		Parameters:
		Return: value indicating if a connection was successfully created
		"""
		# import Swift Serial libraries
		from io.UART import swiftuarthdlc

		connection_type = "hdlc"
		info_dict = dict()
		self._trace_output("adding {} connection... ".format(connection_type), newline=0, msg_tracelevel=1)

		# define serial object
		if self._tracelevel > 2:
			connection_instance = swiftuarthdlc.SwiftUartHDLC(port=port, baudrate=int(baud), timeout=int(timeout), codec_loglevel=logging.DEBUG)
		elif self._tracelevel == 2:
			connection_instance = swiftuarthdlc.SwiftUartHDLC(port=port, baudrate=int(baud), timeout=int(timeout), codec_loglevel=logging.WARN)
		else:
			connection_instance = swiftuarthdlc.SwiftUartHDLC(port=port, baudrate=int(baud), timeout=int(timeout))

		# assign a receive thread to this connection. (asynchronous thread, reads in streaming data)
		connection_thread = swift_threads.SwiftHDLC422RxThread(DataInterface = connection_instance, endianess = data_endianess)

		# assign a default connection name if not given
		if name == None:
			name = connection_type + str(len(self._connection_list))

		# create an information dictionary describing this connection protocol's attributes
		info_dict = {"serial_port":port, "baudrate":int(baud), "timeout":timeout, "framing":framing}

		# create default execute command settings dict
		command_settings = self._create_default_execute_settings()
		command_settings.cmdline_syntax = cmd_text_translator

		# create an information dictionary describing the connection attributes and store in this instances connection list
		self._connection_list.append({"name":name, "instance":connection_instance, "type":connection_type, "packet_list":list(), "isopen":False,
									 "thread":connection_thread, "translator":cmd_text_translator, "endianess":data_endianess,
									 "execute_settings":command_settings,
									"spacewire":None, "ethernet":None, "serial":info_dict})

		self._trace_output("done.", msg_tracelevel=1, radioname=0)

		return 1

	def check_connection_status(self, name=None):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description:
		Parameters:
		Return: 1 - connection is currently open
			   	0 - connection is closed
			   	-1 - connection does not exist
		"""
		radio_connection = self._find_connection(name)

		if radio_connection != -1:

			if radio_connection["isopen"] == True:
				return 1
			else:
				return 0

		else:
			raise SwiftRadioError("cannot check status, specified connection does not exist.")

	def clear_packet_list(self, name = None):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description: all packets received from the radio are stored in a list object (each connection created will have
					 it's own "packet list"). this list can be cleared using this method.
		Optional Parameters: name - specific connection whose packet list to clear
		Return: status integer. 1 indicates a successful clearing, 0 indicates a clear failure.
		"""
		connection = self._find_connection(name)

		if connection != -1:
			connection["packet_list"] = []
			return 1
		else:
			return 0

	def commandtable_registration_info(self):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description: Returns the number of commands and parameters currently registered in the SwiftRadioInterface
					 object's command table.
		Parameters:
		Return: two-item tuple containing the following information:
				total number of commands registered in the command table
				total number of packets registered in the command table
				Format:
				return_info = ( num_cmds_registered, num_params_registered)
		"""
		registered_cmds = self._command_table.get_num_cmds_registered()
		registered_params = self._command_table.get_num_params_registered()

		return registered_cmds, registered_params

	def connect(self, name=None, fail_exception = True):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description: establishes a connection for communicating with the radio.
		Optional Parameters:	name - 	name of the connection to connect to, useful if multiple connections have been created
										for the SwiftRadioInstance. (Defaults to first connection in connection list if no name is specified)
								fail_exception - a program exception is thrown if any error occurs while attempting to connect to a radio.
		Return: a boolean value, True if connect attempt was successful or False if unsuccessful. This is only relevant if fail_exception is False.
		Note: a connection must be created (using the add_X_connection() method) before you can use the connect() method.
		Note: the name parameter can be defined as "-a" to connect to all available connections created for this instance.
		Note: if no 'name' parameter is specified (i.e. name = None), the first connection in the connection list will be used.
		Example:
				radio = SwiftRadioInstance()
				radio.add_ethernet_connection("123.456.789.10", name = "packet_interface")
				radio.connect(name = "packet_interface", fail_exception = True)
				...
		"""
		connect_complete = False
		radio_connection = None

		if name == "-a":
			# if specified name is "-a", connect to all connections in radio's connection list
			for connection in self._connection_list:

				# connect to specified "connection object" (i.e. created pyserial or socket instance for a serial or ethernet connection)
				if (connection["instance"] != None) and (connection["isopen"] != True):
					self._trace_output("{}: connecting... ".format(connection["name"]), newline=0, msg_tracelevel=1)
					connect_complete = connection["instance"].connect()
					if connect_complete == False:
						connect_complete = False
						self._trace_output("fail.", msg_tracelevel=1, radioname=0)
					else:
						connection["isopen"] = True
						self._trace_output("done.", msg_tracelevel=1, radioname=0)

				# start the receive thread
				if (connection["thread"] != None) and (connect_complete == True):
					connection["thread"].start()

		else:
			# locate specific connection in connection list
			radio_connection = self._find_connection(name)

			if radio_connection != -1:
				# connect to specified "connection object" (i.e. created pyserial or socket instance for a serial or ethernet connection)
				if (radio_connection["instance"] != None) and (radio_connection["isopen"] != True):
					self._trace_output("{}: connecting... ".format(radio_connection["name"]), newline=0, msg_tracelevel=1)
					connect_complete = radio_connection["instance"].connect()
					if connect_complete == False:
						connect_complete = False
						self._trace_output("fail.", msg_tracelevel=1, radioname=0)
					else:
						radio_connection["isopen"] = True
						self._trace_output("done.", msg_tracelevel=1, radioname=0)

				# start the receive thread
				if (radio_connection["thread"] != None) and (connect_complete == True):
					# time.sleep(1)
					radio_connection["thread"].start()
			else:
				raise SwiftRadioError("cannot connect to radio. no connection defined.")

		# throw an exception if a connection error occurred and fail exceptions option is on
		if (connect_complete == False) and (fail_exception == True):
			raise SwiftRadioError("radio connect attempt failed.")

		return connect_complete

	def disconnect(self, name=None):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description: disconnect from specified connection. note that this will also close the associated receive thread.
		Optional Parameters:	name - 	name of the connection to connect to, useful if multiple connections have been created
										for the SwiftRadioInstance. (Defaults to first connection in connection list if no name is specified.
		Note: a connection must be created (using add_X_connection()) and established (using connect()) before you can use the disconnect() method.
		Note: the name parameter can be defined as "-a" to disconnect from all currently active connections.
		Return: None
		"""

		radio_connection = None

		if name == "-a":
			# disconnect from all currently open connections in connection list
			for connection in self._connection_list:

				# verify if this connection is open
				if connection["isopen"] == True:

					# close the receive threads (this must be done before closing the connection
					# to avoid crashing and "hanging" on program exit)
					if (connection["thread"] != None):
						connection["thread"].close()

					# close connections
					if (connection["instance"] != None):
						self._trace_output("{}: disconnecting... ".format(connection["name"]), newline=0, msg_tracelevel=1)
						connection["instance"].close()
						self._trace_output("done.", msg_tracelevel=1, radioname=0)
						connection["isopen"] = False
		else:
			# locate specific connection in connection list
			radio_connection = self._find_connection(name)

			if (radio_connection != -1):

				# verify if this connection is open
				if radio_connection["isopen"] == True:

					# close the receive thread (this must be done before closing the connection
					# to avoid crashing and "hanging" on program exit)
					if radio_connection["thread"] != None:
						radio_connection["thread"].close()

					# close connection
					if radio_connection["instance"] != None:
						self._trace_output("{}: disconnecting... ".format(radio_connection["name"]), newline=0, msg_tracelevel=1)
						radio_connection["instance"].close()
						self._trace_output("done.", msg_tracelevel=1, radioname=0)
						radio_connection["isopen"] = False

	def download_command(self, command = "all", cmds_filename = None, connection_name = None, update_file = True, validate_download=True, timeout = 15):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description:
		Optional Parameters: command - name of the command whose info you wish to download ('rxen', 'devid' ect.) or "all" for every command.
							 connection - name of the connection to start the transfer over (defaults to first connection in connection list)
							 update_file - True/False boolean value that determines if the new command info downloaded will be written to the downloaded table file
							 validate_download - True/False boolean. True performs a download error check by requesting a transaction info packet from radio.
		Return: a 3-element tuple containing 1) a status integer indicating if the download process was successful (This value is negative if the
				download procedure failed) 2) a tuple containing the number of commands downloaded from the radio and the expected number of commands downloaded 3)
				a tuple containing the number of parameters downloaded from the radio and the exepected number of parameters.
				return format: ( status, (commands_downloaded, expected_commands), (parameters_downloaded, expected_parameters) )
				status integer values:
				 1 = successful download
				 0 = a command execution error occurred (i.e. a timeout or received invsync packet)
				-1 = did not receive a transaction info packet (this is needed to error check the data download) from radio
				-2 = The number of commands received does not match the expected commands value in transaction info packet
				-3 = The number of parameters received does not match the expected parameters value in transaction info packet
				-4 = download timeout. check your network connection
		todo: return commands received vs expected and parameters received vs. expected information.
			  need to implement a parameter and a mechanism for reattempting failed downloads.
		"""
		temp_table = None						# temporary holder for new command table instance that will replace existing command table instance
		dlcmdinfo_pkts = list()					# list packets received from executing the dlcmdinfo command
		reserved_dl_transid = 0xFFFE			# transaction identifier for tracking all dlcmdinfo packets
		dlstatus = 0 							# flag indicating if dlcmdinfo command executed to completion
		default_filename = "swiftradio_cmds.txt" 	# default download file name and directory location
		default_filedir = "{}/commands/downloads/".format(os.path.dirname(os.path.realpath(__file__)))

		# execute dlcmdinfo command to get command information
		dlcmdinfo_pkts, error_code, error_type = self.execute("dlcmdinfo {} -t".format(command), name=connection_name,
															  transid=reserved_dl_transid, return_error=True, timeout=timeout)

		# if no errors, process downloaded command packets and register in command table
		if error_code == 0:
			self._command_table, dlstatus, cmdinfo, paraminfo = register_downloaded_commands.register_dlcmdinfo_command_pkts(self._command_table, dlcmdinfo_pkts,
																							   error_check = validate_download)

			# if update_file option is set to true, write new command table to file
			if update_file == True:

				# if no cmds_filename was given, create in default directory with default name
				if cmds_filename == None:
					filename_with_dir = default_filedir + default_filename

				# if cmds_filename is given, but no explicit file path is given in the cmds_filename, use default file location
				elif ("/" not in cmds_filename) and ("\\" not in cmds_filename):
					filename_with_dir = default_filedir + cmds_filename

				# if a name with a file path is given, leave name as is
				else:
					filename_with_dir = cmds_filename

				# make sure the file directory exists before trying to write to it!
				filedir = os.path.dirname(os.path.realpath(filename_with_dir))

				if os.path.isdir(filedir):

					# write command table to file
					self._command_table.write_table_to_file(filename_with_dir)

				# raise error if not
				else:
					raise SwiftRadioError("Cannot write file '{}' because directory '{}' does not exist!".format(cmds_filename, filedir) )

			# return code to indicate cmd download status
			return dlstatus, cmdinfo, paraminfo

		# if a timeout error occurred, report timeout
		elif error_type == -999:
			return -4, (0,0), (0,0)

		# otherwise, an invsync or negative cmderr value received
		else:
			return 0, (0,0), (0,0)

	def download_command_v2(self, command = "all", connection = None, dlvalidate = True, dlretries = 1,  dltimeout = 5, overwrite_table = False, update_file = True):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description:
		Optional Parameters: command - name of the command whose info you wish to download ('rxen', 'devid' ect.) or "all" for every command.
							 connection - name of the connection to start the transfer over (defaults to first connection in connection list)
							 dlvalidate - True/False boolean. True performs a download error check by requesting a transaction info packet from radio.
							 dlretries - number of download attempts on failed downloads
							 dltimeout - timeout, in seconds, for executing the dlcmdinfo
							 overwrite_table - if True, only commands that have been downloaded via dlcmdinfo will be saved to SwiftRadioInterface
							 				   object's command table. note that any commands registered in table previous to download will be deleted.
							 update_file - if True, every command registered to the SwiftRadioInterface's command table post-download will be written
							 			   to the SwiftRadio_CommandTable.txt file.
		Return: a 3-element tuple containing 1) a status integer indicating if the download process was successful (This value is negative if the
				download procedure failed) 2) a tuple containing the number of commands downloaded from the radio and the expected number of commands downloaded 3)
				a tuple containing the number of parameters downloaded from the radio and the exepected number of parameters.
				return format: ( status, (commands_downloaded, expected_commands), (parameters_downloaded, expected_commands) )
				status integer values:
				 1 = successful download
				 0 = a command execution error occurred (i.e. a timeout or received invsync packet)
				-1 = did not receive a transaction info packet (this is needed to error check the data download) from radio
				-2 = The number of commands received does not match the expected commands value in transaction info packet
				-3 = The number of parameters received does not match the expected parameters value in transaction info packet
				-4 = download timeout. check connection to radio
		todo: return commands received vs expected and parameters received vs. expected information.
			  need to implement a parameter and a mechanism for reattempting failed downloads.
		"""
		temp_table = None						# temporary holder for new command table instance that will replace existing command table instance
		dlcmdinfo_pkts = list()					# list packets received from executing the dlcmdinfo command
		reserved_dl_transid = 0xFFFE			# transaction identifier for tracking all dlcmdinfo packets
		dlstatus = 0 							# flag indicating if dlcmdinfo command executed to completion
		dlcmdparaminfo = dict()
		trans_cmds_params = None
		download_complete = False
		dlpkts = list()
		dlattempts = 0

		# [1] download commands from radio, reattempt any failed downloads if necessary
		while (download_complete == False) and (dlattempts <= dlretries):

			# execute dlcmdinfo command
			pkts, error_code, error_type = self.execute("dlcmdinfo {} -t".format(command), name=connection,
																  transid=reserved_dl_transid, return_error=True, timeout=dltimeout)

			# get command and parameter info
			if error_code == 0:

				# get command, parameter and transaction information from downloaded packets as dictionaries
				new_cmds_params, new_transinfo = Download_Commands.get_command_info_from_packets(pkts)

				# save transaction information (if it hasn't already been saved by a previous download attempt)
				if trans_cmds_params == None:			# note that if the last download produced no transinfo packet, new_transinfo
					trans_cmds_params = new_transinfo 	# will be a NoneType object (making trans_cmds_params also NoneType)

				# save new packets downloaded from radio
				dlpkts += pkts 							# note that duplicate packets will be ignored during command registration,
														# so just save all packets (even duplicates due to reattempted downloads)

				# save new command/parameter info parsed from packets
				dlcmdparaminfo = Download_Commands.add_new_command_info(new_cmds_params, dlcmdparaminfo)

				# check that all commands and parameters have been downloaded
				if dlvalidate:
					download_complete = Download_Commands.verify_all_cmds_params_downloaded(dlcmdparaminfo, trans_cmds_params)
				else:
					download_complete = True

			# update download attempt counter
			dlattempts += 1

		# [2] register new commands in command table (create a fresh command table to register commands if necessary)
		if overwrite_table:
			self._command_table = command_table.SwiftCmdhostCommandTable()
		self._command_table, dlstatus, cmdinfo, paraminfo = Download_Commands.register_downloaded_commands(dlpkts, self._command_table)

		# [3] write new command table to file (if update_file is set to True)
		if update_file == True:
			self._command_table.write_table_to_file(self._commands_filename)

		# [4] return code to indicate cmd download status
		return dlstatus, cmdinfo, paraminfo

	def execute(self, command, name = None, return_error = None, transid = None, auto_throttle = None,
				timeout = None, fail_exception= None, fail_retry = None, max_retries = None, cmdline_syntax=None):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description: Execute a radio command.
		Parameters: command - if text_translator is on, buffer is a command line string (i.e. "rxdis -a"), otherwise it's a list of 'byte' or 'hex' objects.
		Optional Parameters:	name - 	name of the connection to send the command data over, useful if multiple connections have been created
										for the SwiftRadioInstance. (Defaults to first connection in connection list if no name is specified)
								return_error - if True, returns an error "code" and "type" integer in addition to any swiftradio packets as a 3-element tuple (packet_list, code, type)
								transid - arbitrary transaction identifier. any packets returned from the radio as a result of this execution procedure will also
										  carry the same transaction identifier
								auto_throttle - if True, the SwiftRadioInstance will wait (block) until a valid DESYNC is received from the radio or a timeout has occurred. if False,
												command data is sent to the radio and the program resumes (non-blocking). Note: any subsequent packets received from the radio are still
												placed in the SwiftRadioInstance's packet list as the handling of received data is performed in a separate thread.
								timeout - the time period, in seconds, the SwiftRadioInstance will wait for a DESYNC packet. defaults to 2 seconds.
								fail_exception - raises a SwiftRadioError exception if the command failed to execute due to any error condition. conditions include a received INVSYNC
											 	 control sequence, a execution timeout, or a CMDERR control sequence containing an error code (negative value).
								fail_retry - if True, the SwiftRadioInstance will resend a command if a timeout execution error condition occurs.
								max_retries - maximum number of times to resend a command. defaults to 5
		Return: if return_error is false, returns a list of "packets" (RPCMessageFrame objects) received from the radio. if return_error if True, a 3-element tuple is returned.
				the tuple includes the packet list in addition to error code and error type values: (packetlist, error_code, error_type).
		Example:
				radio = SwiftRadioInstance(trace = 1)
				radio.add_ethernet_connection("123.45.67.89", name = "packet_interface", cmd_text_translator = 'on')
				radio.connect(name = "packet_interface")
				devid_pkts = radio.execute("devid", name = "packet_interface")
		"""
		command_complete = False
		command_retries = 0
		pkt_list = Packet_Classes.SwiftPacketList()
		settings = None
		error_code = 0
		error_type = 0

		# [1] find the connection in connection list to send command. defaults to 1st connection in list if not specified
		radio_connection = self._find_connection(name)

		# if the connection was not found, exit
		if radio_connection == -1:
			self._trace_output("**execute fail: connection '{}' does not exist**".format(name), msg_tracelevel=1)
			error_code = -997
			command_complete = True
		else:
			# verify connection status is good before sending (i.e. connection has been opened)
			# self.check_connection_status returns 1 if the connection is open
			if self.check_connection_status(radio_connection["name"]) != 1:
				self._trace_output("{}(closed): **please open connection using connect() method**".format(radio_connection["name"]), msg_tracelevel=1)
				error_code = -998
				command_complete = True

		# [2] get settings for executing this command
		if error_code == 0:
			settings = self._get_execute_settings(name, return_error, auto_throttle, timeout, fail_exception, fail_retry,
												max_retries, transid, cmdline_syntax)
		else:
			settings = self._get_execute_settings()

		# [3] execute command, can optionally repeat procedure depending on fail_retry parameter setting
		while (command_complete == False) and (command_retries <= settings.max_retries):

			# [2] check if data is a text command-line string that first needs to be converted from string to a byte list
			if settings.cmdline_syntax == "on":

				# A) convert text string to a message packet
				packet_buffer = Packet_Translator.text_to_swiftbytelist(command, self._command_table, transid=settings.transid, packet_endianess=radio_connection["endianess"])

				if packet_buffer == -1:
					packet_buffer = []
					break

				# B) check if packet needs to be wrapped in a framing protocol (this is needed for uart comms)
				if radio_connection["type"] == "uart":

					# wrap buffer in framing info message
					info = radio_connection["uart"]
					packet_buffer = info["framing_layer"](packet_buffer)
			else:

				# data is already in raw binary packet format, send packet to radio as is
				packet_buffer = command

			self._trace_output("{}: sending {} bytes: ".format(radio_connection["name"], len(packet_buffer)), msg_tracelevel=3, newline=0)
			self._trace_output(packet_buffer, msg_tracelevel=3, radioname=0)

			# [4] wait for command to finish (if auto throttle option is true)
			if (settings.auto_throttle == True) and (settings.cmdline_syntax == "on"):
				if command_retries > 0:
					self._trace_output("{}: fail retry {}: executing '{}'... ".format(radio_connection["name"], command_retries, command), newline=0, msg_tracelevel=1)
				else:
					self._trace_output("{}: executing '{}'... ".format(radio_connection["name"], command), newline=0, msg_tracelevel=1)

				# [5] Send packet to radio
				radio_connection["instance"].write(packet_buffer)

				# throttle until command is finished
				pkt_list, error_code, error_type = self._command_throttle(settings.timeout, settings.transid, radio_connection["name"])

				# check if command was successful
				if error_code == 0:

					# command completed successfully, exit loop and return packets
					self._trace_output("done.", msg_tracelevel=1, radioname=0)
					command_complete = True
				else:

					# indicate that the command failed
					self._trace_output("**fail** ", msg_tracelevel=1, radioname=0, newline = 0)

					# display the error information for debugging purposes
					self._print_error_msg(error_code, error_type)

					# resend the command if fail_retry is set to true
					if (settings.fail_retry == True):
						command_complete = False
						command_retries += 1
					else:
						command_complete = True
			else:
				self._trace_output("{}: executing '{}'... ".format(radio_connection["name"], command), newline=0, msg_tracelevel=1)
				# [5] Send packet to radio
				radio_connection["instance"].write(packet_buffer)
				self._trace_output("done.", msg_tracelevel=1, radioname=0)
				command_complete = True

		if (error_code != 0) and (settings.cmdline_syntax == "on"):
			self._trace_output("**could not execute '{}'**".format(command), msg_tracelevel=1)
		elif (error_code != 0) and (settings.cmdline_syntax == "off"):
			self._trace_output("**could not send raw data**".format(), msg_tracelevel=1)

		# throw exception if command failed exception option is set to True
		if error_code != 0 and settings.fail_exception == True:
			raise SwiftRadioError("Command Fail: '{}' failed to execute.".format(command))

		# return packet data
		if settings.return_error == True:
			return pkt_list, error_code, error_type
		else:
			return pkt_list

	def get_command_table(self):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description: gets the current instance of the command table
		Parameters: None
		Return: CommandTable object
		"""
		return self._command_table

	def get_packet(self, packet_num = None, delete = False, connection_name = None, connection_num = None):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description: Get packet in a connection's packet list
		Parameters: packet_num - packet location in a connection's SwiftPacketList.
					delete - delete packet from list. (packet is still returned to caller)
					connection_name - name of the connection to retrieve packet from.
		Return: SwiftPacket object.
		"""
		# make sure connection's packet list is updated with newest received packets
		self._update_packet_list(connection_name, connection_num)

		# retrieve connection instance
		connection = self._find_connection(connection_name, connection_num)

		# retrieve first packet in packet list if no packet number is specified
		if packet_num == None:

			# check that there is at least one packet in packet list
			if len(connection["packet_list"]) > 0:

				# extract first packet
				packet = connection["packet_list"][0]

				# delete this packet from the packet list if option is set
				if delete == True:
					del connection["packet_list"][0]

				# return this packet to caller
				return packet

			# return None value if no packets in list
			else:
				return None

		# retrieve packet in list specified by provided packet number
		else:

			# retrieve packet in list
			if (int(packet_num) >= 0) and (int(packet_num) < len(connection["packet_list"])):

				# extract specified packet
				packet = connection["packet_list"][int(packet_num)]

				# delete this packet from the packet list if option is set
				if delete == True:
					del connection["packet_list"][int(packet_num)]

				# return packet to caller
				return packet
			else:
				return None

	def get_devid(self):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description: gets the current instance device identification string
		Parameters: None
		Return: - 16 digit device identifier as a string
				- None object if the devid has not been defined
		Note: all alphabetic characters in string are capitalized
		"""
		return self._devid

	def get_name(self):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description: Gets name defined for a SwiftRadioInterface object.
		Parameters: None
		Return: - name of set
				- None object if no name was defined
		"""
		return self._radio_name

	def get_packet_list(self, name=None, transid = None, dequeue = False):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description: returns the packet list for the specified connection
		Optional Parameters:
		Return:
		"""
		# make sure connection's packet list is updated with newest received packets
		self._update_packet_list(name)

		# retrieve connection instance
		connection = self._find_connection(name)

		# create return packets list, this will be what's returned to caller
		return_packets = list()

		# check that there is at least one packet in packet list
		if len(connection["packet_list"]) > 0:

			# check if packets should be retrieve based on a specified transaction identifier
			if transid == None:

				# create shallow copy of the connection's packet list, this ensures that return packets list
				# won't be modified by changes made to the connection's packet list
				return_packets = list(connection["packet_list"])

				# delete connection's packet list if dequeue is true
				if dequeue == True:
					connection["packet_list"] = []

			# retrieve packets with specified trans id
			else:
				connection_save_list = list()

				# iterate through packet list, store packets with matching transid
				for i in range(len(connection["packet_list"])):

					# retrieve packet from connection's packet list
					packet = connection["packet_list"][i]

					# check that this is a packet is SwiftPacket (which has a transid attribute)
					if isinstance(packet, Packet_Classes.SwiftPacket):

						# get packet information
						packet_info = packet.get_packet_info()

						# check for matching id...
						if int(transid) == int(packet_info["transid"]):

							# store in return list if transid match
							return_packets.append(packet)

						# store non matching packets (this helps with late updates to connection's packet list)
						else:
							if dequeue == True:

								# save packet in save list
								connection_save_list.append(connection["packet_list"][i])

				# remove packets with matching trans id if dequeue is true
				if dequeue == True:
					connection["packet_list"] = connection_save_list

			# return packet list
			return return_packets
		else:
			# print "packet list is empty"
			return []

	def get_tracelevel(self):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description: Gets current trace level.
		Parameters: None
		Return: trace level as an integer object
		"""
		return self._tracelevel

	def get_connection_info(self, connection_name=None):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description:
		Parameters:
		Return:
		"""
		connection = self._find_connection(connection_name)

		if connection != -1:
			connection_type = connection["type"]
			connection_info = connection[connection_type]
		else:
			connection_info = -1

		return connection_info

	def list_connections(self):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description: Prints information about all the connections that have been
					 created for a SwiftRadioInterface instance to console (stdout).
		Parameters: None
		Return: None
		"""
		i = 0

		for connection in self._connection_list:
			self._logger.write( "Connection[" + str(i) + "]\n" )
			if connection["type"] == "serial":
				info = connection["serial"]
				self._logger.write( "{:>15} {}\n".format("name: ", str(connection["name"])) )
				self._logger.write( "{:>15} {}\n".format("type: ", str(connection["type"])) )
				self._logger.write( "{:>15} {}\n".format("com: ", str(info["comport"])) )
				self._logger.write( "{:>15} {}\n".format("baud: ", str(info["baudrate"]))	 )
			elif connection["type"] == "ethernet":
				info = connection["ethernet"]
				self._logger.write( "{:>15} {}\n".format("name: ", str(connection["name"])) )
				self._logger.write( "{:>15} {}\n".format("type: ", str(connection["type"])) )
				self._logger.write( "{:>15} {}\n".format("host ip: ", str(info["host"])) )
				self._logger.write( "{:>15} {}\n".format("port: ", str(info["port"]))	 )
				self._logger.write( "{:>15} {}\n".format("protocol: ", str(info["protocol"])) )
				self._logger.write( "{:>15} {}\n".format("transport: ", str(info["transport_layer"])) )
			elif connection["type"] == "spacewire":
				info = connection["spacewire"]
				self._logger.write( "{:>15} {}\n".format("name: ", str(connection["name"])) )
				self._logger.write( "{:>15} {}\n".format("type: ", str(connection["type"])) )
				self._logger.write( "{:>15} {}\n".format("identifier: ", str(info["identifier"])) )
				self._logger.write( "{:>15} {}\n".format("mode: ", str(info["mode"]))	 )
			self._logger.write( "\n" )
			i += 1

	def packets_received(self, connection_name=None, connection_num = None):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description:
		Parameters:
		Return:
		"""
		# Update packet list to include any new packets
		self._update_packet_list(connection_name, connection_num)
		connection = self._find_connection(connection_name, connection_num)

		# return updated packet number
		return len(connection["packet_list"])

	def print_registered_cmds(self):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description:
		Parameters:
		Return:
		"""
		self._command_table.print_command_table()

	def print_packet_list(self, connection_name = None, connection_num = None, data_type = "raw"):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description:
		Parameters:
		Return:
		"""
		packet_ctr = 0  		# packet counter

		# make sure connection's packet list is updated with newest received packets
		self._update_packet_list(connection_name, connection_num)

		# retrieve radio's connection from registered connection list
		connection = self._find_connection(connection_name, connection_num)

		# iterate through packet list, print contents of each packet
		for packet in connection["packet_list"]:
			self._logger.write( "== PACKET {} ==\n".format(packet_ctr+1) )
			packet.print_contents(data_type)
			self._logger.write( "--\n" )
			packet_ctr += 1

	def remove_connection(self, name = None):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description:
		Parameters:
		Return:
		"""
		delete_index = 0
		connection_found = False

		# find connection in connection list by name
		if (name != None):

			# iterate through list and check for matching name
			for i in range(len(self._connection_list)):
				if name == str(self._connection_list[i]["name"]):
					delete_index = i
					connection_found = True

			# if connection with given name was not found, report error to caller
			if connection_found != True:
				return False

		# use first connection in list if connection name not specified
		else:
			delete_index = 0

		# remove connection:

		# if this connect is open, close it first
		if self._connection_list[delete_index]["isopen"]:
			self.disconnect(self._connection_list[delete_index]["name"])

		# remove reference to thread (python garbage collecting thing, ensures the __del__
		# method of the swiftrxthread instance will be called)
		self._connection_list[delete_index]["thread"] = None
		self._trace_output("connection '{}' was removed. ".format(self._connection_list[delete_index]["name"]), msg_tracelevel=2)

		# delete connection item in list
		del self._connection_list[delete_index]

		# return true
		return True

	def set_command_table(self, table):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description:
		Parameters:
		Return:
		"""
		correct_table_type = "SwiftCmdhostCommandTable"
		given_table_type = table.__class__.__name__

		# make sure this is the correct object before setting
		if given_table_type == correct_table_type:
			self._command_table = table
		else:
			raise SwiftRadioError("**cannot set object '{}' as command table! must be a '{}' object**".format(given_table_type, correct_table_type))

	def set_execute_settings(self, connection_name=None, return_error=None, auto_throttle=None, timeout=None,
							fail_exception=None, fail_retry=None, max_retries=None, transid=None, cmdline_syntax=None):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description:
		Parameters:
		Return:
		"""
		done = 0

		# get the specified connection's execute settings to configure
		connection = self._find_connection(connection_name)
		execute_settings = connection["execute_settings"]

		if connection != -1:
			# identify which settings caller changed, then save settings
			if return_error != None:
				execute_settings.return_error 	= return_error
			if auto_throttle != None:
				execute_settings.auto_throttle 	= auto_throttle
			if timeout != None:
				execute_settings.timeout 		= timeout
			if fail_exception != None:
				execute_settings.fail_exception	= fail_exception
			if fail_retry != None:
				execute_settings.fail_retry		= fail_retry
			if max_retries != None:
				execute_settings.max_retries	= max_retries
			if transid != None:
				execute_settings.transid		= transid
			if cmdline_syntax != None:
				execute_settings.cmdline_syntax	= cmdline_syntax

			connection["execute_settings"] = execute_settings

			done = 1

		return done

	def set_connection_name(self, newname, oldname=None):
		"""
		change the name of a connection in the connection list
		"""
		# get connection from list
		connection = self._find_connection(oldname)
		oldname = connection["name"]

		for i in range(len(self._connection_list)):
			if oldname == self._connection_list[i]["name"]:
				# set name of this connection
				if type(newname) is str:
					self._connection_list[i]["name"] = newname
					self._trace_output("connection name is now {}, was {}".format(self._connection_list[i]["name"], oldname), msg_tracelevel=2)
				else:
					raise SwiftRadioError("could not set connection name. given value '{}' is not a string.".format(oldname))


	def set_devid(self, device_identifier):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
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
								raise SwiftRadioError("could not set devid. all characters must be upper case.")

					# set device id
					self._devid = device_identifier
					self._trace_output("device id set to {}".format(self._devid), msg_tracelevel=2)
					return 1

				# raise error if not
				else:
					raise SwiftRadioError("could not set devid. one or more characters in given string is non-alphanumeric.")

			# raise error if not
			else:
				raise SwiftRadioError("could not set devid. string must be at least 16 characters in length.")

		# raise error if not
		else:
			raise SwiftRadioError("could not set devid. given value is not a string.")

		# if here, return an error code
		return -1

	def set_name(self, name):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description: defines the radio name
		Parameters: name - name of the virtual SwiftRadioInterface
		Return: 1 - name successfully set
				0 - could not define name. possibly due to invalid name (i.e. not a string)
		"""

		# make sure the name is a valid string value
		if type(name) is str:
			self._radio_name = name
			return 1
		else:
			return 0

	def set_tracelevel(self, input_tracelevel):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description: set the traceoutput level
		Parameters: trace level integer. valid integer values are (1 through 4)
		Return: None
		"""
		if stringconversions.strval_numtype(input_tracelevel) == 'int':
			old_trace = self._tracelevel
			self._tracelevel = input_tracelevel
			self._trace_output("trace level is now {}, was {}".format(self._tracelevel, old_trace), msg_tracelevel=2)

	def set_loglevel(self, level):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description: set the log level
		Parameters: level - log level
		Return: None
		"""
		log_levels = [ 	"off",
						"critical",
						"error",
						"warning",
						"info",
						"debug"
		]

		# if given a valid log level, set new log level
		if level in log_levels:

			self._trace_output("log level:", msg_tracelevel=1)
			for i in range( len(log_levels) ):
				if log_levels[i] == level:
					self._trace_output(" -> {}".format(level), msg_tracelevel=2, radioname=False)
					self._tracelevel = i
				else:
					self._trace_output("    {}".format(log_levels[i]), msg_tracelevel=2, radioname=False)

		# if not raise error
		else:
			raise SwiftRadioError("cannot set log level. {} invalid value".format(level))

	def get_loglevel(self):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description: set the log level
		Parameters: level - log level
		Return: None
		"""
		log_levels = { 	0:"off",
						1:"critical",
						2:"error",
						3:"warning",
						4:"info",
						5:"debug"
		}

		if self._tracelevel not in log_levels:
			return None
		else:
			return log_levels[self._tracelevel]

	# ===========================================================================================================================
	# 	Private Methods
	# ===========================================================================================================================

	def _command_throttle(self, timeout=None, transid=0x0000, connection_name = None):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description:
		Parameters:
		Return:
		"""
		connection = self._find_connection(connection_name)
		packets_received = len(connection["packet_list"])
		return_pkts = Packet_Classes.SwiftPacketList()
		error_code = 0
		error_type = 0
		cmd_complete = False
		cmd_nack = False

		# get current time in seconds
		current_time = time.time()

		# get end time if timeout is specified
		if timeout != None:
			end_time = current_time + int(timeout)
		else:
			end_time = None

		# poll packet list for a confirmation desync value
		while (cmd_complete == False) and (current_time <= end_time):

			# extract packet from packet list
			packet = self.get_packet(packets_received, connection_name=connection_name)

			# a None value is returned if there are no packets to extract
			if packet != None:

				# place this packet into a packet list that will later be returned to caller
				return_pkts.append(packet)
				packets_received += 1

				# verify control code of this packet, exit poll state if desync is received
				if (packet.get_frame_control_code("str") == "DESYNC"):

					# verify transid of packet
					# if int(transid) == int(packet.transid):

					# desync received! exit loop
					cmd_complete = True

				# check if an error control code was received
				errors = packet.get_error_info()
				if ( len(errors) > 0 ):
					error_type = errors[0][0]
					error_code = errors[0][1]

			# update time
			current_time =  time.time()

		# if a command failed to complete and no desync or error codes received, treat as a timeout
		if (cmd_complete == False) and (error_code == 0):
			error_code = -999

			# determine error code
			if len(return_pkts) > 0:

				# packets received from radio but no DESYNC detected
				error_type = -2
			else:

				# no packets received from radio
				error_type = -1

		# return packets and error codes
		return return_pkts, error_code, error_type

	def _get_execute_settings(self, connection_name=None, return_error=None, auto_throttle=None, timeout=None,
								fail_exception=None, fail_retry=None, max_retries=None, transid=None, cmdline_syntax=None):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description:
		Parameters:
		Return:
		"""
		settings = executecmd.ExecuteSettings()

		# get the specified connection's execute settings to configure
		connection = self._find_connection(connection_name)

		# check if connect was found
		if connection != -1:

			default_settings = connection["execute_settings"]

			# for every setting caller did not change, use the default value
			if return_error == None:
				settings.return_error = default_settings.return_error
			else:
				settings.return_error = return_error

			if auto_throttle == None:
				settings.auto_throttle = default_settings.auto_throttle
			else:
				settings.auto_throttle = auto_throttle

			if timeout == None:
				settings.timeout = default_settings.timeout
			else:
				settings.timeout = timeout

			if fail_exception == None:
				settings.fail_exception = default_settings.fail_exception
			else:
				settings.fail_exception = fail_exception

			if fail_retry == None:
				settings.fail_retry = default_settings.fail_retry
			else:
				settings.fail_retry = fail_retry

			if max_retries == None:
				settings.max_retries = default_settings.max_retries
			else:
				settings.max_retries = max_retries

			if transid == None:
				settings.transid = default_settings.transid
			else:
				settings.transid = transid

			if cmdline_syntax == None:
				settings.cmdline_syntax = default_settings.cmdline_syntax
			else:
				settings.cmdline_syntax = cmdline_syntax

		# if no connection found, simply use default settings
		else:
			settings = -1

		return settings

	def _create_default_execute_settings(self):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description:
		Parameters:
		Return:
		"""
		exe_settings = executecmd.ExecuteSettings()

		return exe_settings

	def _set_logger(self, logger):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description:
		Parameters:
		Return:
		"""
		# # if no logger is provided, use stdout as default
		# if logger = None:
		pass

	def _find_connection(self, connection_name=None, connection_num=None, fail_exception=False):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description: locate a connection within the connection list.
		Parameters: name of connection, connection number (list index)
		Return: 'connection instance' (i.e. Serial, Socket instance)
		"""
		# Find connection by name
		if connection_name != None:

			# iterate through connection list
			for connection in self._connection_list:
				if str(connection_name).lower() == connection["name"]:
					return connection
			return -1

		# Find connection using location in connection list
		elif connection_num != None:
			if (connection_num >= 0) and (connection_num < len(self._connection_list)):
				return self._connection_list[int(connection_num)]
			else:
				raise SwiftRadioError("No existing radio connection corresponding to given connection number {}".format(connection_num))

		# If no connection information specified, return first connection in list
		else:

			# make sure there is a connection in list to return
			if len(self._connection_list) > 0:
				return self._connection_list[0]
			else:
				return -1

	def _destroy_connection_list(self):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description: this is called when a class instance is garbage collected from memory.
		Parameters: name of connection, connection number (list index)
		Return: 'connection instance' (i.e. Serial, Socket instance)
		"""
		# disconnect all connections
		self.disconnect("-a")

		# get number of connections in connection list
		num_connections = len(self._connection_list)

		# remove each connection from list
		for i in range(num_connections):
			self.remove_connection()

	def _print_error_msg(self, error_code, error_type):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description:
		Parameters:
		Return:
		Note: an error_type of -999 indicates a timeout--this is not in the official rpc protocol
		"""
		error_msg = ""
		# use error code to construct proper error message
		if error_code == -999:

			# there are two types of timeouts
			if error_type == -2:
				error_msg = "timeout. (missing desync)"
			else:
				error_msg = "timeout. (no response)"
			self._trace_output("{}".format(error_msg), msg_tracelevel=1, radioname=0)
		else:
			error_msg = "{} received.".format(error_type)
			# print error code
			self._trace_output("{} (code = {})".format(error_msg, error_code), msg_tracelevel=1, radioname=0)

	def _register_default_cmds(self, cmdtable):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description:
		Parameters:
		Return: a fully populated CommandTable object containing all cmdhost command information
		"""
		self._trace_output("registering default commands... ", newline=0, msg_tracelevel=2)
		cmdtable = register_default_commands.register_default_cmds(cmdtable)
		self._trace_output("done.", msg_tracelevel=2, radioname=0)

		# return command table
		return cmdtable

	def _register_download_file_cmds(self, cmdtable, filename = None, missing_file_warn = True):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description:
		Parameters:
		Return: a fully populated CommandTable object containing all cmdhost command information
		"""
		# format filename as necessary for locating the downloaded commands file:

		# default file name and directory location
		default_filename = "swiftradio_cmds.txt"
		default_filedir = "{}/Commands/downloads/".format(os.path.dirname(os.path.realpath(__file__)))

		# if no filename was given, use default name
		if filename == None:
			filename = default_filename

		# if no explicit file path is given in the filename, use default file location
		if ("/" not in filename) and ("\\" not in filename):
			filename_with_dir = default_filedir + filename
		else:
			filename_with_dir = filename

		# locate file:

		# if file exists at specified location, register file commands
		if os.path.isfile(filename_with_dir):

			# register to command table from file
			self._trace_output("registering {} commands... ".format(filename), newline=0, msg_tracelevel=2)
			new_cmdtable = register_file_commands.register_file_commands(cmdtable, filename_with_dir)

			# check that all commands were registered
			if new_cmdtable != -1:
				self._trace_output("done.", msg_tracelevel=2, radioname=0)
				cmdtable = new_cmdtable
			else:
				self._trace_output("fail.", msg_tracelevel=2, radioname=0)
				self._trace_output("**file commands could not be registered**", msg_tracelevel=1, radioname=0)

		# if file was not found, skip registration and output warning message if missing_file_warn is True
		else:
			self._trace_output("no command file found.", msg_tracelevel=2, radioname=0)

			if missing_file_warn is True:
				warnings.warn("radio commands file '{}' not detected, some commands may not be available for execution.".format(filename_with_dir))

		# ** SAVE FILE NAME ** this may be needed for downloading commands later?
		self._commands_filename = filename_with_dir

		# return command table
		return cmdtable

	def _trace_output(self, output, msg_tracelevel=1, newline=1, radioname=1):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description: prints a output message to console. the radio's current tracelevel must be set higher than the
					 message output tracelevel for the message to be printed
		Parameters: output message, tracelevel of output message, flag indicating if message should be terminated with a newline
					when printed (terminates with a space otherwise)
		Return: None
		"""

		if self._tracelevel >= msg_tracelevel:
			if radioname == 1:
				output = self._radio_name + "->" + output

			if newline == 0:
				# Note: stdout may not be portable across OS platforms
				sys.stdout.write(output)
			else:
				sys.stdout.write( str(output)	+ "\n" )

	def _update_packet_list(self, connection_name=None, connection_num=None):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description:
		Parameters:
		Return:
		"""
		# find connection
		if (connection_name == None) and (connection_num == None):
			connection = self._connection_list[0]
		else:
			connection = self._find_connection(connection_name, connection_num)

		# check if any new packets have been received over this connection
		new_packets = connection["thread"].packets_received()

		# add any new packets to connection's packet list
		if new_packets > 0:

			# fetch new packets from receive thread, place in packet list
			for i in range( new_packets ):

				packet = connection["thread"].get_packets(0)

				# make sure a valid packet was retrieved
				if packet != -1:
					connection["packet_list"].append(packet)

		return 1

	def __del__(self):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description: class destructor function
		Parameters:
		Return:
		"""
		# to prevent hangups from active threads, safely place all connections in neutral state and remove connections
		# from list
		self._trace_output( "destroying {} connections...".format( len(self._connection_list) ), 3 )
		self._destroy_connection_list()
		self._trace_output( "deleting radio '{}' instance.".format(self.get_name()), 3 )
		self._logger = None

class SwiftRadioInstance(SwiftRadioInterface):
	pass

class SwiftRadioClient(SwiftRadioInterface):
	"""
	Author: S. Alvarado
	Created: 8/30/14
	Description: main class used for commanding and controlling a SWIFT-SDR device over a variety
				 of physical connection types.
	"""
	_LOGLEVELS = {	"notset":logging.NOTSET, "debug":logging.DEBUG, "info":logging.INFO,
					"warning":logging.WARNING, "error":logging.ERROR, "critical":logging.CRITICAL }
	def __init__(self, name=None, trace=0, commands_file=None, logger=None, register_file_cmds = False, 
				nofile_warn = True):
		"""
		Author: S. Alvarado
		Last Updated: 6/8/15
		Description: General class constructor for instantiating a SwiftRadioInterface object.
		Parameters: name - arbitrary name of the SwiftRadioInterface object. defaults to 'SwiftRadioInterface'.
					devid - unique device identifier as a 16-character hex string (i.e.'013C4F2AC427C20B')
					trace - trace level for automatic log outputs to stdout.
					commands_file  - name of the commands .txt file to register from. By default, the SwiftRadioInterface
									 object will use the swiftradio_cmds.txt file unless otherwise specified.
					register_file_cmds - If set to True, the SwiftRadioInterface object will automatically search for a commands
										text file from which to register command information. If False, no command file is used to
										register command information.
					nofile_warn - If True, a warning will be issued if a commands .txt file has not been downloaded and saved in the default directory
								 within the swiftradio package. Setting to False will turn off warnings.
					logfile - name of file to write automatic log outputs. defaults to stdout if not provided.
		Return: SwiftRadioInterface instance
		"""
		self._radio_name = name 					# arbitrary name that can be assigned to instances
		self._devid = None 							# radio device identifier
		self._connection_list = list() 				# list of connections created
		self._tracelevel = trace 					# verbosity trace level for automatic logging
		self._commands_filename = commands_file 	# name of the commands file for registering command information
		self._logger = None 						# file object used to write log outputs
		self._command_table = None 					# command table object for storing command information
		self._swiftfirm_handler = None 				# object used to upload firmware images

		# set default radio name if none provided
		if self._radio_name == None:
			self._radio_name = self.__class__.__name__

		# create logger for message printouts
		if logger == None:
			# create default logger if not given. printouts will be to stdout
			logging.basicConfig( format="%(message)s", level=logging.INFO )
			self._logger = logging.getLogger( __name__ )
		else:
			self._logger = logger

		# create firmware handler (if swiftfirm package is available)
		try:
			from swiftfirm import SwiftfirmFTP
			self._swiftfirm_handler = SwiftfirmFTP( logger=self._logger )
		except ImportError:
			self._swiftfirm_handler = None

		# create radio commands table
		self._command_table = command_table.SwiftCmdhostCommandTable()

		# register basic radio commands that every SwiftRadioInterface has access to
		self._command_table = self._register_default_cmds(self._command_table)

		# register commands from downloaded commands file
		if register_file_cmds:
			self._command_table = self._register_download_file_cmds(self._command_table, self._commands_filename, nofile_warn)

	def set_client_loglevel(self, loglevel):
		"""
		Author: S. Alvarado
		Last Updated: 8/7/15
		Description: set the logging level for printouts used by the swift client
		Parameters: loglevel - string specifying the lowest priority log level that will be printed,
					available options (from highest to lowest priority) include:
							* critical - numerical value 50
							* error - numerical value 40
							* warning - numerical value 30
							* info - numerical value 20
							* debug - numerical value 10
		Return: None
		"""

		# make sure loglevel parameter is a string
		if type(loglevel) is not str:
			raise SwiftRadioError("cannot set log level. value must be a string.")

		# make sure loglevel parameter is a valid option
		if loglevel not in self._LOGLEVELS:
			valid_loglevels = list()
			for key, value in self._LOGLEVELS:
				valid_loglevels.append(key)
			raise SwiftRadioError("invalid log level {}. valid log levels include: {}".format(loglevel, " ,",join(valid_loglevels) ) )

		# set log level
		self._logger.setLevel( self._LOGLEVELS[loglevel] )

	def get_client_loglevel(self, numeric_format=False):
		"""
		Author: S. Alvarado
		Last Updated: 8/7/15
		Description: set the logging level used by the swift client's logging system.
		Parameters: numeric_format - returns the numerical representation of the log level.
		Return: the current loglevel of the SwiftRadioClient object's logger in the
				following format
					* the textual representation as a string (lower case)
					or
					* the numerical representation (if numeric_format is set to True)
		"""
		# get the level of the logger (this will be a numerical value)
		level = self._logger.getEffectiveLevel()

		# translate this into a string
		if numeric_format is False:
			level = self._logger.getLevelName( level )

		return level

	def software_image_upload(self, archive_dir, chunksize = 1024, default_image=False, lock=False):
		"""
		Author: S. Alvarado
		Last Updated: 8/7/15
		Description: parse the software image archive directory contents and upload the application.elf file to the radio.
		Parameters: archive_dir - directory containing the firmware image (.elf) and release.py files
					chunksize - size of each chunk (in bytes) of image data sent to the radio. must be between 1 and 10000
					default_image - make this image the primary boot image after checksum validation.
					lock - lock the image after checksum validation.
		Return: status integer
				1 - upload successful
				or
				0 - upload unsuccessful
		"""
		if self._swiftfirm_handler is None:
			raise SwiftRadioError("cannot upload image. swiftfirm sub-package missing.")

		return self._swiftfirm_handler.software_image_upload(archive_dir, self, chunksize, default_image, lock)

	def hardware_image_upload(self, archive_dir, chunksize = 1024, default_image=False, lock=False):
		"""
		Author: S. Alvarado
		Last Updated: 8/7/15
		Description: parse the hardware image archive directory contents and upload the boatload.bin file to the radio.
		Parameters: archive_dir - directory containing the firmware image (.bin) and release.py files.
					chunksize - size of each chunk (in bytes) of image data sent to the radio. must be between 1 and 10000
					default_image - make this image the primary boot image after checksum validation.
					lock - lock the image after checksum validation.
		Return: status integer
				1 - upload successful
				or
				0 - upload unsuccessful
		"""
		if self._swiftfirm_handler is None:
			raise SwiftRadioError("cannot upload image. swiftfirm sub-package missing.")

		return self._swiftfirm_handler.hardware_image_upload(archive_dir, self, chunksize, default_image, lock)
