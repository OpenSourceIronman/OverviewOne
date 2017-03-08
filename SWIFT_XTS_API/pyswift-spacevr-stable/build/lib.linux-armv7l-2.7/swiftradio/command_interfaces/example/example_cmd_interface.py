import os
import sys
import time
import traceback
from .. import swiftcmdbase

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__company__ = "Tethers Unlimited Inc."
__status__ = "Development"
__date__ = "Created: 05/10/16"

class DummyCommandInterface(swiftcmdbase.SwiftCommandInterface):

	def square(self, x):
		return x**2

	def get_radioclient_name(self):
		return self._radio.get_name()

	def get_devid(self):
		sysinfo = self._radio.execute_command("sysinfo")
		return sysinfo["id"]

	def _cleanup_interface(self):
		print "performing command interface cleanup..."

#########################################################
# Test Code
#########################################################
if __name__ == "__main__":

	command_interface1 = DummyCommandInterface
	command_interface2 = DummyCommandInterface

	radio_client = RadioClientDummy()

	radio_client.attach_command_interface( "dummy_commands1", command_interface1 )
	# radio_client.attach_command_interface( "dummy_commands2", command_interface2 )

	# print radio client attributes
	import inspect
	# print "\nclient attributes:"
	# members = inspect.getmembers(radio_client)
	#
	# for member_name, member_val in members:
	# 	print "{}".format(member_name)

	# test methods
	print radio_client.dummy_commands1.square(2)
	print radio_client.dummy_commands1.mult(2, 8)
	print radio_client.dummy_commands1.get_radioclient_name()

	# print radio_client.dummy_commands2.square(4)
	# print radio_client.dummy_commands2.mult(4, 8)
	# print radio_client.dummy_commands2.get_radioclient_name()

	radio_client.destroy_command_interfaces()

	# print "\nclient attributes:"
	# members = inspect.getmembers(radio_client)
	# for member_name, member_val in members:
	# 	print "{}".format(member_name)
