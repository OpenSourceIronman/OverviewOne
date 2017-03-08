import os
import sys
import time
import warnings
import logging
import traceback
from libs.commands import command_table
from libs.commands.registration import register_default_commands, command_download
from libs.packet import packets
from libs.packet import parsing
from libs.settings import executecmd

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__company__ = "Tethers Unlimited Inc."
__status__ = "Development"
__date__ = "Created: 4/29/16"

class SwiftRadioInterfaceV2(object):
	"""
	Base class for commanding and controlling a SWIFT-SDR device over a variety of physical
	connection types.

	Created: 4/29/16

	Author: S. Alvarado
	"""
	def __init__(self, name=None, trace=0, stdout=sys.stdout):
		"""
		Class constructor.

		Last Updated: 5/2/16

		:param str name: Arbitrary name of the SwiftRadioInterface object. defaults to 'SwiftRadioInterface'.
		:param int trace: Trace level for automatic log outputs to stdout.
		:param obj stdout: Object for streaming trace output. Object must have a write() method for \
		trace infomation to be correctly piped. Defaults to sys.stdout (console printouts).

		.. todo:: Get rid of command table stuff. Let RPC Client handle it.

		.. todo:: need better error handling. need to figure out returning error messages and handling multiple\
		error packets from same transaction.

		.. todo:: update the set_execute_settings()

		.. todo:: Get rid of connections_list
		"""
		self._radio_name = name 					# arbitrary name that can be assigned to instances
		self._rpc_interface = None 					# client for sending raw data to radio
		self._tracelevel = None 					# verbosity trace level for automatic logging
		self._logger = None 						# file object used to write log outputs
		self._command_table = None 					# command table object for storing command information
		self._command_interface_names = list()		# list of command interface attribute names

		# set default radio name if none provided
		if self._radio_name == None:
			self._radio_name = self.__class__.__name__

		# get tracelevel
		self.set_tracelevel(trace)

		# define RPC Command Client
		# self._command_client = SwiftCommandClient()

		# create radio commands table
		self._command_table = command_table.SwiftCmdhostCommandTable()

		# register basic radio commands that every SwiftRadioInterface has access to
		self._command_table = self._register_default_cmds(self._command_table)

	# ===========================================================================================================================
	# 	Public Methods
	# ===========================================================================================================================

	def attach_command_interface( self, name, interface_class ):
		"""
		Assign a Command Interface object as an attribute of this client instance. Note that \
		interface_class must be some class that inherits from the SwiftCommandInterface base \
		class.

		:param str name: The name of the attribute that will be assigned to radio client. Note \
		that an exception will be raised if a client already has an attribute with the same name.
		:param class interface_class: A class derived from SwiftCommandInterface.

		**Example**:

		.. code-block:: python
			:linenos:

			from swiftradio.command_interfaces import swiftfirm_cmds
			from swiftradio.clients import SwiftRadioEthernet

			radio = SwiftRadioEthernet("123.45.67.89")
			radio.attach_command_interface("swiftfirm", swiftfirm_cmds)

		.. note:: command interface mechanism is still in beta testing as of 05/11/16 (SRA)

		Last Updated: 05/11/16 (SRA)
		"""
		# check that object is derived from SwiftCommandInterface.
		class_bases = [base.__name__ for base in interface_class.__bases__ ]
		if "SwiftCommandInterface" not in class_bases:
			raise SwiftRadioError( "A command interface class must inherit from "
				"SwiftCommandInterface. Detected base classes {} ".format(", ".join(class_bases)) )

		# error check name is a string and command interface of the same name does not already exist
		if name in self._command_interface_names:
			raise SwiftRadioError( "a command interface with name '{}' already exists.".format(name) )

		# make sure this attribute does not already exist
		try:
			getattr( self, name )
			raise SwiftRadioError( "Client already has attribute with name '{}'".format(name) )
		except AttributeError:
			pass

		# initialize object
		temp_obj = None
		temp_obj = interface_class( self )

		# set this object as an attribute
		setattr( self, name, temp_obj )

		# add object name
		self._command_interface_names.append( name )

	def connect(self, fail_exception = False):
		"""
		Connect to a SWIFT-SDR device.

		:param bool fail_exception: If True, a SwiftRadioError exception is thrown if any error \
		occurs while attempting to connect to a radio.
		:returns: True if connect attempt was successful, or False if unsuccessful. Note that if \
		the radio is already connected, True will be returned.
		:raises: SwiftRadioError if fail_exception is set to True and a connection failure occurred.

		**Example**:

		.. code-block:: python
			:linenos:

			from swiftradio.clients import SwiftRadioEthernet
			radio = SwiftRadioEthernet("123.45.67.89")

			# connect to radio, exit program on connection failure
			if radio.connect():
				# continue program
				pass

			else:
				print "failed to connect to radio!"
				sys.exit(1)

			# always disconnect from radio before program exit
			if radio.connection_isopen():
				radio.disconnect()

		.. warning::

			Always close a opened connection using the disconnect() method before exiting program. \
			Failure to close an open connection may result in unclosed Python processes (commonly \
			manifested by program "hanging") or improper memory deallocation upon program exit.

		Last Updated: 5/6/16 (SRA)
		"""
		name=None
		connect_complete = False
		radio_connection = None

		# locate specific connection in connection list
		radio_connection = self._rpc_interface

		# continue if connection was found.
		if radio_connection is not None:

			# check if connection has been created and is not already open
			if (radio_connection["instance"] != None) and (radio_connection["isopen"] != True):

				# connect to specified "connection object"
				self._trace_output("{}: connecting... ".format(radio_connection["name"]), newline=0, msg_tracelevel=1)
				try:
					instance_connected = radio_connection["instance"].connect()
				except:
					# traceback.print_exc()
					instance_connected = 0

				# check if connect attempt was successful
				if instance_connected == 0:
					connect_complete = False
					radio_connection["isopen"] = False
					self._trace_output("fail.", msg_tracelevel=1, radioname=0)
				else:
					# start the receive thread
					if (radio_connection["thread"] is not None):
						radio_connection["thread"].start()

						# send ping to radio so we know radio is active
						radio_connection["isopen"] = True
						if self._ping_radio():
							connect_complete = True
							self._trace_output("done.", msg_tracelevel=1, radioname=0)
						else:
							self._trace_output("fail. (no ping response from radio)", msg_tracelevel=1, radioname=0)
							oldtrace = self.get_tracelevel()
							self.set_tracelevel(oldtrace)
							self.set_tracelevel(0)
							self.disconnect()
							self.set_tracelevel(oldtrace)
							connect_complete = False
					else:
						raise SwiftRadioError("connection thread has not been created!")

			else:
				connect_complete = True

		else:
			raise SwiftRadioError("cannot connect to radio. no connection defined.")

		# throw an exception if a connection error occurred and fail exceptions option is on
		if (connect_complete is False) and (fail_exception is True):
			raise SwiftRadioError("radio connect attempt failed.")

		return connect_complete

	def connection_isopen(self):
		"""
		Check if connection to radio is currently open.

		:returns: True if the connection is currently open, or False if the connection is closed.

		Last Updated: 5/6/16
		"""

		if self._rpc_interface is not None:

			if self._rpc_interface["isopen"] == True:
				return True
			else:
				return False

		else:
			raise SwiftRadioError("cannot check status, specified connection does not exist.")

	def default_execmd_settings(self, timeout=4, fail_retries=2, fail_exception=False,
								fail_rpc_error=True, return_rpc_error=False):
		"""
		Set default parameters for the execute_command() method. All subsequent calls to \
		execute_command() will have these parameter settings by default. The default settings can \
		be overridden by setting the execute_command() parameters directly.

		:param int timeout: The timeout period, in seconds, for a radio command to finish executing.
		:param int fail_retries: If a command error condition occurs, client will resend the command\
		 up to fail_retries.
		:param bool fail_exception: Raises a SwiftRadioError exception if the command failed to execute\
		 due to an error condition.
		:param bool fail_rpc_error: non-zero RPC CMDERR codes will be treated as a error condition.
		:param bool return_rpc_error: if True, execute_command() returns the rpc error code.

		**Example**:

		.. code-block:: python
			:linenos:

			# raise an exception on command failure by default. set nominal timeout to 1 second.
			radio_interface.default_execmd_settings(timeout=1, fail_exception=True)

			try:
				time = radio_interface.execute_command("systime")
			except:
				print "**systime command failed to execute**"
				sys.exit(1)

		Last Updated: 5/27/16 (TDN)
		"""
		done = 0

		# get the specified connection's execute settings to configure
		connection = self._rpc_interface
		execute_settings = connection["execute_settings"]

		if connection is not None:
			# identify which settings caller changed, then save settings
			if return_rpc_error != None:
				execute_settings.return_rpc_error 	= return_rpc_error
			if timeout != None:
				execute_settings.timeout 			= timeout
			if fail_exception != None:
				execute_settings.fail_exception		= fail_exception
			if fail_retries != None:
				execute_settings.fail_retries		= fail_retries
			if fail_rpc_error != None:
				execute_settings.fail_rpc_error		= fail_rpc_error

			connection["execute_settings"] = execute_settings

			done = 1

		return done

	def destroy_command_interfaces( self ):
		"""
		Deleted all created class interface objects.

		.. note:: command interface mechanism is still in beta testing as of 05/11/16 (SRA)

		Last Updated: 05/10/16 (SRA)
		"""
		delete_indices = list()

		for i, interface in enumerate(self._command_interface_names):

			try:
				# call clean up method
				self.__dict__[interface]._cleanup_interface()

				# delete object attribute from client.
				delattr(self, interface)

				delete_indices.append(i)

			except KeyError:
				pass

		# delete names from command interface list
		for index in delete_indices:
			del self._command_interface_names[index]

	def disconnect(self):
		"""
		Disconnect from SWIFT-SDR Device.

		:returns: True if disconnect attempt was successful, or False if unsuccessful. Note that if \
		the radio is already closed, True will be returned.

		Last Updated: 6/8/15
		"""
		disconnect_complete = False
		name = None
		radio_connection = None

		# locate specific connection in connection list
		radio_connection = self._rpc_interface

		if (radio_connection is not None):

			# verify if this connection is open
			if radio_connection["isopen"] is True:

				# close the receive thread (this must be done before closing the connection
				# to avoid crashing and "hanging" on program exit)
				if radio_connection["thread"] != None:
					radio_connection["thread"].close()

				# close connection
				if radio_connection["instance"] != None:

					self._trace_output("{}: disconnecting... ".format(radio_connection["name"]), newline=0, msg_tracelevel=1)
					radio_connection["instance"].disconnect()
					self._trace_output("done.", msg_tracelevel=1, radioname=0)
					radio_connection["isopen"] = False
					disconnect_complete = True

			else:
				disconnect_complete = True

		return disconnect_complete

	def execute_command(self, command, timeout = None, fail_retries=None, fail_exception=None, fail_rpc_error=None,
			return_rpc_error=None,	return_swiftlist=False):
		"""
		Send a command to radio and return any command response data.

		:param str command: Radio command, in POSIX syntax, to execute. (i.e. "rxdis -a", "systime", \
		"linkfreq -f 2.4e9")
		:param int timeout: The timeout period, in seconds, for a radio command to finish executing. \
		Defaults to 2 seconds.
		:param int fail_retries: If a command error condition occurs, client will resend the command\
		 up to fail_retries.
		:param bool fail_exception: Raises a SwiftRadioError exception if the command failed to execute\
		 due to an error condition.
		:param bool fail_rpc_error: non-zero RPC CMDERR codes will be treated as a error condition.
		:param bool return_rpc_error: if True, execute_command() returns the rpc error code.

		:raises: SwiftRadioError if connection to the radio has not been opened using connect().
		:raises: SwiftRadioError if fail_exception is True and the command failed to execute.

		:returns: A dictionary containing the command response data (if any) as well as any command \
		error information. The returned dictionary is formatted so that each entry contains the \
		name of the command response as the key, and the response data (formatted as the appropriate \
		:ref:`data type <api_datatypes>`) as the entry value. In addition to command response data, \
		the dictionary will also include error information which you can access with the key \
		"_error". If no errors occurred during execution, this entry will be a NoneType object, \
		otherwise the entry value will be a dictionary containing the error information.

			Return Data Format:

			.. code-block:: python

				return_data = {
					"response_name1": response_data1,
					"response_name2": response_data2,
					...
					"response_nameN": response_dataN,
					"_error": error_info
				}

			Error Info Formats:

			.. code-block:: python

				# if an error occurred during command execution
				error_info = {
					"code": error_code_int, 	# RPC return error code, see RPC documentation
					"type": response_data2, 	# "INVCMD", "INVPARAM"
					"msg": "error description" 	# Error description
				}

			.. code-block:: python

				# if no error occurred
				error_info = None

		**Example**:

		.. code-block:: python
			:linenos:

			from swiftradio.clients import SwiftRadioEthernet

			radio = SwiftRadioEthernet("123.45.67.89")

			radio.connect()

			cmd_data = radio.execute_command("systime")

			print cmd_data

			if cmd_data["_error"] is None:
				radio_time = cmd_data["seconds"] + cmd_data["sub_seconds"]
				print "\\nRadio Internal Time: {:.2f} secs".format( radio_time )

			radio.disconnect()

		Console Output:

		.. code-block:: console

			{'sync_state': 'holdover', 'sync_bias': 0.0, 'sync_error': 0.0, '_error': None, 'seconds': 955, 'sub_seconds': 0.40963064}

			Radio Internal Time: 955.41 secs

		.. note:: This is an updated version of the now deprecated *execute()* method.

		Last Updated: 05/19/16 (SRA)
		"""
		return_val = 0
		cmd_info = dict()

		# [1] get connection to send command. defaults to 1st connection in list if not specified
		radio_connection = self._rpc_interface

		# if the connection was not found, exit
		if radio_connection is None:
			raise SwiftRadioError( "**execute fail: connection '{}' does not exist**".format(radio_connection["name"] ) )

		# verify connection status is good before sending (i.e. connection has been opened)
		# self.connection_isopen returns True if the connection is open
		if self.connection_isopen() is False:
			raise SwiftRadioError( "{}(closed): **please open connection using connect() method**".format( radio_connection["name"] ) )

		# [2] settings for executing this command
		settings = self._get_execute_settings( timeout=timeout, fail_retries=fail_retries, fail_exception=fail_exception,
												return_rpc_error=return_rpc_error, fail_rpc_error=fail_rpc_error)
		# [3] error check command string
		if type(command) is not str:
			raise SwiftRadioError("cannot execute command '{}'. Must be a str data type, not {} ".format( command, type(command).__name__ ) )

		# [4] Cache Command
		if " " in command:
			command_name = command.split(" ")[0]
		else:
			command_name = command
		# if this radio command is not in cache table, attempt cache.
		cmd_registered = self._command_table.verify_command_registered(command_name)
		if cmd_registered == 0:

			# cache command
			hide_trace = False
			if self.get_tracelevel() < 4:
				hide_trace = True

			cmd_registered, code, etype = self._cache_command( command_name, suppress_trace=hide_trace )

		# [5] Execute command
		if cmd_registered == 1:
			cmd_info = self._send_radio_command(command, radio_connection, settings, return_swiftlist=return_swiftlist )

		else:
			if code == -1:
				self._trace_output("{}: cache failure: {}".format(radio_connection["name"], command_name), msg_tracelevel=1)
				if settings.fail_exception is True:
					raise SwiftRadioError("**cache failure** could not cache '{}' command.".format(command_name))


			else:
				self._trace_output("{}: **'{}' command failed** ".format(radio_connection["name"], command_name), msg_tracelevel=1, newline=0)
				self._print_error_msg(code, etype, tracelevel=1)

			if settings.return_rpc_error:
				cmd_info = (
					{
						"_error": {
							"code": code,
							"type": etype,
							"msg": ""
						}
					},
					None
				)
			else:
				cmd_info["_error"] = {
					"code": code,
					"type": etype,
					"msg": ""
				}


		return cmd_info

	def get_name(self):
		"""
		Gets name defined for a SwiftRadioInterface object.

		:returns: Name, as a string.
		"""
		return self._radio_name

	def get_tracelevel(self):
		"""
		Gets current trace level.

		:returns: The trace level, as an integer.

		Last Updated: 6/8/15
		"""
		return self._tracelevel

	def set_name(self, name):
		"""
		Define (or change) the object name.

		:param str name: New name of object.
		:returns: 1 if the name was successfully set, or 0 if the new name could not be assigned. \
		Possibly due to invalid name format such as a non-string value.

		Last Updated: 6/8/15
		"""

		# make sure the name is a valid string value
		if type(name) is str:
			self._radio_name = name
			return 1
		else:
			return 0

	def set_tracelevel(self, input_tracelevel):
		"""
		Set the trace output level. Returns the previous trace output level so that it can be restored.

		:param int input_tracelevel: trace level as an int. Valid integer values are 0 through 4.
		:returns: previous trace output level
		:raises SwiftRadioError: If tracelevel is not an integer.
		:raises SwiftRadioError: If tracelevel is not within the specified range.

		Last Updated: 05/27/16 (SRA)
		"""
		if type(input_tracelevel) is not int:
			raise SwiftRadioError( "input_tracelevel must be int type, not {}.".format(
				type(input_tracelevel).__name__))

		old_trace = self._tracelevel
		if (input_tracelevel >= 0) and (input_tracelevel <= 4):
			self._tracelevel = input_tracelevel
			self._trace_output("trace level is now {}, was {}".format(self._tracelevel, old_trace), msg_tracelevel=3)
		else:
			raise SwiftRadioError( "input_tracelevel is out of range (0-4).")

		return old_trace

	# ===========================================================================================================================
	# 	Private Methods
	# ===========================================================================================================================

	def _add_connection( self ):
		"""
		Define RPC command connection to radio.

		.. warning:: This needs to be overwritten by subclass.

		Last Updated: 6/8/15 (SRA)
		"""
		raise SwiftRadioError("_add_connection() method needs to be overwritten by subclass.")

	def _cache_command(self, command, suppress_trace=False):
		"""
		Cache a radio command for future execution. This function is called internally and should \
		only be used by the application if pre-caching commands is required.

		:param str command: Name of the command whose info you wish to cache ('rxen', 'devid' ect.).
		:param bool suppress_trace: Set trace level to 0 during caching process.

		:returns: a 3-element tuple containing 1) a status integer indicating if the cache attempt \
		was successful (1 for success, 0 for failure), 2) an error code and 3) an error type value \
		for additional information if the cache failed.

		.. note:: This method is still in beta testing and is not guaranteed to work in all situations.

		Last Updated: 05/27/16 (SRA)
		"""
		cache_status = 0 				# flag indicating if help command executed to completion
		cache_trace_suppressed = False
		ecode = 0
		etype = 0

		# make sure a connection is open
		if self.connection_isopen():

			self._trace_output( "caching '{}' command... ".format(command), msg_tracelevel=2, newline=0 )

			# do not show the help command trace output except if tracelevel is > 3 or explicitly commanded to
			if suppress_trace or (self.get_tracelevel() < 3):
				old_trace = self.get_tracelevel()
				self.set_tracelevel(0)
				cache_trace_suppressed = True

			# cache command
			help_info = self._help( command, timeout=5 )
			if help_info["_error"] is None:
				cache_status = 1
				ecode = 0
				etype = 0
			else:
				cache_status = 0
				ecode = help_info["_error"]["code"]
				etype = help_info["_error"]["type"]

			# restore tracelevel
			if cache_trace_suppressed:
				self.set_tracelevel(old_trace)

			# report if cache was successful.
			if cache_status == 1:
				self._trace_output("done.", msg_tracelevel=2, radioname=0 )
			else:
				self._trace_output("**fail**", msg_tracelevel=2, radioname=0, newline=0)
				self._print_error_msg(ecode, etype, tracelevel=2)
		else:
			raise SwiftRadioError( "**please open connection using connect() method**")

		return cache_status, ecode, etype

	def _command_throttle(self, timeout=None, connection_name = None):
		"""
		Collect all response packet(s) from radio until a DESYNC is received or timeout condition \
		has occurred.

		:param int timeout: timeout period in seconds.
		:returns: a SwiftPacketList containing returned packets wrapped in SwiftPacket objects.

		Last Updated: 05/31/16 (SRA)
		"""
		connection = self._rpc_interface
		packets_received = len(connection["packet_list"])
		return_pkts = packets.SwiftPacketList()
		error_code = 0
		error_type = 0
		rpc_code = None
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
			packet = self._get_packet(packets_received, connection_name=connection_name)

			# a None value is returned if there are no packets to extract
			if packet != None:

				# place this packet into a packet list that will later be returned to caller
				return_pkts.append(packet)
				packets_received += 1
				for e in packet.frame_element_list:
					element = e[0]
					if element.__class__.__name__ != "RPCParameterAndResponse":
						code = element.get_control_code_str()
						if(code == "DESYNC"):
							cmd_complete = True

				# get rpc code
				if rpc_code is None:
					rpc_code = packet.get_rpc_code()

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
		return return_pkts, error_code, error_type, rpc_code

	def _create_default_execute_settings(self):
		"""
		Initialize a new execute settings object for a command connection.

		:returns: ExecuteSettings object.

		Last Updated: 05/31/16 (SRA)
		"""
		exe_settings = executecmd.ExecuteSettings()

		return exe_settings

	def _help(self, command, timeout=5, fail_retries=5):
		"""
		Get information about a specified command using the 'help' command, then parse command \
		information and store in dictionary. See below for return dictionary format.

		:param str command: Name of the command whose info you wish to download ('rxen', 'devid' ect.).
		:param int timeout: timeout time in seconds.

		:returns: TBD

		Last Updated: 05/01/16
		"""
		help_info = dict()
		attempts = 0
		cache_success = False

		# execute dlcmdinfo command to get command information
		if command == "":
			raise SwiftRadioError("'help' command requires a command to be specified.")

		#
		while (cache_success is False) and (attempts < fail_retries):
			help_pkts, ecode, etype = self.execute_command("help -c {}".format(command), fail_retries=0,
																timeout=timeout, return_swiftlist=True)

			# if no errors, process downloaded command packets and register in command table
			if ecode == 0:

				# parse help packets into a more manageable dictionary.
				try:
					parsed_help_info = command_download.parse_returned_help_packets( help_pkts )
					cache_success = True

					# register info in command table
					if parsed_help_info is not None:
						self._command_table = command_download.register_help_commands(parsed_help_info, self._command_table)

					# return as dictionary
					if " " in command:
						command_name = command.split(" ")[0]
					else:
						command_name = command

					outputs = self._command_table.get_output_list(command_name)

					if outputs is None:
						self._trace_output("**help parse fail**", msg_tracelevel=4 )
						help_info["_error"] = {
							"code": -997,
							"type": "CACHE FAIL",
							"msg": "Failed to parse help packets."
						}
					else:
						help_info = self._swiftpackets_to_dict(help_pkts, ecode, etype, outputs)

				except command_download.SwiftHelpParseError, e:
					self._trace_output("**help parse fail** {}".format(traceback.format_exception_only(type(e), e)[0] ), msg_tracelevel=4 )
					help_info["_error"] = {
						"code": -997,
						"type": "CACHE FAIL",
						"msg": "Failed to parse help packets."
					}

			else:
				help_info["_error"] = {
					"code": ecode,
					"type": etype,
					"msg": ""
				}
			attempts += 1

		return help_info

	def _get_packet(self, packet_num=None, delete=False, connection_name=None, connection_num=None):
		"""
		Get packet in a connection's packet list

		:param int packet_num: packet location in a connection's SwiftPacketList.
		:param bool delete: delete packet from list. (packet is still returned to caller)
		:param str connection_name: name of the connection to retrieve packet from.

		:returns: SwiftPacket object.

		Last Updated: 6/8/15
		"""
		# make sure connection's packet list is updated with newest received packets
		self._update_packet_list(connection_name, connection_num)

		# retrieve connection instance
		connection = self._rpc_interface

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

	def _get_execute_settings(self, timeout=None, fail_retries=None, fail_exception=None,
								fail_rpc_error=None, return_rpc_error=None):
		"""
		Called by execute_command() method to retrieve "settings"for executing a command.

		:param int timeout: the time period, in seconds, the SwiftRadioInterface will wait for a\
		 DESYNC packet.
		:param int fail_retries: If a command error condition occurs, client will resend a command\
		 up to fail_retries.
		:param bool fail_exception: raises a SwiftRadioError exception if the command failed to\
		 execute due to any error condition. conditions include a received INVSYNC control sequence,\
		 a execution timeout, or a CMDERR control sequence containing an error code (negative value).
		:param bool fail_rpc_error: non-zero RPC CMDERR codes will be treated as a error condition.
		:param bool return_rpc_error: if True, execute_command() returns the rpc error code.

		:returns: ExecuteSettings object.

		Last Updated: 06/02/16 (SRA)
		"""
		settings = executecmd.ExecuteSettings()

		# get the specified connection's execute settings to configure
		connection = self._rpc_interface

		# check if connect was found
		if connection is not None:

			default_settings = connection["execute_settings"]

			# for every setting caller did not change, use the default value
			if timeout is None:
				settings.timeout = default_settings.timeout
			else:
				settings.timeout = timeout

			if fail_retries is None:
				settings.fail_retries = default_settings.fail_retries
			else:
				settings.fail_retries = fail_retries

			if fail_exception is None:
				settings.fail_exception = default_settings.fail_exception
			else:
				settings.fail_exception = fail_exception

			if fail_rpc_error is None:
				settings.fail_rpc_error = default_settings.fail_rpc_error
			else:
				settings.fail_rpc_error = fail_rpc_error

			if return_rpc_error is None:
				settings.return_rpc_error = default_settings.return_rpc_error
			else:
				settings.return_rpc_error = return_rpc_error

		# if no connection found, simply use default settings
		else:
			settings = -1

		return settings

	def _ping_radio(self, timeout = 2):
		"""
		Send command to radio to test client<->radio communications.

		:returns: True if client responded to ping, False if not

		Last Updated: 05/31/16 (SRA)
		"""
		ping_successful = False

		if self.connection_isopen():
			old_trace = self.get_tracelevel()
			self.set_tracelevel(0)
			cmddata = self.execute_command("help -c help", return_rpc_error=False, fail_rpc_error=True,
											fail_exception=False, timeout=timeout, fail_retries=1)
			self.set_tracelevel(old_trace)

			if cmddata["_error"] is None:
				ping_successful = True

		return ping_successful

	def _print_error_msg(self, error_code, error_type, tracelevel=1):
		"""
		Print timeout error message using trace output.

		:param int error_code: RPC or (Python timeout) error code.
		:param int error_type: string indicating type of timeout error. -2 indicates a missing \
		DESYNC packet, -1 indicates that radio did not respond to command.

		.. note:: an error_type of -999 indicates a timeout--this is not in the official rpc protocol

		Last Updated: 05/31/16 (SRA)
		"""
		error_msg = ""
		# use error code to construct proper error message
		if error_code == -999:

			# there are two types of timeouts
			if error_type == -2:
				error_msg = "timeout. (missing desync)"
			else:
				error_msg = "timeout. (no response)"
			self._trace_output("{}".format(error_msg), msg_tracelevel=tracelevel, radioname=0)
		else:
			error_msg = "{} received.".format(error_type)
			# print error code
			self._trace_output("{} (code = {})".format(error_msg, error_code), msg_tracelevel=tracelevel, radioname=0)

	def _register_default_cmds(self, cmdtable):
		"""
		Register any default commands into the command table. This will generally include commands\
		for retrieving command information such as "help" or "bindown".

		:param SwiftCmdhostCommandTable cmdtable: command table object.
		:returns: a fully populated CommandTable object containing all cmdhost command information

		Last Updated: 05/31/16 (SRA)
		"""
		self._trace_output("registering default commands... ", newline=0, msg_tracelevel=2)
		cmdtable = register_default_commands.register_default_cmds(cmdtable)
		self._trace_output("done.", msg_tracelevel=2, radioname=0)

		# return command table
		return cmdtable

	def _send_radio_command(self, command, connection, settings, return_swiftlist=False):
		"""
		Send a command to radio and wait for response. This method is purely concerned with the \
		sending of command info and parsing the response info and returning to caller. Caching \
		considerations and settings configuration is done in the public execute_command() method.

		:param str command: Command line string in standard POSIX format (i.e. "rxdis -a").
		:param bool return_swiftlist: return a legacy SwiftPacketList object instead of dictionary \
		if True.

		Last Updated: 06/27/16 (SRA)
		"""
		command_data = dict()
		command_complete = False
		command_retries = 0
		radio_connection = connection
		pkt_list = packets.SwiftPacketList()
		error_code = 0
		error_type = 0

		# [1] execute command, can optionally repeat procedure depending on fail_retries parameter setting
		while (command_complete is False) and (command_retries <= settings.fail_retries):
			# convert text string to a message packet
			packet_buffer = parsing.text_to_swiftbytelist(command, self._command_table, packet_endianess=radio_connection["endianess"])
			if packet_buffer == -1:
				packet_buffer = []
				break

			# trace printouts
			self._trace_output("{}: sending {} bytes: '{}' ".format(radio_connection["name"], len(packet_buffer), packet_buffer), msg_tracelevel=4)
			if command_retries > 0:
				self._trace_output("{}: fail retry {}: executing '{}'... ".format(radio_connection["name"], command_retries, command), newline=0, msg_tracelevel=1)
			else:
				self._trace_output("{}: executing '{}'... ".format(radio_connection["name"], command), newline=0, msg_tracelevel=1)

			# Send packet to radio
			radio_connection["instance"].write(packet_buffer)

			# throttle until command is finished
			pkt_list, error_code, error_type, rpc_code = self._command_throttle(settings.timeout, radio_connection["name"])

			# check if command was successful
			if error_code == 0:

				# command completed successfully
				self._trace_output("done.", msg_tracelevel=1, radioname=0)

				# exit loop and return packets
				command_complete = True

			elif error_code == -999:

				# indicate that the command failed
				self._trace_output("**fail** ", msg_tracelevel=1, radioname=0, newline = 0)

				# display the error information for debugging purposes
				self._print_error_msg(error_code, error_type)

				# indicate that command needs to be reattempted if fail_retries is set to true
				command_retries += 1

			else:
				if (settings.fail_rpc_error == True):

					# indicate that the command failed
					self._trace_output("**fail** ", msg_tracelevel=1, radioname=0, newline = 0)

					# display the error information for debugging purposes
					self._print_error_msg(error_code, error_type)

					# indicate that command needs to be reattempted if fail_retries is set to true
					command_retries += 1

				else:

					# command completed successfully, but returned a non-zero error code, pass this up a level
					self._trace_output("done. (error={})".format(error_code), msg_tracelevel=1, radioname=0)

					# exit loop and return packets
					command_complete = True

		# Post-Command Execution Operations:

		# if command failed, print message and optionally raise exception
		if command_complete is False:
			self._trace_output("**could not execute '{}' command**".format(command.split(" ")[0] ), msg_tracelevel=1)
		# throw exception if command failed exception option is set to True
		if (command_complete is False) and (settings.fail_exception is True):
			raise SwiftRadioError("Command Fail: '{}' failed to execute.".format(command))

		# format returned data as a dictionary for easier handling
		if return_swiftlist is False:
			if " " in command:
				command_name = command.split(" ")[0]
			else:
				command_name = command
			outputs = self._command_table.get_output_list(command_name)
			return_val = self._swiftpackets_to_dict(pkt_list, error_code, error_type, outputs)

			if settings.return_rpc_error is True:
				return_val = return_val, rpc_code
		else:
			return_val = (pkt_list, error_code, error_type)

		return return_val

	def _swiftpackets_to_dict(self, pkts, error_code, error_type, outputs):
		"""
		Convert SwiftPacket object information (legacy Packet wrapper objects) into a single \
		dictionary.

		:param SwiftPacketList pkts: list of packet objects.
		:param int error_code: any error code resulting from command execution.
		:param int error_type: type of error.
		:param obj outputs: help command packet wrappers. info will be used to convert packet data \
		to correct data type with an associated response name.

		:returns: a dictionary containing command info

			.. code-block: python

				return_info = {
					"output_val1": VALUE,
					"output_val2": VALUE,
					"output_val3": VALUE,
					"output_val4": VALUE,
					"_error": {
						"code": CODE,
						"type": TYPE,
						"msg": MSG
					}
				}

		.. todo:: include error messages!
		"""
		returned_info = dict()

		# create outputs entries
		for swiftpkt in pkts:
			for e in swiftpkt.frame_element_list:
				if e[2] != "parameter/response":
					continue
				name_hash = swiftpkt.get_field(e[1], "name")
				tag_name = e[1]
				if name_hash is not None:
					output_def = None

					# find this return value definition
					for output in outputs:
						if output.name_hash == name_hash:
							output_def = output
							break

					# if the returned value is not recognized, use hash as key
					if output_def is None:
						if name_hash not in returned_info:
							returned_info[name_hash] = list()
						returned_info[name_hash].append( "".join(swiftpkt.get_command_data("raw",tag_name)) )

					# otherwise, use the name as the key and format data correctly
					else:
						value = None
						if (output_def.type == "str"):
							value = swiftpkt.get_command_data("str",tag_name)
						elif (output_def.type == "int") or (output_def.type == "hex") or (output_def.type == "bool"):
							value = swiftpkt.get_command_data("int",tag_name)
						elif (output_def.type == "bool"):
							value = bool(swiftpkt.get_command_data("int",tag_name))
						elif (output_def.type == "float"):
							value = swiftpkt.get_command_data("float",tag_name)
						else: # unknown, stropt, bin, ip4adx
							value = "".join(swiftpkt.get_command_data("raw",tag_name))

						if output_def.name not in returned_info:
							returned_info[output_def.name] = list()
						returned_info[output_def.name].append(value)

		temp_dict = dict()
		for key, val in returned_info.items():
			if len(val) == 1:
				temp_dict[key] = val[0]
			else:
				temp_dict[key] = val
		returned_info = temp_dict

		# create error entry
		if error_code != 0:
			returned_info["_error"] = {
				"code": error_code,
				"type": error_type,
				"msg": ""
			}
		else:
			returned_info["_error"] = None

		return returned_info

	def _trace_output(self, output, msg_tracelevel=1, newline=1, radioname=1, prepend_cr=0):
		"""
		Prints a output message to console. the radio's current tracelevel must be set higher than the
		message output tracelevel for the message to be printed.

		:param str output: trace message to output to console (stdout).
		:param int tracelevel: trace level of output message
		:param int newline: Flag indicating if message should be terminated with a newline when \
		printed (terminates with a space otherwise)
		:param int radioname: prepend output message with the name of the client object.
		:param int prepend_cr: prepend output message with a carriage return character.

		Last Updated: 5/27/16 (TDN)
		"""

		if self._tracelevel >= msg_tracelevel:
			if radioname == 1:
				output = self._radio_name + "->" + output

			if prepend_cr == 1:
				output = "\r" + output

			if newline == 0:
				# Note: stdout may not be portable across OS platforms
				sys.stdout.write(output)
			else:
				sys.stdout.write( str(output) + "\n" )

	def _update_packet_list(self, connection_name=None, connection_num=None):
		"""
		Update the returned command connection packet list.

		Last Updated: 05/31/16 (SRA)
		"""
		connection = self._rpc_interface

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
		Pseudo-class destructor function. Closes any active threads as well as any associated command \
		interfaces.

		Last Updated: 05/31/16 (SRA)
		"""
		# close threads to prevent active
		self.disconnect()

		# destroy command interfaces
		self._trace_output( "destroying command interfaces...", 4 )
		self.destroy_command_interfaces()

class SwiftRadioError(RuntimeError):
	pass
