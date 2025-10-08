"""Entity Information/Interaction PDU record types"""

__all__ = [
    "ArticulatedPart",
    "AttachedPart",
    "VariableParameterRecord",
    "getVariableParameterClass",
    "appearance",
]

from typing import TypeVar

from opendis.record import base, bitfield
from opendis.record.common import *
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


VP = TypeVar('VP', bound="VariableParameterRecord")

# Interfaces

class VariableParameterRecord(base.Record):
    """6.2.94 Variable Parameter (VP) Record

    Additional information associated with an entity or detonation, not
    otherwise accounted for in a PDU,
    This record shall provide information on articulated parts, attached parts,
    and other data associated with an entity or detonation.
    This record shall be contained in the Variable Parameter records field of PDUs that have that field.
    One or more Variable Parameter records may be contained in the
    Variable Parameter records field up to the maximum size of the PDU.
    """
    recordType: enum8  # [UID 56]

    def marshalledSize(self) -> int:
        return 16

    def serialize(self, outputStream: DataOutputStream) -> None:
        super().serialize(outputStream)
        outputStream.write_uint8(self.recordType)


class ArticulatedPart(VariableParameterRecord):
    """6.2.94.2 Articulated Part VP Record

    Articulated parts for movable parts and a combination of moveable/attached
    parts of an entity.
    marshalledSize is 16 bytes as fixed by VariableParameterRecord.
    """
    recordType: enum8 = 0  # [UID 56]

    def __init__(self,
                 changeIndicator: uint8 = 0,
                 partAttachedTo: uint16 = 0,
                 parameterType: enum32 = 0,  # [UID 58-59]
                 parameterValue: float32 = 0):
        self.changeIndicator = changeIndicator
        """indicate the change of any parameter for any articulated part. Starts at zero, incremented for each change"""
        self.partAttachedTo = partAttachedTo
        """the identification of the articulated part to which this articulation parameter is attached. This field shall be specified by a 16-bit unsigned integer. This field shall contain the value zero if the articulated part is attached directly to the entity."""
        self.parameterType = parameterType
        """the type of parameter represented, 32 bit enumeration"""
        self.parameterValue = parameterValue
        """The definition of the 64 bits shall be determined based on the type of parameter specified in the Parameter Type field"""
        # TODO: Further decompose parameterValue into typeClass and typeMetric

    def serialize(self, outputStream: DataOutputStream) -> None:
        super().serialize(outputStream)
        outputStream.write_uint8(self.changeIndicator)
        outputStream.write_uint16(self.partAttachedTo)
        outputStream.write_uint32(self.parameterType)
        outputStream.write_float32(self.parameterValue)

    def parse(self, inputStream: DataInputStream) -> None:
        """Assume recordType has already been read from the stream."""
        self.changeIndicator = inputStream.read_uint8()
        self.partAttachedTo = inputStream.read_uint16()
        self.parameterType = inputStream.read_uint32()
        self.parameterValue = inputStream.read_float32()


class AttachedPart(VariableParameterRecord):
    """6.2.94.3 Attached Part VP Record
    
    Removable parts that may be attached to an entity.
    marshalledSize is 16 bytes as fixed by VariableParameterRecord.
    """
    recordType: enum8 = 1  # [UID 56]

    def __init__(self,
                 detachedIndicator: enum8 = 0,  # [UID 415]
                 partAttachedTo: uint16 = 0,
                 parameterType: enum32 = 0,  # [UID 57]
                 attachedPartType: EntityType | None = None):
        self.detachedIndicator = detachedIndicator
        """0 = attached, 1 = detached. See I.2.3.1 for state transition diagram"""
        self.partAttachedTo = partAttachedTo
        """the identification of the articulated part to which this articulation parameter is attached. This field shall be specified by a 16-bit unsigned integer. This field shall contain the value zero if the articulated part is attached directly to the entity."""
        self.parameterType = parameterType
        """The location or station to which the part is attached"""
        self.attachedPartType = attachedPartType or EntityType()
        """The definition of the 64 bits shall be determined based on the type of parameter specified in the Parameter Type field"""

    def serialize(self, outputStream: DataOutputStream) -> None:
        super().serialize(outputStream)
        outputStream.write_uint8(self.detachedIndicator)
        outputStream.write_uint16(self.partAttachedTo)
        outputStream.write_uint32(self.parameterType)
        outputStream.write_float32(self.parameterValue)

    def parse(self, inputStream: DataInputStream) -> None:
        """Assume recordType has already been read from the stream."""
        self.recordType = inputStream.read_uint8()  # TODO: validate
        self.detachedIndicator = inputStream.read_uint8()
        self.partAttachedTo = inputStream.read_uint16()
        self.parameterType = inputStream.read_uint32()
        self.parameterValue = inputStream.read_float32()


# [UID 56] Variable Parameter Record types
__variableParameterClasses: dict[int, type[VariableParameterRecord]] = {
    0: ArticulatedPart,
    1: AttachedPart,
}

def getVariableParameterClass(recordType: int) -> type[VariableParameterRecord]:
    """Return a VariableParameterRecord subclass for the given recordType."""

    # Declare a local class since the recordType class variable will need to be
    # set for each new unrecognised record type.
    class UnknownVariableParameterRecord(VariableParameterRecord):
        """A placeholder class for unrecognised Variable Parameter Records."""
        recordType: enum32

        def __init__(self, data: bytes = b'\0' * 16) -> None:
            self.data = data

        def serialize(self, outputStream: DataOutputStream) -> None:
            super().serialize(outputStream)
            outputStream.write_bytes(self.data)

        def parse(self, inputStream: DataInputStream) -> None:
            super().parse(inputStream)
            # Subtract 6 bytes for type and length
            self.data = inputStream.read_bytes(self.marshalledSize())

    if not isinstance(recordType, int) or recordType < 0:
        raise ValueError(
            f"recordType must be a non-negative integer, got {recordType!r}"
        )
    vrClass = __variableParameterClasses.get(
        recordType,
        UnknownVariableParameterRecord
    )
    if isinstance(vrClass, UnknownVariableParameterRecord):
        vrClass.recordType = recordType
    assert issubclass(vrClass, VariableParameterRecord)  # for static checkers
    return vrClass
