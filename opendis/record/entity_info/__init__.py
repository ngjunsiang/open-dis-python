"""Entity Information/Interaction PDU record types"""

__all__ = [
    "ArticulatedPart",
    "AttachedPart",
    "SilentEntitySystem",
    "VariableParameterRecord",
    "appearance",
    "getVariableParameterClass",
    "getEntityAppearanceClass",
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

from opendis.record.common import EntityType

from .appearance import *

VP = TypeVar('VP', bound="VariableParameterRecord")


def getEntityAppearanceClass(
        entityType: enum8,
        domain: enum8 | None = None,
) -> type[appearance.AppearanceRecord]:
    """Return an AppearanceRecord subclass for the given entityType and domain.
    
    If not determinable, return UnknownAppearance.
    """
    match (entityType, domain):
        case (0, _):  # Entity Kind: Other
            return appearance.UnknownAppearance
        case (1, 1):  # Entity Kind: Platform, Domain: Land
            return appearance.LandPlatformAppearance
        case (1, 2):  # Entity Kind: Platform, Domain: Air
            return appearance.AirPlatformAppearance
        case (1, 3):  # Entity Kind: Platform, Domain: Surface
            return appearance.SurfacePlatformAppearance
        case (1, 4):  # Entity Kind: Platform, Domain: Subsurface
            return appearance.SubsurfacePlatformAppearance
        case (1, 5):  # Entity Kind: Platform, Domain: Space
            return appearance.SpacePlatformAppearance
        case (2, _):  # Entity Kind: Munition
            return appearance.MunitionAppearance
        case (3, _):  # Entity Kind: Life form
            # Only human lifeform appearance supported for now
            return appearance.HumanLifeFormAppearance
        case (4, _):  # Entity Kind: Environmental
            return appearance.EnvironmentalAppearance
        case (5, _):  # Entity Kind: Cultural feature
            return appearance.CulturalFeatureAppearance
        case (6, _):  # Entity Kind: Supply
            return appearance.SupplyAppearance
        case (7, _):  # Entity Kind: Radio
            return appearance.RadioAppearance
        case (8, _):  # Entity Kind: Expendable
            return appearance.ExpendableAppearance
        case (9, _):  # Entity Kind: Sensor/Emitter
            return appearance.SensorEmitterAppearance
        case _:
            return appearance.UnknownAppearance


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


# Implementations

class SilentEntitySystem(base.VariableRecord):
    """6.2.79 Silent Entity System record
    
    Information about an entity not producing Entity State PDUs.
    """

    def __init__(self,
                 entityCount: uint16 = 0,
                 entityType: EntityType | None = None,
                 entityAppearances: list[appearance.AppearanceRecord] | None = None):
        self.entityCount = entityCount
        """number of the type specified by the entity type field"""
        self.entityType = entityType or EntityType()
        # Entity appearances of entities in the aggregate that
        # deviate from the default.
        self.entityAppearances: list[appearance.AppearanceRecord] = (
            entityAppearances or []
        )

    def marshalledSize(self) -> int:
        size = 12  # entityCount (2) + appearanceRecordCount (2) + entityType (8)
        size += self.appearanceRecordCount * 4  # each appearance is 4 bytes
        return size

    @property
    def appearanceRecordCount(self) -> uint16:
        return len(self.entityAppearances)

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.entityCount)
        outputStream.write_uint16(self.appearanceRecordCount)
        self.entityType.serialize(outputStream)
        for apRecord in self.entityAppearances:
            apRecord.serialize(outputStream)

    def parse(self,
              inputStream: DataInputStream,
              bytelength: int | None = None) -> None:
        self.entityCount = inputStream.read_uint16()
        appearanceRecordCount = inputStream.read_uint16()
        self.entityType.parse(inputStream)
        for _ in range(0, appearanceRecordCount):
            entityAppearanceClass = getEntityAppearanceClass(
                entityType=self.entityType.entityKind,
                domain=self.entityType.domain
            )
            entityAppearanceRecord = entityAppearanceClass()
            entityAppearanceRecord.parse(inputStream)
            self.entityAppearances.append(entityAppearanceRecord)


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
