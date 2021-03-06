##===------------------------------------------------------------------------------*- CMake -*-===##
##
##                                   S E R I A L B O X
##
## This file is distributed under terms of BSD license.
## See LICENSE.txt for more information.
##
##===------------------------------------------------------------------------------------------===##

cmake_minimum_required(VERSION 3.1)

## Install ppser
install(
  FILES ${CMAKE_SOURCE_DIR}/src/serialbox-python/pp_ser/pp_ser.py
  DESTINATION python/pp_ser
  PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE
  )

## Install serialbox
if(SERIALBOX_ENABLE_PYTHON)
  if(NOT(SERIALBOX_ENABLE_C))
    message(FATAL_ERROR
            "Python Interface requires the C Interface (set SERIALBOX_ENABLE_C=ON)")
  endif()

  if(NOT(SERIALBOX_BUILD_SHARED))
    message(FATAL_ERROR
            "Python Interface requires shared libraries (set SERIALBOX_BUILD_SHARED=ON)")
  endif()

  file(GLOB_RECURSE SERIALBOX_PYTHON_SOURCE
       ${CMAKE_SOURCE_DIR}/src/serialbox-python/
       ${CMAKE_SOURCE_DIR}/src/serialbox-python/*.py
       ${CMAKE_SOURCE_DIR}/src/serialbox-python/serialbox/*.py)

  # Copy serialbox python code to python build dir (this will fail if there are "dead" symlinks to
  # libSerialboxC.so/.dylib in the source tree from other builds, thus we scan for broken links
  # first)
  if(SERIALBOX_COMPILER_MSVC)
    set(REMOVE_OBSOLETE_SYMLINKS_OR_NOP rem) # nop
  else()
    if(APPLE)
        set(REMOVE_OBSOLETE_SYMLINKS_OR_NOP
            find -L ${CMAKE_SOURCE_DIR}/src/serialbox-python/serialbox -type l -exec rm -- {} +)
    else()
        set(REMOVE_OBSOLETE_SYMLINKS_OR_NOP
            find -L ${CMAKE_SOURCE_DIR}/src/serialbox-python/serialbox -type l -delete)
    endif()
  endif()

  add_custom_target(SerialboxPython
                    COMMAND ${REMOVE_OBSOLETE_SYMLINKS_OR_NOP}
                    COMMAND ${CMAKE_COMMAND} -E copy_directory
                    ${CMAKE_SOURCE_DIR}/src/serialbox-python/serialbox
                    ${CMAKE_BINARY_DIR}/src/serialbox-python/serialbox
                    DEPENDS "${SERIALBOX_PYTHON_SOURCE}")
  add_dependencies(SerialboxCLibraryShared SerialboxPython)

  # Install python source
  install(DIRECTORY ${CMAKE_SOURCE_DIR}/src/serialbox-python/serialbox/
          DESTINATION python/serialbox
          FILES_MATCHING PATTERN "*.py"
          PATTERN "*__pycache__*" EXCLUDE)

  # Create a symlink (or copy) the serialboxC shared library
  if(SERIALBOX_COMPILER_MSVC)
    install(CODE "
      EXECUTE_PROCESS(COMMAND
        \"${CMAKE_COMMAND}\" -E copy
        \"${CMAKE_INSTALL_PREFIX}/lib/SerialboxC${CMAKE_SHARED_LIBRARY_SUFFIX}\"
        \"${CMAKE_INSTALL_PREFIX}/python/serialbox/SerialboxC${CMAKE_SHARED_LIBRARY_SUFFIX}\")
    ")
  else()
    install(CODE "
      EXECUTE_PROCESS(COMMAND
        ln -sf
        ${CMAKE_INSTALL_PREFIX}/lib/libSerialboxC${CMAKE_SHARED_LIBRARY_SUFFIX}
        ${CMAKE_INSTALL_PREFIX}/python/serialbox/libSerialboxC${CMAKE_SHARED_LIBRARY_SUFFIX})
    ")
  endif()

endif()

## Install sdb
if(SERIALBOX_ENABLE_SDB)

  if(NOT(SERIALBOX_ENABLE_PYTHON))
    message(FATAL_ERROR
            "sdb requires the Python interface (set SERIALBOX_ENABLE_PYTHON=ON)")
  endif()

  file(GLOB_RECURSE SDB_PYTHON_SOURCE
       ${CMAKE_SOURCE_DIR}/src/serialbox-python/
       ${CMAKE_SOURCE_DIR}/src/serialbox-python/*.py
       ${CMAKE_SOURCE_DIR}/src/serialbox-python/sdb/*.py)

  add_custom_target(sdbPython
                    COMMAND ${CMAKE_COMMAND} -E copy_directory
                    ${CMAKE_SOURCE_DIR}/src/serialbox-python/sdb
                    ${CMAKE_BINARY_DIR}/src/serialbox-python/sdb
                    DEPENDS "${SDB_PYTHON_SOURCE}")
  add_dependencies(SerialboxPython sdbPython)

  # Install python source
  install(DIRECTORY ${CMAKE_SOURCE_DIR}/src/serialbox-python/sdb/
          DESTINATION python/sdb
          FILES_MATCHING PATTERN "*.py" PATTERN "*.png"
          PATTERN "*__pycache__*" EXCLUDE)

endif()
