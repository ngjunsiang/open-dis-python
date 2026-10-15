"""Entity Information / Interaction family (IEEE 1278.1-2012 §5.3).

Target-state vertical slice: EntityStatePdu with frozen identity records,
kind-aware EntityAppearance/Capabilities bitfield views, byte-based
variable parameters, and derived (never stored) counts.
"""

from dataclasses import dataclass, field
from typing import ClassVar

from opendis.bitfields import (
    AirPlatformAppearance,
    AirPlatformCapabilities,
    LandPlatformAppearance,
    LandPlatformCapabilities,
)
from opendis.enum_registry import rich_or_int
from opendis.record.common import (
    EntityIdentifier,
    EntityMarking,
    EntityType,
    EulerAngles,
    Vector3Float,
    WorldCoordinates,
)
from opendis.record.pdu import Pdu
from opendis.stream import DataInputStream, DataOutputStream
from opendis.types import enum8, enum32, uint8, uint32

__all__ = [
    "DeadReckoningParameters",
    "EntityInformationFamilyPdu",
    "EntityStatePdu",
    "VariableParameter",
]


@dataclass(slots=True)
class DeadReckoningParameters:
    """Dead Reckoning Parameters record (used by §7.2.2 Entity State PDU).

    The 15 ``parameters`` bytes are algorithm-dependent (§E.8) and opaque
    to the library — bytes, not a per-byte list. Field name follows the
    XML and legacy dis7.py (ruled 2026-10-14).
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
            + len(self.parameters)
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
    """§6.2.94 Variable Parameter record (general form, §6.2.94.1)

    Specification of additional information associated with an entity or
    detonation, not otherwise accounted for in a PDU. The 15
    record-specific bytes stay opaque; typed decoders (articulated parts
    etc.) ride the StandardVariableRecord registry separately.
    """

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "recordType": 56,
    }

    recordType: enum8 = 0  # [UID 56]
    recordSpecificFields: bytes = b"\x00" * 15

    def marshalledSize(self) -> int:
        return 1 + len(self.recordSpecificFields)

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
        vp = cls()
        vp.parse(inputStream)
        return vp


@dataclass(slots=True)
class EntityInformationFamilyPdu(Pdu):
    """§5.3.3 marker for the Entity Information/Interaction family.

    Implementation role moved to the registry; kept as a thin marker for
    compatibility while family metadata lives in PDU_FAMILIES.
    """

    protocolFamily: ClassVar[int] = 1  # [UID 5]


# generator: context-dependent bitfield layouts — the EntityAppearance /
# EntityCapabilities tables depend on entity kind (and, for platforms, on
# domain). Parse wraps the raw uint32 into the matching view; unknown
# kinds keep the plain int. The marshaller writes int(field) either way.
_APPEARANCE_VIEWS: dict[tuple[int, int], type] = {
    (1, 1): LandPlatformAppearance,  # platform, land domain [UID 31]
    (1, 2): AirPlatformAppearance,  # platform, air domain [UID 32]
}
_CAPABILITY_VIEWS: dict[tuple[int, int], type] = {
    (1, 1): LandPlatformCapabilities,  # [UID 450]
    (1, 2): AirPlatformCapabilities,  # [UID 451]
}


@dataclass(slots=True)
class EntityStatePdu(EntityInformationFamilyPdu):
    """§7.2.2 Entity State PDU

    Represents the position and state of one entity in the world.
    ``entityAppearance`` and ``capabilities`` hold the raw uint32 on the
    wire; after parsing a known entity kind they hold the matching
    bitfield view (``int(view)`` is the raw value, so round-trips are
    byte-exact and unknown bits survive).
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
        """How many variable parameters are in the variable length list."""
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
            + sum(vp.marshalledSize() for vp in self.variableParameters)
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
        for anObj in self.variableParameters:
            anObj.serialize(outputStream)

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
            self._parseVariableParameter(inputStream)
            for _ in range(numberOfVariableParameters)
        ]
        key = (int(self.entityType.entityKind), int(self.entityType.domain))
        appearanceView = _APPEARANCE_VIEWS.get(key)
        if appearanceView is not None:
            self.entityAppearance = appearanceView(self.entityAppearance)
        capabilityView = _CAPABILITY_VIEWS.get(key)
        if capabilityView is not None:
            self.capabilities = capabilityView(self.capabilities)

    # generator: hook point for typed VariableParameter decoding; the
    # slice keeps them opaque
    @staticmethod
    def _parseVariableParameter(inputStream: DataInputStream) -> VariableParameter:
        vp = VariableParameter()
        vp.parse(inputStream)
        return vp
