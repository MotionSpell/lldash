#!/bin/bash
if [ $# -ne 1 ]; then
    echo "Usage: $0 preset"
    exit 1
fi
preset=$1
# Update repo
git fetch --recurse-submodules
git pull
git submodule update --remote evanescent signals bin2dash sub
rm -rf build installed
cmake --preset $preset
cmake --build --preset $preset
cmake --install --preset $preset
cpack --preset $preset
realpath build/package/*
