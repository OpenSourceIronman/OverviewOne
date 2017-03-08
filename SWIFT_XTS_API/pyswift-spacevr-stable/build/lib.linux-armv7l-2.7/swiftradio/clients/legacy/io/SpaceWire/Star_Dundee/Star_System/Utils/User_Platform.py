import os
import platform
from .Star_System_Error import StarSystemError

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__status__ = "Development"
__date__ = "Late Updated: 11/06/14"

def get_system_os_name():
	"""
	Description: 
	Parameters: 
	Return: name of system operating system, as a string or None object if it could
			be found.
			'Windows'
			'Linux'
			None - os could not be found
	"""
	os_name = None
	
	# get this computer's OS info
	os_info = platform.platform()

	if "-" in os_info:
		# remove extra os information and just return name
		os_info = os_info.split("-")
		os_name = os_info[0]

		# make sure a valid os name was retrieved
		if os_name != 'Windows' and os_name != 'Linux' and os_name != 'Macintosh':
			os_name = None

	# return os name
	return os_name


def get_starsystem_bin_lib_path(current_dir, bin_name):
	"""
	Description: 
	Parameters: 
	Return:
	"""

	# get name of current operating system
	os_name = get_system_os_name()
	if os_name == None:
		raise StarSystemError("could find os name!")
		return None
	
	# get binary file extension (file type will be different depending on the OS)
	if os_name == "Windows":
		file_extension = "dll"

		# construct file path (caller's current dir \ name of os \ bin \ file.extension )
		file_path = "{}\\{}\\bin\\{}.{}".format(current_dir, os_name, bin_name, file_extension)

	else:
		raise StarSystemError("SpaceWire drivers for the {} OS are not supported by the star system library".format(os_name) )
		return None
	
	# check if this file exists
	if os.path.isfile(file_path) == False:
		raise StarSystemError("file does not exist at '{}'".format(file_path) )
		return None

	return file_path	


	