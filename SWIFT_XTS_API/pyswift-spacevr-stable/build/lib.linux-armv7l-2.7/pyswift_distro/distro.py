"""
parse json file containing pyswift distro information.
"""
import sys, os
import json
import traceback

DISTRO = None

# pyswift distro dependency info (used by dependency checker)
SUPPORTED_PYTHON_VERSIONS = None
PYSWIFT_PKGS = None
THIRDPARTY_LIBS = None
LOCAL_PKGS_DIR = None
THIRDPARTY_PKGS_DIR = None

# pyswift distro radio database info (used by radio search scripts)
RADIO_MODULE_NAMES = None
RADIO_REG_MODULES = None

# get name of json config file containing pyswift distro information
CONFIG_FILE = None

# first option: use filename given by the environmental variable DISTRO_CONFIG if it has been set
_DISTRO_CONFIG = os.environ.get('DISTRO_CONFIG')
if (_DISTRO_CONFIG is not None) and (_DISTRO_CONFIG != "default"):
	# if DISTRO_CONFIG is set to 'global', then we should use this package's internal config file
	if _DISTRO_CONFIG == "global":
		CONFIG_FILE = os.path.dirname(os.path.realpath(__file__)) + "/distro_config.json"
	# if DISTRO_CONFIG is set to 'global', then try to use the distro_config.json file in the current working dir.
	elif _DISTRO_CONFIG == "local":
		CONFIG_FILE = "distro_config.json"
	# otherwise, use the given file name
	else:
		CONFIG_FILE = _DISTRO_CONFIG

# second option: check if there's a config file in the current working directory
elif os.path.isfile("distro_config.json"):
	CONFIG_FILE = "distro_config.json"

# third option: use the config file inside this package
else:
	CONFIG_FILE = os.path.dirname(os.path.realpath(__file__)) + "/distro_config.json"


# check that config file exists
if os.path.isfile( CONFIG_FILE ):

	# open json file and import dependency contents
	with open( CONFIG_FILE, 'rt') as f:
		try:
			_config_contents = json.load(f)
		except ValueError, e:
			raise ImportError("error in distro_config.json file formatting.\ndistro_config.json: {}".format( traceback.format_exception_only(type(e), e)[0] ) )

	# distro name
	DISTRO = _config_contents["distro"]

	# get distro dependency info
	_dependency_info = _config_contents["dependencies"]
	SUPPORTED_PYTHON_VERSIONS = _dependency_info["python_versions"]
	PYSWIFT_PKGS = _dependency_info["pyswift_pkgs"]
	THIRDPARTY_LIBS = _dependency_info["thirdparty_libs"]
	LOCAL_PKGS_DIR = _config_contents["local_directories"]["pyswift_packages"]
	THIRDPARTY_PKGS_DIR = _config_contents["local_directories"]["pyswift_thirdparty"]

	# get radio database info
	_radio_info = _config_contents["radio_database"]

	# this distribution should have access to these radio registration modules.
	RADIO_MODULE_NAMES = _radio_info["modules"]

	# list of *imported* registration modules
	RADIO_REG_MODULES = list()

	# file path to the radio registration modules for importing
	_radiodb_dir = None

	# possible locations of the radio registration modules
	_radio_reg_module_locations = [
		os.path.dirname(os.path.realpath(__file__)) + "/db/radios",
		"." + _radio_info["modules_dir"]
	]

	# find the directory containing radio database modules
	for possible_radio_reg_directory in _radio_reg_module_locations:
		if os.path.isdir( possible_radio_reg_directory ):
			_radiodb_dir = possible_radio_reg_directory
	if _radiodb_dir is not None:

		# import radio modules and store in list
		sys.path.insert(1, _radiodb_dir)
		for module_name in RADIO_MODULE_NAMES:
			try:
				module = __import__(module_name)
				RADIO_REG_MODULES.append(module)
			except:
				del sys.path[1]
				raise ImportError("Warning: radio registration file '{}.py' listed in distro_config.json does " +
					"not exist in any of these locations: {}".format( module_name, _radio_reg_module_locations ) )
		del sys.path[1]
	else:
		pass
		# raise ImportError("Could not find directory containing radio database registration files " +
		# 	"in any of these locations: {}".format(_radio_reg_module_locations) )

else:
	raise ImportError( "pyswift_distro: cannot find file '{}'".format(CONFIG_FILE) )


if __name__ == "__main__":
	print SUPPORTED_PYTHON_VERSIONS
	print PYSWIFT_PKGS
	print THIRDPARTY_LIBS
	print LOCAL_PKGS_DIR
	print THIRDPARTY_PKGS_DIR

	# pyswift distro radio database info (used by radio search scripts)
	print RADIO_MODULE_NAMES
	print RADIO_REG_MODULES
