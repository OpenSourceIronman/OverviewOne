from __future__ import print_function

#!/usr/bin/env python
##
# @file dependency_check.py
# @brief checks for missing python dependencies.
# @author Steve Alvarado <alvarado@tethers.com>, Tethers Unlimited, Inc.
# @attention Copyright (c) 2016, Tethers Unlimited, Inc.

__author__ = "Steve Alvarado"
__credits__ = ["Steve Alvarado", "Tyrel Newton"]
__maintainer__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__company__ = "Tethers Unlimited Inc."
__date__ = "Late Updated: 06/10/16 (SRA)"
__doc__ = ("checks for missing python dependencies.")

import sys
import traceback
try:
	sys.path.insert(1, "../../Packages")
	import pyswift_distro
	del sys.path[1]
except:
	print("Failed to import:")
	print("  'pyswift_distro'")
	print("Define the distribution depencies here.")
	sys.exit(1)

#---------------------------------------------------------------------------------------------------
# 	Main Program
#---------------------------------------------------------------------------------------------------
VERSION = '2.0.2'

if __name__ == "__main__":
	missing_dependency_list = list()
	uninstalled_dependency_list = list()
	failed_imports_list = list()

	print("--")
	print("Dependency Checker Program")
	print("Version {}".format(VERSION))
	print("Tethers Unlimited Inc. (c)")

	print("\nstarting dependency check for distribution '{}'...".format(pyswift_distro.DISTRO))

	try:
		print("\n====================================")
		print(" Python")
		print("====================================")

		# validate python version
		print("validating Python version...", end=" ")
		detected_python_version = float( "{}.{}".format( sys.version_info[0], sys.version_info[1] ) )
		if detected_python_version not in pyswift_distro.SUPPORTED_PYTHON_VERSIONS:
			print("**failed** (Python version {} not supported)\n\nsupported Python versions: {}".format(detected_python_version,
																							pyswift_distro.SUPPORTED_PYTHON_VERSIONS) )
			print("\nexiting program...")
			sys.exit()
		else:
			print( "done. (version {} detected)".format(detected_python_version) )

		# validating required third-party libraries
		if len( pyswift_distro.THIRDPARTY_LIBS ) > 0:
			print("\n====================================")
			print(" Third-Party Libraries")
			print("====================================")
			for pkg in pyswift_distro.THIRDPARTY_LIBS:
				try:
					# check if library is in site packages
					print("validating {} library installation...".format(pkg), end=" ")
					__import__(pkg)
					print("done.")
				except ImportError:
					if len( pyswift_distro.THIRDPARTY_PKGS_DIR ) > 0:
						sys.path.append( pyswift_distro.THIRDPARTY_PKGS_DIR )
						# check if in local Thirdparty directory.
						try:
							__import__(pkg)
							print( "done. (found in '{}')".format(pyswift_distro.THIRDPARTY_PKGS_DIR) )
							uninstalled_dependency_list.append(pkg)
						# package could not be found
						except ImportError:
							missing_dependency = (traceback.format_exc().splitlines()[-1]).split(" ")[-1]
							print("**failed**")
							if (pkg, missing_dependency) not in missing_dependency_list:
								missing_dependency_list.append( missing_dependency )
						del sys.path[-1]

		# validating pyswift package installations
		if len( pyswift_distro.PYSWIFT_PKGS ) > 0:
			print("\n====================================")
			print(" SWIFT Packages")
			print("====================================")
			for pkg in pyswift_distro.PYSWIFT_PKGS:
				try:
					# check if package is in Global Site-Packages directory.
					print("validating {} package installation...".format(pkg), end=" ")
					__import__(pkg)
					print("done.")
				except ImportError:
					sys.path.insert( 1, pyswift_distro.LOCAL_PKGS_DIR )
					# check if package is in local Packages directory.
					try:
						__import__(pkg)
						print( "done. (found in '{}')".format(pyswift_distro.LOCAL_PKGS_DIR) )
						uninstalled_dependency_list.append(pkg)
					# report if could not be found.
					except ImportError:
						missing_dependency = (traceback.format_exc().splitlines()[-1]).split(" ")[-1]
						if missing_dependency == pkg:
							print("**failed**")
							if missing_dependency not in missing_dependency_list:
								missing_dependency_list.append(missing_dependency)
						# package found but could not be imported due to a missing dependency
						else:
							print("**failed**")
							if (pkg, missing_dependency) not in failed_imports_list:
								failed_imports_list.append( (pkg, missing_dependency) )
					del sys.path[ 1 ]

		# print dependency check results
		print("\nDependency check complete.\n")
		print("--")
		errors = len( missing_dependency_list ) + len( failed_imports_list )
		warnings = len( uninstalled_dependency_list )

		# print any warning info
		if warnings != 0:
			print( "Warnings: {}".format( warnings ) )
			if len( uninstalled_dependency_list ) > 0:
				for i, dependency in enumerate(uninstalled_dependency_list):
					if dependency in pyswift_distro.THIRDPARTY_LIBS:
						print( " ({}) Uninstalled package '{}'. Not installed in Site-Packages but found locally in '{}'.".format(i+1, dependency, pyswift_distro.THIRDPARTY_PKGS_DIR) )
					else:
						print( " ({}) Uninstalled package '{}'. Not installed in Site-Packages but found locally in '{}'.".format(i+1, dependency, pyswift_distro.LOCAL_PKGS_DIR) )
			print("")

		# print any error info
		if errors != 0:
			print( "Errors: {}".format( errors ) )
			errors_ctr = 1
			if len( missing_dependency_list ) > 0:
				for dependency in missing_dependency_list:
					if dependency in pyswift_distro.THIRDPARTY_LIBS:
						print( " ({}) Missing dependency '{}'. Not installed in Site-Packages or '{}'.".format(errors_ctr, dependency, pyswift_distro.THIRDPARTY_PKGS_DIR) )
					else:
						print( " ({}) Missing dependency '{}'. Not installed in Site-Packages or '{}'.".format(errors_ctr, dependency, pyswift_distro.LOCAL_PKGS_DIR) )
					errors_ctr += 1

			if len( failed_imports_list ) > 0:
				for pkg_name, missing_dependency in failed_imports_list:
					print( " ({}) Cannot import package '{}' because it requires a missing dependency ('{}').".format(errors_ctr, pkg_name, missing_dependency) )
					errors_ctr += 1
			print("")

		if warnings == 0 and errors == 0:
			print("\nNo dependency issues detected.")

	except SystemExit:
		pass
