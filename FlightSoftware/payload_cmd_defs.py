"""
Payload command IDs, as used in spacepackets to communicate between
  the payload agents on the Supernova bus.

Copyright SpaceVR, 2017.  All rights reserved.
"""

import sys
from enum import Enum

# Assert Python 2.7
assert sys.version_info[0:2] == (2,7)

class PayloadCommandId(Enum):
    """
    Defines the payload command IDs.
    """

    # No operation.  Do nothing.
    NO_OP = 0x10

    # If camera capture is in progress, abort it immediately.
    ABORT_CAPTURE = 0x11
