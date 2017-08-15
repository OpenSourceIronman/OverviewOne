################################################################################ 
#(C) Copyright Pumpkin, Inc. All Rights Reserved.
#
#This file may be distributed under the terms of the License
#Agreement provided with this software.
#
#THIS FILE IS PROVIDED AS IS WITH NO WARRANTY OF ANY KIND,
#INCLUDING THE WARRANTY OF DESIGN, MERCHANTABILITY AND
#FITNESS FOR A PARTICULAR PURPOSE.
################################################################################
"""
Functions to support SUPERNOVA_Apps.

"""

import logging

# LOGGING:
#    LOG.error() is called whenever an exception is explicitly
#        raised or handled.
LOG = logging.getLogger(__name__)

def verify_range(min_, max_, name, value):
    """
    Check that `value` named `name` is in range [min_, max_].

    """
    if not min_ <= value <= max_:
        msg = '{} must be between {} and {}'.format(value, name, min_, max_)
        LOG.error(msg)
        raise ValueError(msg)

def verify_bytearray_length(min_, max_, name, array):
    """
    Check that `array` named `name` is a bytearray and of len in [min_, max_].

    """
    if type(array) is bytearray:
        if not min_ <= len(array) <= max_:
            msg = '{} must be between {} and {} bytes.'.format(name, min_, max_)
            LOG.error(msg)
            raise ValueError(msg)
    else:
        msg = '{} must be of type `bytearray`.'.format(name)
        LOG.error(msg)
        raise TypeError(msg)
