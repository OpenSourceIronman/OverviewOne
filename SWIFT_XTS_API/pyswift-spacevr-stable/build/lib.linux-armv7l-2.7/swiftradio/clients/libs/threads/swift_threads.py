import traceback
from threading import Thread

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
