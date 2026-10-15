"""Live Entity Information/Interaction family (IEEE 1278.1-2012 §9)
— target-state PDUs.

Wire ground truth: xml-fixed/LiveEntityFamilyPdus.xml with the
conditional-attribute vocabulary: presentIf flag-gated fields, when-
variant identifier shapes (elided vs full, per the ruled identifier
taxonomy), and the cross-scope LEMunitionDescriptor optionals.

The LE sub-header (§9.3.2) is the standard 12-byte PDU header with the
PDU Status byte carrying the subprotocol number [UID 417] — exposed as
``subprotocolNumber`` over the composed header's ``pduStatus`` byte, so
LE PDUs add zero bytes beyond the standard header.

XML deltas applied deliberately (see docs/design/sample-review.md):
- TSPI's flag-conditional state-vector fields are NOT modeled in the
  XML (no presentIf); this implementation follows the XML mechanically
  (all fields always present) — a candidate XML fix.
- Appearance-bitmap fields ([UID 229/31-43/55]) stay raw integers in
  this pass.
"""

from dataclasses import dataclass, field
from typing import ClassVar

from opendis.enum_registry import rich_or_int
from opendis.record.common import (
    EntityMarking,
    EntityType,
)
from opendis.record.entity_information import VariableParameter
from opendis.record.pdu import Pdu
from opendis.stream import DataInputStream, DataOutputStream
from opendis.types import enum8, enum16, uint8, uint16, uint32

__all__ = [
    "AppearancePdu",
    "ArticulatedPartsPdu",
    "EventIdentifierLiveEntity",
    "EventIdentifierLiveEntityElided",
    "LEDetonationPdu",
    "LEMunitionDescriptor",
    "LEVector3FixedByte",
    "LiveDeadReckoningParameters",
    "LiveEntityDetonationPdu",
    "LiveEntityFirePdu",
    "LiveEntityIdentifier",
    "LiveEntityIdentifierElided",
    "LiveEntityLinearVelocity",
    "LiveEntityOrientation",
    "LiveEntityOrientation16",
    "LiveEntityOrientationError",
    "LiveEntityPositionError",
    "LiveEntityRelativeEntityCoordinates",
    "LiveEntityRelativeWorldCoordinates",
    "LiveEntityFamilyPdu",
    "LiveSimulationAddress",
    "TimeSpacePositionInformationPdu",
]


@dataclass(frozen=True, slots=True)
class LiveSimulationAddress:
    """§6.2.54 Live Simulation Address record (site u8 +
    application u8)."""

    liveSiteNumber: uint8 = 0
    liveApplicationNumber: uint8 = 0

    def marshalledSize(self) -> int:
        return 2

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint8(self.liveSiteNumber)
        outputStream.write_uint8(self.liveApplicationNumber)

    @classmethod
    def parse(cls, inputStream: DataInputStream) -> "LiveSimulationAddress":
        return cls(inputStream.read_uint8(), inputStream.read_uint8())


@dataclass(frozen=True, slots=True)
class LiveEntityIdentifier:
    """§6.2.53 Live Entity Identifier record — the 4-byte live
    shape of the ruled identifier taxonomy."""

    liveSimulationAddress: LiveSimulationAddress = field(
        default_factory=LiveSimulationAddress
    )
    entityNumber: uint16 = 0

    def marshalledSize(self) -> int:
        return self.liveSimulationAddress.marshalledSize() + 2

    def serialize(self, outputStream: DataOutputStream) -> None:
        self.liveSimulationAddress.serialize(outputStream)
        outputStream.write_uint16(self.entityNumber)

    @classmethod
    def parse(cls, inputStream: DataInputStream) -> "LiveEntityIdentifier":
        return cls(LiveSimulationAddress.parse(inputStream), inputStream.read_uint16())


@dataclass(frozen=True, slots=True)
class LiveEntityIdentifierElided:
    """Elided live entity identifier (entity number only, 2 bytes) —
    the flag-conditional elision shape of the ruled taxonomy."""

    entityNumber: uint16 = 0

    def marshalledSize(self) -> int:
        return 2

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.entityNumber)

    @classmethod
    def parse(cls, inputStream: DataInputStream) -> "LiveEntityIdentifierElided":
        return cls(inputStream.read_uint16())


@dataclass(frozen=True, slots=True)
class EventIdentifierLiveEntity:
    """Event Identifier for LE PDUs (§9.4.5): live site u8, live
    application u8, event number u16 — the 4-byte live event shape."""

    siteNumber: uint8 = 0
    applicationNumber: uint8 = 0
    eventNumber: uint16 = 0

    def marshalledSize(self) -> int:
        return 4

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint8(self.siteNumber)
        outputStream.write_uint8(self.applicationNumber)
        outputStream.write_uint16(self.eventNumber)

    @classmethod
    def parse(cls, inputStream: DataInputStream) -> "EventIdentifierLiveEntity":
        return cls(
            inputStream.read_uint8(),
            inputStream.read_uint8(),
            inputStream.read_uint16(),
        )


@dataclass(frozen=True, slots=True)
class EventIdentifierLiveEntityElided:
    """Elided LE event identifier (event number only, 2 bytes)."""

    eventNumber: uint16 = 0

    def marshalledSize(self) -> int:
        return 2

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.eventNumber)

    @classmethod
    def parse(cls, inputStream: DataInputStream) -> "EventIdentifierLiveEntityElided":
        return cls(inputStream.read_uint16())


@dataclass(slots=True)
class LEMunitionDescriptor:
    """Munition Descriptor record (§6.2.19.2) as used by the LE Fire and
    LE Detonation PDUs: munition type always; warhead/fuse when the
    owning PDU's flag bit 4 is set; quantity/rate when bit 5 is set
    (None = absent on the wire)."""

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "warhead": 60,
        "fuse": 61,
    }

    munitionType: EntityType = field(default_factory=EntityType)
    warhead: enum16 | None = None  # [UID 60]
    fuse: enum16 | None = None  # [UID 61]
    quantity: uint16 | None = None
    rate: uint16 | None = None

    def marshalledSize(self) -> int:
        size = self.munitionType.marshalledSize()
        if self.warhead is not None:
            size += 2
        if self.fuse is not None:
            size += 2
        if self.quantity is not None:
            size += 2
        if self.rate is not None:
            size += 2
        return size

    def serialize(self, outputStream: DataOutputStream) -> None:
        self.munitionType.serialize(outputStream)
        if self.warhead is not None:
            outputStream.write_uint16(self.warhead)
        if self.fuse is not None:
            outputStream.write_uint16(self.fuse)
        if self.quantity is not None:
            outputStream.write_uint16(self.quantity)
        if self.rate is not None:
            outputStream.write_uint16(self.rate)

    @classmethod
    def parse(
        cls,
        inputStream: DataInputStream,
        includeWarheadFuse: bool,
        includeQuantityRate: bool,
    ) -> "LEMunitionDescriptor":
        descriptor = cls()
        descriptor.munitionType = EntityType.parse(inputStream)
        if includeWarheadFuse:
            descriptor.warhead = rich_or_int(60, inputStream.read_uint16())
            descriptor.fuse = rich_or_int(61, inputStream.read_uint16())
        if includeQuantityRate:
            descriptor.quantity = inputStream.read_uint16()
            descriptor.rate = inputStream.read_uint16()
        return descriptor


@dataclass(slots=True)
class LiveEntityRelativeWorldCoordinates:
    """LE relative world coordinates (§9.4.6.8): reference point u16
    plus three 16-bit fixed-binary deltas. 8 bytes."""

    referencePoint: uint16 = 0
    deltaX: uint16 = 0
    deltaY: uint16 = 0
    deltaZ: uint16 = 0

    def marshalledSize(self) -> int:
        return 8

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.referencePoint)
        outputStream.write_uint16(self.deltaX)
        outputStream.write_uint16(self.deltaY)
        outputStream.write_uint16(self.deltaZ)

    def parse(self, inputStream: DataInputStream) -> None:
        self.referencePoint = inputStream.read_uint16()
        self.deltaX = inputStream.read_uint16()
        self.deltaY = inputStream.read_uint16()
        self.deltaZ = inputStream.read_uint16()


@dataclass(slots=True)
class LiveEntityLinearVelocity:
    """LE linear velocity: three 16-bit fixed-binary components."""

    xComponent: uint16 = 0
    yComponent: uint16 = 0
    zComponent: uint16 = 0

    def marshalledSize(self) -> int:
        return 6

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.xComponent)
        outputStream.write_uint16(self.yComponent)
        outputStream.write_uint16(self.zComponent)

    def parse(self, inputStream: DataInputStream) -> None:
        self.xComponent = inputStream.read_uint16()
        self.yComponent = inputStream.read_uint16()
        self.zComponent = inputStream.read_uint16()


@dataclass(slots=True)
class LiveEntityOrientation:
    """LE orientation: three 8-bit fields (psi/theta/phi)."""

    psi: uint8 = 0
    theta: uint8 = 0
    phi: uint8 = 0

    def marshalledSize(self) -> int:
        return 3

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint8(self.psi)
        outputStream.write_uint8(self.theta)
        outputStream.write_uint8(self.phi)

    def parse(self, inputStream: DataInputStream) -> None:
        self.psi = inputStream.read_uint8()
        self.theta = inputStream.read_uint8()
        self.phi = inputStream.read_uint8()


@dataclass(slots=True)
class LiveEntityOrientation16:
    """LE orientation with 16-bit fields (LE Detonation munition
    orientation, §9.4.6.8)."""

    psi: uint16 = 0
    theta: uint16 = 0
    phi: uint16 = 0

    def marshalledSize(self) -> int:
        return 6

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.psi)
        outputStream.write_uint16(self.theta)
        outputStream.write_uint16(self.phi)

    def parse(self, inputStream: DataInputStream) -> None:
        self.psi = inputStream.read_uint16()
        self.theta = inputStream.read_uint16()
        self.phi = inputStream.read_uint16()


@dataclass(slots=True)
class LiveEntityPositionError:
    """LE position error: horizontal + vertical, 16-bit each."""

    horizontalError: uint16 = 0
    verticalError: uint16 = 0

    def marshalledSize(self) -> int:
        return 4

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.horizontalError)
        outputStream.write_uint16(self.verticalError)

    def parse(self, inputStream: DataInputStream) -> None:
        self.horizontalError = inputStream.read_uint16()
        self.verticalError = inputStream.read_uint16()


@dataclass(slots=True)
class LiveEntityOrientationError:
    """LE orientation error: azimuth/elevation/rotation, 16-bit each."""

    azimuthError: uint16 = 0
    elevationError: uint16 = 0
    rotationError: uint16 = 0

    def marshalledSize(self) -> int:
        return 6

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.azimuthError)
        outputStream.write_uint16(self.elevationError)
        outputStream.write_uint16(self.rotationError)

    def parse(self, inputStream: DataInputStream) -> None:
        self.azimuthError = inputStream.read_uint16()
        self.elevationError = inputStream.read_uint16()
        self.rotationError = inputStream.read_uint16()


@dataclass(slots=True)
class LEVector3FixedByte:
    """Three 8-bit fixed-binary components (LE DR parameters)."""

    x: uint8 = 0
    y: uint8 = 0
    z: uint8 = 0

    def marshalledSize(self) -> int:
        return 3

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint8(self.x)
        outputStream.write_uint8(self.y)
        outputStream.write_uint8(self.z)

    def parse(self, inputStream: DataInputStream) -> None:
        self.x = inputStream.read_uint8()
        self.y = inputStream.read_uint8()
        self.z = inputStream.read_uint8()


@dataclass(slots=True)
class LiveDeadReckoningParameters:
    """LE dead reckoning parameters: algorithm + acceleration + angular
    velocity (8-bit fixed binaries). 7 bytes."""

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "deadReckoningAlgorithm": 44,
    }

    deadReckoningAlgorithm: enum8 = 0  # [UID 44]
    entityLinearAcceleration: LEVector3FixedByte = field(
        default_factory=LEVector3FixedByte
    )
    entityAngularVelocity: LEVector3FixedByte = field(
        default_factory=LEVector3FixedByte
    )

    def marshalledSize(self) -> int:
        return (
            1
            + self.entityLinearAcceleration.marshalledSize()
            + self.entityAngularVelocity.marshalledSize()
        )

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint8(self.deadReckoningAlgorithm)
        self.entityLinearAcceleration.serialize(outputStream)
        self.entityAngularVelocity.serialize(outputStream)

    def parse(self, inputStream: DataInputStream) -> None:
        self.deadReckoningAlgorithm = rich_or_int(44, inputStream.read_uint8())
        self.entityLinearAcceleration.parse(inputStream)
        self.entityAngularVelocity.parse(inputStream)


@dataclass(slots=True)
class LiveEntityRelativeEntityCoordinates:
    """Location in entity coordinates (§9.4.6.8 k): three 16-bit fixed
    binaries. 6 bytes."""

    deltaX: uint16 = 0
    deltaY: uint16 = 0
    deltaZ: uint16 = 0

    def marshalledSize(self) -> int:
        return 6

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.deltaX)
        outputStream.write_uint16(self.deltaY)
        outputStream.write_uint16(self.deltaZ)

    def parse(self, inputStream: DataInputStream) -> None:
        self.deltaX = inputStream.read_uint16()
        self.deltaY = inputStream.read_uint16()
        self.deltaZ = inputStream.read_uint16()


@dataclass(slots=True)
class LiveEntityFamilyPdu(Pdu):
    """§9.3.2 base for LE PDUs: the standard 12-byte header with
    the PDU Status byte carrying the subprotocol number [UID 417]."""

    protocolFamily: ClassVar[int] = 11  # [UID 5]

    @property
    def subprotocolNumber(self) -> uint8:
        """Subprotocol used to decode the PDU (§13 of EBV) — rides the
        header's PDU Status byte."""
        return self.header.pduStatus

    @subprotocolNumber.setter
    def subprotocolNumber(self, value: uint8) -> None:
        self.header.pduStatus = value


@dataclass(slots=True)
class TimeSpacePositionInformationPdu(LiveEntityFamilyPdu):
    """§9.4.2 Time Space Position Information PDU

    The LE's state vector. NOTE: the standard's TSPIFlag-conditional
    fields are not modeled in the XML; this implementation serializes
    every state-vector field unconditionally (mechanical XML fidelity —
    see module docstring)."""

    pduType: ClassVar[int] = 46  # [UID 4]

    liveEntityId: LiveEntityIdentifier = field(default_factory=LiveEntityIdentifier)
    TSPIFlag: uint8 = 0
    entityLocation: LiveEntityRelativeWorldCoordinates = field(
        default_factory=LiveEntityRelativeWorldCoordinates
    )
    entityLinearVelocity: LiveEntityLinearVelocity = field(
        default_factory=LiveEntityLinearVelocity
    )
    entityOrientation: LiveEntityOrientation = field(
        default_factory=LiveEntityOrientation
    )
    positionError: LiveEntityPositionError = field(
        default_factory=LiveEntityPositionError
    )
    orientationError: LiveEntityOrientationError = field(
        default_factory=LiveEntityOrientationError
    )
    deadReckoningParameters: LiveDeadReckoningParameters = field(
        default_factory=LiveDeadReckoningParameters
    )
    measuredSpeed: uint16 = 0  # 16-bit fixed binary
    systemSpecificData: bytes = b""

    @property
    def systemSpecificDataLength(self) -> uint8:
        return len(self.systemSpecificData)

    def _marshalledBodySize(self) -> int:
        return (
            self.liveEntityId.marshalledSize()
            + 1
            + self.entityLocation.marshalledSize()
            + self.entityLinearVelocity.marshalledSize()
            + self.entityOrientation.marshalledSize()
            + self.positionError.marshalledSize()
            + self.orientationError.marshalledSize()
            + self.deadReckoningParameters.marshalledSize()
            + 2
            + 1
            + len(self.systemSpecificData)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.liveEntityId.serialize(outputStream)
        outputStream.write_uint8(self.TSPIFlag)
        self.entityLocation.serialize(outputStream)
        self.entityLinearVelocity.serialize(outputStream)
        self.entityOrientation.serialize(outputStream)
        self.positionError.serialize(outputStream)
        self.orientationError.serialize(outputStream)
        self.deadReckoningParameters.serialize(outputStream)
        outputStream.write_uint16(self.measuredSpeed)
        outputStream.write_uint8(self.systemSpecificDataLength)
        outputStream.write_bytes(self.systemSpecificData)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.liveEntityId = LiveEntityIdentifier.parse(inputStream)
        self.TSPIFlag = inputStream.read_uint8()
        self.entityLocation.parse(inputStream)
        self.entityLinearVelocity.parse(inputStream)
        self.entityOrientation.parse(inputStream)
        self.positionError.parse(inputStream)
        self.orientationError.parse(inputStream)
        self.deadReckoningParameters.parse(inputStream)
        self.measuredSpeed = inputStream.read_uint16()
        systemSpecificDataLength = inputStream.read_uint8()
        self.systemSpecificData = inputStream.read_bytes(systemSpecificDataLength)


TSPIPdu = TimeSpacePositionInformationPdu


@dataclass(slots=True)
class AppearancePdu(LiveEntityFamilyPdu):
    """§9.4.3 Appearance PDU

    Flag-conditional appearance data: Appearance Flag-1 (Table 221)
    gates every optional field; bit 7 also brings in Appearance Flag-2
    (Table 222), which gates the EM and Audio appearance records.
    Absent fields are ``None``. Base PDU size is 18 bytes."""

    pduType: ClassVar[int] = 47  # [UID 4]

    liveEntityId: LiveEntityIdentifier = field(default_factory=LiveEntityIdentifier)
    appearanceFlag1: uint16 = 0
    appearanceFlag2: uint8 | None = None
    forceId: enum8 | None = None  # [UID 6]
    entityType: EntityType | None = None
    alternateEntityType: EntityType | None = None
    entityMarking: EntityMarking | None = None
    capabilities: uint32 | None = None  # [UID 55] bitmap
    appearanceVisual: uint32 | None = None  # [UID 31-43]
    appearanceIR: uint32 | None = None
    appearanceEM: uint32 | None = None
    appearanceAudio: uint32 | None = None

    def _marshalledBodySize(self) -> int:
        size = self.liveEntityId.marshalledSize() + 2
        for value in (self.appearanceFlag2, self.forceId):
            if value is not None:
                size += 1
        for record in (self.entityType, self.alternateEntityType):
            if record is not None:
                size += record.marshalledSize()
        if self.entityMarking is not None:
            size += self.entityMarking.marshalledSize()
        for value in (
            self.capabilities,
            self.appearanceVisual,
            self.appearanceIR,
            self.appearanceEM,
            self.appearanceAudio,
        ):
            if value is not None:
                size += 4
        return size

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.liveEntityId.serialize(outputStream)
        outputStream.write_uint16(self.appearanceFlag1)
        if self.appearanceFlag2 is not None:
            outputStream.write_uint8(self.appearanceFlag2)
        if self.forceId is not None:
            outputStream.write_uint8(self.forceId)
        if self.entityType is not None:
            self.entityType.serialize(outputStream)
        if self.alternateEntityType is not None:
            self.alternateEntityType.serialize(outputStream)
        if self.entityMarking is not None:
            self.entityMarking.serialize(outputStream)
        if self.capabilities is not None:
            outputStream.write_uint32(self.capabilities)
        if self.appearanceVisual is not None:
            outputStream.write_uint32(self.appearanceVisual)
        if self.appearanceIR is not None:
            outputStream.write_uint32(self.appearanceIR)
        if self.appearanceEM is not None:
            outputStream.write_uint32(self.appearanceEM)
        if self.appearanceAudio is not None:
            outputStream.write_uint32(self.appearanceAudio)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        flag2Available = False
        self.liveEntityId = LiveEntityIdentifier.parse(inputStream)
        self.appearanceFlag1 = inputStream.read_uint16()
        flag1 = self.appearanceFlag1
        if flag1 & (1 << 7):
            self.appearanceFlag2 = inputStream.read_uint8()
            flag2Available = True
        if flag1 & (1 << 0):
            self.forceId = rich_or_int(6, inputStream.read_uint8())
        if flag1 & (1 << 1):
            self.entityType = EntityType.parse(inputStream)
        if flag1 & (1 << 2):
            self.alternateEntityType = EntityType.parse(inputStream)
        if flag1 & (1 << 3):
            self.entityMarking = EntityMarking()
            self.entityMarking.parse(inputStream)
        if flag1 & (1 << 4):
            self.capabilities = inputStream.read_uint32()
        if flag1 & (1 << 5):
            self.appearanceVisual = inputStream.read_uint32()
        if flag1 & (1 << 6):
            self.appearanceIR = inputStream.read_uint32()
        if flag2Available and self.appearanceFlag2 & (1 << 0):
            self.appearanceEM = inputStream.read_uint32()
        if flag2Available and self.appearanceFlag2 & (1 << 1):
            self.appearanceAudio = inputStream.read_uint32()


@dataclass(slots=True)
class ArticulatedPartsPdu(LiveEntityFamilyPdu):
    """§9.4.4 Articulated Parts PDU

    Communicates an entity's articulated and attached parts as
    §6.2.94 Variable Parameter records. Base PDU size is 17 bytes."""

    pduType: ClassVar[int] = 48  # [UID 4]

    liveEntityId: LiveEntityIdentifier = field(default_factory=LiveEntityIdentifier)
    variableParameters: list[VariableParameter] = field(default_factory=list)

    @property
    def numberOfParameterRecords(self) -> uint8:
        return len(self.variableParameters)

    def _marshalledBodySize(self) -> int:
        return (
            self.liveEntityId.marshalledSize()
            + 1
            + sum(vp.marshalledSize() for vp in self.variableParameters)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.liveEntityId.serialize(outputStream)
        outputStream.write_uint8(self.numberOfParameterRecords)
        for variableParameter in self.variableParameters:
            variableParameter.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.liveEntityId = LiveEntityIdentifier.parse(inputStream)
        numberOfParameterRecords = inputStream.read_uint8()
        self.variableParameters = [
            VariableParameter.parseFrom(inputStream)
            for _ in range(numberOfParameterRecords)
        ]


@dataclass(slots=True)
class LiveEntityFirePdu(LiveEntityFamilyPdu):
    """§9.4.5 LE Fire PDU

    Fire Flag (Table 225) gates: target entity (bit 0), munition id
    elided/full (bits 2/1), event id elided/full (bit 3 — always
    present in one of the two shapes), location (bit 6), and the
    munition descriptor's warhead/fuse (bit 4) and quantity/rate
    (bit 5). Table 226 parity: 35 bytes minimum."""

    pduType: ClassVar[int] = 49  # [UID 4]

    firingLiveEntityId: LiveEntityIdentifier = field(
        default_factory=LiveEntityIdentifier
    )
    fireFlag: uint8 = 0
    targetLiveEntityId: LiveEntityIdentifier | None = None
    munitionLiveEntityId: LiveEntityIdentifierElided | LiveEntityIdentifier | None = (
        None
    )
    eventId: EventIdentifierLiveEntityElided | EventIdentifierLiveEntity = field(
        default_factory=EventIdentifierLiveEntityElided
    )
    location: LiveEntityRelativeWorldCoordinates | None = None
    munitionDescriptor: LEMunitionDescriptor = field(
        default_factory=LEMunitionDescriptor
    )
    velocity: LiveEntityLinearVelocity = field(default_factory=LiveEntityLinearVelocity)
    range: uint16 = 0

    def _marshalledBodySize(self) -> int:
        size = (
            self.firingLiveEntityId.marshalledSize()
            + 1
            + self.eventId.marshalledSize()
            + self.munitionDescriptor.marshalledSize()
            + self.velocity.marshalledSize()
            + 2
        )
        if self.targetLiveEntityId is not None:
            size += self.targetLiveEntityId.marshalledSize()
        if self.munitionLiveEntityId is not None:
            size += self.munitionLiveEntityId.marshalledSize()
        if self.location is not None:
            size += self.location.marshalledSize()
        return size

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.firingLiveEntityId.serialize(outputStream)
        outputStream.write_uint8(self.fireFlag)
        if self.targetLiveEntityId is not None:
            self.targetLiveEntityId.serialize(outputStream)
        if self.munitionLiveEntityId is not None:
            self.munitionLiveEntityId.serialize(outputStream)
        self.eventId.serialize(outputStream)
        if self.location is not None:
            self.location.serialize(outputStream)
        self.munitionDescriptor.serialize(outputStream)
        self.velocity.serialize(outputStream)
        outputStream.write_uint16(self.range)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.firingLiveEntityId = LiveEntityIdentifier.parse(inputStream)
        fireFlag = inputStream.read_uint8()
        self.fireFlag = fireFlag
        if fireFlag & (1 << 0):
            self.targetLiveEntityId = LiveEntityIdentifier.parse(inputStream)
        if fireFlag & (1 << 2):
            if fireFlag & (1 << 1):
                self.munitionLiveEntityId = LiveEntityIdentifier.parse(inputStream)
            else:
                self.munitionLiveEntityId = LiveEntityIdentifierElided.parse(
                    inputStream
                )
        if fireFlag & (1 << 3):
            self.eventId = EventIdentifierLiveEntity.parse(inputStream)
        else:
            self.eventId = EventIdentifierLiveEntityElided.parse(inputStream)
        if fireFlag & (1 << 6):
            self.location = LiveEntityRelativeWorldCoordinates()
            self.location.parse(inputStream)
        self.munitionDescriptor = LEMunitionDescriptor.parse(
            inputStream,
            includeWarheadFuse=bool(fireFlag & (1 << 4)),
            includeQuantityRate=bool(fireFlag & (1 << 5)),
        )
        self.velocity.parse(inputStream)
        self.range = inputStream.read_uint16()


LEFirePdu = LiveEntityFirePdu


@dataclass(slots=True)
class LiveEntityDetonationPdu(LiveEntityFamilyPdu):
    """§9.4.6 LE Detonation PDU

    Detonation Flag-1 (Table 227) gates flag-2 presence (bit 7), target
    (bit 0), munition id (bit 2, elided/full by bit 1), event id (bits
    7+flag2-bit-1, elided/full by bit 3), world location (present when
    bit 6 = 0), entity-coordinates location (bit 6), and the descriptor
    optionals (bits 4/5). Flag-2 bit 0 gates the 16-bit munition
    orientation. Table 229 parity: 32 bytes minimum."""

    pduType: ClassVar[int] = 50  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "detonationResult": 62,
    }

    firingLiveEntityId: LiveEntityIdentifier = field(
        default_factory=LiveEntityIdentifier
    )
    detonationFlag1: uint8 = 0
    detonationFlag2: uint8 | None = None
    targetLiveEntityId: LiveEntityIdentifier | None = None
    munitionLiveEntityId: LiveEntityIdentifierElided | LiveEntityIdentifier | None = (
        None
    )
    eventId: EventIdentifierLiveEntityElided | EventIdentifierLiveEntity | None = None
    worldLocation: LiveEntityRelativeWorldCoordinates | None = None
    velocity: LiveEntityLinearVelocity = field(default_factory=LiveEntityLinearVelocity)
    munitionOrientation: LiveEntityOrientation16 | None = None
    munitionDescriptor: LEMunitionDescriptor = field(
        default_factory=LEMunitionDescriptor
    )
    entityLocation: LiveEntityRelativeEntityCoordinates | None = None
    detonationResult: enum8 = 0  # [UID 62]

    def _marshalledBodySize(self) -> int:
        size = (
            self.firingLiveEntityId.marshalledSize()
            + 1
            + self.velocity.marshalledSize()
            + self.munitionDescriptor.marshalledSize()
            + 1
        )
        if self.detonationFlag2 is not None:
            size += 1
        if self.targetLiveEntityId is not None:
            size += self.targetLiveEntityId.marshalledSize()
        if self.munitionLiveEntityId is not None:
            size += self.munitionLiveEntityId.marshalledSize()
        if self.eventId is not None:
            size += self.eventId.marshalledSize()
        if self.worldLocation is not None:
            size += self.worldLocation.marshalledSize()
        if self.munitionOrientation is not None:
            size += self.munitionOrientation.marshalledSize()
        if self.entityLocation is not None:
            size += self.entityLocation.marshalledSize()
        return size

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.firingLiveEntityId.serialize(outputStream)
        outputStream.write_uint8(self.detonationFlag1)
        if self.detonationFlag2 is not None:
            outputStream.write_uint8(self.detonationFlag2)
        if self.targetLiveEntityId is not None:
            self.targetLiveEntityId.serialize(outputStream)
        if self.munitionLiveEntityId is not None:
            self.munitionLiveEntityId.serialize(outputStream)
        if self.eventId is not None:
            self.eventId.serialize(outputStream)
        if self.worldLocation is not None:
            self.worldLocation.serialize(outputStream)
        self.velocity.serialize(outputStream)
        if self.munitionOrientation is not None:
            self.munitionOrientation.serialize(outputStream)
        self.munitionDescriptor.serialize(outputStream)
        if self.entityLocation is not None:
            self.entityLocation.serialize(outputStream)
        outputStream.write_uint8(self.detonationResult)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.firingLiveEntityId = LiveEntityIdentifier.parse(inputStream)
        detonationFlag1 = inputStream.read_uint8()
        self.detonationFlag1 = detonationFlag1
        flag2 = detonationFlag1 & (1 << 7)
        detonationFlag2 = 0
        if flag2:
            detonationFlag2 = inputStream.read_uint8()
            self.detonationFlag2 = detonationFlag2
        if detonationFlag1 & (1 << 0):
            self.targetLiveEntityId = LiveEntityIdentifier.parse(inputStream)
        if detonationFlag1 & (1 << 2):
            if detonationFlag1 & (1 << 1):
                self.munitionLiveEntityId = LiveEntityIdentifier.parse(inputStream)
            else:
                self.munitionLiveEntityId = LiveEntityIdentifierElided.parse(
                    inputStream
                )
        if flag2 and detonationFlag2 & (1 << 1):
            if detonationFlag1 & (1 << 3):
                self.eventId = EventIdentifierLiveEntity.parse(inputStream)
            else:
                self.eventId = EventIdentifierLiveEntityElided.parse(inputStream)
        if not detonationFlag1 & (1 << 6):
            self.worldLocation = LiveEntityRelativeWorldCoordinates()
            self.worldLocation.parse(inputStream)
        self.velocity.parse(inputStream)
        if flag2 and detonationFlag2 & (1 << 0):
            self.munitionOrientation = LiveEntityOrientation16()
            self.munitionOrientation.parse(inputStream)
        self.munitionDescriptor = LEMunitionDescriptor.parse(
            inputStream,
            includeWarheadFuse=bool(detonationFlag1 & (1 << 4)),
            includeQuantityRate=bool(detonationFlag1 & (1 << 5)),
        )
        if detonationFlag1 & (1 << 6):
            self.entityLocation = LiveEntityRelativeEntityCoordinates()
            self.entityLocation.parse(inputStream)
        self.detonationResult = rich_or_int(62, inputStream.read_uint8())


LEDetonationPdu = LiveEntityDetonationPdu
