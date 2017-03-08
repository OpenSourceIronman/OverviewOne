import sys, os
import socket

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__company__ = "Tethers Unlimited Inc."
__status__ = "Development"
__date__ = "Late Updated: 5/8/15"

class UdpDgramSocket():
	"""
	Description:
	"""		
	def __init__(self, host, port, bind_port, timeout = 10, protocol = "IPv4", name = None):
		"""
		Author: S. Alvarado
		Last Updated: 4/30/15 (SRA)		
		Description:
		Parameters: 
		"""			
		self.host = str(host)
		self.port = port
		self.bind_port = bind_port
		self.timeout = timeout
		self.protocol = protocol
		self.name = name
		self.connection_status = 0
		self.ethernet_socket = None

		# use the IPv4 protocol
		if self.protocol == "IPv4":

			# create dgram socket client instance using the python socket library
			self.ethernet_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

			# specify this machine's service port
			self.ethernet_socket.bind(('', bind_port))

		# use the IPv6 protocol
		elif self.protocol == "IPv6":
			raise UdpDgramSocketError("IPv6 protocol type not yet implemented")

		# report unrecognized protocol	
		else:
			raise UdpDgramSocketError("unrecognized protocol type")

	# Swift IO Connections Public Interface (these need to be overwritten by all subclasses)
	def connect(self):
		"""
		Author: S. Alvarado 
		Updated: 4/17/15 (SRA)
		Description: open a connection to device. a connection must first be 
					 opened before commands can be sent.
		Return: 0 - connection could not be opened
				1 - connection successfully opened
		Note: UDP IP is not a connection based protocol, thus nothing needs to be done to 
			"connect" to a device but this method is included to conform with the swiftio
			public interface standard.
		"""		
		self.connection_status = 1
		return 1

	def disconnect(self):
		"""
		Author: S. Alvarado
		Updated: 4/17/15 (SRA)
		Description: close a connection to device. note that a 0 will be returned
					 if you try to close a connection that is not open.
		Return: 1  - disconnection attempt successful or connection already closed
			   	0  - disconnection attempt failed 
		Note: UDP IP is not a connection based protocol, thus nothing needs to be done to 
			"disconnect" to a device but this method is included to conform with the swiftio
			public interface standard.			   	
		"""	
		self.connection_status = 0
		return 1

	def open_status(self):
		"""
		Author: S. Alvarado
		Updated: 4/17/15 (SRA)
		Description: get the open/closed status of the connection.
		Return: 0 - connection is closed
				1 - connection is open
		"""	
		return self.connection_status

	def read(self, length = 1, timeout = 1):	
		"""
		Author: S. Alvarado
		Updated: 4/17/15 (SRA)
		Description: read data from an opened connection
		Parameters: length - number of bytes to read, defaults to 1
					timeout - length of time, in seconds to wait for read data
		Return: read data - a list of byte objects representing the data read 
							from device. will be empty if no data was read in.
		"""	
		read_buffer = list()

		# check if connection is open
		if self.open_status() == 1:

			# set socket read timeout
			self.ethernet_socket.settimeout(timeout)

			# attempt socket read, an exception will be thrown if a timeout
			# occurs before data is read in
			try:
				# read data from socket
				returned_socket_data, src_info = self.ethernet_socket.recv(length)

				# make sure the data received is from our host
				if str(src_info[0]) == self.host:

					# socket library returns a string, make sure to convert to list
					# to conform with swift IO standards
					if len(returned_socket_data) > 0:
						read_buffer = list(returned_socket_data)

			# no data received from socket, return empty string
			except socket.timeout:
				pass
		else:
			raise UdpDgramSocketError("error reading from socket. please open connection using open() before attempting read.")
		
		# return data to user			
		return read_buffer


	def write(self, write_buffer, length = None):
		"""
		Author: S. Alvarado
		Last Updated: 4/17/15 (SRA)
		Description: send data to a device via the opened connection.
		Parameters: write_buffer - a list of data to be sent over connection
					length - length of data to be written. Note that if length
							is None, all bytes in list will be written.
		Return: number of bytes written - positive non-zero integer representing number of
			   				   			  bytes sent to device
				0 - write attempt unsuccessful			   				   
			   -1 - length value invalid
		"""				
		totalsent = 0
		msg_len = 0
		sent = 0

		# [1] check if connection is open
		if self.open_status() == 1:

			# [2] make sure the write_buffer is a list, return error code -1 if not
			if (type(write_buffer) is not list) and (type(write_buffer) is not str):
				return -1

			# convert the list to a string (socket library requires string objects for read/write operations)	
			elif type(write_buffer) is list:
				write_buffer = "".join(write_buffer)

			# [3] determine size of data to send

			# use entire list size if length not specified
			if length == None:	

				# set length value
				msg_len = len(write_buffer)

			# otherwise, use length value
			else:

				# error check length value
				if ( length < 0 ) or ( length > len(write_buffer) ):
					return -1

				# set length value 
				msg_len = length

			# [4] send data to socket device
			while totalsent < msg_len:

				# write data
				sent = self.ethernet_socket.sendto(write_buffer[totalsent:msg_len],  (self.host, self.port))

				# if no data sent, exit while statement to prevent infinite loop
				if sent == 0:
					break

				# keep track of total bytes sent
				totalsent = totalsent + sent

		else:
			raise UdpDgramSocketError("error writing to socket. please open connection using open() before attempting write.")

		return totalsent	

	# (optional) private methods
	def _check_write_parameters(self, write_buffer, length):
		"""
		Description: 
		Return: 
		"""
		# make sure the write_buffer is a list, return error code -1 if not
		if type(write_buffer) is not list:
			return -1

		# valid length values = NoneType or integer greater that zero but 
		# less than or equal to write_buffer length.

		if length == None:	
			return 1

		# otherwise, use length value
		else:

			# error check length value
			if ( length < 0 ) or ( length > len(write_buffer) ):
				return -1

			return 1

	def __del__(self):
		"""
		Description:
		"""		
		if self.open_status():
			self.disconnect()

class UdpDgramSocketError(RuntimeError):
	"""
	Description:
	"""
	def __init__(self, error_msg):
		"""
		Description:
		Parameters: 
		"""
		self.error = str(error_msg)	

	def get_error(self):
		"""
		Description:
		Parameters: 
		Return: 
		"""
		class_name = self.__class__.__name__
		return_error = "\n{}: {}".format(str(class_name), str(self.error))
		return return_error	