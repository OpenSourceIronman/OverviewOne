"""
swiftradio utils sub-package
"""
import dataconversions
from dataconversions import convert_raw_bytelist, convert_raw

from packet_tools import find_command_data_by_name

# add search functions here (make try/except statements)
try:
	from search import swift_com_search
	from search import swift_com_enumerate
except ImportError:
	pass
try:
	from search import swift_network_search
	from search import swift_network_enumerate
except ImportError:
	pass

# gives access to the error modules, useful when trying to catch SwiftRadioError exceptions
# thrown by the swiftradio library (move this somewhere else)
from error import SwiftRadioError
