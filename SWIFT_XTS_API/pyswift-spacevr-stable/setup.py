import setuptools_bs
setuptools_bs.use_setuptools()
from setuptools import setup, find_packages

setup(
	name = "pyswift-spacevr",
	version="stable",
	description='SWIFT Python Libraries',
	author='Steve Alvarado',
	author_email='alvarado@tethers.com',
	url='https://support.tethers.com/display/SWIFTUG/pyswift',

	# pyswift packages
	packages = find_packages( "Packages",

		# included pyswift packages
		include=[
			"pyswift_distro", "pyswift_distro.*",
			"swiftradio", "swiftradio.*",
		],
		# do not include these files
		exclude=[
			"swiftradio.clients.rs422*"
		]
	),
	# include additional package files that are not *.py files.
	package_dir = {"": "Packages"},
	package_data = {

		# include any .txt and .json files
		"": ["*.txt", "*.json"],
	},
)
