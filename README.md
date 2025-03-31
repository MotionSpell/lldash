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

lldash can be built using CMake with presets and `vcpkg` to manage dependencies. Below are the instructions for building the project.

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


# Documentation

Documentation is both a set of markdown files and a doxygen. .

# Contributing

We welcome contributions to improve lldash. Please read the contributing guidelines before submitting a pull request.

# License




