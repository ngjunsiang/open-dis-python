"""Live Entity family (IEEE 1278.1-2012 §9) — target-state PDUs.

Wire ground truth: submodules/open-dis-spec-xml/xml/LiveEntityFamilyPdus.xml.
The LE information family (TSPI, Appearance, Articulated Parts, Fire,
Detonation) over the §9.3.2 header whose PDU Status byte carries the
subprotocol number [UID 417], plus the 4-byte live identifier taxonomy
(§6.2.53/§6.2.54) and the fixed-binary state-vector records.

The conditional PDUs are the conditional-attribute vocabulary's
reference implementation: presentIf gates and when= elided/full
variants are hand-curated (METHOD_BODIES); the TSPIFlag-conditional
state-vector fields are not modeled in the XML and serialize
unconditionally (mechanical XML fidelity).
"""

from dataclasses import dataclass, field
from typing import ClassVar

from opendis.enum_registry import rich_or_int
from opendis.record.common import EntityMarking, EntityType
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
    "LEFirePdu",
    "LEMunitionDescriptor",
    "LEVector3FixedByte",
    "LiveDeadReckoningParameters",
    "LiveEntityDetonationPdu",
    "LiveEntityFamilyPdu",
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
    "LiveSimulationAddress",
    "TSPIPdu",
    "TimeSpacePositionInformationPdu",
]


@dataclass(frozen=True, slots=True)
class LiveSimulationAddress:
    """§6.2.54 Live Simulation Address record

    A simulation's designation associated with all Live Entity IDs contained
    in Live Entity PDUs.
    """

    liveSiteNumber: uint8 = 0
    liveApplicationNumber: uint8 = 0

    def marshalledSize(self) -> int:
        return 2

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint8(self.liveSiteNumber)
        outputStream.write_uint8(self.liveApplicationNumber)

    @classmethod
    def parse(cls, inputStream: DataInputStream) -> "LiveSimulationAddress":
        liveSiteNumber = inputStream.read_uint8()
        liveApplicationNumber = inputStream.read_uint8()
        return cls(liveSiteNumber, liveApplicationNumber)


@dataclass(frozen=True, slots=True)
class LiveEntityIdentifier:
    """§6.2.53 Live Entity Identifier record

    The unique designation of each entity in an event or exercise that is
    contained in a Live Entity PDU.

    The 4-byte live shape of the ruled identifier taxonomy (§6.2.53).
    """

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
        liveSimulationAddress = LiveSimulationAddress.parse(inputStream)
        entityNumber = inputStream.read_uint16()
        return cls(liveSimulationAddress, entityNumber)


@dataclass(frozen=True, slots=True)
class LiveEntityIdentifierElided:
    """Live Entity Identifier, elided form: Entity Number only (16 bits). Used
    for LE Fire/Detonation Munition ID when the Site/Application numbers
    equal the Firing Live Entity ID's (see 9.4.5 e)).
    """

    entityNumber: uint16 = 0

    def marshalledSize(self) -> int:
        return 2

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.entityNumber)

    @classmethod
    def parse(cls, inputStream: DataInputStream) -> "LiveEntityIdentifierElided":
        entityNumber = inputStream.read_uint16()
        return cls(entityNumber)


@dataclass(frozen=True, slots=True)
class EventIdentifierLiveEntity:
    """§9.4.5 Live Event Identifier record

    Identifies an event in the world. Use this format for ONLY the
    LiveEntityPdu.

    The 4-byte live event shape (§9.4.5) of the ruled event-identifier
    taxonomy.
    """

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
        siteNumber = inputStream.read_uint8()
        applicationNumber = inputStream.read_uint8()
        eventNumber = inputStream.read_uint16()
        return cls(siteNumber, applicationNumber, eventNumber)


@dataclass(frozen=True, slots=True)
class EventIdentifierLiveEntityElided:
    """Event ID, live-entity elided form: Event Number only (16 bits). Used
    when the Site/Application numbers equal the Firing Live Entity ID's and
    are therefore not included (see 9.4.5 f), 9.4.6 f)). Named shape per the
    pinned event taxonomy.
    """

    eventNumber: uint16 = 0

    def marshalledSize(self) -> int:
        return 2

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.eventNumber)

    @classmethod
    def parse(cls, inputStream: DataInputStream) -> "EventIdentifierLiveEntityElided":
        eventNumber = inputStream.read_uint16()
        return cls(eventNumber)


@dataclass(slots=True)
class LEMunitionDescriptor:
    """Munition Descriptor record (6.2.19.2) as used in the LE
    Information/Interaction protocol: warhead, fuse, quantity and rate are
    optional, governed by the owning PDU's Fire/Detonation flag fields
    (cross-scope presentIf; 9.4.5 h), 9.4.6 j)).

    Warhead/fuse ride the owning PDU's flag bit 4, quantity/rate bit 5 (None
    = absent on the wire); ``parse`` takes the inclusion flags (cross-scope
    presentIf, §6.2.19.2).
    """

    munitionType: EntityType = field(default_factory=EntityType)
    warhead: enum16 | None = None  # [UID 60]
    fuse: enum16 | None = None  # [UID 61]
    quantity: uint16 | None = None
    rate: uint16 | None = None

    def marshalledSize(self):
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

    def serialize(self, outputStream: DataOutputStream):
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
    """16-bit fixed binaries."""

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
    """16-bit fixed binaries."""

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
    """8-bit fixed binaries."""

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
    """16-bit fixed binaries."""

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
    """16-bit fixed binaries."""

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
    """16-bit fixed binaries."""

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
    """3 x 8-bit fixed binary."""

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
    """16-bit fixed binaries."""

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
    """Location in Entity's Coordinates for LE PDUs: Entity Coordinate Vector
    (§6.2.96 item a) subject to the decreased field sizes of the LE protocol
    — three 16-bit fixed-binary components (48 bits). See §9.4.6.8 k).
    """

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
    """Does not inherit from PduBase.  See section 9."""

    protocolFamily: ClassVar[int] = 11  # [UID 5] Live Entity

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

    The Time Space Position Information (TSPI) PDU shall communicate
    information about the LE’s state vector. Canonical descriptive name;
    TSPIPdu is an alias.

    The standard's TSPIFlag-conditional fields are not modeled in the XML;
    this implementation serializes every state-vector field unconditionally
    (mechanical XML fidelity).
    """

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
    measuredSpeed: uint16 = 0
    systemSpecificData: bytes = b""

    @property
    def systemSpecificDataLength(self) -> uint8:
        """systemSpecificDataLength"""
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

    Communicate information about the appearance of a live entity.
    """

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

    def _marshalledBodySize(self):
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

    def _serializeBody(self, outputStream: DataOutputStream):
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

    def _parseBody(self, inputStream: DataInputStream):
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

    Communicate information about an entity’s articulated and attached
    parts.
    """

    pduType: ClassVar[int] = 48  # [UID 4]

    liveEntityId: LiveEntityIdentifier = field(default_factory=LiveEntityIdentifier)
    variableParameters: list[VariableParameter] = field(default_factory=list)

    @property
    def numberOfParameterRecords(self) -> uint8:
        """numberOfParameterRecords"""
        return len(self.variableParameters)

    def _marshalledBodySize(self) -> int:
        return (
            self.liveEntityId.marshalledSize()
            + 1
            + sum(item.marshalledSize() for item in self.variableParameters)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.liveEntityId.serialize(outputStream)
        outputStream.write_uint8(self.numberOfParameterRecords)
        for item in self.variableParameters:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.liveEntityId = LiveEntityIdentifier.parse(inputStream)
        numberOfParameterRecords = inputStream.read_uint8()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.variableParameters = [
            VariableParameter.parseFrom(inputStream)
            for _ in range(numberOfParameterRecords)
        ]


@dataclass(slots=True)
class LiveEntityFirePdu(LiveEntityFamilyPdu):
    """§9.4.5 LE Fire PDU

    Representation of weapons fire in a DIS exercise involving LEs.
    Canonical descriptive name; LEFirePdu is an alias.
    """

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

    def _marshalledBodySize(self):
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

    def _serializeBody(self, outputStream: DataOutputStream):
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

    def _parseBody(self, inputStream: DataInputStream):
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

    Communicate information associated with the impact or detonation of a
    munition. Canonical descriptive name; LEDetonationPdu is an alias.
    """

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

    def _marshalledBodySize(self):
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

    def _serializeBody(self, outputStream: DataOutputStream):
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

    def _parseBody(self, inputStream: DataInputStream):
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
