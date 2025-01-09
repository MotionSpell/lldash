#!/bin/bash
if [ $# -ne 1 ]; then
    echo "Usage: $0 preset"
    exit 1
fi
preset=$1
rm -rf build
cmake --preset $preset
cmake --build --preset $preset
cpack --preset $preset
