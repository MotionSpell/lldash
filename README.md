# lldash
[![Build and Test](https://github.com/MotionSpell/lldash/actions/workflows/build-test.yml/badge.svg)](https://github.com/MotionSpell/lldash/actions/workflows/build-test.yml)

Umbrella repository for Motion Spell/CWI Low Latency DASH

**Table of Contents** 

- [Introduction](#introduction)
- [Components](#components)
- [Build](#build)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)


# Introduction

lldash is a comprehensive repository that includes various components for Low Latency DASH streaming.

# Components

The repository includes the following components:

- **lldash-relay**: A low-latency HTTP server for relaying DASH streams.
- **lldash-playout**: A component for receiving compressed video from the network.
- **lldash-srd-packager**: A component for packaging point clouds and TVMs into DASH streams.

These components rely on **signals**, a modern C++ framework to build modular applications.

# Build

lldash can be built using `CMake` with presets and `vcpkg` to manage dependencies. Builds have been tested on Linux, Windows (64 bit Intel) and Mac (Intel or Silicon).

If you get the build working for Linux or Windows on arm64: please let us know.

## Build Prerequisites

### Windows (Intel 64 bit)

- Install Visual Studio 2022 (community edition is good enough)
  - Install at least the "Desktop Development with C++" tools.
  - You only really need the compilers for vcpkg to build some auxiliary tools, but its just as easy to install the whole visual studio.
- Optionally install Visual Studio Code from https://code.visualstudio.com/
  - Install the C++ extensions
  - Install the Python extensions
  - Install the cmake extensions
- Install git from https://git-scm.com/downloads/win
- Install CMake from https://cmake.org/download/ (64 bit version)
- Install MSYS2 from https://www.msys2.org/
  - By default MSYS2 will open a UCRT64 shell, but testing has been done with the MINGW64 shell and toolset.
    - For now we have opted to use MINGW64 and not UCRT64, but we may revisit that choice later.
  - In the MINGW64 shell, run `scripts/install_mingw64_prerequisites.sh`
  - Add `C:\msys64\mingw64\bin` and `C:\msys64\usr\bin` to your system-wide search path:
    - Open System Properties, Advanced, Environment Variables
    - Add to `Path` in the System Variables section.

### Mac (Intel or Silicon)

- Install `XCode`, or at least the developer tools.
- Install `Homebrew` from https://brew.sh
- Run `scripts/install_homebrew_prerequisites.sh`

### Linux (Intel)

These instructions have only been tested on Ubuntu 24.04 on Intel 64bit hardware. 
Please let us know if you get them working on other Linux distributions, or on Arm64 machines.

- Run `scripts/install_debian_prerequisites.sh`

## Building

You can build from the command line or from vscode. The first time you build will take very long (about 30 minutes) because `vcpkg` will have to build all of the dependency packages. These are cached, however, so subsequent builds will be a lot quicker.

Do not try to use the `CMake` GUI, it is known not to work.

Do not try to use another `vcpkg` installation than the one included as a submodule of this repo, it is known not to work.

> Or let us know that it _does_ work by posting an issue on github...

### Windows

In powershell, run `scripts\buildpackage.ps1`. You have to supply the preset you want to build (but these will be listed if you don't supply the argument).

This will build everything, install into `.\installed` and create an installable package.

### Linux, Mac

Run `scripts/buildpackage.sh`. You have to supply the preset you want to build (but these will be listed if you don't supply the argument).

This will build everything, install into `./installed` and create an installable package.

## Building with vscode

Use the `cmake: select preset` command to select your preset. (control-shift-P or command-shift-P allows you to run the command, or use the CMake sidebar)
Then use `cmake: configure`, `cmake: build`, `cmake: package`

## Testing your build

There is currently one integration test that creates a full pipeline, runs it for a while and then reports latency and frame loss. If this works it is a good indication that everything has build correctly.

### Windows

Use PowerShell, run

```
& tests\setup_test_environment.ps1
```

This downloads and installs the test prerequisites (mainly `cwipc`) and prepares the Python `venv` to run the tests.

Then run the test with

```
python .\tests\testlatency\testlatency.py --seg_dur 1000 --duration 30
```

### Mac, Linux

Run

```
source tests/setup_test_environment.sh
```

This downloads and installs the test prerequisites (mainly `cwipc`) and prepares the Python `venv` to run the tests. Note you must use `source` because `PATH` and some other environment variables are changed.

Then run the test with

```
python ./tests/testlatency/testlatency.py --seg_dur 1000 --duration 30
```

## Dependencies

Ensure you have all the necessary dependencies installed. You can use [`vcpkg`](https://github.com/microsoft/vcpkg) to manage dependencies.

## Configure the Project

Create a build directory and run CMake to configure the project using presets.

### Presets

The project uses CMake presets and `vcpkg` to build various components. Here are some of the available presets:

- `linux-production`: Build for production on Linux.
- `linux-develop`: Build for development on Linux.
- `mac-production`: Build for production on Mac.
- `mac-develop`: Build for development on Mac.
- `intelmac-production`: Build for production on Intel Mac.
- `intelmac-develop`: Build for development on Intel Mac.
- `mingw-production`: Build for production on Windows with MinGW.
- `mingw-develop`: Build for development on Windows with MinGW.

### Building the Package

To build the package, use the `buildpackage.sh` script. This script will update the repository, configure the project, build it, install it, and create a package using CPack.

usage: 

```
./scripts/buildpackage.sh preset

```
## Install the Project (optional)

You can install the built binaries as follows:

```
cmake --install build 
```

## Updating the vcpkg dependencies

Once in a while you should update the `vcpkg` dependencies to the latest version:

```
cd .\vcpkg
git checkout master
git pull
.\bootstrap-vcpkg.bat
cd ..
.\vcpkg\vcpkg x-update-baseline
.\vcpkg\vcpkg install --triplet=x64-linux-dynamic
git commit -a -m "Vcpkg packages updated to most recent version"
```

Replacing `x64-linux-dynamic` with whatever is the correct triplet for the platform you are on.

# Documentation

Documentation is both a set of markdown files and a doxygen. .

# Contributing

We welcome contributions to improve lldash. Please read the contributing guidelines before submitting a pull request.

# License

BSD-3 "New", see LICENSE file.
