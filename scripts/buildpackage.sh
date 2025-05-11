#!/bin/bash
if [ $# -ne 1 ]; then
    echo "Usage: $0 preset"
    echo
    cmake --list-presets
    exit 1
fi

preset=$1
# Update repo
# git fetch --recurse-submodules
# git pull
# git submodule update --remote lldash-relay signals lldash-srd-packager lldash-playout
rm -rf build installed
./vcpkg/bootstrap-vcpkg.sh
cmake --preset $preset
cmake --build --preset $preset
cmake --install build
cpack --preset $preset
realpath build/package/*
