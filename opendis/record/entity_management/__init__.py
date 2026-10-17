"""Entity Management family (IEEE 1278.1-2012 §7.8) — target-state PDUs.

Wire ground truth: submodules/open-dis-spec-xml/xml/EntityManagementFamilyPdus.xml.
Aggregate State, IsGroupOf, Transfer Ownership, and IsPartOf, plus the
aggregate records (§6.2.5/§6.2.7 Identifier/Type, §6.2.62 Named Location
Identification, §6.2.63 Relationship).

Python-side deltas from the XML (sample-review rulings): AggregateMarking
reuses EntityMarking (same shape and semantics; the XML declares a
separate class); IsGroupOf's Grouped Entity Descriptions are category-
dependent (§7.8.3) and held as EntityIdentifier entries — the XML's
VariableDatum classRef is un-parseable specing; TransferOwnership's
record list is flat (count + record sets), not wrapped in the XML's
RecordSpecification layer; IsPartOf keeps the XML's
``orginatingEntityID`` spelling (name variant, not a wire issue).
"""

from dataclasses import dataclass, field
import logging
from typing import ClassVar

from opendis.enum_registry import rich_or_int
from opendis.record.common import (
    EntityIdentifier,
    EntityType,
    SimulationAddress,
    Vector3Double,
    Vector3Float,
)
from opendis.record.pdu import Pdu
from opendis.record.simulation_management import VariableDatum
from opendis.record.simulation_management_with_reliability import (
    RecordSpecificationElement,
)
from opendis.stream import DataInputStream, DataOutputStream
from opendis.types import enum8, enum16, enum32, float64, uint8, uint16, uint32

_logger = logging.getLogger(__name__)

__all__ = [
    "AggregateIdentifier",
    "AggregateMarking",
    "AggregateStatePdu",
    "AggregateType",
    "EntityManagementFamilyPdu",
    "IsGroupOfPdu",
    "IsPartOfPdu",
    "NamedLocationIdentification",
    "Relationship",
    "SilentAggregateSystem",
    "SilentEntitySystem",
    "TransferOwnershipPdu",
]


@dataclass(frozen=True, slots=True)
class AggregateIdentifier:
    """§6.2.3 Aggregate Identifier record

    The unique designation of each aggregate in an exercise is specified by
    an aggregate identifier record. The aggregate ID is not an entity and
    shall not be treated as such.
    """

    simulationAddress: SimulationAddress = field(default_factory=SimulationAddress)
    aggregateID: uint16 = 0

    def marshalledSize(self) -> int:
        return self.simulationAddress.marshalledSize() + 2

    def serialize(self, outputStream: DataOutputStream) -> None:
        self.simulationAddress.serialize(outputStream)
        outputStream.write_uint16(self.aggregateID)

    @classmethod
    def parse(cls, inputStream: DataInputStream) -> "AggregateIdentifier":
        simulationAddress = SimulationAddress.parse(inputStream)
        aggregateID = inputStream.read_uint16()
        return cls(simulationAddress, aggregateID)


@dataclass(frozen=True, slots=True)
class AggregateType:
    """§6.2.5 Aggregate Type record

    Identifies the type and organization of an aggregate.
    """

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "aggregateKind": 206,
        "domain": 8,
        "country": 29,
        "subcategory": 208,
        "specificInfo": 209,
    }

    aggregateKind: enum8 = 0  # [UID 206]
    domain: enum8 = 0  # [UID 8]
    country: enum16 = 0  # [UID 29]
    category: uint8 = 0
    subcategory: enum8 = 0  # [UID 208]
    specificInfo: enum8 = 0  # [UID 209]
    extra: uint8 = 0

    def marshalledSize(self) -> int:
        return 8

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint8(self.aggregateKind)
        outputStream.write_uint8(self.domain)
        outputStream.write_uint16(self.country)
        outputStream.write_uint8(self.category)
        outputStream.write_uint8(self.subcategory)
        outputStream.write_uint8(self.specificInfo)
        outputStream.write_uint8(self.extra)

    @classmethod
    def parse(cls, inputStream: DataInputStream) -> "AggregateType":
        aggregateKind = rich_or_int(206, inputStream.read_uint8())
        domain = rich_or_int(8, inputStream.read_uint8())
        country = rich_or_int(29, inputStream.read_uint16())
        category = inputStream.read_uint8()
        subcategory = rich_or_int(208, inputStream.read_uint8())
        specificInfo = rich_or_int(209, inputStream.read_uint8())
        extra = inputStream.read_uint8()
        return cls(
            aggregateKind, domain, country, category, subcategory, specificInfo, extra
        )


@dataclass(slots=True)
class AggregateMarking:
    """§6.2.4 Aggregate Marking record

    Specifies the character set used in the first byte, followed by up to 31
    characters of text data.
    """

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "characterSet": 45,
    }

    characterSet: enum8 = 0  # [UID 45]
    characters: bytes = b"\x00" * 31

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
        if len(data) > 31:
            _logger.warning("AggregateMarking string %r truncated to 31 bytes", value)
        self.characters = data[:31].ljust(31, b"\x00")

    def marshalledSize(self) -> int:
        return 32

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint8(self.characterSet)
        outputStream.write_bytes(self.characters[:31].ljust(31, b"\x00"))

    def parse(self, inputStream: DataInputStream) -> None:
        self.characterSet = rich_or_int(45, inputStream.read_uint8())
        self.characters = inputStream.read_bytes(31)


@dataclass(slots=True)
class Relationship:
    """§6.2.74 Relationship record

    The relationship of the part entity to its host entity.
    """

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "nature": 210,
        "position": 211,
    }

    nature: enum16 = 0  # [UID 210]
    position: enum16 = 0  # [UID 211]

    def marshalledSize(self) -> int:
        return 4

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.nature)
        outputStream.write_uint16(self.position)

    def parse(self, inputStream: DataInputStream) -> None:
        self.nature = rich_or_int(210, inputStream.read_uint16())
        self.position = rich_or_int(211, inputStream.read_uint16())


@dataclass(slots=True)
class NamedLocationIdentification:
    """§6.2.62 Named Location Identification record

    Information about the discrete positional relationship of the part
    entity with respect to the its host entity.
    """

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "stationName": 212,
    }

    stationName: enum16 = 0  # [UID 212]
    stationNumber: uint16 = 0

    def marshalledSize(self) -> int:
        return 4

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.stationName)
        outputStream.write_uint16(self.stationNumber)

    def parse(self, inputStream: DataInputStream) -> None:
        self.stationName = rich_or_int(212, inputStream.read_uint16())
        self.stationNumber = inputStream.read_uint16()


@dataclass(slots=True)
class SilentAggregateSystem:
    """An aggregate not issuing Aggregate State PDUs, carried in the Aggregate
    State PDU's Silent Aggregate System records. Table 183 / 7.8.2: 96 bits
    (Number of Aggregates + Padding + Aggregate Type).
    """

    numberOfAggregates: uint16 = 0
    aggregateType: AggregateType = field(default_factory=AggregateType)
    # Padding ruling: explicit attribute, out of __init__ (zero by default,
    # holds the wire value after parse so odd pads round-trip byte-exact).
    padding: uint16 = field(init=False, default=0)

    def marshalledSize(self) -> int:
        return 2 + 2 + self.aggregateType.marshalledSize()

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.numberOfAggregates)
        outputStream.write_uint16(self.padding)
        self.aggregateType.serialize(outputStream)

    def parse(self, inputStream: DataInputStream) -> None:
        self.numberOfAggregates = inputStream.read_uint16()
        self.padding = inputStream.read_uint16()
        self.aggregateType = AggregateType.parse(inputStream)

    @classmethod
    def parseFrom(cls, inputStream: DataInputStream) -> "SilentAggregateSystem":
        """Construct a new record from the stream (list-parse helper; the
        mutating ``parse`` above satisfies the Record protocol)."""
        item = cls()
        item.parse(inputStream)
        return item


@dataclass(slots=True)
class SilentEntitySystem:
    """§6.2.79 Silent Entity System record

    Information about an entity not producing Entity State PDUs.

    One Silent Entity System record stands for a number of same-typed silent
    entities; the appearance-record list carries one raw uint32 appearance
    per entity (§6.2.79, Table 183).
    """

    numberOfEntities: uint16 = 0
    entityType: EntityType = field(default_factory=EntityType)
    appearanceRecordList: list[uint32] = field(default_factory=list)

    @property
    def numberOfAppearanceRecords(self) -> uint16:
        """number of entity appearance records that follow."""
        return len(self.appearanceRecordList)

    def marshalledSize(self) -> int:
        return (
            2
            + 2
            + self.entityType.marshalledSize()
            + 4 * len(self.appearanceRecordList)
        )

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.numberOfEntities)
        outputStream.write_uint16(self.numberOfAppearanceRecords)
        self.entityType.serialize(outputStream)
        for item in self.appearanceRecordList:
            outputStream.write_uint32(item)

    def parse(self, inputStream: DataInputStream) -> None:
        self.numberOfEntities = inputStream.read_uint16()
        numberOfAppearanceRecords = inputStream.read_uint16()
        self.entityType = EntityType.parse(inputStream)
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.appearanceRecordList = [
            inputStream.read_uint32() for _ in range(numberOfAppearanceRecords)
        ]

    @classmethod
    def parseFrom(cls, inputStream: DataInputStream) -> "SilentEntitySystem":
        """Construct a new record from the stream (list-parse helper; the
        mutating ``parse`` above satisfies the Record protocol)."""
        item = cls()
        item.parse(inputStream)
        return item


@dataclass(slots=True)
class EntityManagementFamilyPdu(Pdu):
    """§7.8 Entity Management family PDU

    Managment of grouping of PDUs, and more.
    """

    protocolFamily: ClassVar[int] = 7  # [UID 5] Entity Management


def _padTo32(byteCount: int) -> int:
    """Pad bytes needed to bring the PDU to a 32-bit boundary."""
    return (4 - byteCount % 4) % 4


@dataclass(slots=True)
class AggregateStatePdu(EntityManagementFamilyPdu):
    """§7.8.2 Aggregate State PDU

    The Aggregate State PDU shall be used to communicate the state and other
    pertinent information about an aggregated unit.
    """

    pduType: ClassVar[int] = 33  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "forceID": 6,
        "aggregateState": 204,
        "formation": 205,
    }

    aggregateID: AggregateIdentifier = field(default_factory=AggregateIdentifier)
    forceID: enum8 = 0  # [UID 6]
    aggregateState: enum8 = 0  # [UID 204]
    aggregateType: AggregateType = field(default_factory=AggregateType)
    formation: enum32 = 0  # [UID 205]
    aggregateMarking: AggregateMarking = field(default_factory=AggregateMarking)
    dimensions: Vector3Float = field(default_factory=Vector3Float)
    orientation: Vector3Float = field(default_factory=Vector3Float)
    centerOfMass: Vector3Double = field(default_factory=Vector3Double)
    velocity: Vector3Float = field(default_factory=Vector3Float)
    aggregateIDList: list[AggregateIdentifier] = field(default_factory=list)
    entityIDList: list[EntityIdentifier] = field(default_factory=list)
    silentAggregateSystemList: list[SilentAggregateSystem] = field(default_factory=list)
    silentEntitySystemList: list[SilentEntitySystem] = field(default_factory=list)
    variableDatumList: list[VariableDatum] = field(default_factory=list)

    @property
    def numberOfDisAggregates(self) -> uint16:
        """number of aggregates."""
        return len(self.aggregateIDList)

    @property
    def numberOfDisEntities(self) -> uint16:
        """number of entities."""
        return len(self.entityIDList)

    @property
    def numberOfSilentAggregateTypes(self) -> uint16:
        """number of silent aggregate types."""
        return len(self.silentAggregateSystemList)

    @property
    def numberOfSilentEntityTypes(self) -> uint16:
        """Number of silent entity types, handled automatically by marshaller at
        run time (and not modifiable by end-user programmers).
        """
        return len(self.silentEntitySystemList)

    @property
    def numberOfVariableDatumRecords(self) -> uint32:
        """Number of variable datum records, handled automatically by marshaller at
        run time (and not modifiable by end-user programmers).
        """
        return len(self.variableDatumList)

    def _prefixSize(self) -> int:
        return (
            self.aggregateID.marshalledSize()
            + 1
            + 1
            + self.aggregateType.marshalledSize()
            + 4
            + self.aggregateMarking.marshalledSize()
            + self.dimensions.marshalledSize()
            + self.orientation.marshalledSize()
            + self.centerOfMass.marshalledSize()
            + self.velocity.marshalledSize()
            + 2
            + 2
            + 2
            + 2
        )

    def _marshalledBodySize(self):
        idLists = sum(a.marshalledSize() for a in self.aggregateIDList) + sum(
            e.marshalledSize() for e in self.entityIDList
        )
        size = (
            self._prefixSize()
            + idLists
            + _padTo32(12 + self._prefixSize() + idLists)
            + sum(t.marshalledSize() for t in self.silentAggregateSystemList)
            + sum(t.marshalledSize() for t in self.silentEntitySystemList)
            + 4
            + sum(vd.marshalledSize() for vd in self.variableDatumList)
        )
        return size

    def _serializeBody(self, outputStream: DataOutputStream):
        self.aggregateID.serialize(outputStream)
        outputStream.write_uint8(self.forceID)
        outputStream.write_uint8(self.aggregateState)
        self.aggregateType.serialize(outputStream)
        outputStream.write_uint32(self.formation)
        self.aggregateMarking.serialize(outputStream)
        self.dimensions.serialize(outputStream)
        self.orientation.serialize(outputStream)
        self.centerOfMass.serialize(outputStream)
        self.velocity.serialize(outputStream)
        outputStream.write_uint16(self.numberOfDisAggregates)
        outputStream.write_uint16(self.numberOfDisEntities)
        outputStream.write_uint16(self.numberOfSilentAggregateTypes)
        outputStream.write_uint16(self.numberOfSilentEntityTypes)
        for aggregate in self.aggregateIDList:
            aggregate.serialize(outputStream)
        for entity in self.entityIDList:
            entity.serialize(outputStream)
        idLists = sum(a.marshalledSize() for a in self.aggregateIDList) + sum(
            e.marshalledSize() for e in self.entityIDList
        )
        padding = _padTo32(12 + self._prefixSize() + idLists)
        if padding:
            outputStream.write_bytes(b"\x00" * padding)
        for aggregateType in self.silentAggregateSystemList:
            aggregateType.serialize(outputStream)
        for entityType in self.silentEntitySystemList:
            entityType.serialize(outputStream)
        outputStream.write_uint32(self.numberOfVariableDatumRecords)
        for datum in self.variableDatumList:
            datum.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream):
        self.aggregateID = AggregateIdentifier.parse(inputStream)
        self.forceID = rich_or_int(6, inputStream.read_uint8())
        self.aggregateState = rich_or_int(204, inputStream.read_uint8())
        self.aggregateType = AggregateType.parse(inputStream)
        self.formation = rich_or_int(205, inputStream.read_uint32())
        self.aggregateMarking = AggregateMarking()
        self.aggregateMarking.parse(inputStream)
        self.dimensions.parse(inputStream)
        self.orientation.parse(inputStream)
        self.centerOfMass.parse(inputStream)
        self.velocity.parse(inputStream)
        numberOfDisAggregates = inputStream.read_uint16()
        numberOfDisEntities = inputStream.read_uint16()
        numberOfSilentAggregateTypes = inputStream.read_uint16()
        numberOfSilentEntityTypes = inputStream.read_uint16()
        self.aggregateIDList = [
            AggregateIdentifier.parse(inputStream) for _ in range(numberOfDisAggregates)
        ]
        self.entityIDList = [
            EntityIdentifier.parse(inputStream) for _ in range(numberOfDisEntities)
        ]
        idLists = 6 * numberOfDisAggregates + 6 * numberOfDisEntities
        padding = _padTo32(12 + self._prefixSize() + idLists)
        if padding:
            inputStream.read_bytes(padding)
        self.silentAggregateSystemList = [
            SilentAggregateSystem.parseFrom(inputStream)
            for _ in range(numberOfSilentAggregateTypes)
        ]
        self.silentEntitySystemList = [
            SilentEntitySystem.parseFrom(inputStream)
            for _ in range(numberOfSilentEntityTypes)
        ]
        numberOfVariableDatumRecords = inputStream.read_uint32()
        self.variableDatumList = [
            VariableDatum.parseFrom(inputStream)
            for _ in range(numberOfVariableDatumRecords)
        ]


@dataclass(slots=True)
class IsGroupOfPdu(EntityManagementFamilyPdu):
    """§7.8.3 IsGroupOf PDU

    The IsGroupOf PDU shall communicate information about the individual
    states of a group of entities, including state information that is
    necessary for the receiving simulation applications to represent the
    issuing group of entities in the simulation applications’ own
    simulation.
    """

    pduType: ClassVar[int] = 34  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "groupedEntityCategory": 213,
    }

    groupEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    groupedEntityCategory: enum8 = 0  # [UID 213]
    latitude: float64 = 0.0
    longitude: float64 = 0.0
    groupedEntityDescriptions: list[EntityIdentifier] = field(default_factory=list)
    pad: uint32 = field(init=False, default=0)

    @property
    def numberOfGroupedEntities(self) -> uint8:
        """Number of individual entities constituting the group."""
        return len(self.groupedEntityDescriptions)

    def _marshalledBodySize(self) -> int:
        return (
            self.groupEntityID.marshalledSize()
            + 1
            + 1
            + 4
            + 8
            + 8
            + sum(item.marshalledSize() for item in self.groupedEntityDescriptions)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.groupEntityID.serialize(outputStream)
        outputStream.write_uint8(self.groupedEntityCategory)
        outputStream.write_uint8(self.numberOfGroupedEntities)
        outputStream.write_uint32(self.pad)
        outputStream.write_float64(self.latitude)
        outputStream.write_float64(self.longitude)
        for item in self.groupedEntityDescriptions:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.groupEntityID = EntityIdentifier.parse(inputStream)
        self.groupedEntityCategory = rich_or_int(213, inputStream.read_uint8())
        numberOfGroupedEntities = inputStream.read_uint8()
        self.pad = inputStream.read_uint32()
        self.latitude = inputStream.read_float64()
        self.longitude = inputStream.read_float64()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.groupedEntityDescriptions = [
            EntityIdentifier.parse(inputStream) for _ in range(numberOfGroupedEntities)
        ]


@dataclass(slots=True)
class TransferOwnershipPdu(EntityManagementFamilyPdu):
    """§7.8.4 Transfer Ownership PDU

    Information initiating the dynamic allocation and control of simulation
    entities between two simulation applications.
    """

    pduType: ClassVar[int] = 35  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "requiredReliabilityService": 74,
        "transferType": 224,
    }

    originatingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    receivingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    requestID: uint32 = 0
    requiredReliabilityService: enum8 = 0  # [UID 74]
    transferType: enum8 = 0  # [UID 224]
    transferEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    recordSets: list[RecordSpecificationElement] = field(default_factory=list)

    @property
    def numberOfRecordSets(self) -> uint32:
        """Number of Record Sets (R), Table 185."""
        return len(self.recordSets)

    def _marshalledBodySize(self) -> int:
        return (
            self.originatingEntityID.marshalledSize()
            + self.receivingEntityID.marshalledSize()
            + 4
            + 1
            + 1
            + self.transferEntityID.marshalledSize()
            + 4
            + sum(item.marshalledSize() for item in self.recordSets)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.originatingEntityID.serialize(outputStream)
        self.receivingEntityID.serialize(outputStream)
        outputStream.write_uint32(self.requestID)
        outputStream.write_uint8(self.requiredReliabilityService)
        outputStream.write_uint8(self.transferType)
        self.transferEntityID.serialize(outputStream)
        outputStream.write_uint32(self.numberOfRecordSets)
        for item in self.recordSets:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.originatingEntityID = EntityIdentifier.parse(inputStream)
        self.receivingEntityID = EntityIdentifier.parse(inputStream)
        self.requestID = inputStream.read_uint32()
        self.requiredReliabilityService = rich_or_int(74, inputStream.read_uint8())
        self.transferType = rich_or_int(224, inputStream.read_uint8())
        self.transferEntityID = EntityIdentifier.parse(inputStream)
        numberOfRecordSets = inputStream.read_uint32()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.recordSets = [
            RecordSpecificationElement.parseFrom(inputStream)
            for _ in range(numberOfRecordSets)
        ]


@dataclass(slots=True)
class IsPartOfPdu(EntityManagementFamilyPdu):
    """§7.8.5 IsPartOf PDU

    Used to request hierarchical linkage of separately hosted simulation
    entities.
    """

    pduType: ClassVar[int] = 36  # [UID 4]

    originatingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    receivingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    relationship: Relationship = field(default_factory=Relationship)
    partLocation: Vector3Float = field(default_factory=Vector3Float)
    namedLocationID: NamedLocationIdentification = field(
        default_factory=NamedLocationIdentification
    )
    partEntityType: EntityType = field(default_factory=EntityType)

    def _marshalledBodySize(self) -> int:
        return (
            self.originatingEntityID.marshalledSize()
            + self.receivingEntityID.marshalledSize()
            + self.relationship.marshalledSize()
            + self.partLocation.marshalledSize()
            + self.namedLocationID.marshalledSize()
            + self.partEntityType.marshalledSize()
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.originatingEntityID.serialize(outputStream)
        self.receivingEntityID.serialize(outputStream)
        self.relationship.serialize(outputStream)
        self.partLocation.serialize(outputStream)
        self.namedLocationID.serialize(outputStream)
        self.partEntityType.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.originatingEntityID = EntityIdentifier.parse(inputStream)
        self.receivingEntityID = EntityIdentifier.parse(inputStream)
        self.relationship.parse(inputStream)
        self.partLocation.parse(inputStream)
        self.namedLocationID.parse(inputStream)
        self.partEntityType = EntityType.parse(inputStream)
