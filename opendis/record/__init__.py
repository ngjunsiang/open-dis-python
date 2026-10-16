"""Record type classes for OpenDIS7.

This module defines classes for various record types used in DIS PDUs.
"""

from typing import TypeVar

from opendis.stream import DataInputStream, DataOutputStream
from opendis.types import (
    enum8,
    enum16,
    enum32,
    bf_enum,
    bf_int,
    bf_uint,
    float32,
    float64,
    struct8,
    uint8,
    uint16,
    uint32,
)

from . import base, bitfield, symbolic_names as sym
from .base import StandardVariableRecord
from .common import *
from .radio import *
from .warfare import *

SV = TypeVar("SV", bound=base.StandardVariableRecord)


__variableRecordClasses: dict[int, type[base.StandardVariableRecord]] = {
    3000: HighFidelityHAVEQUICKRadio,  # generated (radio)
    4000: DirectedEnergyPrecisionAimpoint,  # generated (warfare)
    4001: DirectedEnergyAreaAimpoint,  # generated (warfare)
    4500: DirectedEnergyDamage,  # generated (warfare)
}


def isKnownStandardVariableRecord(recordType: int) -> bool:
    """True when a typed decoder is registered for this record type [UID 66]."""
    return (
        isinstance(recordType, int)
        and recordType >= 0
        and recordType in __variableRecordClasses
    )


def getStandardVariableClass(
    recordType: int, expectedType: type[SV] = base.StandardVariableRecord
) -> type[SV]:
    """Return a StandardVariableRecord subclass for the given recordType."""

    # Declare a local class since the recordType class variable will need to be
    # set for each new unrecognised record type.
    class UnknownStandardVariableRecord(base.StandardVariableRecord):
        """A placeholder class for unrecognised Standard Variable Records."""

        recordType: enum32

        def __init__(self, data: bytes = b"") -> None:
            self.data = data

        def marshalledSize(self) -> uint16:
            return 6 + len(self.data)

        def serialize(self, outputStream: DataOutputStream) -> None:
            super().serialize(outputStream)
            outputStream.write_uint32(self.recordType)
            outputStream.write_uint16(self.recordLength)
            outputStream.write_bytes(self.data)

        def parse(self, inputStream: DataInputStream, bytelength: int) -> None:
            super().parse(inputStream, bytelength)
            # Subtract 6 bytes for type and length
            self.data = inputStream.read_bytes(bytelength - 6)

    if not isinstance(recordType, int) or recordType < 0:
        raise ValueError(
            f"recordType must be a non-negative integer, got {recordType!r}"
        )
    UnknownStandardVariableRecord.recordType = recordType
    vrClass = __variableRecordClasses.get(recordType, UnknownStandardVariableRecord)
    if not issubclass(vrClass, expectedType):
        raise TypeError(
            f"Record Type {recordType}: Record class {vrClass.__name__} is not "
            f"a subclass of {expectedType.__name__}"
        )
    return vrClass


def parseStandardVariableRecord(
    inputStream: DataInputStream,
) -> base.StandardVariableRecord:
    """Parse one uid-66 Standard Variable record from the stream.

    Consumes the record header (recordType u32 + recordLength u16,
    §6.2.83) and delegates the remainder to the registered class; an
    unregistered recordType parses as the opaque placeholder whose
    ``data`` preserves the raw bytes byte-exact. Record Length shall be
    a multiple of 8 (§6.2.83) — validated here once for every typed or
    placeholder decoder.
    """
    recordType = inputStream.read_uint32()
    recordLength = inputStream.read_uint16()
    if recordLength % 8 != 0:
        raise ValueError(f"recordLength must be a multiple of 8, got {recordLength!r}")
    vrClass = getStandardVariableClass(recordType)
    record = vrClass()
    record.parse(inputStream, recordLength)
    return record
