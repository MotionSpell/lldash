#!/bin/bash
#
# This script should be run *after* setup_test_environment.sh
#
# It expects a cwipc source tree at ../cwipc
#
# It removes cwipc_util from the current venv, and installs an editable
# version of cwipc_util from ../cwipc/cwipc_util/python
#
# It's probably only useful for Jack
pip uninstall cwipc_util
pip install -e ../cwipc/cwipc_util/python
