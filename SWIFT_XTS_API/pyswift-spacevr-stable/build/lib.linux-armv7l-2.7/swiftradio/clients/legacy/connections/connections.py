"""
not quite ready for primetime
"""
__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__status__ = "Unstable"
__company__ = "Tethers Unlimited, Inc."
__date__ = "Late Updated: 3/20/15"

class UartConnection(SwiftRadioInterfaceConnection):
	"""
	Description: 
	"""	
	type = "ethernet"

class SpacewireConnection(SwiftRadioInterfaceConnection):
	"""
	Description: 
	"""	
	type = "ethernet"

class EthernetConnection(SwiftRadioInterfaceConnection):
	"""
	Description: 
	"""	
	type = "ethernet"

class SwiftRadioInterfaceConnection:
	"""
	Description: 
	"""		
	type = "undefined"			# connection type (i.e. ethernet, uart, spacewire)

	def __init__(self, name=None):
		"""
		Description: class constructor function
		Parameters: name - arbitrary name assigned to this connection instance
		"""
		if name == None:
			self._name = self.type					
		else:
			self._name = name
			
		self._packet_list = list() 					# every created connection has a packet buffer
		self._packet_type = None 					# 
		self._execute_settings = ExecuteSettings() 	# settings used when executing the execute() SwiftRadioInterface method
		self._connection_obj = None 				# socket, serial, spacewire objects used for writing/reading data to/from radio
		self._rx_thread = None 						# 
		self._open_status = 0 						# connection status "open", "closed"
		self._info = dict() 						# 

		self._setup_complete = False

	def __del__(self):
		"""
		Description: class constructor function
		"""
		self.disconnect

	# setup methods
	def setup(self):
		"""
		Description: this function needs to be overwritten by derived classes
		"""		
		# create Interface object (i.e. SwiftEthernetInterface)
		pass

		# create rx thread
		pass

		# create info dict
		pass

	# class attributes get/set functions
	def get_name(self):
		"""
		Description: 
		"""				
		return self._name

	def set_name(self, name):
		"""
		Description: 
		"""				
		# error check name
		pass

		# set name
		self._name = name		

	def get_execute_settings(self):
		"""
		Description: 
		"""				
		return self._execute_settings

	def set_execute_settings(self, exe_settings):
		"""
		Description: 
		"""				
		# error check value
		pass

		# set execute settings
		self._execute_settings = exe_settings

	def get_connection_details(self):
		"""
		Description: 
		"""				
		return self._info

	def get_packet_list(self, name=None, transid = None, dequeue = False):
		"""
		Description: returns the packet list for the specified connection
		Optional Parameters: 	
		Return: 
		"""		
		return self._packet_list

	def get_packet(self, packet_num = None, delete = False, connection_name = None, connection_num = None):
		"""
		Description: 
		Parameters: 
		Return: 
		"""				
		pass

	# connection methods
	def check_connection_status(self, name=None):	
		"""
		Description: 
		Parameters: 
		Return: 1  - connection is currently open
			   	0  - connection is closed 
		"""	
		return self._open_status

	def connect(self):
		"""
		Description: 
		"""		
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

	def disconnect(self):
		"""
		Description: 
		"""		
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

	def clear_packet_list(self, name = None):
		"""
		Description: all packets received from the radio are stored in a list object (each connection created will have
					 it's own "packet list"). this list can be cleared using this method.    
		Optional Parameters: name - specific connection whose packet list to clear
		Return: status integer. 1 indicates a successful clearing, -1 indicates a clear failure.
		"""			
		pass

	def _update_packet_list(self, connection_name=None, connection_num=None):
		"""
		Description: 
		Parameters: 
		Return: 
		"""
		# find connection
		if (connection_name == None) and (connection_num == None):
			connection = self.connection_list[0]
		else:
			connection = self._find_connection(connection_name, connection_num)

		# check if any new packets have been received over this connection	
		new_packets = connection["thread"].packets_received()

		# add any new packets to connection's packet list
		if new_packets > 0:

			# fetch new packets from receive thread, place in packet list 
			for i in range(int(new_packets)):				
				connection["packet_list"].append(connection["thread"].get_packets(0))

		return 1		

if __name__ == '__main__':
	pass