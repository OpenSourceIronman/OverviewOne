import traceback
import socket

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__company__ = "Tethers Unlimited Inc."
__status__ = "Development"
__date__ = "Late Updated: 11/10/14"

class SwiftEthernetInterface:
	def __init__(self, host, port=12345, discovery_port=802, protocol = "IPv4", 
				 ethernet_socket=None, transport_layer="UDP", bind_port=40000, timeout=10):
		"""
		Description:
		Parameters: 
		Return: 
		"""			
		self.connection_good = False
		self.host = str(host)
		self.local = None
		self.port = int(port)
		self.bind_port = int(bind_port)
		self.discovery_port = discovery_port
		self.protocol = protocol
		self.transport_layer = transport_layer
		self.timeout = timeout
		self.ethernet_socket = None

		# check if socket instance was provided (uncommon)
		if ethernet_socket != None:
			self.ethernet_socket = ethernet_socket
		# create a socket object. socket settings are specific to protocol specified by user	
		else:
			# use the IPv4 protocol
			if self.protocol == "IPv4":
				# create TCP/IP streaming socket client instance (can be used for textual interface or outputting syslog)
				if self.transport_layer == "TCP":
					self.ethernet_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				# create TCP/IP streaming socket client instance (used for cmdhost dgram packet interface)	
				elif self.transport_layer == "UDP":
					self.ethernet_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
					self.ethernet_socket.bind(('', bind_port))
					self.local = socket.gethostbyname(socket.gethostname())
					if len(self.local) != 1:
						self.local = ""
					else:
						self.local = str(self.local[0])
			# use the IPv6 protocol (uncommon)		
			elif self.protocol == "IPv6":
				pass
			# report unrecognized protocol	
			else:
				print "unrecognized address type"
				# raise exception
		
		self.connection_good = True	

	def connect(self, trace=0):
		"""
		Description:
		Parameters: 
		Return: True - successful connection
				False - failed to connect
		"""				
		if self.ethernet_socket != None:
			if self.transport_layer == "TCP":
				if self.ethernet_socket.connect((self.host, self.bind_port)):
					return True
				else:
					return False
			else:
				return True		
		else:
			return False

	def close(self):
		"""
		Description:
		Parameters: 
		Return: 
		"""				
		if self.ethernet_socket != None:
			# self.ethernet_socket.shutdown(socket.SHUT_RDWR)
			if self.transport_layer == "TCP":
				self.ethernet_socket.close()
			# self.ethernet_socket = None

	def is_open(self):
		"""
		Description:
		Parameters: 
		Return: 
		"""	
		if self.ethernet_socket != None:
			return False
		else:
			return True

	
	def write(self, write_buffer, length = 0, auto_lf = False):
		"""
		Description:
		Parameters: 
		Return: 
		"""				
		totalsent = 0
		msg_len = 0
		sent = 0
		if type(write_buffer) is list:
			write_buffer = "".join(write_buffer)

		if self.ethernet_socket != None:
			if auto_lf == True:
				write_buffer = str(write_buffer) + '\r'
			# determine size of data to send
			if length == 0:	
				# if write byte length is not specified, write entire write_buffer
				msg_len = len(write_buffer)
			else:
				msg_len = length
			# send data
			while totalsent < msg_len:
				sent = self.ethernet_socket.sendto(write_buffer[totalsent:], (self.host, self.port))
				if sent == 0:
					raise RuntimeError("socket connection broken")
				totalsent = totalsent + sent
	
	def read(self, length = 1, timeout=1):	
		"""
		Description:
		Parameters: 
		Return: 
		"""		
		read_buffer = ""
		src_info = ("","")
		dest_info = (self.local, self.bind_port)
		
		# make sure socket object is defined
		if self.ethernet_socket != None:
			# set socket read timeout
			self.ethernet_socket.settimeout(timeout)
			try:
				if self.transport_layer == "TCP":
					self.ethernet_socket.setblocking(0)
					read_buffer = self.ethernet_socket.recv(length)
				elif self.transport_layer == "UDP":
					# self.ethernet_socket.setblocking(1)
					read_buffer, src_info = self.ethernet_socket.recvfrom(length)
					# print src_info
					if (str(src_info[0]) != self.host):
						read_buffer = "" 	
			except socket.timeout:
				# no data received from socket, return empty string
				pass
			return read_buffer, src_info, dest_info
		else:
			print "No Socket Object!"

	def __del__(self):
		"""
		Description: class destructor function
		Parameters: 
		Return: 
		"""
		if self.ethernet_socket != None:
			self.close()
