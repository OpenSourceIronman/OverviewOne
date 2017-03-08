++ Meta ++
	Copyright: Copyright (c) 2015, Tethers Unlimited, Inc.
	Author: Steve Alvarado <mailto://alvarado@tethers.com>
	Contributors: Tyrel Newton <mailto://newton@tethers.com>
	Created: 2/11/2015
	Last Updated: 05/18/2016 (SRA)

++ Description ++
	pyswift is a python repository containing a collection of python scripts, libraries and frameworks used for a variety of software applications--including libraries for interfacing with Swift-SDR radios and test equipment.

++ Requirements ++
	- Operating System -
	Tested on the following operating systems:
	* Windows XP & 7
	* Linux (Ubuntu 14.04 LTS and 14.10)

	- Software -
	* Python 2.7x (currently not compatible with python 3.x)
	* Essential Third-Party Python Libraries
		* setuptools (https://pypi.python.org/pypi/setuptools)

++ Documentation ++
	Please refer to the pyswift wiki page from the SWIFT User's Guide (https://support.tethers.com/display/SWIFTUG/pyswift) for more information.

++ Installation ++
	Ensure that the previously listed software dependencies are installed. Note that if you are connected to the Internet during the installation procedure, an included bootstrap file will attempt to download and install setuptools automatically (this may also be true for Package dependencies). Please refer to the official Package Python Index (https://pypi.python.org/pypi) repository for downloading missing libraries.

	[1] Packages Installation

	If installing from an archive, run from the command line:
		python setup.py install

	This will build and install all the necessary pyswift Python packages into the standard location for third-party Python modules ("C:\PythonX.Y\Lib\site-packages" for Windows) using the setuptools library. If you'd prefer to install the packages into a different directory, often the easiest way to do this is to use 'build' command line option instead of 'install'. You can then manually relocate the post-build packages located in the /build/lib directory to a location of your choosing.

	[2] Verify Installation
	After installation, navigate to Scripts/common and run:
		python dependency_check.py
		
	This will check two things:
		1) That the dependencies for pyswift listed above are installed on your host system.
		2) That the pyswift packages were correctly installed by the setup.py script.
