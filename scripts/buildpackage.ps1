#!/bin/bash
if ( $args.Count -ne 1) {
    "You must supply a preset argument. Available presets: "
    cmake --list-presets
    exit
}
$makepath=(Get-Command mingw32-make).Path
$preset=$args[0]
# Update repo
# git fetch --recurse-submodules
# git pull
# git submodule update --remote lldash-relay signals lldash-srd-packager lldash-playout
if (Test-Path .\build) {
    Remove-Item .\build -Recurse
}
if (Test-Path .\installed) {
    Remove-Item .\installed -Recurse
}
.\vcpkg\bootstrap-vcpkg.bat
cmake --preset $preset -DCMAKE_MAKE_PROGRAM=$makepath
cmake --build --preset $preset
cmake --install build
cpack --preset $preset
