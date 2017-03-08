import os
import sys
import time
import traceback

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__company__ = "Tethers Unlimited Inc."
__status__ = "Development"
__date__ = "Created: 05/10/16"

class SwiftCommandInterface( object ):
	"""
	<description>

	Created: 05/10/16

	Author: S. Alvarado
	"""

	def __init__(self, radio_instance):
		"""
		Initialization is done by the radio client.
		"""
		# ensure client instance is a SwiftRadioInterfaceV2 object.
		REQUIRED_CLIENT_CLASS = "SwiftRadioInterfaceV2"
		class_bases = [base.__name__ for base in radio_instance.__class__.__bases__ ]
		if REQUIRED_CLIENT_CLASS not in class_bases:
			raise SwiftCommandInterfaceError( "radio_instance must be an object created from the "
				"{} or daughter class. Detected base classes: {}".format(REQUIRED_CLIENT_CLASS, ", ".join(class_bases)) )

		# set instance
		self._radio = radio_instance

	def _cleanup_interface(self):
		"""
		Perform any required cleanup code here.

		.. note:: This method must be overwritten by daughter class.
		"""
		raise SwiftCommandInterfaceError("subclass '{}' must provide a _cleanup_interface() method.".format(
			self.__class__.__name__))

class SwiftCommandInterfaceError( RuntimeError ):
	pass

#########################################################
# Test Code
#########################################################
if __name__ == "__main__":

	class DummyCommandInterface(SwiftCommandInterface):

		def square(self, x):
			return x**2

		def mult(self, x, y):
			return x*y

		def get_radioclient_name(self):
			return self._radio.get_name()

		def _cleanup_interface(self):
			print "cleaning shit up"

	class RadioClientDummy( object ):

		def __init__(self):
			self._command_interface_names = list()

		def get_name(self):
			return "SwiftRadioInterfaceV2"

		def attach_command_interface(self, name, interface_class):
			"""
			Assign a Command Interface object as an attribute of this client instance. Note that \
			interface_class must be some class that inherits from the SwiftCommandInterface base \
			class.

			:param str name: The name of the attribute that will be assigned to radio client. Note \
			that an exception will be raised if a client already has an attribute with the same name.
			:param class interface_class: A class derived from SwiftCommandInterface.

			**Example**:

			.. code-block:: python
				...

			Last Updated: 05/10/16 (SRA)
			"""
			# check that object is derived from SwiftCommandInterface.
			class_bases = [base.__name__ for base in interface_class.__bases__ ]
			print ", ".join( class_bases )
			if SwiftCommandInterface not in interface_class.__bases__:
				class_bases = [ base.__name__ for base in interface_class.__bases__ ]
				raise RuntimeError( "A command interface class must inherit from "
					"SwiftCommandInterface. Detected base classes {} ".format(", ".join(class_bases)) )

			# error check name is a string and command interface of the same name does not already exist
			if name in self._command_interface_names:
				raise RuntimeError( "a command interface with name '{}' already exists.".format(name) )

			# make sure this attribute does not already exist
			try:
				getattr( self, name )
				raise RuntimeError( "Client already has attribute with name '{}'".format(name) )
			except AttributeError:
				pass

			# initialize object
			temp_obj = None
			temp_obj = interface_class( self )

			# set this object as an attribute
			setattr( self, name, temp_obj )

			# add object name
			self._command_interface_names.append( name )

		def destroy_command_interfaces(self):
			"""
			Deleted all created class interface objects.

			Last Updated: 05/10/16 (SRA)
			"""
			for interface in self._command_interface_names:

				try:
					# call clean up method
					self.__dict__[interface]._cleanup_interface()

					# delete object attribute from client.
					delattr(self, interface)

				except KeyError:

					raise RuntimeError("error occurred while destroying '{}' attribute".format(interface))

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
