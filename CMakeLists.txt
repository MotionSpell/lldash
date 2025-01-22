cmake_minimum_required(VERSION 3.28)

# Add extension directories (for things like Find<package>)
set(CMAKE_MODULE_PATH
${CMAKE_CURRENT_LIST_DIR}/CMakeFiles
${CMAKE_CURRENT_LIST_DIR}/signals/CMakeFiles
${CMAKE_MODULE_PATH}
	)

# Get version from git if not specified on the command line
if(NOT LLDASH_VERSION)
	include(GetGitVersion)
	get_git_version(VERSION_VAR LLDASH_VERSION)
endif()
if(LLDASH_VERSION)
	message(STATUS "LLDASH_VERSION=${LLDASH_VERSION}")
	add_compile_definitions(LLDASH_VERSION=${LLDASH_VERSION})
	set(ENV{LLDASH_VERSION} ${LLDASH_VERSION})
	# Remove patch from version before we pass it to the project VERSION argument (it doesn't understand)
	string(REGEX REPLACE "\\+.*" "" LLDASH_BASE_VERSION ${LLDASH_VERSION})
endif()


project(lldash VERSION ${LLDASH_BASE_VERSION})

# Include macros that help with installing
include(SignalsMacros)

# Set the C++ standard
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

#
# Note that this umbrella project is intended for building executables and dynamic libraries that will
# be packaged all together, in isolation from the rest of the system, *not* for building and installing into
# the normal places. We copy all the needed dynamic libraries into our $prefix installation directory, which
# is generally not what you want to do for a system-wide installation.
#
# Some options we want for everything.
# On MacOS, we want to use the RPATH to find libraries.
set(CMAKE_MACOSX_RPATH ON)
# On rpath-supporting systems (MacOS, Linux) we keep the dynamic libraries in ../lib
if (CMAKE_SYSTEM_NAME STREQUAL "Darwin")
    set(CMAKE_INSTALL_RPATH "@loader_path;@loader_path/../lib")
elseif (CMAKE_SYSTEM_NAME STREQUAL "Linux")
    set(CMAKE_INSTALL_RPATH "\$ORIGIN;\$ORIGIN/../lib")
endif()

# Some submodules can also be built independenty. This variable signals that we are now
# building the lldash umbrella project.
set(LLDASH_UMBRELLA_BUILD ON)

# Find some packages that we need all over the place. We do this early, so any problems appear early.
find_package(PkgConfig REQUIRED)
find_package(OpenSSL REQUIRED)
find_package(SDL2 REQUIRED)
find_package(libjpeg-turbo REQUIRED)
find_package(CURL REQUIRED)
find_package(FFmpeg REQUIRED COMPONENTS AVUTIL AVFILTER AVCODEC AVFORMAT AVDEVICE SWSCALE SWRESAMPLE)
find_package(GPAC QUIET)
if (NOT TARGET gpac::gpac)
    find_package(GPAC QUIET)
    if (NOT GPAC_FOUND)
        # Find it using pkgconfig, for now.
        # This is a huge hack, especially the way we get the windows IMPORTED_LOCATION
        pkg_check_modules(GPAC REQUIRED gpac)
        add_library(gpac::gpac SHARED IMPORTED)
        if(${CMAKE_SYSTEM_NAME} STREQUAL "Windows")
            # xxxjack this is valid for mingw.
            set_target_properties(gpac::gpac PROPERTIES
                IMPORTED_IMPLIB "${GPAC_LIBDIR}/libgpac.dll.a"
                IMPORTED_LOCATION "${GPAC_LIBDIR}/../bin/libgpac.dll"
                INTERFACE_INCLUDE_DIRECTORIES "${GPAC_INCLUDEDIR}"
            )
        else()
            set_target_properties(gpac::gpac PROPERTIES
                IMPORTED_LOCATION "${GPAC_LIBDIR}/${CMAKE_SHARED_LIBRARY_PREFIX}gpac${CMAKE_SHARED_LIBRARY_SUFFIX}"
                INTERFACE_INCLUDE_DIRECTORIES "${GPAC_INCLUDEDIR}"
            )
        endif()
        set(GPAC_FOUND TRUE)
    endif()
endif()

# Add all the source subdirectories
add_subdirectory(lldash-relay)
add_subdirectory(signals)
add_subdirectory(lldash-srd-packager)
add_subdirectory(lldash-playout)

# And create the installer
set(CPACK_GENERATOR TGZ)
set(CPACK_PACKAGE_VENDOR "Motion Spell, CWI DIS Group")
set(CPACK_PACKAGE_CONTACT "Jack.Jansen@cwi.nl")
set(CPACK_PACKAGE_VERSION ${LLDASH_BASE_VERSION})
#set(CPACK_RESOURCE_FILE_LICENSE "${CMAKE_CURRENT_SOURCE_DIR}/LICENSE.txt")
#set(CPACK_RESOURCE_FILE_README "${CMAKE_CURRENT_SOURCE_DIR}/readme.md")
#set(CPACK_RESOURCE_FILE_WELCOME "${CMAKE_CURRENT_SOURCE_DIR}/readme.md")
set(CPACK_OUTPUT_FILE_PREFIX "${CMAKE_CURRENT_BINARY_DIR}/package")
set(CPACK_PACKAGE_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR})
string(TOLOWER ${CMAKE_SYSTEM_PROCESSOR} _arch)
string(TOLOWER ${CMAKE_SYSTEM_NAME} _sys)
string(TOLOWER ${PROJECT_NAME} _project_lower)
set(CPACK_PACKAGE_FILE_NAME "${_project_lower}-${_sys}-${_arch}-${LLDASH_VERSION}")
set(CPACK_SOURCE_PACKAGE_FILE_NAME "${_project_lower}-${LLDASH_VERSION}-source")
#
## not .gitignore as its regex syntax is distinct
#file(READ ${CMAKE_CURRENT_LIST_DIR}/.cpack_ignore _cpack_ignore)
#string(REGEX REPLACE "\n" ";" _cpack_ignore ${_cpack_ignore})
#set(CPACK_SOURCE_IGNORE_FILES "${_cpack_ignore};vcpkg/buildtrees;vcpkg/packages;vcpkg/downloads")
#
#install(FILES ${CPACK_RESOURCE_FILE_README} ${CPACK_RESOURCE_FILE_LICENSE}
#  DESTINATION share/docs/${PROJECT_NAME})

include(CPack)
