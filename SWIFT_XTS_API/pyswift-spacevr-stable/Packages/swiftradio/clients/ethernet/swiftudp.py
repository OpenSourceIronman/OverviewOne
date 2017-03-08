import sys, os
import socket
import traceback

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__company__ = "Tethers Unlimited Inc."
__date__ = "Created: 5/8/16"

class SwiftUDPClient():
	"""
	Description:
	"""
	def __init__(self, host, port, bind_port=None, timeout = 10, name = None):
		"""
		Author: S. Alvarado
		Last Updated: 5/12/16 (SRA)
		Description:
		Parameters:
		"""
		self.host = host
		self.port = port
		self.bind_port = bind_port
		self.timeout = timeout
		self.name = name
		self.connection_status = 0
		self.udp_socket = None

		# make sure host is a IPv4 formatted string
		host_is_ipv4 = False
		if type(self.host) is str:
			if "." in self.host:
				ipv4_octets = self.host.split(".")

				# must be 4 octets in string, each being a number 0-255
				if len(ipv4_octets) == 4:
					bad_octet = False
					for octet in ipv4_octets:
						try:
							if (int(octet) < 0) or (int(octet) > 256):
								bad_octet = True
						except ValueError:
							bad_octet = True
					if bad_octet is False:
						host_is_ipv4 = True
		if host_is_ipv4 is False:
			raise SwiftUDPClientError("Invalid host value '{}'. Host ip must be a string in IPv4 \
			format. (i.e. '123.45.67.89')".format(self.host) )

		# create dgram socket client instance using the python socket library
		self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		# specify this machine's service port
		if bind_port is not None:
			try:
				self.udp_socket.bind( ('', bind_port) )
			except:
				traceback.print_exc()
				raise SwiftUDPClientError("Cannot bind UDP/IP connection to port {}. Already in \
				use.".format(bind_port))

		# if not specified, assign an open bind port in range (40000 to 40999)
		else:
			for i in range(999):
				bind_port = 40000 + i
				try:
					self.udp_socket.bind( ('', bind_port) )
					break
				except socket.error:
					bind_port = None
			if bind_port is None:
				raise SwiftUDPClientError("unable to assign a bind port in range 40000 to 40999")

	# Public Interface
	def connect(self):
		"""
		Author: S. Alvarado
		Updated: 7/20/15 (SRA)
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
		Updated: 7/20/15 (SRA)
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
		Updated: 7/20/15 (SRA)
		Description: get the open/closed status of the connection.
		Return: 0 - connection is closed
				1 - connection is open
		"""
		return self.connection_status

	def read(self, length = 1, timeout = 1):
		"""
		Author: S. Alvarado
		Updated: 7/20/15 (SRA)
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
			self.udp_socket.settimeout(timeout)

			# attempt socket read, an exception will be thrown if a timeout
			# occurs before data is read in
			try:
				# read data from socket
				returned_socket_data = self.udp_socket.recv(length)

				# socket library returns a string, make sure to convert to list
				# to conform with swift IO standards
				if len(returned_socket_data) > 0:
					read_buffer = list(returned_socket_data)

			# no data received from socket, return empty string
			except socket.timeout:
				pass
		else:
			raise SwiftUDPClientError("error reading from socket. please open connection using connect() before attempting read.")

		# return data to user
		return read_buffer


	def write(self, write_buffer, length = None):
		"""
		Author: S. Alvarado
		Last Updated: 7/20/15 (SRA)
		Description: send data to a device via the opened connection.
		Parameters: write_buffer (list/str) - a list of data to be sent over connection
					length (int) - length of data to be written. Note that if length
							is None, all bytes in list will be written.
		Return: number of bytes written - positive non-zero integer representing number of
			   				   			  bytes sent to device
				0 - write attempt unsuccessful
		"""
		totalsent = 0
		msg_len = 0
		sent = 0

		# [1] check if connection is open
		if self.open_status() == 1:

			# [2] make sure the write_buffer is a list, return error code -1 if not
			if (type(write_buffer) is not list) and (type(write_buffer) is not str):
				raise SwiftUDPClientError("write_buffer must be a string or list. Not {}".format(
					type(write_buffer).__name__))

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
				sent = self.udp_socket.sendto(write_buffer[totalsent:msg_len],  (self.host, self.port))

				# if no data sent, exit while statement to prevent infinite loop
				if sent == 0:
					break

				# keep track of total bytes sent
				totalsent = totalsent + sent

		else:
			raise SwiftUDPClientError("error writing to socket. please open connection using open() before attempting write.")

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

class SwiftUDPClientError(RuntimeError):
	pass

if __name__ == '__main__':

	hostip = 172.23
	client = SwiftUDPClient(hostip, 12345)
