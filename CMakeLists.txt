cmake_minimum_required(VERSION 3.28)

project(lldash VERSION 1.0)
# Add extension directories (for things like Find<package>)
set(CMAKE_MODULE_PATH
	${CMAKE_CURRENT_LIST_DIR}/signals/CMakeFiles
	${CMAKE_MODULE_PATH}
	)
    
include(SignalsMacros)

    # Set the C++ standard
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(LLDASH_UMBRELLA_BUILD ON)

find_package(PkgConfig REQUIRED)
find_package(openssl REQUIRED)
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
add_subdirectory(evanescent)
add_subdirectory(signals)
add_subdirectory(HelloSignals)
add_subdirectory(bin2dash)
add_subdirectory(sub)
