# lldash

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

- **signals**: A modern C++ framework to build modular applications.
- **lldash-relay**: A low-latency HTTP server for relaying DASH streams.
- **lldash-playout**: A component for receiving compressed video from the network.
- **lldash-srd-packager**: A component for packaging point clouds and TVMs into DASH streams.

# Build

lldash can be built using `CMake` with presets and `vcpkg` to manage dependencies. Builds have been tested on Linux, Windows (64 bit Intel) and Mac (Intel or Silicon).

If you get the build working for Linux or Windows on Arm64: please let us know.

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
  - In the MINGw64 shell, run `scripts/install_mingw64_prerequisites.sh`
  - Add `C:\msys64\mingw64\bin` to your system-wide search path:
    - Open System Properties, Advanced, Environment Variables
    - Add to `Path` in the System Variables section.

### Mac (Intel or Silicon)

To be provided

### Linux (Intel)

To be provided

## Building from the command line

to be provided

### Windows

to be provided

### Linux, Mac

to be provided

## Building with vscode

to be provided

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




