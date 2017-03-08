"""
imports key command interface sub-classes
"""
try:
	from example.example_cmd_interface import DummyCommandInterface
except ImportError:
	pass

try:
	from firmware_interface.interface_class import SwiftFirmwareInterface
	from firmware_interface.interface_class import SwiftFirmwareError
except ImportError:
	pass
