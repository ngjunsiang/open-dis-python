"""Entity Management family (IEEE 1278.1-2012 §7.8) — target-state PDUs.

Wire ground truth: xml-fixed/EntityManagementFamilyPdus.xml. Aggregate
State, IsGroupOf, Transfer Ownership, and IsPartOf, plus the aggregate
records (§6.2.4/5/7 Aggregate Marking/Identifier/Type, §6.2.62 Named
Location Identification, §6.2.63 Relationship).

XML deltas applied deliberately (see docs/design/sample-review.md):
- AggregateMarking reuses EntityMarking (same shape and semantics; the
  XML declares a separate class).
- IsGroupOf's Grouped Entity Descriptions are category-dependent (§7.8.3);
  the XML's VariableDatum classRef is un-parseable specing. Represented
  as EntityIdentifier entries — the form used by the defined categories.
- TransferOwnership's record list is flat (count + record sets), not
  wrapped in the XML's RecordSpecification layer.
- IsPartOf keeps the XML's ``orginatingEntityID`` spelling (name
  variant, not a wire issue).
"""

from dataclasses import dataclass, field
from typing import ClassVar

from opendis.enum_registry import rich_or_int
from opendis.record.common import (
    EntityIdentifier,
    EntityMarking,
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
from opendis.types import enum8, enum16, enum32, float32, float64, uint8, uint16, uint32

__all__ = [
    "AggregateIdentifier",
    "AggregateStatePdu",
    "AggregateType",
    "EntityManagementFamilyPdu",
    "IsGroupOfPdu",
    "IsPartOfPdu",
    "NamedLocationIdentification",
    "Relationship",
    "TransferOwnershipPdu",
]


@dataclass(frozen=True, slots=True)
class AggregateIdentifier:
    """Section 6.2.5 Aggregate Identifier record

    Unique identifier for an aggregate: simulation address plus
    aggregate number. Frozen identity type, same taxonomy as
    EntityIdentifier."""

    simulationAddress: SimulationAddress = field(default_factory=SimulationAddress)
    aggregateID: uint16 = 0

    def marshalledSize(self) -> int:
        return self.simulationAddress.marshalledSize() + 2

    def serialize(self, outputStream: DataOutputStream) -> None:
        self.simulationAddress.serialize(outputStream)
        outputStream.write_uint16(self.aggregateID)

    @classmethod
    def parse(cls, inputStream: DataInputStream) -> "AggregateIdentifier":
        return cls(SimulationAddress.parse(inputStream),
                   inputStream.read_uint16())


@dataclass(frozen=True, slots=True)
class AggregateType:
    """Section 6.2.7 Aggregate Type record

    The type of an aggregate — the aggregate-kind analogue of an
    EntityType."""

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
        return cls(rich_or_int(206, inputStream.read_uint8()),
                   rich_or_int(8, inputStream.read_uint8()),
                   rich_or_int(29, inputStream.read_uint16()),
                   inputStream.read_uint8(),
                   rich_or_int(208, inputStream.read_uint8()),
                   rich_or_int(209, inputStream.read_uint8()),
                   inputStream.read_uint8())


@dataclass(slots=True)
class Relationship:
    """Section 6.2.63 Relationship record

    The relationship of a part to its host: nature and position."""

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "nature": 210,
        "position": 211,
    }

    nature: enum8 = 0  # [UID 210]
    position: enum8 = 0  # [UID 211]

    def marshalledSize(self) -> int:
        return 2

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint8(self.nature)
        outputStream.write_uint8(self.position)

    def parse(self, inputStream: DataInputStream) -> None:
        self.nature = rich_or_int(210, inputStream.read_uint8())
        self.position = rich_or_int(211, inputStream.read_uint8())


@dataclass(slots=True)
class NamedLocationIdentification:
    """Section 6.2.62 Named Location Identification record

    Station name (16-bit enumeration [UID 212]) and station number."""

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
class EntityManagementFamilyPdu(Pdu):
    """Section 7.8 marker for the Entity Management family."""

    protocolFamily: ClassVar[int] = 7  # [UID 5]


def _padTo32(byteCount: int) -> int:
    """Pad bytes needed to bring the PDU to a 32-bit boundary."""
    return (4 - byteCount % 4) % 4


@dataclass(slots=True)
class AggregateStatePdu(EntityManagementFamilyPdu):
    """Section 7.8.2 Aggregate State PDU

    Communicates the state and other pertinent information about an
    aggregated unit: geometry, silent-entity tables, constituent ID
    lists, and variable datums. Base PDU size is 112 bytes before
    lists; the ID lists are padded to a 32-bit boundary before the
    silent-entity lists."""

    pduType: ClassVar[int] = 33  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "forceID": 6,
        "aggregateState": 204,
        "formation": 205,
    }

    aggregateID: AggregateIdentifier = field(
        default_factory=AggregateIdentifier)
    forceID: enum8 = 0  # [UID 6]
    aggregateState: enum8 = 0  # [UID 204]
    aggregateType: AggregateType = field(default_factory=AggregateType)
    formation: enum32 = 0  # [UID 205]
    aggregateMarking: EntityMarking = field(default_factory=EntityMarking)
    dimensions: Vector3Float = field(default_factory=Vector3Float)
    orientation: Vector3Float = field(default_factory=Vector3Float)
    centerOfMass: Vector3Double = field(default_factory=Vector3Double)
    velocity: Vector3Float = field(default_factory=Vector3Float)
    aggregateIDList: list[AggregateIdentifier] = field(default_factory=list)
    entityIDList: list[EntityIdentifier] = field(default_factory=list)
    silentAggregateSystemList: list[EntityType] = field(default_factory=list)
    silentEntitySystemList: list[EntityType] = field(default_factory=list)
    variableDatumList: list[VariableDatum] = field(default_factory=list)

    @property
    def numberOfDisAggregates(self) -> uint16:
        return len(self.aggregateIDList)

    @property
    def numberOfDisEntities(self) -> uint16:
        return len(self.entityIDList)

    @property
    def numberOfSilentAggregateTypes(self) -> uint16:
        return len(self.silentAggregateSystemList)

    @property
    def numberOfSilentEntityTypes(self) -> uint16:
        return len(self.silentEntitySystemList)

    @property
    def numberOfVariableDatumRecords(self) -> uint32:
        return len(self.variableDatumList)

    def _prefixSize(self) -> int:
        return (self.aggregateID.marshalledSize()
                + 1 + 1
                + self.aggregateType.marshalledSize()
                + 4
                + self.aggregateMarking.marshalledSize()
                + self.dimensions.marshalledSize()
                + self.orientation.marshalledSize()
                + self.centerOfMass.marshalledSize()
                + self.velocity.marshalledSize()
                + 2 + 2 + 2 + 2)

    def _marshalledBodySize(self) -> int:
        idLists = (sum(a.marshalledSize() for a in self.aggregateIDList)
                   + sum(e.marshalledSize() for e in self.entityIDList))
        size = (self._prefixSize() + idLists
                + _padTo32(12 + self._prefixSize() + idLists)
                + sum(t.marshalledSize()
                      for t in self.silentAggregateSystemList)
                + sum(t.marshalledSize() for t in self.silentEntitySystemList)
                + 4
                + sum(vd.marshalledSize() for vd in self.variableDatumList))
        return size

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
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
        idLists = (sum(a.marshalledSize() for a in self.aggregateIDList)
                   + sum(e.marshalledSize() for e in self.entityIDList))
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

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.aggregateID = AggregateIdentifier.parse(inputStream)
        self.forceID = rich_or_int(6, inputStream.read_uint8())
        self.aggregateState = rich_or_int(204, inputStream.read_uint8())
        self.aggregateType = AggregateType.parse(inputStream)
        self.formation = rich_or_int(205, inputStream.read_uint32())
        self.aggregateMarking = EntityMarking()
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
            AggregateIdentifier.parse(inputStream)
            for _ in range(numberOfDisAggregates)
        ]
        self.entityIDList = [
            EntityIdentifier.parse(inputStream)
            for _ in range(numberOfDisEntities)
        ]
        idLists = 6 * numberOfDisAggregates + 6 * numberOfDisEntities
        padding = _padTo32(12 + self._prefixSize() + idLists)
        if padding:
            inputStream.read_bytes(padding)
        self.silentAggregateSystemList = [
            EntityType.parse(inputStream)
            for _ in range(numberOfSilentAggregateTypes)
        ]
        self.silentEntitySystemList = [
            EntityType.parse(inputStream)
            for _ in range(numberOfSilentEntityTypes)
        ]
        numberOfVariableDatumRecords = inputStream.read_uint32()
        self.variableDatumList = [
            VariableDatum.parseFrom(inputStream)
            for _ in range(numberOfVariableDatumRecords)
        ]


@dataclass(slots=True)
class IsGroupOfPdu(EntityManagementFamilyPdu):
    """Section 7.8.3 IsGroupOf PDU

    Communicates the individual states of a group of entities. The
    Grouped Entity Descriptions are category-dependent (§7.8.3);
    represented as EntityIdentifier entries, the form used by the
    defined categories. Base PDU size is 40 bytes plus descriptions."""

    pduType: ClassVar[int] = 34  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "groupedEntityCategory": 213,
    }

    groupEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    groupedEntityCategory: enum8 = 0  # [UID 213]
    groupedEntityDescriptions: list[EntityIdentifier] = field(
        default_factory=list)

    pad: uint32 = field(init=False, default=0)
    latitude: float64 = 0.0
    longitude: float64 = 0.0

    @property
    def numberOfGroupedEntities(self) -> uint8:
        return len(self.groupedEntityDescriptions)

    def _marshalledBodySize(self) -> int:
        return (self.groupEntityID.marshalledSize()
                + 1 + 1 + 4 + 8 + 8
                + sum(d.marshalledSize()
                      for d in self.groupedEntityDescriptions))

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.groupEntityID.serialize(outputStream)
        outputStream.write_uint8(self.groupedEntityCategory)
        outputStream.write_uint8(self.numberOfGroupedEntities)
        outputStream.write_uint32(self.pad)
        outputStream.write_float64(self.latitude)
        outputStream.write_float64(self.longitude)
        for description in self.groupedEntityDescriptions:
            description.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.groupEntityID = EntityIdentifier.parse(inputStream)
        self.groupedEntityCategory = rich_or_int(
            213, inputStream.read_uint8())
        numberOfGroupedEntities = inputStream.read_uint8()
        self.pad = inputStream.read_uint32()
        self.latitude = inputStream.read_float64()
        self.longitude = inputStream.read_float64()
        self.groupedEntityDescriptions = [
            EntityIdentifier.parse(inputStream)
            for _ in range(numberOfGroupedEntities)
        ]


@dataclass(slots=True)
class TransferOwnershipPdu(EntityManagementFamilyPdu):
    """Section 7.9.4 Transfer Ownership PDU

    Initiates the dynamic allocation and control of simulation entities
    between two simulation applications, carrying record sets (§6.2.73).
    Base PDU size is 40 bytes plus record sets."""

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
        return len(self.recordSets)

    def _marshalledBodySize(self) -> int:
        return (self.originatingEntityID.marshalledSize()
                + self.receivingEntityID.marshalledSize()
                + 4 + 1 + 1
                + self.transferEntityID.marshalledSize()
                + 4
                + sum(rs.marshalledSize() for rs in self.recordSets))

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.originatingEntityID.serialize(outputStream)
        self.receivingEntityID.serialize(outputStream)
        outputStream.write_uint32(self.requestID)
        outputStream.write_uint8(self.requiredReliabilityService)
        outputStream.write_uint8(self.transferType)
        self.transferEntityID.serialize(outputStream)
        outputStream.write_uint32(self.numberOfRecordSets)
        for recordSet in self.recordSets:
            recordSet.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.originatingEntityID = EntityIdentifier.parse(inputStream)
        self.receivingEntityID = EntityIdentifier.parse(inputStream)
        self.requestID = inputStream.read_uint32()
        self.requiredReliabilityService = rich_or_int(
            74, inputStream.read_uint8())
        self.transferType = rich_or_int(224, inputStream.read_uint8())
        self.transferEntityID = EntityIdentifier.parse(inputStream)
        numberOfRecordSets = inputStream.read_uint32()
        self.recordSets = [
            RecordSpecificationElement.parseFrom(inputStream)
            for _ in range(numberOfRecordSets)
        ]


@dataclass(slots=True)
class IsPartOfPdu(EntityManagementFamilyPdu):
    """Section 7.9.5 IsPartOf PDU

    Requests hierarchical linkage of separately hosted simulation
    entities (part-to-host). Total PDU size is 50 bytes."""

    pduType: ClassVar[int] = 36  # [UID 4]

    # XML spelling kept verbatim ("orginatingEntityID")
    orginatingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    receivingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    relationship: Relationship = field(default_factory=Relationship)
    partLocation: Vector3Float = field(default_factory=Vector3Float)
    namedLocationID: NamedLocationIdentification = field(
        default_factory=NamedLocationIdentification)
    partEntityType: EntityType = field(default_factory=EntityType)

    def _marshalledBodySize(self) -> int:
        return (self.orginatingEntityID.marshalledSize()
                + self.receivingEntityID.marshalledSize()
                + self.relationship.marshalledSize()
                + self.partLocation.marshalledSize()
                + self.namedLocationID.marshalledSize()
                + self.partEntityType.marshalledSize())

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.orginatingEntityID.serialize(outputStream)
        self.receivingEntityID.serialize(outputStream)
        self.relationship.serialize(outputStream)
        self.partLocation.serialize(outputStream)
        self.namedLocationID.serialize(outputStream)
        self.partEntityType.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.orginatingEntityID = EntityIdentifier.parse(inputStream)
        self.receivingEntityID = EntityIdentifier.parse(inputStream)
        self.relationship = Relationship()
        self.relationship.parse(inputStream)
        self.partLocation.parse(inputStream)
        self.namedLocationID = NamedLocationIdentification()
        self.namedLocationID.parse(inputStream)
        self.partEntityType = EntityType.parse(inputStream)
