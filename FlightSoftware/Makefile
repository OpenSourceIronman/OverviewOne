# Copyright SpaceVR, 2017.  All rights reserved.

.PHONY: test

# All Python files in the current directory.
ALL_PYTHON = $(wildcard *.py)

# The core sources exclude test and executable code.
CORE_SOURCES = $(filter-out run_% test_% %_main.py, $(ALL_PYTHON))

# Options to 'pytest' to report coverage on all core modules.
CORE_SOURCES_COV_OPTS = $(patsubst %.py,--cov=%,$(CORE_SOURCES))

test:
	SUPERNOVA_ID=1 \
	pytest $(CORE_SOURCES_COV_OPTS) --cov-report term-missing

test-verbose:
	SUPERNOVA_ID=1 \
	pytest -s $(CORE_SOURCES_COV_OPTS) --cov-report term-missing

default: test

