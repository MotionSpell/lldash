#!/bin/sh
pacman --sync --refresh --needed --noconfirm \
    base-devel  \
    mingw-w64-x86_64-toolchain \
    mingw-w64-x86_64-toolchain \
    mingw-w64-x86_64-cmake \
    mingw-w64-x86_64-ninja \
    mingw-w64-x86_64-pkgconf \
    mingw-w64-x86_64-nasm \
    mingw-w64-x86_64-yasm \
    mingw-w64-x86_64-autotools \
    mingw-w64-x86_64-gcc \
    git \
    make \
    curl \
    mingw-w64-x86_64-libtool \
    mingw-w64-x86_64-python3 \
    mingw-w64-x86_64-python-pip \
    mingw-w64-x86_64-ca-certificates \
    mingw-w64-x86_64-freetype