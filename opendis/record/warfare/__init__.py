"""Warfare family (IEEE 1278.1-2012 §7.3) — target-state PDUs.

Wire ground truth: submodules/open-dis-spec-xml/xml/WarfareFamilyPdus.xml.
Fire, Detonation, Directed Energy Fire, and Entity Damage Status. The DE
records and damage-description records are uid-66 Standard Variable
records decoded via the registry (unknown record types stay raw bytes);
named padding fields are wire-only state (``field(init=False)``).
"""

from dataclasses import dataclass, field
from typing import ClassVar

from opendis.bitfields import DEFireFlags as DEFireFlagsView
from opendis.enum_registry import rich_or_int
from opendis.record.common import (
    ClockTime,
    EntityIdentifier,
    EntityType,
    EventIdentifier,
    MunitionDescriptor,
    Vector3Float,
    WorldCoordinates,
)
from opendis.record.entity_information import VariableParameter
from opendis.record.pdu import Pdu
from opendis.stream import DataInputStream, DataOutputStream
from opendis.types import enum8, float32, uint8, uint16, uint32

__all__ = [
    "DetonationPdu",
    "DirectedEnergyFirePdu",
    "EntityDamageStatusPdu",
    "FirePdu",
    "WarfareFamilyPdu",
]


@dataclass(slots=True)
class WarfareFamilyPdu(Pdu):
    """§7.3 Warfare family PDU

    Abstract superclass for fire and detonation pdus that have shared
    information.

    Thin family marker — per-class identity lives in the
    ``pduType``/``protocolFamily`` ClassVars; family metadata for middleware
    lives in ``PDU_FAMILIES`` (opendis.record.factory).
    """

    protocolFamily: ClassVar[int] = 2  # [UID 5] Warfare


@dataclass(slots=True)
class FirePdu(WarfareFamilyPdu):
    """§7.3.2 Fire PDU

    Used to communicate the firing of a weapon or expendable.
    """

    pduType: ClassVar[int] = 2  # [UID 4]

    firingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    targetEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    munitionExpendibleID: EntityIdentifier = field(default_factory=EntityIdentifier)
    eventID: EventIdentifier = field(default_factory=EventIdentifier)
    fireMissionIndex: uint32 = 0
    locationInWorldCoordinates: WorldCoordinates = field(
        default_factory=WorldCoordinates
    )
    descriptor: MunitionDescriptor = field(default_factory=MunitionDescriptor)
    velocity: Vector3Float = field(default_factory=Vector3Float)
    range: float32 = 0.0

    def _marshalledBodySize(self) -> int:
        return (
            self.firingEntityID.marshalledSize()
            + self.targetEntityID.marshalledSize()
            + self.munitionExpendibleID.marshalledSize()
            + self.eventID.marshalledSize()
            + 4
            + self.locationInWorldCoordinates.marshalledSize()
            + self.descriptor.marshalledSize()
            + self.velocity.marshalledSize()
            + 4
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.firingEntityID.serialize(outputStream)
        self.targetEntityID.serialize(outputStream)
        self.munitionExpendibleID.serialize(outputStream)
        self.eventID.serialize(outputStream)
        outputStream.write_uint32(self.fireMissionIndex)
        self.locationInWorldCoordinates.serialize(outputStream)
        self.descriptor.serialize(outputStream)
        self.velocity.serialize(outputStream)
        outputStream.write_float32(self.range)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.firingEntityID = EntityIdentifier.parse(inputStream)
        self.targetEntityID = EntityIdentifier.parse(inputStream)
        self.munitionExpendibleID = EntityIdentifier.parse(inputStream)
        self.eventID = EventIdentifier.parse(inputStream)
        self.fireMissionIndex = inputStream.read_uint32()
        self.locationInWorldCoordinates.parse(inputStream)
        self.descriptor.parse(inputStream)
        self.velocity.parse(inputStream)
        self.range = inputStream.read_float32()


@dataclass(slots=True)
class DetonationPdu(WarfareFamilyPdu):
    """§7.3.3 Detonation PDU

    Used to communicate the detonation or impact of munitions, as well as
    non-munition explosions, the burst or initial bloom of chaff, and the
    ignition of a flare.
    """

    pduType: ClassVar[int] = 3  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "detonationResult": 62,
    }

    sourceEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    targetEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    explodingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    eventID: EventIdentifier = field(default_factory=EventIdentifier)
    velocity: Vector3Float = field(default_factory=Vector3Float)
    locationInWorldCoordinates: WorldCoordinates = field(
        default_factory=WorldCoordinates
    )
    descriptor: MunitionDescriptor = field(default_factory=MunitionDescriptor)
    locationOfEntityCoordinates: Vector3Float = field(default_factory=Vector3Float)
    detonationResult: enum8 = 0  # [UID 62]
    variableParameters: list[VariableParameter] = field(default_factory=list)
    # Padding ruling: explicit attribute, out of __init__ (zero by default,
    # holds the wire value after parse so odd pads round-trip byte-exact).
    pad: uint16 = field(init=False, default=0)

    @property
    def numberOfVariableParameters(self) -> uint8:
        """How many articulation parameters we have."""
        return len(self.variableParameters)

    def _marshalledBodySize(self) -> int:
        return (
            self.sourceEntityID.marshalledSize()
            + self.targetEntityID.marshalledSize()
            + self.explodingEntityID.marshalledSize()
            + self.eventID.marshalledSize()
            + self.velocity.marshalledSize()
            + self.locationInWorldCoordinates.marshalledSize()
            + self.descriptor.marshalledSize()
            + self.locationOfEntityCoordinates.marshalledSize()
            + 1
            + 1
            + 2
            + sum(item.marshalledSize() for item in self.variableParameters)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.sourceEntityID.serialize(outputStream)
        self.targetEntityID.serialize(outputStream)
        self.explodingEntityID.serialize(outputStream)
        self.eventID.serialize(outputStream)
        self.velocity.serialize(outputStream)
        self.locationInWorldCoordinates.serialize(outputStream)
        self.descriptor.serialize(outputStream)
        self.locationOfEntityCoordinates.serialize(outputStream)
        outputStream.write_uint8(self.detonationResult)
        outputStream.write_uint8(self.numberOfVariableParameters)
        outputStream.write_uint16(self.pad)
        for item in self.variableParameters:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.sourceEntityID = EntityIdentifier.parse(inputStream)
        self.targetEntityID = EntityIdentifier.parse(inputStream)
        self.explodingEntityID = EntityIdentifier.parse(inputStream)
        self.eventID = EventIdentifier.parse(inputStream)
        self.velocity.parse(inputStream)
        self.locationInWorldCoordinates.parse(inputStream)
        self.descriptor.parse(inputStream)
        self.locationOfEntityCoordinates.parse(inputStream)
        self.detonationResult = rich_or_int(62, inputStream.read_uint8())
        numberOfVariableParameters = inputStream.read_uint8()
        self.pad = inputStream.read_uint16()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.variableParameters = [
            VariableParameter.parseFrom(inputStream)
            for _ in range(numberOfVariableParameters)
        ]


@dataclass(slots=True)
class DirectedEnergyFirePdu(WarfareFamilyPdu):
    """§7.3.4 Directed Energy Fire PDU

    Used to communicate the firing of a directed energy weapon.

    ``flags`` holds the raw uint16 until parsed, then the [UID 313] view.
    The DE records are uid-66 Standard Variable records decoded via the
    registry; unknown record types stay raw bytes. Field names are XML-
    verbatim, including the ``commulativeShotTime`` spelling.
    """

    pduType: ClassVar[int] = 68  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "pulseShape": 312,
    }

    firingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    eventID: EventIdentifier = field(default_factory=EventIdentifier)
    munitionType: EntityType = field(default_factory=EntityType)
    shotStartTime: ClockTime = field(default_factory=ClockTime)
    commulativeShotTime: float32 = 0.0
    apertureEmitterLocation: Vector3Float = field(default_factory=Vector3Float)
    apertureDiameter: float32 = 0.0
    wavelength: float32 = 0.0
    pulseRepititionFrequency: float32 = 0.0
    pulseWidth: float32 = 0.0
    flags: uint16 = 0  # [UID 313] or the DEFireFlags view
    pulseShape: enum8 = 0  # [UID 312]
    dERecords: list = field(default_factory=list)
    pad1: uint32 = field(init=False, default=0)
    pad2: uint8 = field(init=False, default=0)
    pad3: uint32 = field(init=False, default=0)
    pad4: uint16 = field(init=False, default=0)

    @property
    def numberOfDERecords(self) -> uint16:
        """Field shall specify the number of DE records."""
        return len(self.dERecords)

    def _marshalledBodySize(self) -> int:
        return (
            self.firingEntityID.marshalledSize()
            + self.eventID.marshalledSize()
            + self.munitionType.marshalledSize()
            + self.shotStartTime.marshalledSize()
            + 4
            + self.apertureEmitterLocation.marshalledSize()
            + 4
            + 4
            + 4
            + 4
            + 4
            + 2
            + 1
            + 1
            + 4
            + 2
            + 2
            + sum(item.marshalledSize() for item in self.dERecords)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.firingEntityID.serialize(outputStream)
        self.eventID.serialize(outputStream)
        self.munitionType.serialize(outputStream)
        self.shotStartTime.serialize(outputStream)
        outputStream.write_float32(self.commulativeShotTime)
        self.apertureEmitterLocation.serialize(outputStream)
        outputStream.write_float32(self.apertureDiameter)
        outputStream.write_float32(self.wavelength)
        outputStream.write_uint32(self.pad1)
        outputStream.write_float32(self.pulseRepititionFrequency)
        outputStream.write_float32(self.pulseWidth)
        outputStream.write_uint16(int(self.flags))
        outputStream.write_uint8(self.pulseShape)
        outputStream.write_uint8(self.pad2)
        outputStream.write_uint32(self.pad3)
        outputStream.write_uint16(self.pad4)
        outputStream.write_uint16(self.numberOfDERecords)
        for item in self.dERecords:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        from opendis.record import parseStandardVariableRecord

        self.firingEntityID = EntityIdentifier.parse(inputStream)
        self.eventID = EventIdentifier.parse(inputStream)
        self.munitionType = EntityType.parse(inputStream)
        self.shotStartTime.parse(inputStream)
        self.commulativeShotTime = inputStream.read_float32()
        self.apertureEmitterLocation.parse(inputStream)
        self.apertureDiameter = inputStream.read_float32()
        self.wavelength = inputStream.read_float32()
        self.pad1 = inputStream.read_uint32()
        self.pulseRepititionFrequency = inputStream.read_float32()
        self.pulseWidth = inputStream.read_float32()
        self.flags = DEFireFlagsView(inputStream.read_uint16())
        self.pulseShape = rich_or_int(312, inputStream.read_uint8())
        self.pad2 = inputStream.read_uint8()
        self.pad3 = inputStream.read_uint32()
        self.pad4 = inputStream.read_uint16()
        numberOfDERecords = inputStream.read_uint16()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.dERecords = [
            parseStandardVariableRecord(inputStream) for _ in range(numberOfDERecords)
        ]


@dataclass(slots=True)
class EntityDamageStatusPdu(WarfareFamilyPdu):
    """§7.3.5 Entity Damage Status PDU

    Used to communicate detailed damage information sustained by an entity
    regardless of the source of the damage.

    The damage-description list carries uid-66 Standard Variable records
    (§6.2.17 Damage Description family) decoded via the registry; unknown
    record types stay raw bytes.
    """

    pduType: ClassVar[int] = 69  # [UID 4]

    damagedEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    damageDescriptionRecords: list = field(default_factory=list)
    padding1: uint16 = field(init=False, default=0)
    padding2: uint16 = field(init=False, default=0)

    @property
    def numberOfDamageDescription(self) -> uint16:
        """field shall specify the number of Damage Description records."""
        return len(self.damageDescriptionRecords)

    def _marshalledBodySize(self) -> int:
        return (
            self.damagedEntityID.marshalledSize()
            + 2
            + 2
            + 2
            + sum(item.marshalledSize() for item in self.damageDescriptionRecords)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.damagedEntityID.serialize(outputStream)
        outputStream.write_uint16(self.padding1)
        outputStream.write_uint16(self.padding2)
        outputStream.write_uint16(self.numberOfDamageDescription)
        for item in self.damageDescriptionRecords:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        from opendis.record import parseStandardVariableRecord

        self.damagedEntityID = EntityIdentifier.parse(inputStream)
        self.padding1 = inputStream.read_uint16()
        self.padding2 = inputStream.read_uint16()
        numberOfDamageDescription = inputStream.read_uint16()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.damageDescriptionRecords = [
            parseStandardVariableRecord(inputStream)
            for _ in range(numberOfDamageDescription)
        ]
