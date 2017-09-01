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

    # ---
    NO_OP = 0x10
    """
    Summary:     Do nothing
    Description: Send a no-op to the payload computer.  This is for testing purposes.

    Data:
        None
    """

    # ---
    ABORT_CAPTURE = 0x11
    """
    Summary:     Abort any in-progress capture
    Description: Immediately halt any capture that is in progress.

    Data:
        None
    """

    # ---
    CAPTURE_360 = 0x12
    """
    Summary:     Capture a 360-degree sequence.
    Description: This will capture photos from all 8 cameras.
                 They must be powered on.

    Data:
        UInt8 - Number of frames (per camera)
    """

    # ---
    CAPTURE_180 = 0x13
    """
    Summary:     Capture a 180-degree sequence.
    Description: This will capture photos from 4 cameras.
                 They must be powered on.

    Data:
        UInt8 - Number of frames (per camera)
    """

