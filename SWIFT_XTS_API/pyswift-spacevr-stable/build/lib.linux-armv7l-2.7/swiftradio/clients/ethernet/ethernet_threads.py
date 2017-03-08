import datetime
import traceback
from ..libs.packet import parsing, packets
from ..libs.threads import swift_threads

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__status__ = "Development"
__date__ = "Late Updated: 11/12/14"

MAX_UDP_SWIFTPACKET_LEN = 65507

class UdpSwiftPacketRxThread(swift_threads.SwiftBaseRxThread):
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
		time_stamp = 0
		self._thread_status = "running"

		try:
			# start thread loop (keep spinning until close() method is called)
			while self._thread_open:

				# read in data
				udp_swiftpacket = self._swift_interface.read(MAX_UDP_SWIFTPACKET_LEN, 0.1)

				# confirm if data was read in
				if len( udp_swiftpacket ) > 0:

					time_stamp = datetime.datetime.now().strftime( "%H:%M:%S.%f" )
					swift_msg_data = list( udp_swiftpacket )
					packet = parsing.rawbytelist_to_swiftpacket( swift_msg_data, len(swift_msg_data), time_stamp, self._endianess )

					# check if frame was successfully parsed, otherwise drop as corrupt frame
					if packet != -1:
						self._packet_list.append( packet )
						self._packet_count += 1

					udp_swiftpacket = ""
		except:
			traceback.print_exc()
			print "Error in listen. Closing Thread."

		self._thread_status = "closed"
