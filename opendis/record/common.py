"""Common record types used across multiple protocol families.

Target-state DIS 7 representation (design: docs/design/dis7-representation.md
§3.3). Identity types are frozen dataclasses — hashable, usable as dict keys,
and type-sensitive so same-shaped identifiers never compare equal. They parse
constructively (``parse`` returns a new instance) because frozen records
cannot be repopulated in place; mutable value records keep the mutating
``parse`` of the ``Record`` protocol.

# generator: frozen records get constructor-style parse (classmethod);
# mutable records keep mutating parse. Both satisfy the runtime-checkable
# Record protocol, but only the mutating form matches its static signature.
"""

from dataclasses import dataclass, field
import logging
from typing import ClassVar

from opendis.enum_registry import rich_or_int
from opendis.stream import DataInputStream, DataOutputStream
from opendis.types import (
    enum8,
    enum16,
    float32,
    float64,
    uint8,
    uint16,
    uint32,
)

from . import symbolic_names as sym

_logger = logging.getLogger(__name__)

__all__ = [
    "ClockTime",
    "EulerAngles",
    "EntityIdentifier",
    "EntityMarking",
    "EntityType",
    "EventIdentifier",
    "MunitionDescriptor",
    "SimulationAddress",
    "Vector3Double",
    "Vector3Float",
    "WorldCoordinates",
]

# [UID 8] Entity Domain (platforms and non-munition kinds)
PLATFORM_DOMAIN_UID = 8
# [UID 14] Entity Domain (munition entities: domain of the target)
MUNITION_DOMAIN_UID = 14


@dataclass(frozen=True, slots=True)
class SimulationAddress:
    """§6.2.80 Simulation Address record

    Simulation designation associated with all object identifiers except
    those contained in Live Entity PDUs.
    """

    site: uint16 = 0
    """A site is defined as a facility, installation, organizational unit or
    a geographic location that has one or more simulation applications
    capable of participating in a distributed event."""
    application: uint16 = 0
    """An application is defined as a software program that is used to
    generate and process distributed simulation data including live, virtual
    and constructive data."""

    ALL_SITES: ClassVar[int] = sym.ALL_SITES
    ALL_APPLICATIONS: ClassVar[int] = sym.ALL_APPLIC

    def marshalledSize(self) -> int:
        return 4

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.site)
        outputStream.write_uint16(self.application)

    @classmethod
    def parse(cls, inputStream: DataInputStream) -> "SimulationAddress":
        return cls(inputStream.read_uint16(), inputStream.read_uint16())


@dataclass(frozen=True, slots=True)
class EntityIdentifier:
    """§6.2.28 Entity Identifier record

    Unique designation of each entity in an event or exercise that is not
    contained in a Live Entity PDU. This is the standard 6-byte shape of
    the ruled entity-identifier taxonomy; the 4-byte live form (6.2.53)
    belongs to the Live Entity family. Frozen: entity-keyed dicts and
    Fire → Detonation event correlation must not confuse this with
    same-shaped identifiers such as EventIdentifier.
    """

    simulationAddress: SimulationAddress = field(default_factory=SimulationAddress)
    entityNumber: uint16 = 0

    ALL_ENTITIES: ClassVar[int] = sym.ALL_ENTITIES

    def marshalledSize(self) -> int:
        return self.simulationAddress.marshalledSize() + 2

    def serialize(self, outputStream: DataOutputStream) -> None:
        self.simulationAddress.serialize(outputStream)
        outputStream.write_uint16(self.entityNumber)

    @classmethod
    def parse(cls, inputStream: DataInputStream) -> "EntityIdentifier":
        return cls(SimulationAddress.parse(inputStream), inputStream.read_uint16())


@dataclass(frozen=True, slots=True)
class EventIdentifier:
    """§6.2.33 Event Identifier record

    Identifies an event in the world. Use this format for every PDU EXCEPT
    the LiveEntityPdu. Ruled event-identifier taxonomy: this 6-byte shape,
    the 4-byte live form (EventIdentifierLiveEntity), a 2-byte
    flag-conditional elision, and absent-as-None — parse code may
    construct only these named shapes (see .references/decisions.md).
    """

    simulationAddress: SimulationAddress = field(default_factory=SimulationAddress)
    eventNumber: uint16 = 0

    def marshalledSize(self) -> int:
        return self.simulationAddress.marshalledSize() + 2

    def serialize(self, outputStream: DataOutputStream) -> None:
        self.simulationAddress.serialize(outputStream)
        outputStream.write_uint16(self.eventNumber)

    @classmethod
    def parse(cls, inputStream: DataInputStream) -> "EventIdentifier":
        return cls(SimulationAddress.parse(inputStream), inputStream.read_uint16())


@dataclass(frozen=True, slots=True)
class EntityType:
    """§6.2.30 Entity Type record

    Identifies the type of Entity. The domain field is dual-tabled: its
    SISO enumeration is [UID 8] for every entity kind except munitions
    (entity kind 2), which use [UID 14] to describe the target's domain
    (design §9.4); parse resolves the right table from entityKind, and the
    raw field stays a plain integer either way.
    """

    entityKind: enum8 = 0  # [UID 7]
    domain: enum8 = 0  # [UID 8] / [UID 14] for munitions
    country: enum16 = 0  # [UID 29]
    category: uint8 = 0
    subCategory: uint8 = 0
    specific: uint8 = 0
    extra: uint8 = 0

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "entityKind": 7,
        "domain": PLATFORM_DOMAIN_UID,
        "country": 29,
    }

    def marshalledSize(self) -> int:
        return 8

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint8(self.entityKind)
        outputStream.write_uint8(self.domain)
        outputStream.write_uint16(self.country)
        outputStream.write_uint8(self.category)
        outputStream.write_uint8(self.subCategory)
        outputStream.write_uint8(self.specific)
        outputStream.write_uint8(self.extra)

    @classmethod
    def parse(cls, inputStream: DataInputStream) -> "EntityType":
        entityKind = rich_or_int(7, inputStream.read_uint8())
        domainRaw = inputStream.read_uint8()
        # generator: domain's enum table is kind-dependent (UID 14 for
        # munitions, UID 8 otherwise) — the XML's own TODO #9
        domainUid = MUNITION_DOMAIN_UID if int(entityKind) == 2 else PLATFORM_DOMAIN_UID
        domain = rich_or_int(domainUid, domainRaw)
        country = rich_or_int(29, inputStream.read_uint16())
        return cls(
            entityKind,
            domain,
            country,
            inputStream.read_uint8(),
            inputStream.read_uint8(),
            inputStream.read_uint8(),
            inputStream.read_uint8(),
        )


@dataclass(slots=True)
class EulerAngles:
    """§6.2.32 Euler Angles record

    Three floating point values representing an orientation, psi, theta,
    and phi, aka the euler angles, in radians.
    These angles shall be specified with respect to the entity's coordinate
    system.
    """

    psi: float32 = 0.0
    theta: float32 = 0.0
    phi: float32 = 0.0

    def marshalledSize(self) -> int:
        return 12

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_float32(self.psi)
        outputStream.write_float32(self.theta)
        outputStream.write_float32(self.phi)

    def parse(self, inputStream: DataInputStream) -> None:
        self.psi = inputStream.read_float32()
        self.theta = inputStream.read_float32()
        self.phi = inputStream.read_float32()


@dataclass(slots=True)
class Vector3Float:
    """§6.2.96 Vector record

    Vector values for entity coordinates, linear acceleration, and linear
    velocity shall be represented using a Vector record. This record shall
    consist of three fields, each a 32-bit floating point number.
    The unit of measure represented by these fields shall depend on the
    information represented.
    """

    x: float32 = 0.0
    y: float32 = 0.0
    z: float32 = 0.0

    def marshalledSize(self) -> int:
        return 12

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_float32(self.x)
        outputStream.write_float32(self.y)
        outputStream.write_float32(self.z)

    def parse(self, inputStream: DataInputStream) -> None:
        self.x = inputStream.read_float32()
        self.y = inputStream.read_float32()
        self.z = inputStream.read_float32()


@dataclass(slots=True)
class Vector3Double:
    """Three 64-bit floating point values, used for entity location.

    Ruled 2026-10-14: the XML class name ``Vector3Double`` is canonical —
    it is the only 3x-f64 class in the XML (13 classRefs, all location
    fields) and the standard's only 3x-f64 record is World Coordinates
    (6.2.98; 6.2.97 is Vectoring Nozzle System Data, and an earlier
    revision of this docstring wrongly cited it). ``WorldCoordinates`` is
    a plain alias below, not a subclass — separate same-shaped classes
    would split type-sensitive equality and isinstance across the two
    names. The XML-fix session may rename the XML class so the alias
    flips direction. The class stays semantics-neutral (x/y/z only);
    geodetic helpers live in a separate module (RangeCoordinates.py
    precedent).
    """

    x: float64 = 0.0
    y: float64 = 0.0
    z: float64 = 0.0

    def marshalledSize(self) -> int:
        return 24

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_float64(self.x)
        outputStream.write_float64(self.y)
        outputStream.write_float64(self.z)

    def parse(self, inputStream: DataInputStream) -> None:
        self.x = inputStream.read_float64()
        self.y = inputStream.read_float64()
        self.z = inputStream.read_float64()


# generator: plain alias per the 2026-10-14 ruling — never re-declare as a
# separate class
WorldCoordinates = Vector3Double


@dataclass(slots=True)
class ClockTime:
    """§6.2.14 Clock Time record

    Time measurements that surpass one hour. Hour is hours since
    0000 h 1 January 1970 UTC; timePastHour is a Timestamp record
    (§6.2.88) held as its raw 32-bit value — 64 bits each way the record
    is 8 bytes.
    """

    hour: uint32 = 0
    timePastHour: uint32 = 0

    def marshalledSize(self) -> int:
        return 8

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint32(self.hour)
        outputStream.write_uint32(self.timePastHour)

    def parse(self, inputStream: DataInputStream) -> None:
        self.hour = inputStream.read_uint32()
        self.timePastHour = inputStream.read_uint32()


@dataclass(slots=True)
class MunitionDescriptor:
    """§6.2.19.2 Munition Descriptor record

    Describes the firing or detonation of a munition: the munition type
    plus warhead, fuse, quantity, and rate. The Expendable Descriptor
    (§6.2.19.4) shares this slot on the wire with a same-sized shape
    (expendable type + 64 bits of padding).
    """

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "warhead": 60,
        "fuse": 61,
    }

    munitionType: EntityType = field(default_factory=EntityType)
    warhead: enum16 = 0  # [UID 60]
    fuse: enum16 = 0  # [UID 61]
    quantity: uint16 = 0
    rate: uint16 = 0

    def marshalledSize(self) -> int:
        return self.munitionType.marshalledSize() + 2 + 2 + 2 + 2

    def serialize(self, outputStream: DataOutputStream) -> None:
        self.munitionType.serialize(outputStream)
        outputStream.write_uint16(self.warhead)
        outputStream.write_uint16(self.fuse)
        outputStream.write_uint16(self.quantity)
        outputStream.write_uint16(self.rate)

    def parse(self, inputStream: DataInputStream) -> None:
        self.munitionType = EntityType.parse(inputStream)
        self.warhead = rich_or_int(60, inputStream.read_uint16())
        self.fuse = rich_or_int(61, inputStream.read_uint16())
        self.quantity = inputStream.read_uint16()
        self.rate = inputStream.read_uint16()


@dataclass(slots=True)
class EntityMarking:
    """§6.2.29 Entity Marking record

    A character set followed by 11 characters of text data. The wire state
    is the raw 11 bytes; ``string`` is a NUL-trimmed view that pads on
    assignment.

    # generator: the str-backed string property (NUL-trimmed, latin-1 to
    # stay byte-faithful, truncated to 11 with a logged warning) is
    # beyond mechanical generation.
    """

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "characterSet": 45,
    }

    characterSet: enum8 = 0  # [UID 45]
    characters: bytes = b"\x00" * 11

    @property
    def string(self) -> str:
        """The marking text, NUL-trimmed."""
        return self.characters.split(b"\x00", 1)[0].decode("latin-1")

    # generator: truncation warning is beyond mechanical generation
    # (ruled 2026-10-14: silent truncation would eat bugs; silence via
    # log level or stderr redirect)
    @string.setter
    def string(self, value: str) -> None:
        data = value.encode("latin-1")
        if len(data) > 11:
            _logger.warning("EntityMarking string %r truncated to 11 bytes", value)
        self.characters = data[:11].ljust(11, b"\x00")

    def marshalledSize(self) -> int:
        return 12

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint8(self.characterSet)
        outputStream.write_bytes(self.characters[:11].ljust(11, b"\x00"))

    def parse(self, inputStream: DataInputStream) -> None:
        self.characterSet = rich_or_int(45, inputStream.read_uint8())
        self.characters = inputStream.read_bytes(11)
