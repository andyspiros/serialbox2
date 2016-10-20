#!/usr/bin/python3
# -*- coding: utf-8 -*-
##===-----------------------------------------------------------------------------*- Python -*-===##
##
##                                   S E R I A L B O X
##
## This file is distributed under terms of BSD license. 
## See LICENSE.txt for more information.
##
##===------------------------------------------------------------------------------------------===##
##
## This file contains the Serializer implementation of the Python Interface.
##
##===------------------------------------------------------------------------------------------===##

from ctypes import c_char_p, c_void_p, c_int, Structure, POINTER

from .archive import Archive
from .common import get_library, extract_string
from .error import invoke, SerialboxError
from .fieldmetainfo import FieldMetaInfo, FieldMetaInfoImpl
from .metainfomap import MetaInfoMap, MetaInfoImpl, ArrayOfStringImpl
from .savepoint import Savepoint, SavepointImpl
from .type import *
import numpy as np

lib = get_library()


class SerializerImpl(Structure):
    """ Mapping of serialboxSerializer_t """
    _fields_ = [("impl", c_void_p), ("ownsData", c_int)]


def register_library(library):
    #
    # Construction & Destruction
    #
    library.serialboxSerializerCreate.argtypes = [c_int, c_char_p, c_char_p, c_char_p]
    library.serialboxSerializerCreate.restype = POINTER(SerializerImpl)

    library.serialboxSerializerDestroy.argtypes = [POINTER(SerializerImpl)]
    library.serialboxSerializerDestroy.restype = None

    #
    # Utility
    #
    library.serialboxSerializerGetMode.argtypes = [POINTER(SerializerImpl)]
    library.serialboxSerializerGetMode.restype = c_int

    library.serialboxSerializerGetDirectory.argtypes = [POINTER(SerializerImpl)]
    library.serialboxSerializerGetDirectory.restype = c_char_p

    library.serialboxSerializerGetPrefix.argtypes = [POINTER(SerializerImpl)]
    library.serialboxSerializerGetPrefix.restype = c_char_p

    library.serialboxSerializerUpdateMetaData.argtypes = [POINTER(SerializerImpl)]
    library.serialboxSerializerUpdateMetaData.restype = None

    library.serialboxEnableSerialization.argtypes = None
    library.serialboxEnableSerialization.restype = None

    library.serialboxDisableSerialization.argtypes = None
    library.serialboxDisableSerialization.restype = None

    library.serialboxSerializationStatus.argtypes = None
    library.serialboxSerializationStatus.restype = c_int

    #
    # Global Meta-information
    #
    library.serialboxSerializerGetGlobalMetaInfo.argtypes = [POINTER(SerializerImpl)]
    library.serialboxSerializerGetGlobalMetaInfo.restype = POINTER(MetaInfoImpl)

    #
    #  Register and Query Savepoints
    #
    library.serialboxSerializerAddSavepoint.argtypes = [POINTER(SerializerImpl),
                                                        POINTER(SavepointImpl)]
    library.serialboxSerializerAddSavepoint.restype = c_int

    library.serialboxSerializerHasSavepoint.argtypes = [POINTER(SerializerImpl),
                                                        POINTER(SavepointImpl)]
    library.serialboxSerializerHasSavepoint.restype = c_int

    library.serialboxSerializerGetNumSavepoints.argtypes = [POINTER(SerializerImpl)]
    library.serialboxSerializerGetNumSavepoints.restype = c_int

    library.serialboxSerializerGetSavepointVector.argtypes = [POINTER(SerializerImpl)]
    library.serialboxSerializerGetSavepointVector.restype = POINTER(POINTER(SavepointImpl))

    library.serialboxSerializerDestroySavepointVector.argtypes = [POINTER(POINTER(SavepointImpl)),
                                                                  c_int]
    library.serialboxSerializerDestroySavepointVector.restype = None

    library.serialboxSerializerGetFieldnamesAtSavepoint.argtypes = [POINTER(SerializerImpl),
                                                                    POINTER(SavepointImpl)]
    library.serialboxSerializerGetFieldnamesAtSavepoint.restype = POINTER(ArrayOfStringImpl)

    library.serialboxSavepointCreateFromSavepoint.argtypes = [POINTER(SavepointImpl)]
    library.serialboxSavepointCreateFromSavepoint.restype = POINTER(SavepointImpl)

    #
    #  Register and Query Fields
    #
    library.serialboxSerializerAddField.argtypes = [POINTER(SerializerImpl), c_char_p,
                                                    POINTER(FieldMetaInfoImpl)]
    library.serialboxSerializerAddField.restype = c_int

    library.serialboxSerializerHasField.argtypes = [POINTER(SerializerImpl), c_char_p]
    library.serialboxSerializerHasField.restype = c_int

    library.serialboxSerializerGetFieldMetaInfo.argtypes = [POINTER(SerializerImpl), c_char_p]
    library.serialboxSerializerGetFieldMetaInfo.restype = POINTER(FieldMetaInfoImpl)

    library.serialboxSerializerGetFieldnames.argtypes = [POINTER(SerializerImpl)]
    library.serialboxSerializerGetFieldnames.restype = POINTER(ArrayOfStringImpl)

    #
    # Writing & Reading
    #
    library.serialboxSerializerWrite.argtypes = [POINTER(SerializerImpl),
                                                 c_char_p,
                                                 POINTER(SavepointImpl),
                                                 c_void_p,
                                                 POINTER(c_int),
                                                 c_int]
    library.serialboxSerializerWrite.restype = None

    library.serialboxSerializerRead.argtypes = [POINTER(SerializerImpl),
                                                c_char_p,
                                                POINTER(SavepointImpl),
                                                c_void_p,
                                                POINTER(c_int),
                                                c_int]
    library.serialboxSerializerRead.restype = None

    #
    # Array
    #
    library.serialboxArrayOfStringDestroy.argtypes = [POINTER(ArrayOfStringImpl)]
    library.serialboxArrayOfStringDestroy.restype = None


class Serializer(object):
    """Serializer implementation of the Python Interface.
    """

    def __init__(self, mode, directory, prefix, archive="Binary"):
        """Initialize the Serializer and prepare it to perform input/output operations.

        The serializer is attached to a specific `directory` and to a specific `prefix`, with which
        all files read and written will start. There are three modes to open a serializer: `Read`,
        `Write` and `Append` (see :class:`OpenModeKind`). `Read` will give a read-only access to the
        serialized data; `Write` will erase all files of a previous run of a serializer with same
        `directory` and `prefix`; `Append` will import all existing information and allow the user
        to add more data.

        :param mode: Mode of the Serializer
        :type mode: OpenModeKind
        :param directory: The directory where the files will be stored (will be created if
                          necessary)
        :type directory: str
        :param prefix: The prefix of the files
        :type prefix: str
        :param archive: String used to construct the Archive
                        (see :func:`serialbox.Archive.registered_archives`)
        :type archive: str
        """
        self.__serializer = None

        #
        # Convert mode
        #
        if isinstance(mode, OpenModeKind):
            mode = mode.value
        modeint = c_int(mode)

        #
        # Validate archive
        #
        archives = Archive.registered_archives()
        if archive not in archives:
            raise SerialboxError(
                "'%s' is not a valid archive. Registered archives: %s" % (archive, archives))

        #
        # Create serializer
        #
        dirstr = extract_string(directory)[0]
        prefixstr = extract_string(prefix)[0]
        archivestr = extract_string(archive)[0]

        self.__serializer = invoke(lib.serialboxSerializerCreate, modeint, dirstr, prefixstr,
                                   archivestr)

    # ===----------------------------------------------------------------------------------------===
    #   Utility
    # ==-----------------------------------------------------------------------------------------===

    @property
    def mode(self):
        """Return mode of the Serializer.

        :return: Mode of the Serializer
        :rtype: OpenModeKind
        """
        return OpenModeKind(invoke(lib.serialboxSerializerGetMode, self.__serializer))

    @property
    def prefix(self):
        """Return the prefix of all filenames.

        :return: prefix of all filenames
        :rtype: str
        """
        return invoke(lib.serialboxSerializerGetPrefix, self.__serializer).decode()

    @property
    def directory(self):
        """Return the directory of the Serializer.

        :return: directory of the Serializer
        :rtype: str
        """
        return invoke(lib.serialboxSerializerGetDirectory, self.__serializer).decode()

    def update_meta_data(self):
        """ Write meta-data to disk.
        """
        invoke(lib.serialboxSerializerUpdateMetaData, self.__serializer)

    @staticmethod
    def enable():
        """Enable serialization.

        Serialization is enabled by default, but it can be disabled either by setting the
        environment variable `STELLA_SERIALIZATION_DISABLE` to a positive value or by calling the
        funcion :func:`Serializer.disable`. With this function you enable the serialization
        independently of the current environment.

        The serialization can be only globally enabled or disabled. There is no way to enable or
        disable only a specific serializer.
        """
        invoke(lib.serialboxEnableSerialization)

    @staticmethod
    def disable():
        """Disable serialization.

        Serialization is enabled by default, but it can be disabled either by setting the
        environment variable `STELLA_SERIALIZATION_DISABLE` to a positive value or by calling the
        funcion :func:`Serializer.disable`. With this function you disable the serialization
        independently of the current environment.

        The serialization can be only globally enabled or disabled. There is no way to enable or
        disable only a specific serializer.
        """
        invoke(lib.serialboxDisableSerialization)

    @staticmethod
    def status():
        """Get the status of serialization

        The status is represented as an integer which can take the following values:

        - 0: the variable is not yet initialized i.e the serialization is enabled if the environment
          variable `STELLA_SERIALIZATION_DISABLE` or `SERIALBOX_SERIALIZATION_DISABLE` is not set
          to a positive value. The first Serializer which is initialized has to set this value
          either to +1 or to -1 according to the environment.
        - +1: the serialization is enabled, independently of the environment
        - -1: the serialization is disabled, independently of the environment

        See :func:`Serializer.enable` and :func:`Serializer.disable`.

        :return: serialization status
        :rtype: int
        """
        return int(invoke(lib.serialboxSerializationStatus))

    # ===----------------------------------------------------------------------------------------===
    #   Global Meta-information
    # ==-----------------------------------------------------------------------------------------===

    @property
    def global_metainfo(self):
        """Global meta-information of the serializer.

        :return: Refrence to the meta-information map
        :rtype: MetaInfoMap
        """
        return MetaInfoMap(impl=invoke(lib.serialboxSerializerGetGlobalMetaInfo, self.__serializer))

    # ===----------------------------------------------------------------------------------------===
    #    Register and Query Savepoints
    # ==-----------------------------------------------------------------------------------------===

    def register_savepoint(self, savepoint):
        """Register savepoint `savepoint` within the Serializer.

        :param savepoint: Savepoint to add
        :type savepoint: Savepoint
        :raises SerialboxError: Savepoint already exists within the Serializer
        """
        if not invoke(lib.serialboxSerializerAddSavepoint, self.__serializer, savepoint.impl()):
            raise SerialboxError(
                "savepoint '%s' already exists withing the Serializer" % (savepoint.__str__()))

    def has_savepoint(self, savepoint):
        """Check if `savepoint` exists in the Serializer.

        :param savepoint: Savepoint to search for
        :type savepoint: Savepoint

        :return: True if Savepoint exists, False otherwise
        :rtype: bool
        """
        return bool(
            invoke(lib.serialboxSerializerHasSavepoint, self.__serializer, savepoint.impl()))

    def get_savepoint(self, name):
        """Get a list of Savepoint(s) identified by `name` in the order they were registered

        Savepoints can have the same `name` but their meta-data has to be different.

        :param name: Name of the savepoint(s)
        :type name: str
        :return: List of registered Savepoint(s) identified  by `name`
        :rtype: list[Savepoint]
        """
        return [sp for sp in self.savepoints() if sp.name == name]

    def fields_at_savepoint(self, savepoint):
        """Get a list of the registered fieldnames at `savepoint`.

        :param savepoint: Savepoint to use
        :type savepoint: Savepoint
        :return: list of fieldsnames
        :rtype: list[str]
        :raises SerialboxError: Savepoint does not exists
        """
        array = invoke(lib.serialboxSerializerGetFieldnamesAtSavepoint, self.__serializer,
                       savepoint.impl())
        list_array = []
        for i in range(array.contents.len):
            list_array += [array.contents.data[i].decode()]
        invoke(lib.serialboxArrayOfStringDestroy, array)
        return list_array

    def savepoints(self):
        """ Get a list of registered savepoints within the Serializer.

        The Savepoints in the list are copy-constructed from the Savepoints in the Serializer and
        inserted in the order they were registered.

        :return: List of registered savepoints
        :rtype: list[Savepoint]
        """
        vec_savepoint = lib.serialboxSerializerGetSavepointVector(self.__serializer)
        num_savepoints = lib.serialboxSerializerGetNumSavepoints(self.__serializer)

        list_savepoint = []
        for i in range(num_savepoints):
            list_savepoint += [Savepoint('',
                                         impl=invoke(lib.serialboxSavepointCreateFromSavepoint,
                                                     vec_savepoint[i].contents))]
        invoke(lib.serialboxSerializerDestroySavepointVector, vec_savepoint, num_savepoints)
        return list_savepoint

    # ===----------------------------------------------------------------------------------------===
    #    Register and Query Fields
    # ==-----------------------------------------------------------------------------------------===

    def register_field(self, name, fieldmetainfo):
        """Add field given by `name` with field meta-information `fieldmetainfo` to the Serializer.

        :param name: Name of the newly registered field
        :type name: str
        :param fieldmetainfo: Field meta-information of the newly registered field
        :type fieldmetainfo: FieldMetaInfo

        :raises SerialboxError: Field with given name already exists within the Serializer
        """
        namestr = extract_string(name)[0]
        if not invoke(lib.serialboxSerializerAddField, self.__serializer, namestr,
                      fieldmetainfo.impl()):
            raise SerialboxError("field '%s' already exists withing the Serializer" % name)

    def has_field(self, field):
        """Check if `field` is registered within the Serializer.

        :param field: Name of the field to check for
        :type field: str
        :return: True if field exists, False otherwise
        :rtype: bool
        """
        fieldstr = extract_string(field)[0]
        return bool(invoke(lib.serialboxSerializerHasField, self.__serializer, fieldstr))

    def get_field_metainfo(self, field):
        """Get the :class:`FieldMetaInfo` of `field`.

        :param field: Name of the field
        :type field: str
        :return: Copy of the field meta-information of `field`
        :rtype: FieldMetaInfo
        :raises SerialboxError: `field` does not exist within the Serializer
        """
        fieldstr = extract_string(field)[0]
        return FieldMetaInfo(None, [],
                             impl=invoke(lib.serialboxSerializerGetFieldMetaInfo, self.__serializer,
                                         fieldstr))

    def fieldnames(self):
        """Get a list of registered fieldnames within the Serializer.

        :return: list of fieldsnames
        :rtype: list[str]
        """
        array = invoke(lib.serialboxSerializerGetFieldnames, self.__serializer)
        list_array = []
        for i in range(array.contents.len):
            list_array += [array.contents.data[i].decode()]
        invoke(lib.serialboxArrayOfStringDestroy, array)
        return list_array

    # ===----------------------------------------------------------------------------------------===
    #    Writing & Reading
    # ==-----------------------------------------------------------------------------------------===

    def write(self, name, field, savepoint, register_field=True):
        """ Serialize `field` identified by `name` at `savepoint` to disk

        The `savepoint` will be registered at field `name` if not yet present. If `register_field`
        is True, the field will be registered if necessary.

        :param name: Name of the field
        :type name: str
        :param field: Field to serialize
        :type field: numpy.array
        :param savepoint: Savepoint to at which the field will be serialized
        :type savepoint: Savepoint
        :param register_field: Register the field if not present
        :type register: bool

        :raises SerialboxError: Serialization failed
        """
        if self.mode == OpenModeKind.Read:
            raise SerialboxError("write operations are not permitted in OpenModeKind.Read")

        if not self.has_field(name):
            if register_field:
                info = FieldMetaInfo(numpy2TypeID(field.dtype), list(field.shape))
                self.register_field(name, info)
            else:
                raise SerialboxError("field '%s' is not registered within the Serializer" % name)

        #
        # Extract strides and convert to unit-strides
        #
        strides = (c_int * len(field.strides))()
        for i in range(len(field.strides)):
            strides[i] = int(field.strides[i] / field.dtype.itemsize)
        num_strides = c_int(len(field.strides))

        #
        # Write to disk
        #
        origin_ptr = c_void_p(field.ctypes.data)
        namestr = extract_string(name)[0]
        invoke(lib.serialboxSerializerWrite, self.__serializer, namestr, savepoint.impl(),
               origin_ptr, strides, num_strides)

    def read(self, name, savepoint):
        """ Deserialize `field` identified by `name` at `savepoint` from disk

        The method will allocate a `numpy.array` with the registered dimensions and type and fill it
        with the specified data from disk.

        :param name: Name of the field
        :type name: str
        :param savepoint: Savepoint to at which the field will be serialized
        :type savepoint: Savepoint

        :return: Newly allocated and deserialized field
        :rtype: numpy.array

        :raises SerialboxError: Deserialization failed
        """
        if self.mode != OpenModeKind.Read:
            raise SerialboxError("read operations are not permitted in OpenModeKind.%s" % self.mode)

        if not self.has_field(name):
            raise SerialboxError("field '%s' is not registered within the Serializer" % name)

        info = self.get_field_metainfo(name)
        field = np.ndarray(shape=info.dims, dtype=typeID2numpy(info.type))

        #
        # Extract strides and convert to unit-strides
        #
        strides = (c_int * len(field.strides))()
        for i in range(len(field.strides)):
            strides[i] = int(field.strides[i] / field.dtype.itemsize)
        num_strides = c_int(len(field.strides))

        #
        # Write to disk
        #
        origin_ptr = c_void_p(field.ctypes.data)
        namestr = extract_string(name)[0]
        invoke(lib.serialboxSerializerRead, self.__serializer, namestr, savepoint.impl(),
               origin_ptr, strides, num_strides)

        return field

    def __del__(self):
        if self.__serializer:
            invoke(lib.serialboxSerializerDestroy, self.__serializer)


register_library(lib)
