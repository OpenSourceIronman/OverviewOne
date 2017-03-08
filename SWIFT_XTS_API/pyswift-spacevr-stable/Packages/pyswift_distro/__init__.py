"""
The pyswift_distro package
"""
# package information
PROJECT = u'pyswift_distro'
COPYRIGHT = u'2016, Tethers Unlimited, Inc'
AUTHOR = u'Steve Alvarado'
VERSION = '0.0.1'
RELEASE = '0.0.1.beta'

from distro import DISTRO

# import this distribution's dependency info
from distro import SUPPORTED_PYTHON_VERSIONS
from distro import LOCAL_PKGS_DIR
from distro import THIRDPARTY_PKGS_DIR
from distro import PYSWIFT_PKGS
from distro import THIRDPARTY_LIBS

# import relevant radio info
from distro import RADIO_MODULE_NAMES
from distro import RADIO_REG_MODULES
