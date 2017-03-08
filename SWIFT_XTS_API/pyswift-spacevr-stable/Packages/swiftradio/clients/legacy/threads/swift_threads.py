import datetime
import traceback
from threading import Thread
from time import strftime
from ..packet.Packet_Utilities import Packet_Parsing
from ..packet import Packet_Classes

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__status__ = "Development"
__date__ = "Late Updated: 11/12/14"

class SwiftBaseRxThread:
	"""
	Description: base class for all packet thread daughter classes
	"""				
	def __init__(self, thread_name='', DataInterface = None, endianess = "little"):
		"""
		Author: S. Alvarado
		Last Updated: 5/19/15 (SRA)		
		Description:
		Parameters: 
		"""	
		self._thread_name = thread_name
		self._swift_interface = DataInterface
		self._thread_open = False
		self._packet_count = 0
		self._packet_list = list()
		self._thread_status = "closed"
		self._endianess = endianess

	def start(self):
		"""
		Author: S. Alvarado
		Last Updated: 5/19/15 (SRA)		
		Description:
		Parameters: 
		"""	
		self._thread_open = True	
		Thread(target=self.listen).start()	

	def packets_received(self):
		"""
		Author: S. Alvarado
		Last Updated: 5/19/15 (SRA)		
		Description:
		Parameters: 
		"""	
		return self._packet_count
		
	def get_packets(self, packet_num = None):
		"""
		Author: S. Alvarado
		Last Updated: 5/19/15 (SRA)		
		Description:
		Parameters: 
		"""	
		# get all packets in list if packet_num not specified
		if packet_num == None:

			# make sure packet list has at least 1 packet
			if len(self._packet_list) > 0:

				# copy packets into a new packet list
				new_packet_list = list()
				size = len(self._packet_list)
				new_packet_list = self._packet_list

				# delete old packet list
				for i in range(size):
					del self._packet_list[0]
					self._packet_count -= 1

				# return list of packets
				return new_packet_list

			# return error if not
			else:
				return -1

		# otherwise, get specified packet
		else:

			# error check packet_num
			if ( int(packet_num) >=0 ) and ( int(packet_num) < len(self._packet_list) ):

				# get packet
				try:
					packet = self._packet_list[int(packet_num)]
					self._packet_count -= 1

					# delete packet from packet list
					del self._packet_list[int(packet_num)]

					# return packet
					return packet

				except IndexError:
					return -1

			# return error if not
			else:
				return -1
		
	def close(self):
		"""
		Author: S. Alvarado
		Last Updated: 5/19/15 (SRA)		
		Description:
		Parameters: 
		"""	
		self._thread_open = False
		while self._thread_status != "closed":
			pass				
		
	def listen(self):
		"""
		Author: S. Alvarado
		Last Updated: 5/19/15 (SRA)		
		Description:
		"""	
		pass

	def __del__(self):
		"""
		Author: S. Alvarado
		Last Updated: 5/19/15 (SRA)		
		Description:
		"""	
		if self._thread_status != "closed":
			self.close()		

class UdpSwiftPacketRxThread(SwiftBaseRxThread):
	"""
	Description:  
	"""					
	def listen(self):
		"""
		Description: 
		Parameters: 
		Return: 
		"""	
		udp_swiftpacket = ""
		swift_msg_data = list()
		MAX_UDP_SWIFTPACKET_LEN = 65507
		t_stamp = 0
		self._thread_status = "running"
		try:
			while self._thread_open:
				udp_swiftpacket, src_info, dest_info = self._swift_interface.read(MAX_UDP_SWIFTPACKET_LEN, 0.1)
				if len( udp_swiftpacket ) > 0:
					t_stamp = datetime.datetime.now().strftime( "%H:%M:%S.%f" ) 
					swift_msg_data = list( udp_swiftpacket )
					packet = Packet_Parsing.rawbytelist_to_swiftpacket( swift_msg_data, len(swift_msg_data), t_stamp, self._endianess )
					if packet != -1:
						self._packet_list.append( packet )
						self._packet_count += 1
					udp_swiftpacket = ""
		except:
			print traceback.print_exc()
			print "Error in listen. Closing Thread."	

		self._thread_status = "closed"		


class RawUdpPacketRxThread(SwiftBaseRxThread):
	"""
	Description: 
	"""					
	def listen(self):
		"""
		Description: 
		Parameters: 
		Return: 
		"""	
		rxbuffer = ""
		MAX_UDP_PACKET_LEN = 65507
		t_stamp = 0
		packet_ctr = 0
		packet = None
		self._thread_status = "running"

		try:
			while self._thread_open:
				# attempt udp socket read
				rxbuffer, (src_addr, src_port), (dest_addr, dest_port) = self._swift_interface.read(MAX_UDP_PACKET_LEN)
				# store udp data
				if len(rxbuffer) > 0:
					# save time
					t_stamp = datetime.datetime.now().strftime("%H:%M:%S.%f") 
					# convert string of data into a list
					rxbuffer_list = list(rxbuffer)
					# create udp packet instance
					packet = Packet_Classes.UdpDgramPacket()
					# set packet attributes
					packet.set_time_stamp(t_stamp)
					packet.set_packet_info(src_addr, dest_addr, src_port, dest_port)
					packet.set_data(rxbuffer_list)
					# store packet in packet list
					self._packet_list.append(packet)
					# packet.print_contents()
					self._packet_count += 1
					rxbuffer = ""
		except:
			print traceback.print_exc()
			print "Error in listen. Closing Thread."						

		self._thread_status = "closed"	


class SwiftSpaceWireRxThread(SwiftBaseRxThread):
	"""
	Description: 
	"""						
	def listen(self):
		"""
		Description: 
		Parameters: 
		Return: 
		"""	
		swift_msg_data = ""
		MAX_SPACEWIRE_MSG = 65535
		swift_msg_data = list()
		t_stamp = 0
		self._thread_status = "running"

		try:
			# start thread loop (keep spinning until close() method is called)
			while self._thread_open:

				# read in data from SpaceWire interface
				swift_msg_data = self._swift_interface.read()

				# confirm if data was read in
				if len(swift_msg_data) > 0:
					t_stamp = datetime.datetime.now().strftime("%H:%M:%S.%f") 
					packet = Packet_Parsing.rawbytelist_to_swiftpacket(swift_msg_data, len(swift_msg_data), t_stamp, self._endianess)

					# check if frame was successfully parsed, otherwise drop as corrupt frame
					if packet != -1:
						self._packet_list.append(packet)
						self._packet_count += 1														
					swift_msg_data = ""
		except:
			print traceback.print_exc()
			print "Error in listen. Closing Thread."	

		self._thread_status = "closed"

class SwiftHDLC422RxThread(SwiftBaseRxThread):
	"""
	Description: 
	"""						
	def listen(self):
		"""
		Description: 
		Parameters: 
		Return: 
		"""	
		encoded_rpc_frame = list()
		time_stamp = 0
		self._thread_status = "running"

		try:
			# start thread loop (keep spinning until close() method is called)
			while self._thread_open:

				# read in data
				encoded_rpc_frame = self._swift_interface.read_frame(timeout = 0.1)

				# confirm if data was read in
				if len( encoded_rpc_frame ) > 0:

					time_stamp = datetime.datetime.now().strftime("%H:%M:%S.%f")
					packet = Packet_Parsing.rawbytelist_to_swiftpacket(encoded_rpc_frame, len(encoded_rpc_frame), time_stamp, self._endianess)

					# check if frame was successfully parsed, otherwise drop as corrupt frame
					if packet != -1:
						self._packet_list.append(packet)
						self._packet_count += 1

					encoded_rpc_frame = list()
		except:
			print traceback.print_exc()
			print "Error in listen. Closing Thread."	

		self._thread_status = "closed"

class SwiftPacketUartThread(SwiftBaseRxThread):
	"""
	Description: 
	"""			
	def listen(self):
		"""
		Description: 
		Parameters: 
		Return: 
		"""	
		serialbuffer_rx = list()
		msg_buffer = list()
		SOF_SEARCH = 0
		FRAME_HEADER_PARSE = 1
		MSG_PARSE = 2
		CHECKSUM_VALIDATE = 3
		DONE = 4
		SYNC1 = 0x35
		SYNC2 = 0x2E
		SYNC3 = 0xF8
		SYNC4 = 0x53
		
		t_stamp = 0
		parse_state = 0
		sync_state = 0
		frame_header_state = 0
		byte_ctr = 0
		frame_length = 0x0000
		payload_offset = 0
		new_pkt = 0

		self._thread_status = "running"
		
		try:
			while self._thread_open:
				byte = self._swift_interface.read(1)
				if len(byte) is not 0:
					# [1] Use Sync Chars to Identify New Packet
					if parse_state == SOF_SEARCH:
						if sync_state == 0:
							if ord(byte) == SYNC1:
								sync_state += 1
								byte_ctr += 1
							else:
								pass
								# print "unknown sync 1 character"
						elif sync_state == 1:
							if ord(byte) == SYNC2:
								sync_state += 1
								byte_ctr += 1
							else:
								# print "unknown sync 2 character"
								sync_state = 0
								byte_ctr = 0
						elif sync_state == 2:
							if ord(byte) == SYNC3:
								sync_state += 1
								byte_ctr += 1
							else:
								# print "unknown sync 3 character"
								sync_state = 0
								byte_ctr = 0
						elif sync_state == 3:
							if ord(byte) == SYNC4:
								# print 'New Packet Detected'
								t_stamp = datetime.datetime.now().strftime("%H:%M:%S.%f") #strftime("%H:%M:%S %m/%d/%y")
								# print t_stamp
								byte_ctr += 1
								sync_state = 0
								serialbuffer_rx.append(chr(SYNC1))
								serialbuffer_rx.append(chr(SYNC2))
								serialbuffer_rx.append(chr(SYNC3))
								serialbuffer_rx.append(chr(SYNC4))
								parse_state += 1
							else:
								# print "unknown sync 4 character"
								sync_state = 0
								byte_ctr = 0
						else:
							print "unknown state."
					# [2] Parse Frame Header Data
					elif parse_state == FRAME_HEADER_PARSE:
						serialbuffer_rx.append(byte)
						byte_ctr += 1
						#payload offset byte
						if frame_header_state == 0:
							frame_header_state += 1
							payload_offset = ord(byte)
						#ht header byte
						elif frame_header_state == 1:
							frame_header_state += 1
							#this header byte is unused for now
						#frame length - Most Significant Byte
						elif frame_header_state == 2:
							frame_header_state += 1
						#frame length - Least Significant Byte
						elif frame_header_state == 3:
							frame_header_state = 0
							parse_state += 1
							frame_length += (ord(serialbuffer_rx[byte_ctr-1]) & 0xFF00) << 8
							frame_length += (ord(byte) & 0x00FF)
							frame_header_state = 0
							byte_ctr = 0
							# print serialbuffer_rx
					# [3] Read in Rest of Byte String		
					elif parse_state == MSG_PARSE:
						serialbuffer_rx.append(byte)
						msg_buffer.append(byte)
						byte_ctr += 1
						if byte_ctr >= (frame_length-8):
							parse_state += 1
							# print msg_buffer
					elif parse_state == CHECKSUM_VALIDATE:
						#verify checksums
						serialbuffer_rx.append(byte)
						byte_ctr += 1
						if byte_ctr >= (frame_length-4):
							parse_state += 1
							# print serialbuffer_rx
					if parse_state == DONE:
						serialbuffer_rx.append(byte)
						# Verify Checksums Here:
						checksums_good = True

						# Create Packet, Store in Packet List
						if checksums_good == True:
							# print 'New Packet Saved'
							packet = Packet_Parsing.rawbytelist_to_swiftpacket(swift_msg_data, len(swift_msg_data), t_stamp, self._endianess)
							if packet != -1:
								self._packet_list.append(packet)
								self._packet_count += 1
						
						payload_offset = 0
						serialbuffer_rx = []
						msg_buffer = []
						parse_state = 0
						frame_header_state = 0
						frame_length = 0
						byte_ctr = 0			
		except:
			print traceback.print_exc()
			print "Error in listen. Closing Thread."	

		self._thread_status = "closed"