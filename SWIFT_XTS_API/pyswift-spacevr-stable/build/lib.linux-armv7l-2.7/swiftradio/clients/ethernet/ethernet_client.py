import os
import sys
from ..swiftradiointerface  import SwiftRadioInterfaceV2

# import i/o client
import swiftudp

# import rx thread client
import ethernet_threads

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__company__ = "Tethers Unlimited Inc."
__status__ = "Development"
__date__ = "Created: 5/6/16"

class SwiftRadioEthernet(SwiftRadioInterfaceV2):
	"""
	Main class used for commanding and controlling a SWIFT-SDR device over an Ethernet connection
	using UDP/IP protocol.

	.. note::

		IPv6 addressing is currently not supported by the Ethernet client.

	"""
	def __init__(self, host, bind_port = None, timeout=0, name=None, trace=0):
		"""
		SwiftRadioEthernet class constructor.

		:param str host: IPv4 address assigned to SWIFT-SDR radio. Note that IPv6 is currently \
		not supported.
		:param int bind_port: bind port for incoming UDP packets. If not specified, the first available \
		bind port from 40000 to 40999 will automatically be assigned.
		:param int timeout: Data transmit timeout, in seconds.
		:param str name: Optional arbitrary name of the SwiftRadioInterface object. Can be useful for \
		differentiating multiple SwiftRadioEthernet instances.
		:param int trace: Trace level for automatic log outputs to stdout. Trace level range is 0 to 4.

		**Example**:

		To setup a connection to an Ethernet SWIFT-SDR, simply provide the host IP address along \
		with any additional optional parameters if desired.

		.. code-block:: python
			:linenos:

			from swiftradio.clients import SwiftRadioEthernet

			radio_interface = SwiftRadioEthernet("123.45.67.89", bind_port = 40025)

		Last Updated: 05/09/16
		"""
		# :param obj stdout: Object for streaming trace output. Object must have a write() method for \
		# trace infomation to be correctly piped. Defaults to sys.stdout (console printouts).
		# Unused parameter
		stdout = None #stdout or sys.stdout

		# initialize parent class
		SwiftRadioInterfaceV2.__init__(self, name, trace, stdout)

		# add connection (must do this before calling parent class __init__ )
		if self._add_connection(host, bind_port, timeout, "little") == -1:
			raise SwiftEthernetError("Could not create ethernet connection.")

	# ===========================================================================================================================
	# 	Public Methods
	# ===========================================================================================================================
	def _add_connection(self, host, bind_port = None, timeout=0, data_endianess="little"):
		"""
		Author: S. Alvarado
		Last Updated: 5/5/16
		Description: adds a "ethernet" connection to instance connection list. Supports UDP and TCP protocols
		Parameters: host - a string representing the ip address of the radio to connect (i.e. '198.22.43.8'). format depends on 'protocol' parameter
					port - radio service port number. defaults to 12345--which is the packet interface port.
		Return: status integer value.
				 1 - successful connection established
				-1 - unsuccessful connect attempt
		"""
		port=12345
		transport_layer="UDP"
		protocol = "IPv4"
		discovery_port=802
		name = None

		connection_type = "ethernet"
		info_dict = dict()
		self._trace_output("adding {} connection... ".format(connection_type), newline=0, msg_tracelevel=2)

		# define object that represents physical interface (ethernet socket).
		connection_instance = swiftudp.SwiftUDPClient(host=host, port=port, bind_port=bind_port, timeout=timeout)

		# assign a receive thread to this connection.
		connection_thread = ethernet_threads.UdpSwiftPacketRxThread(DataInterface=connection_instance, endianess=data_endianess)

		# assign a default connection name if not given
		if name == None:
			name = connection_type

		# create an information dictionary describing this connection protocol attributes
		info_dict = {"host":host, "port":port, "bind_port":bind_port,"discovery_port":discovery_port, "protocol":protocol, "transport_layer":transport_layer,"timeout":timeout}

		# create default execute command settings dict
		command_settings = self._create_default_execute_settings()

		# create an information dictionary describing the connection and store in this instances connection list
		self._rpc_interface = {"name":name, "instance":connection_instance, "type":connection_type, "packet_list":list(), "isopen":False,
								"thread":connection_thread, "translator":"on", "endianess":data_endianess,
								"execute_settings":command_settings,
								"spacewire": None, "ethernet":info_dict, "uart": None}

		self._trace_output("done.", msg_tracelevel=2, radioname=0)

		return 1


class SwiftEthernetError(RuntimeError):
	pass
