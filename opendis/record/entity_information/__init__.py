"""Entity Information / Interaction family (IEEE 1278.1-2012 §5.3).

Generated from the pinned spec XML (source of truth). The PDU header and
the composed ``Pdu`` base live in opendis.record.pdu; concrete PDUs emit
only their body (``_marshalledBodySize`` / ``_serializeBody`` /
``_parseBody``). Counts are derived ``len()`` properties, never stored;
variable-length lists are replaced wholesale on parse (instance-reuse
corruption, PR #49).

The full entity-information surface: Entity State, Collision,
Collision-Elastic (pduType 66 — the standard's §5.2.4 enumeration;
DIS-6-style type 6 is Resupply Offer), Entity State Update, and
Attribute (§7.2.2-§7.2.6) with the §6.2.10 Attribute record (generic
Standard-Variable format; typed decodes ride the registry separately).
"""

from dataclasses import dataclass, field
from typing import ClassVar

from opendis.bitfields import (
    AirPlatformAppearance,
    AirPlatformCapabilities,
    CulturalFeatureAppearance,
    EnvironmentalAppearance,
    ExpendableAppearance,
    LandPlatformAppearance,
    LandPlatformCapabilities,
    LifeFormsAppearance,
    MunitionAppearance,
    MunitionCapabilities,
    RadioAppearance,
    SensorEmitterAppearance,
    SpacePlatformAppearance,
    SpacePlatformCapabilities,
    SubsurfacePlatformAppearance,
    SubsurfacePlatformCapabilities,
    SupplyAppearance,
    SurfacePlatformAppearance,
    SurfacePlatformCapabilities,
)
from opendis.enum_registry import rich_or_int
from opendis.record.common import (
    EntityIdentifier,
    EntityMarking,
    EntityType,
    EulerAngles,
    EventIdentifier,
    SimulationAddress,
    Vector3Double,
    Vector3Float,
    WorldCoordinates,
)
from opendis.record.pdu import Pdu
from opendis.stream import DataInputStream, DataOutputStream
from opendis.types import enum8, enum32, float32, uint8, uint16, uint32, int16, int32

__all__ = [
    "Attribute",
    "AttributePdu",
    "AttributeRecordSet",
    "CollisionElasticPdu",
    "CollisionPdu",
    "DeadReckoningParameters",
    "EntityInformationFamilyPdu",
    "EntityStatePdu",
    "EntityStateUpdatePdu",
    "VariableParameter",
]


@dataclass(slots=True)
class DeadReckoningParameters:
    """Dead Reckoning Parameters field of the ESPDU (§7.2.2 item k): 8-bit Dead
    Reckoning Algorithm enumeration (uid 44), 120 bits reserved for other
    parameters (§5.3.2.3.2 item f), entity linear acceleration, entity
    angular velocity; 320 bits total.

    The 15 ``parameters`` bytes are algorithm-dependent (§E.8) and opaque to
    the library — bytes, not a per-byte list.
    """

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "deadReckoningAlgorithm": 44,
    }

    deadReckoningAlgorithm: enum8 = 0  # [UID 44]
    parameters: bytes = b"\x00" * 15
    entityLinearAcceleration: Vector3Float = field(default_factory=Vector3Float)
    entityAngularVelocity: Vector3Float = field(default_factory=Vector3Float)

    def marshalledSize(self) -> int:
        return (
            1
            + 15
            + self.entityLinearAcceleration.marshalledSize()
            + self.entityAngularVelocity.marshalledSize()
        )

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint8(self.deadReckoningAlgorithm)
        outputStream.write_bytes(self.parameters[:15].ljust(15, b"\x00"))
        self.entityLinearAcceleration.serialize(outputStream)
        self.entityAngularVelocity.serialize(outputStream)

    def parse(self, inputStream: DataInputStream) -> None:
        self.deadReckoningAlgorithm = rich_or_int(44, inputStream.read_uint8())
        self.parameters = inputStream.read_bytes(15)
        self.entityLinearAcceleration.parse(inputStream)
        self.entityAngularVelocity.parse(inputStream)


@dataclass(slots=True)
class VariableParameter:
    """§6.2.94 Variable Parameter record

    Used in DetonationPdu, ArticulatedPartsPdu among others.

    General form (§6.2.94.1). The 15 record-specific bytes stay opaque;
    typed decoders (articulated parts etc.) ride the StandardVariableRecord
    registry separately.
    """

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "recordType": 56,
    }

    recordType: enum8 = 0  # [UID 56]
    recordSpecificFields: bytes = b"\x00" * 15

    def marshalledSize(self) -> int:
        return 16

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint8(self.recordType)
        outputStream.write_bytes(self.recordSpecificFields[:15].ljust(15, b"\x00"))

    def parse(self, inputStream: DataInputStream) -> None:
        self.recordType = rich_or_int(56, inputStream.read_uint8())
        self.recordSpecificFields = inputStream.read_bytes(15)

    @classmethod
    def parseFrom(cls, inputStream: DataInputStream) -> "VariableParameter":
        """Construct a new record from the stream (list-parse helper; the
        mutating ``parse`` above satisfies the Record protocol)."""
        item = cls()
        item.parse(inputStream)
        return item


@dataclass(slots=True)
class EntityInformationFamilyPdu(Pdu):
    """§5.3 Entity Information/Interaction family PDU

    Common superclass for EntityState, Collision, collision-elastic, and
    entity state update PDUs.

    Thin family marker — per-class identity lives in the
    ``pduType``/``protocolFamily`` ClassVars; family metadata for middleware
    lives in ``PDU_FAMILIES`` (opendis.record.factory).
    """

    protocolFamily: ClassVar[int] = 1  # [UID 5] Entity Information/Interaction


# generator: context-dependent bitfield layouts — the EntityAppearance /
# EntityCapabilities tables depend on entity kind (and, for platforms, on
# domain). Parse wraps the raw uint32 into the matching view; kinds with
# no REF-010 table keep the plain int. The marshaller writes int(field)
# either way.
_APPEARANCE_VIEWS: dict[tuple[int, int], type] = {
    (1, 1): LandPlatformAppearance,  # platform, land domain [UID 31]
    (1, 2): AirPlatformAppearance,  # platform, air domain [UID 32]
    (1, 3): SurfacePlatformAppearance,  # platform, surface domain [UID 33]
    (1, 4): SubsurfacePlatformAppearance,  # platform, subsurface domain [UID 34]
    (1, 5): SpacePlatformAppearance,  # platform, space domain [UID 35]
}
_APPEARANCE_KIND_VIEWS: dict[int, type] = {
    2: MunitionAppearance,  # [UID 36]
    3: LifeFormsAppearance,  # [UID 37]
    4: EnvironmentalAppearance,  # [UID 38]
    5: CulturalFeatureAppearance,  # [UID 39]
    6: SupplyAppearance,  # [UID 40]
    7: RadioAppearance,  # [UID 41]
    8: ExpendableAppearance,  # [UID 42]
    9: SensorEmitterAppearance,  # [UID 43]
}
_CAPABILITY_VIEWS: dict[tuple[int, int], type] = {
    (1, 1): LandPlatformCapabilities,  # [UID 450]
    (1, 2): AirPlatformCapabilities,  # [UID 451]
    (1, 3): SurfacePlatformCapabilities,  # [UID 452]
    (1, 4): SubsurfacePlatformCapabilities,  # [UID 453]
    (1, 5): SpacePlatformCapabilities,  # [UID 454]
}
_CAPABILITY_KIND_VIEWS: dict[int, type] = {
    2: MunitionCapabilities,  # [UID 455]
}


@dataclass(slots=True)
class EntityStatePdu(EntityInformationFamilyPdu):
    """§7.2.2 Entity State PDU

    Represents the position and state of one entity in the world. See
    §5.3.2.

    ``entityAppearance`` and ``capabilities`` hold the raw uint32 on the
    wire; after parsing a known entity kind they hold the matching bitfield
    view (``int(view)`` is the raw value, so round-trips are byte-exact and
    unknown bits survive).
    """

    pduType: ClassVar[int] = 1  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "forceId": 6,
    }

    entityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    forceId: enum8 = 0  # [UID 6]
    entityType: EntityType = field(default_factory=EntityType)
    alternativeEntityType: EntityType = field(default_factory=EntityType)
    entityLinearVelocity: Vector3Float = field(default_factory=Vector3Float)
    entityLocation: WorldCoordinates = field(default_factory=WorldCoordinates)
    entityOrientation: EulerAngles = field(default_factory=EulerAngles)
    entityAppearance: uint32 = 0  # [UID 31-43] or a bitfield view
    deadReckoningParameters: DeadReckoningParameters = field(
        default_factory=DeadReckoningParameters
    )
    marking: EntityMarking = field(default_factory=EntityMarking)
    capabilities: uint32 = 0  # [UID 55] or a bitfield view
    variableParameters: list[VariableParameter] = field(default_factory=list)

    @property
    def numberOfVariableParameters(self) -> uint8:
        """How many variable parameters are in the variable length list. In earlier
        versions of DIS these were known as articulation parameters.
        """
        return len(self.variableParameters)

    def _marshalledBodySize(self) -> int:
        return (
            self.entityID.marshalledSize()
            + 1
            + 1
            + self.entityType.marshalledSize()
            + self.alternativeEntityType.marshalledSize()
            + self.entityLinearVelocity.marshalledSize()
            + self.entityLocation.marshalledSize()
            + self.entityOrientation.marshalledSize()
            + 4
            + self.deadReckoningParameters.marshalledSize()
            + self.marking.marshalledSize()
            + 4
            + sum(item.marshalledSize() for item in self.variableParameters)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.entityID.serialize(outputStream)
        outputStream.write_uint8(self.forceId)
        outputStream.write_uint8(self.numberOfVariableParameters)
        self.entityType.serialize(outputStream)
        self.alternativeEntityType.serialize(outputStream)
        self.entityLinearVelocity.serialize(outputStream)
        self.entityLocation.serialize(outputStream)
        self.entityOrientation.serialize(outputStream)
        outputStream.write_uint32(int(self.entityAppearance))
        self.deadReckoningParameters.serialize(outputStream)
        self.marking.serialize(outputStream)
        outputStream.write_uint32(int(self.capabilities))
        for item in self.variableParameters:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.entityID = EntityIdentifier.parse(inputStream)
        self.forceId = rich_or_int(6, inputStream.read_uint8())
        numberOfVariableParameters = inputStream.read_uint8()
        self.entityType = EntityType.parse(inputStream)
        self.alternativeEntityType = EntityType.parse(inputStream)
        self.entityLinearVelocity.parse(inputStream)
        self.entityLocation.parse(inputStream)
        self.entityOrientation.parse(inputStream)
        self.entityAppearance = inputStream.read_uint32()
        self.deadReckoningParameters.parse(inputStream)
        self.marking.parse(inputStream)
        self.capabilities = inputStream.read_uint32()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.variableParameters = [
            VariableParameter.parseFrom(inputStream)
            for _ in range(numberOfVariableParameters)
        ]

        key = (int(self.entityType.entityKind), int(self.entityType.domain))
        appearanceView = _APPEARANCE_VIEWS.get(key) or _APPEARANCE_KIND_VIEWS.get(
            int(self.entityType.entityKind)
        )
        if appearanceView is not None:
            self.entityAppearance = appearanceView(self.entityAppearance)
        capabilityView = _CAPABILITY_VIEWS.get(key) or _CAPABILITY_KIND_VIEWS.get(
            int(self.entityType.entityKind)
        )
        if capabilityView is not None:
            self.capabilities = capabilityView(self.capabilities)


@dataclass(slots=True)
class CollisionPdu(EntityInformationFamilyPdu):
    """§7.2.3 Collision PDU

    Collisions between entities shall be communicated by issuing a Collision
    PDU. See §5.3.3.
    """

    pduType: ClassVar[int] = 4  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "collisionType": 189,
    }

    issuingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    collidingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    eventID: EventIdentifier = field(default_factory=EventIdentifier)
    collisionType: enum8 = 0  # [UID 189]
    velocity: Vector3Float = field(default_factory=Vector3Float)
    mass: float32 = 0.0
    location: Vector3Float = field(default_factory=Vector3Float)
    # Padding ruling: explicit attribute, out of __init__ (zero by default,
    # holds the wire value after parse so odd pads round-trip byte-exact).
    pad: uint8 = field(init=False, default=0)

    def _marshalledBodySize(self) -> int:
        return (
            self.issuingEntityID.marshalledSize()
            + self.collidingEntityID.marshalledSize()
            + self.eventID.marshalledSize()
            + 1
            + 1
            + self.velocity.marshalledSize()
            + 4
            + self.location.marshalledSize()
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.issuingEntityID.serialize(outputStream)
        self.collidingEntityID.serialize(outputStream)
        self.eventID.serialize(outputStream)
        outputStream.write_uint8(self.collisionType)
        outputStream.write_uint8(self.pad)
        self.velocity.serialize(outputStream)
        outputStream.write_float32(self.mass)
        self.location.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.issuingEntityID = EntityIdentifier.parse(inputStream)
        self.collidingEntityID = EntityIdentifier.parse(inputStream)
        self.eventID = EventIdentifier.parse(inputStream)
        self.collisionType = rich_or_int(189, inputStream.read_uint8())
        self.pad = inputStream.read_uint8()
        self.velocity.parse(inputStream)
        self.mass = inputStream.read_float32()
        self.location.parse(inputStream)


@dataclass(slots=True)
class CollisionElasticPdu(EntityInformationFamilyPdu):
    """§7.2.4 Collision-Elastic PDU

    Information about elastic collisions in a DIS exercise shall be
    communicated using a Collision-Elastic PDU. See §5.3.4.

    pduType 66 per the standard's §5.2.4 enumeration and Table 136 — the
    DIS-6-style type 6 legacy code used is Resupply Offer in the 2012
    numbering. The elastic-collision response protocol (§5.3.4): a receiving
    entity that detects the collision answers with its own Collision-Elastic
    PDU.
    """

    pduType: ClassVar[int] = 66  # [UID 4]

    issuingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    collidingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    collisionEventID: EventIdentifier = field(default_factory=EventIdentifier)
    contactVelocity: Vector3Float = field(default_factory=Vector3Float)
    mass: float32 = 0.0
    locationOfImpact: Vector3Float = field(default_factory=Vector3Float)
    collisionIntermediateResultXX: float32 = 0.0
    collisionIntermediateResultXY: float32 = 0.0
    collisionIntermediateResultXZ: float32 = 0.0
    collisionIntermediateResultYY: float32 = 0.0
    collisionIntermediateResultYZ: float32 = 0.0
    collisionIntermediateResultZZ: float32 = 0.0
    unitSurfaceNormal: Vector3Float = field(default_factory=Vector3Float)
    coefficientOfRestitution: float32 = 0.0
    pad: uint16 = field(init=False, default=0)

    def _marshalledBodySize(self) -> int:
        return (
            self.issuingEntityID.marshalledSize()
            + self.collidingEntityID.marshalledSize()
            + self.collisionEventID.marshalledSize()
            + 2
            + self.contactVelocity.marshalledSize()
            + 4
            + self.locationOfImpact.marshalledSize()
            + 4
            + 4
            + 4
            + 4
            + 4
            + 4
            + self.unitSurfaceNormal.marshalledSize()
            + 4
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.issuingEntityID.serialize(outputStream)
        self.collidingEntityID.serialize(outputStream)
        self.collisionEventID.serialize(outputStream)
        outputStream.write_uint16(self.pad)
        self.contactVelocity.serialize(outputStream)
        outputStream.write_float32(self.mass)
        self.locationOfImpact.serialize(outputStream)
        outputStream.write_float32(self.collisionIntermediateResultXX)
        outputStream.write_float32(self.collisionIntermediateResultXY)
        outputStream.write_float32(self.collisionIntermediateResultXZ)
        outputStream.write_float32(self.collisionIntermediateResultYY)
        outputStream.write_float32(self.collisionIntermediateResultYZ)
        outputStream.write_float32(self.collisionIntermediateResultZZ)
        self.unitSurfaceNormal.serialize(outputStream)
        outputStream.write_float32(self.coefficientOfRestitution)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.issuingEntityID = EntityIdentifier.parse(inputStream)
        self.collidingEntityID = EntityIdentifier.parse(inputStream)
        self.collisionEventID = EventIdentifier.parse(inputStream)
        self.pad = inputStream.read_uint16()
        self.contactVelocity.parse(inputStream)
        self.mass = inputStream.read_float32()
        self.locationOfImpact.parse(inputStream)
        self.collisionIntermediateResultXX = inputStream.read_float32()
        self.collisionIntermediateResultXY = inputStream.read_float32()
        self.collisionIntermediateResultXZ = inputStream.read_float32()
        self.collisionIntermediateResultYY = inputStream.read_float32()
        self.collisionIntermediateResultYZ = inputStream.read_float32()
        self.collisionIntermediateResultZZ = inputStream.read_float32()
        self.unitSurfaceNormal.parse(inputStream)
        self.coefficientOfRestitution = inputStream.read_float32()


@dataclass(slots=True)
class EntityStateUpdatePdu(EntityInformationFamilyPdu):
    """§7.2.5 Entity State Update PDU

    Nonstatic information about a particular entity may be communicated by
    issuing an Entity State Update PDU. 5.3.5.

    The PDU carries no entityType, so the appearance uint32 cannot be
    resolved to a bitfield view locally — the receiving application resolves
    it from its cached entity type for the entity (XML comment).
    """

    pduType: ClassVar[int] = 67  # [UID 4]

    entityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    entityLinearVelocity: Vector3Float = field(default_factory=Vector3Float)
    entityLocation: Vector3Double = field(default_factory=Vector3Double)
    entityOrientation: EulerAngles = field(default_factory=EulerAngles)
    entityAppearance: uint32 = 0
    variableParameters: list[VariableParameter] = field(default_factory=list)
    padding1: uint8 = field(init=False, default=0)

    @property
    def numberOfVariableParameters(self) -> uint8:
        """This field shall specify the number of variable parameters present. This
        field shall be represented by an 8-bit unsigned integer (see Annex I).
        """
        return len(self.variableParameters)

    def _marshalledBodySize(self) -> int:
        return (
            self.entityID.marshalledSize()
            + 1
            + 1
            + self.entityLinearVelocity.marshalledSize()
            + self.entityLocation.marshalledSize()
            + self.entityOrientation.marshalledSize()
            + 4
            + sum(item.marshalledSize() for item in self.variableParameters)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.entityID.serialize(outputStream)
        outputStream.write_uint8(self.padding1)
        outputStream.write_uint8(self.numberOfVariableParameters)
        self.entityLinearVelocity.serialize(outputStream)
        self.entityLocation.serialize(outputStream)
        self.entityOrientation.serialize(outputStream)
        outputStream.write_uint32(int(self.entityAppearance))
        for item in self.variableParameters:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.entityID = EntityIdentifier.parse(inputStream)
        self.padding1 = inputStream.read_uint8()
        numberOfVariableParameters = inputStream.read_uint8()
        self.entityLinearVelocity.parse(inputStream)
        self.entityLocation.parse(inputStream)
        self.entityOrientation.parse(inputStream)
        self.entityAppearance = inputStream.read_uint32()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.variableParameters = [
            VariableParameter.parseFrom(inputStream)
            for _ in range(numberOfVariableParameters)
        ]


@dataclass(slots=True)
class Attribute:
    """§6.2.10 Attribute record

    Used to convey information for one or more attributes. Attributes
    conform to the standard variable record format of 6.2.82.

    Generic §6.2.10 Standard-Variable-format record:
    ``recordSpecificFields`` carries the K data octets plus the trailing
    64-bit alignment pad exactly as received, and ``recordLength`` (= 6 + K
    + P, Table 138) stays caller-settable wire state — same contract as
    IntercomCommunicationsParameters. Typed per-record decodes ride the
    registry separately.
    """

    recordType: uint32 = 0
    recordLength: uint16 = 0
    recordSpecificFields: bytes = b""

    def marshalledSize(self):
        return 6 + len(self.recordSpecificFields)

    def serialize(self, outputStream: DataOutputStream):
        outputStream.write_uint32(self.recordType)
        outputStream.write_uint16(self.recordLength)
        outputStream.write_bytes(self.recordSpecificFields)

    def parse(self, inputStream: DataInputStream):
        self.recordType = inputStream.read_uint32()
        self.recordLength = inputStream.read_uint16()
        self.recordSpecificFields = inputStream.read_bytes(self.recordLength - 6)

    @classmethod
    def parseFrom(cls, inputStream: DataInputStream) -> "Attribute":
        """Construct a new record from the stream (list-parse helper; the
        mutating ``parse`` above satisfies the Record protocol)."""
        item = cls()
        item.parse(inputStream)
        return item


@dataclass(slots=True)
class AttributeRecordSet:
    """Each Attribute Record Set shall contain the following information: the
    Entity or Object ID to which all Attribute records in the set apply,
    plus one or more Attribute records.
    """

    entityId: EntityIdentifier = field(default_factory=EntityIdentifier)
    attributeRecords: list[Attribute] = field(default_factory=list)

    @property
    def numberOfAttributeRecords(self) -> uint16:
        """numberOfAttributeRecords"""
        return len(self.attributeRecords)

    def marshalledSize(self) -> int:
        return (
            self.entityId.marshalledSize()
            + 2
            + sum(item.marshalledSize() for item in self.attributeRecords)
        )

    def serialize(self, outputStream: DataOutputStream) -> None:
        self.entityId.serialize(outputStream)
        outputStream.write_uint16(self.numberOfAttributeRecords)
        for item in self.attributeRecords:
            item.serialize(outputStream)

    def parse(self, inputStream: DataInputStream) -> None:
        self.entityId = EntityIdentifier.parse(inputStream)
        numberOfAttributeRecords = inputStream.read_uint16()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.attributeRecords = [
            Attribute.parseFrom(inputStream) for _ in range(numberOfAttributeRecords)
        ]

    @classmethod
    def parseFrom(cls, inputStream: DataInputStream) -> "AttributeRecordSet":
        """Construct a new record from the stream (list-parse helper; the
        mutating ``parse`` above satisfies the Record protocol)."""
        item = cls()
        item.parse(inputStream)
        return item


@dataclass(slots=True)
class AttributePdu(EntityInformationFamilyPdu):
    """§7.2.6 Attribute PDU

    Information about individual attributes for a particular entity, other
    object, or event may be communicated using an Attribute PDU. The
    Attribute PDU shall not be used to exchange data available in any other
    PDU except where explicitly mentioned in the PDU issuance instructions
    within this standard. See §5.3.6.
    """

    pduType: ClassVar[int] = 72  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "attributeRecordPduType": 4,
        "attributeRecordProtocolVersion": 5,
        "masterAttributeRecordType": 66,
        "actionCode": 295,
    }

    originatingSimulationAddress: SimulationAddress = field(
        default_factory=SimulationAddress
    )
    attributeRecordPduType: enum8 = 0  # [UID 4]
    attributeRecordProtocolVersion: enum8 = 0  # [UID 5]
    masterAttributeRecordType: enum32 = 0  # [UID 66]
    actionCode: enum8 = 0  # [UID 295]
    attributeRecordSets: list[AttributeRecordSet] = field(default_factory=list)
    padding1: int32 = field(init=False, default=0)
    padding2: int16 = field(init=False, default=0)
    padding3: uint8 = field(init=False, default=0)

    @property
    def numberAttributeRecordSet(self) -> uint16:
        """This field shall specify the number of Attribute Record Sets that make
        up the remainder of the PDU. It shall be represented by a 16-bit
        unsigned integer.
        """
        return len(self.attributeRecordSets)

    def _marshalledBodySize(self) -> int:
        return (
            self.originatingSimulationAddress.marshalledSize()
            + 4
            + 2
            + 1
            + 1
            + 4
            + 1
            + 1
            + 2
            + sum(item.marshalledSize() for item in self.attributeRecordSets)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.originatingSimulationAddress.serialize(outputStream)
        outputStream.write_int32(self.padding1)
        outputStream.write_int16(self.padding2)
        outputStream.write_uint8(self.attributeRecordPduType)
        outputStream.write_uint8(self.attributeRecordProtocolVersion)
        outputStream.write_uint32(self.masterAttributeRecordType)
        outputStream.write_uint8(self.actionCode)
        outputStream.write_uint8(self.padding3)
        outputStream.write_uint16(self.numberAttributeRecordSet)
        for item in self.attributeRecordSets:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.originatingSimulationAddress = SimulationAddress.parse(inputStream)
        self.padding1 = inputStream.read_int32()
        self.padding2 = inputStream.read_int16()
        self.attributeRecordPduType = rich_or_int(4, inputStream.read_uint8())
        self.attributeRecordProtocolVersion = rich_or_int(5, inputStream.read_uint8())
        self.masterAttributeRecordType = rich_or_int(66, inputStream.read_uint32())
        self.actionCode = rich_or_int(295, inputStream.read_uint8())
        self.padding3 = inputStream.read_uint8()
        numberAttributeRecordSet = inputStream.read_uint16()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.attributeRecordSets = [
            AttributeRecordSet.parseFrom(inputStream)
            for _ in range(numberAttributeRecordSet)
        ]
