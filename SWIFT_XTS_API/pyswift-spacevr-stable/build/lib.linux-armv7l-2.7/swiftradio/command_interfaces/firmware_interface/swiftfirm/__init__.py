"""
imports key modules in the Python Package
"""
import logging
# create root logger for package
logging.getLogger(__name__).addHandler(logging.NullHandler())

# import firmware upload/download wrapper class
from swiftfirm_ftp import SwiftfirmFTP
