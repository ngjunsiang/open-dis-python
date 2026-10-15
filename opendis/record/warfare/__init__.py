"""Warfare Family PDU record types"""

__all__ = [
    "DEFireFlags",
    "DamageDescriptionRecord",
    "DirectedEnergyDamage",
    "DirectedEnergyAreaAimpoint",
    "DirectedEnergyPrecisionAimpoint",
    "DirectedEnergyTargetEnergyDeposition",
]

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

from .enums import DEFireFlags
from opendis.record.radio import BeamAntennaPattern


class DamageDescriptionRecord(base.StandardVariableRecord):
    """§6.2.15 Damage Description record

    Damage Description records shall use the Standard Variable record format of
    the Standard Variable Specification record (see 6.2.83).
    New Damage Description records may be defined at some future date as needed.
    """


class DirectedEnergyDamage(DamageDescriptionRecord):
    """§6.2.15.2 Directed Energy Damage Description record

    Damage sustained by an entity due to directed energy. Location of the
    damage based on a relative x, y, z location from the center of the entity.
    """

    recordType: enum32 = 4500  # [UID 66] Variable Record Type

    def __init__(
        self,
        damageLocation: Vector3Float | None = None,
        damageDiameter: float32 = 0.0,  # in metres
        temperature: float32 = -273.15,  # in degrees Celsius
        componentIdentification: enum8 = 0,  # [UID 314]
        componentDamageStatus: enum8 = 0,  # [UID 315]
        componentVisualDamageStatus: struct8 = 0,  # [UID 317]
        componentVisualSmokeColor: enum8 = 0,  # [UID 316]
        fireEventID: EventIdentifier | None = None,
    ):
        self.padding: uint16 = 0
        self.damageLocation = damageLocation or Vector3Float()
        self.damageDiameter = damageDiameter
        self.temperature = temperature
        self.componentIdentification = componentIdentification
        self.componentDamageStatus = componentDamageStatus
        self.componentVisualDamageStatus = componentVisualDamageStatus
        self.componentVisualSmokeColor = componentVisualSmokeColor
        self.fireEventID = fireEventID or EventIdentifier()
        self.padding2: uint16 = 0

    def marshalledSize(self) -> int:
        return 40

    def serialize(self, outputStream: DataOutputStream) -> None:
        super().serialize(outputStream)
        outputStream.write_uint32(self.recordType)
        outputStream.write_uint16(self.recordLength)
        outputStream.write_uint16(self.padding)
        self.damageLocation.serialize(outputStream)
        outputStream.write_float32(self.damageDiameter)
        outputStream.write_float32(self.temperature)
        outputStream.write_uint8(self.componentIdentification)
        outputStream.write_uint8(self.componentDamageStatus)
        outputStream.write_uint8(self.componentVisualDamageStatus)
        outputStream.write_uint8(self.componentVisualSmokeColor)
        self.fireEventID.serialize(outputStream)
        outputStream.write_uint16(self.padding2)

    def parse(self, inputStream: DataInputStream, bytelength: int) -> None:
        # Validate bytelength argument by calling base method
        super().parse(inputStream, bytelength)
        self.padding = inputStream.read_unsigned_short()
        self.damageLocation.parse(inputStream)
        self.damageDiameter = inputStream.read_float32()
        self.temperature = inputStream.read_float32()
        self.componentIdentification = inputStream.read_uint8()
        self.componentDamageStatus = inputStream.read_uint8()
        self.componentVisualDamageStatus = inputStream.read_uint8()
        self.componentVisualSmokeColor = inputStream.read_uint8()
        self.fireEventID = EventIdentifier.parse(inputStream)
        self.padding2 = inputStream.read_uint16()


class DirectedEnergyAreaAimpoint(DamageDescriptionRecord):
    """§6.2.20.2 DE Area Aimpoint record

    Targeting information when the target of the directed energy weapon is an
    area. The area may or may not be associated with one or more target
    entities.
    """

    recordType: enum32 = 4001  # [UID 66]

    def __init__(
        self,
        beamAntennaPatterns: list["BeamAntennaPattern"] | None = None,
        directedEnergyTargetEnergyDepositions: (
            list["DirectedEnergyTargetEnergyDeposition"] | None
        ) = None,
    ):
        self.padding: uint16 = 0
        self.beamAntennaPatterns: list["BeamAntennaPattern"] = beamAntennaPatterns or []
        self.directedEnergyTargetEnergyDepositions: list[
            "DirectedEnergyTargetEnergyDeposition"
        ] = (directedEnergyTargetEnergyDepositions or [])

    @property
    def beamAntennaPatternCount(self) -> uint16:
        return len(self.beamAntennaPatterns)

    @property
    def directedEnergyTargetEnergyDepositionCount(self) -> uint16:
        return len(self.directedEnergyTargetEnergyDepositions)

    def marshalledSize(self) -> int:
        size = 8  # recordType, recordLength, padding
        for record in self.beamAntennaPatterns:
            size += record.marshalledSize()
        for record in self.directedEnergyTargetEnergyDepositions:
            size += record.marshalledSize()
        return size

    def serialize(self, outputStream: DataOutputStream) -> None:
        super().serialize(outputStream)
        outputStream.write_uint32(self.recordType)
        outputStream.write_uint16(self.recordLength)
        outputStream.write_uint16(self.padding)
        outputStream.write_uint16(self.beamAntennaPatternCount)
        outputStream.write_uint16(self.directedEnergyTargetEnergyDepositionCount)
        for record in self.beamAntennaPatterns:
            record.serialize(outputStream)

        for record in self.directedEnergyTargetEnergyDepositions:
            record.serialize(outputStream)

    def parse(self, inputStream: DataInputStream, bytelength: int) -> None:
        # Validate bytelength argument by calling base method
        super().parse(inputStream, bytelength)
        self.padding = inputStream.read_uint16()
        beamAntennaPatternCount = inputStream.read_uint16()
        directedEnergyTargetEnergyDepositionCount = inputStream.read_uint16()
        for _ in range(0, beamAntennaPatternCount):
            record = BeamAntennaPattern()
            record.parse(inputStream)
            self.beamAntennaPatterns.append(record)
        for _ in range(0, directedEnergyTargetEnergyDepositionCount):
            record = DirectedEnergyTargetEnergyDeposition()
            record.parse(inputStream)
            self.directedEnergyTargetEnergyDepositions.append(record)


class DirectedEnergyPrecisionAimpoint(DamageDescriptionRecord):
    """§6.2.20.3 DE Precision Aimpoint record

    Targeting information when the target of the directed energy weapon is not
    an area but a specific target entity. Use of this record assumes that the DE
    weapon would not fire unless a target is known and is currently tracked.
    """

    recordType: enum32 = 4000

    def __init__(
        self,
        targetSpotLocation: WorldCoordinates | None = None,
        targetSpotEntityLocation: Vector3Float | None = None,
        targetSpotVelocity: Vector3Float | None = None,  # in m/s
        targetSpotAcceleration: Vector3Float | None = None,  # in m/s^2
        targetEntityID: EntityIdentifier | None = None,
        targetComponentID: enum8 = 0,  # [UID 314]
        beamSpotType: enum8 = 0,  # [UID 311]
        beamSpotCrossSectionSemiMajorAxis: float32 = 0.0,  # in meters
        beamSpotCrossSectionSemiMinorAxis: float32 = 0.0,  # in meters
        beamSpotCrossSectionOrientationAngle: float32 = 0.0,  # in radians
        peakIrradiance: float32 = 0.0,
    ):  # in W/m^2
        self.padding: uint16 = 0
        self.targetSpotLocation = targetSpotLocation or WorldCoordinates()
        self.targetSpotEntityLocation = targetSpotEntityLocation or Vector3Float()
        self.targetSpotVelocity = targetSpotVelocity or Vector3Float()
        self.targetSpotAcceleration = targetSpotAcceleration or Vector3Float()
        self.targetEntityID = targetEntityID or EntityIdentifier()
        self.targetComponentID = targetComponentID
        self.beamSpotType = beamSpotType
        self.beamSpotCrossSectionSemiMajorAxis = beamSpotCrossSectionSemiMajorAxis
        self.beamSpotCrossSectionSemiMinorAxis = beamSpotCrossSectionSemiMinorAxis
        self.beamSpotCrossSectionOrientationAngle = beamSpotCrossSectionOrientationAngle
        self.peakIrradiance = peakIrradiance
        self.padding2: uint32 = 0

    def marshalledSize(self) -> int:
        return 96

    def serialize(self, outputStream: DataOutputStream) -> None:
        super().serialize(outputStream)
        outputStream.write_uint32(self.recordType)
        outputStream.write_uint16(self.recordLength)
        outputStream.write_uint16(self.padding)
        self.targetSpotLocation.serialize(outputStream)
        self.targetSpotEntityLocation.serialize(outputStream)
        self.targetSpotVelocity.serialize(outputStream)
        self.targetSpotAcceleration.serialize(outputStream)
        self.targetEntityID.serialize(outputStream)
        outputStream.write_uint8(self.targetComponentID)
        outputStream.write_uint8(self.beamSpotType)
        outputStream.write_float32(self.beamSpotCrossSectionSemiMajorAxis)
        outputStream.write_float32(self.beamSpotCrossSectionSemiMinorAxis)
        outputStream.write_float32(self.beamSpotCrossSectionOrientationAngle)
        outputStream.write_float32(self.peakIrradiance)
        outputStream.write_uint32(self.padding2)

    def parse(self, inputStream: DataInputStream, bytelength: int) -> None:
        """recordType and recordLength are assumed to have been read before
        this method is called.
        """
        # Validate bytelength argument by calling base method
        super().parse(inputStream, bytelength)
        self.padding = inputStream.read_uint16()
        self.targetSpotLocation.parse(inputStream)
        self.targetSpotEntityLocation.parse(inputStream)
        self.targetSpotVelocity.parse(inputStream)
        self.targetSpotAcceleration.parse(inputStream)
        self.targetEntityID = EntityIdentifier.parse(inputStream)
        self.targetComponentID = inputStream.read_uint8()
        self.beamSpotType = inputStream.read_uint8()
        self.beamSpotCrossSectionSemiMajorAxis = inputStream.read_float32()
        self.beamSpotCrossSectionSemiMinorAxis = inputStream.read_float32()
        self.beamSpotCrossSectionOrientationAngle = inputStream.read_float32()
        self.peakIrradiance = inputStream.read_float32()
        self.padding2 = inputStream.read_uint32()


class DirectedEnergyTargetEnergyDeposition(base.Record):
    """§6.2.20.4 DE Target Energy Deposition record

    Directed energy deposition properties for a target entity shall be
    communicated using the DE Target Energy Deposition record. This record is
    required to be included inside another DE record as it does not have a
    record type.
    """

    def __init__(
        self,
        targetEntityID: EntityIdentifier | None = None,
        peakIrradiance: float32 = 0.0,
    ):  # in W/m^2
        self.targetEntityID = targetEntityID or EntityIdentifier()
        self.padding: uint16 = 0
        self.peakIrradiance = peakIrradiance

    def marshalledSize(self) -> int:
        return self.targetEntityID.marshalledSize() + 6

    def serialize(self, outputStream: DataOutputStream) -> None:
        super().serialize(outputStream)
        self.targetEntityID.serialize(outputStream)
        outputStream.write_uint16(self.padding)
        outputStream.write_float32(self.peakIrradiance)

    def parse(self, inputStream: DataInputStream) -> None:
        super().parse(inputStream)
        self.targetEntityID = EntityIdentifier.parse(inputStream)
        self.padding = inputStream.read_uint16()
        self.peakIrradiance = inputStream.read_float32()


# ---------------------------------------------------------------------------
# dis7-ng target-state PDUs (dataclass style, composed PduHeader).
# Wire ground truth: xml-fixed/WarfareFamilyPdus.xml; §7.3.
# ---------------------------------------------------------------------------

from dataclasses import dataclass, field  # noqa: E402
from typing import ClassVar  # noqa: E402

from opendis.bitfields import DEFireFlags as DEFireFlagsView  # noqa: E402
from opendis.enum_registry import rich_or_int  # noqa: E402
from opendis.record.common import (  # noqa: E402
    ClockTime,
    EntityIdentifier,
    EventIdentifier,
    MunitionDescriptor,
    Vector3Float,
    WorldCoordinates,
)
from opendis.record.entity_information import VariableParameter  # noqa: E402
from opendis.record.pdu import Pdu  # noqa: E402


@dataclass(slots=True)
class WarfareFamilyPdu(Pdu):
    """§7.3 marker for the Warfare family (Fire, Detonation,
    Directed Energy Fire, Entity Damage Status)."""

    protocolFamily: ClassVar[int] = 2  # [UID 5]


@dataclass(slots=True)
class FirePdu(WarfareFamilyPdu):
    """§7.3.2 Fire PDU

    Communicates the firing of a weapon or expendable. Total PDU size is
    96 bytes (768 bits) — size-locked by the parity oracle.
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

    Communicates the detonation or impact of munitions, the burst or
    initial bloom of chaff, and the ignition of a flare. Total PDU size is
    104 + 16·N bytes (832 + 128·N bits) — size-locked by the parity
    oracle. ``variableParameters`` reuses the §6.2.94 record from the
    entity-information family (same classRef in the XML).
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
        """How many variable parameters are in the variable length list."""
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
            + 2  # detonationResult + count + pad
            + sum(vp.marshalledSize() for vp in self.variableParameters)
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
        for anObj in self.variableParameters:
            anObj.serialize(outputStream)

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
        # Never append to a pre-existing list (PR #49 corruption pattern).
        self.variableParameters = [
            VariableParameter.parseFrom(inputStream)
            for _ in range(numberOfVariableParameters)
        ]


@dataclass(slots=True)
class DirectedEnergyFirePdu(WarfareFamilyPdu):
    """§7.3.4 Directed Energy Fire PDU

    Communicates the firing of a directed energy weapon. 88 bytes plus the
    DE records (each a uid-66 Standard Variable record, decoded via the
    registry; unknown record types stay raw bytes). Field names follow the
    XML canon (``commulativeShotTime``, ``pad1``…``pad4``).
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
        """How many DE records are in the variable length list."""
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
            + 4  # pad1
            + 4
            + 4
            + 2  # flags
            + 1
            + 1  # pulseShape + pad2
            + 4  # pad3
            + 2  # pad4
            + 2  # numberOfDERecords
            + sum(record.marshalledSize() for record in self.dERecords)
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
        for record in self.dERecords:
            record.serialize(outputStream)

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
        self.dERecords = [
            parseStandardVariableRecord(inputStream) for _ in range(numberOfDERecords)
        ]


@dataclass(slots=True)
class EntityDamageStatusPdu(WarfareFamilyPdu):
    """§7.3.5 Entity Damage Status PDU

    Communicates detailed damage information sustained by an entity
    regardless of the source of the damage. The damage-description list
    carries uid-66 Standard Variable records (§6.2.17 Damage Description
    family) decoded via the registry; unknown record types stay raw.
    """

    pduType: ClassVar[int] = 69  # [UID 4]

    damagedEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    damageDescriptionRecords: list = field(default_factory=list)

    padding1: uint16 = field(init=False, default=0)
    padding2: uint16 = field(init=False, default=0)

    @property
    def numberOfDamageDescription(self) -> uint16:
        """How many damage description records are in the list."""
        return len(self.damageDescriptionRecords)

    def _marshalledBodySize(self) -> int:
        return (
            self.damagedEntityID.marshalledSize()
            + 2
            + 2  # padding1 + padding2
            + 2  # numberOfDamageDescription
            + sum(record.marshalledSize() for record in self.damageDescriptionRecords)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.damagedEntityID.serialize(outputStream)
        outputStream.write_uint16(self.padding1)
        outputStream.write_uint16(self.padding2)
        outputStream.write_uint16(self.numberOfDamageDescription)
        for record in self.damageDescriptionRecords:
            record.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        from opendis.record import parseStandardVariableRecord

        self.damagedEntityID = EntityIdentifier.parse(inputStream)
        self.padding1 = inputStream.read_uint16()
        self.padding2 = inputStream.read_uint16()
        numberOfDamageDescription = inputStream.read_uint16()
        self.damageDescriptionRecords = [
            parseStandardVariableRecord(inputStream)
            for _ in range(numberOfDamageDescription)
        ]
