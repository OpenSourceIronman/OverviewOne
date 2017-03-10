import pytest
import sys, os

from agent import Agent

# Assert Python 2.7
assert sys.version_info[0:2] == (2,7)

def test_init():
    a = Agent()
