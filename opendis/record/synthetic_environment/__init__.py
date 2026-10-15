"""Synthetic Environment family (IEEE 1278.1-2012 §7.10) — target-state PDUs.

Wire ground truth: submodules/open-dis-spec-xml/xml/SyntheticEnvironmentFamilyPdus.xml.
Environmental Process, Point/Linear/Areal Object State, plus the Object
Type/Identifier records, Linear Segment Parameter, and the generic
Environment record (opaque geometry, typed decoders deferred).

Scope note: GriddedDataPdu (type 42) — grid-axis descriptors × grid
data representation types 0–6 — is NOT implemented in this pass; its
pduType stays unregistered, so datagrams degrade to the lossless
``UnrecognizedPdu`` fallback (see docs/design/sample-review.md).

Python-side deltas from the XML (sample-review rulings): the bitfield-
mapped appearance/modification fields (uids 229, 240, 242, 249) stay raw
integers in this pass (views deferred, PduStatus precedent).
"""

from dataclasses import dataclass, field
from typing import ClassVar

from opendis.enum_registry import rich_or_int
from opendis.record.common import (
    EntityIdentifier,
    EntityType,
    EulerAngles,
    SimulationAddress,
    Vector3Double,
)
from opendis.record.pdu import Pdu
from opendis.stream import DataInputStream, DataOutputStream
from opendis.types import enum8, enum32, float32, uint8, uint16, uint32

__all__ = [
    "ArealObjectStatePdu",
    "EnvironmentRecord",
    "EnvironmentalProcessPdu",
    "LinearObjectStatePdu",
    "LinearSegmentParameter",
    "ObjectIdentifier",
    "ObjectType",
    "PointObjectStatePdu",
    "SyntheticEnvironmentFamilyPdu",
]


def _padTo32(byteCount: int) -> int:
    """Pad bytes needed to bring a datagram to a 32-bit boundary."""
    return (4 - byteCount % 4) % 4


@dataclass(frozen=True, slots=True)
class ObjectIdentifier:
    """§6.2.63 Object Identifier record

    The unique designation of an environmental object.
    """

    simulationAddress: SimulationAddress = field(default_factory=SimulationAddress)
    objectNumber: uint16 = 0

    def marshalledSize(self) -> int:
        return self.simulationAddress.marshalledSize() + 2

    def serialize(self, outputStream: DataOutputStream) -> None:
        self.simulationAddress.serialize(outputStream)
        outputStream.write_uint16(self.objectNumber)

    @classmethod
    def parse(cls, inputStream: DataInputStream) -> "ObjectIdentifier":
        simulationAddress = SimulationAddress.parse(inputStream)
        objectNumber = inputStream.read_uint16()
        return cls(simulationAddress, objectNumber)


@dataclass(frozen=True, slots=True)
class ObjectType:
    """§6.2.64 Object Type record

    The unique designation of an environmental object.
    """

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "domain": 8,
        "objectKind": 225,
    }

    domain: enum8 = 0  # [UID 8]
    objectKind: enum8 = 0  # [UID 225]
    category: uint8 = 0
    subCategory: uint8 = 0

    def marshalledSize(self) -> int:
        return 4

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint8(self.domain)
        outputStream.write_uint8(self.objectKind)
        outputStream.write_uint8(self.category)
        outputStream.write_uint8(self.subCategory)

    @classmethod
    def parse(cls, inputStream: DataInputStream) -> "ObjectType":
        domain = rich_or_int(8, inputStream.read_uint8())
        objectKind = rich_or_int(225, inputStream.read_uint8())
        category = inputStream.read_uint8()
        subCategory = inputStream.read_uint8()
        return cls(domain, objectKind, category, subCategory)


@dataclass(slots=True)
class LinearSegmentParameter:
    """§6.2.52 Linear Segment Parameter record

    The specification of an individual segment of a linear segment synthetic
    environment object in a Linear Object State PDU.
    """

    segmentNumber: uint8 = 0
    segmentModification: uint8 = 0  # [UID 241]
    generalSegmentAppearance: uint16 = 0  # [UID 229]
    specificSegmentAppearance: uint32 = 0
    segmentLocation: Vector3Double = field(default_factory=Vector3Double)
    segmentOrientation: EulerAngles = field(default_factory=EulerAngles)
    segmentLength: float32 = 0.0
    segmentWidth: float32 = 0.0
    segmentHeight: float32 = 0.0
    segmentDepth: float32 = 0.0
    # Padding ruling: explicit attribute, out of __init__ (zero by default,
    # holds the wire value after parse so odd pads round-trip byte-exact).
    padding: uint32 = field(init=False, default=0)

    def marshalledSize(self) -> int:
        return (
            1
            + 1
            + 2
            + 4
            + self.segmentLocation.marshalledSize()
            + self.segmentOrientation.marshalledSize()
            + 4
            + 4
            + 4
            + 4
            + 4
        )

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint8(self.segmentNumber)
        outputStream.write_uint8(int(self.segmentModification))
        outputStream.write_uint16(int(self.generalSegmentAppearance))
        outputStream.write_uint32(self.specificSegmentAppearance)
        self.segmentLocation.serialize(outputStream)
        self.segmentOrientation.serialize(outputStream)
        outputStream.write_float32(self.segmentLength)
        outputStream.write_float32(self.segmentWidth)
        outputStream.write_float32(self.segmentHeight)
        outputStream.write_float32(self.segmentDepth)
        outputStream.write_uint32(self.padding)

    def parse(self, inputStream: DataInputStream) -> None:
        self.segmentNumber = inputStream.read_uint8()
        self.segmentModification = inputStream.read_uint8()
        self.generalSegmentAppearance = inputStream.read_uint16()
        self.specificSegmentAppearance = inputStream.read_uint32()
        self.segmentLocation.parse(inputStream)
        self.segmentOrientation.parse(inputStream)
        self.segmentLength = inputStream.read_float32()
        self.segmentWidth = inputStream.read_float32()
        self.segmentHeight = inputStream.read_float32()
        self.segmentDepth = inputStream.read_float32()
        self.padding = inputStream.read_uint32()

    @classmethod
    def parseFrom(cls, inputStream: DataInputStream) -> "LinearSegmentParameter":
        """Construct a new record from the stream (list-parse helper; the
        mutating ``parse`` above satisfies the Record protocol)."""
        item = cls()
        item.parse(inputStream)
        return item


@dataclass(slots=True)
class EnvironmentRecord:
    """Information about a geometry, a state associated with a geometry, a
    bounding volume, or an associated entity ID.  6.2.31, not fully defined.
    'The current definitions can be found in DIS PCR 240'.

    The geometry stays opaque — typed per-record decoders ride the registry
    later (§6.2.31, DIS PCR 240).
    """

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "environmentType": 250,
    }

    environmentType: enum32 = 0  # [UID 250]
    index: uint8 = 0
    geometry: bytes = b""
    padding1: uint8 = field(init=False, default=0)

    def marshalledSize(self):
        return 8 + len(self.geometry) + self._padTo64(len(self.geometry))

    def serialize(self, outputStream: DataOutputStream):
        outputStream.write_uint32(self.environmentType)
        outputStream.write_uint16(self.length)
        outputStream.write_uint8(self.index)
        outputStream.write_uint8(self.padding1)
        outputStream.write_bytes(self.geometry)
        padding = self._padTo64(len(self.geometry))
        if padding:
            outputStream.write_bytes(b"\x00" * padding)

    def parse(self, inputStream: DataInputStream):
        self.environmentType = rich_or_int(250, inputStream.read_uint32())
        length = inputStream.read_uint16()  # bits, header included
        self.index = inputStream.read_uint8()
        self.padding1 = inputStream.read_uint8()
        geometryBytes = max(0, length // 8 - 8)
        self.geometry = inputStream.read_bytes(geometryBytes)
        padding = self._padTo64(geometryBytes)
        if padding:
            inputStream.read_bytes(padding)

    @staticmethod
    def _padTo64(byteCount: int) -> int:
        return (8 - byteCount % 8) % 8

    @property
    def length(self) -> uint16:
        """Record length IN BITS — derived from the geometry bytes."""
        return (8 + len(self.geometry)) * 8

    @classmethod
    def parseFrom(cls, inputStream: DataInputStream) -> "EnvironmentRecord":
        """Construct a new record from the stream (list-parse helper; the
        mutating ``parse`` above satisfies the Record protocol)."""
        item = cls()
        item.parse(inputStream)
        return item


@dataclass(slots=True)
class SyntheticEnvironmentFamilyPdu(Pdu):
    """§7.10: Abstract superclass for synthetic environment PDUs."""

    protocolFamily: ClassVar[int] = 9  # [UID 5] Synthetic Environment


@dataclass(slots=True)
class EnvironmentalProcessPdu(SyntheticEnvironmentFamilyPdu):
    """§7.10.2 Environmental Process PDU

    Used to communicate information about environmental effects and
    processes.
    """

    pduType: ClassVar[int] = 41  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "modelType": 248,
    }

    environementalProcessID: ObjectIdentifier = field(default_factory=ObjectIdentifier)
    environmentType: EntityType = field(default_factory=EntityType)
    modelType: enum8 = 0  # [UID 248]
    environmentStatus: uint8 = 0  # [UID 249] bitmap
    sequenceNumber: uint16 = 0
    environmentRecords: list[EnvironmentRecord] = field(default_factory=list)

    @property
    def numberOfEnvironmentRecords(self) -> uint16:
        """number of environment records."""
        return len(self.environmentRecords)

    def _marshalledBodySize(self) -> int:
        return (
            self.environementalProcessID.marshalledSize()
            + self.environmentType.marshalledSize()
            + 1
            + 1
            + 2
            + 2
            + sum(item.marshalledSize() for item in self.environmentRecords)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.environementalProcessID.serialize(outputStream)
        self.environmentType.serialize(outputStream)
        outputStream.write_uint8(self.modelType)
        outputStream.write_uint8(int(self.environmentStatus))
        outputStream.write_uint16(self.numberOfEnvironmentRecords)
        outputStream.write_uint16(self.sequenceNumber)
        for item in self.environmentRecords:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.environementalProcessID = ObjectIdentifier.parse(inputStream)
        self.environmentType = EntityType.parse(inputStream)
        self.modelType = rich_or_int(248, inputStream.read_uint8())
        self.environmentStatus = inputStream.read_uint8()
        numberOfEnvironmentRecords = inputStream.read_uint16()
        self.sequenceNumber = inputStream.read_uint16()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.environmentRecords = [
            EnvironmentRecord.parseFrom(inputStream)
            for _ in range(numberOfEnvironmentRecords)
        ]


@dataclass(slots=True)
class PointObjectStatePdu(SyntheticEnvironmentFamilyPdu):
    """§7.10.4 Point Object State PDU

    Used to communicate detailed information about the addition/modification
    of a synthetic environment object that is geometrically anchored to the
    terrain with a single point.
    """

    pduType: ClassVar[int] = 43  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "forceID": 6,
    }

    objectID: EntityIdentifier = field(default_factory=EntityIdentifier)
    referencedObjectID: ObjectIdentifier = field(default_factory=ObjectIdentifier)
    updateNumber: uint16 = 0
    forceID: enum8 = 0  # [UID 6]
    modifications: uint8 = 0  # [UID 240]
    objectType: ObjectType = field(default_factory=ObjectType)
    objectLocation: Vector3Double = field(default_factory=Vector3Double)
    objectOrientation: EulerAngles = field(default_factory=EulerAngles)
    specificObjectAppearance: uint32 = 0
    generalObjectAppearance: uint16 = 0  # [UID 229]
    requesterID: SimulationAddress = field(default_factory=SimulationAddress)
    receivingID: SimulationAddress = field(default_factory=SimulationAddress)
    padding1: uint16 = field(init=False, default=0)
    pad2: uint32 = field(init=False, default=0)

    def _marshalledBodySize(self) -> int:
        return (
            self.objectID.marshalledSize()
            + self.referencedObjectID.marshalledSize()
            + 2
            + 1
            + 1
            + self.objectType.marshalledSize()
            + self.objectLocation.marshalledSize()
            + self.objectOrientation.marshalledSize()
            + 4
            + 2
            + 2
            + self.requesterID.marshalledSize()
            + self.receivingID.marshalledSize()
            + 4
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.objectID.serialize(outputStream)
        self.referencedObjectID.serialize(outputStream)
        outputStream.write_uint16(self.updateNumber)
        outputStream.write_uint8(self.forceID)
        outputStream.write_uint8(int(self.modifications))
        self.objectType.serialize(outputStream)
        self.objectLocation.serialize(outputStream)
        self.objectOrientation.serialize(outputStream)
        outputStream.write_uint32(self.specificObjectAppearance)
        outputStream.write_uint16(int(self.generalObjectAppearance))
        outputStream.write_uint16(self.padding1)
        self.requesterID.serialize(outputStream)
        self.receivingID.serialize(outputStream)
        outputStream.write_uint32(self.pad2)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.objectID = EntityIdentifier.parse(inputStream)
        self.referencedObjectID = ObjectIdentifier.parse(inputStream)
        self.updateNumber = inputStream.read_uint16()
        self.forceID = rich_or_int(6, inputStream.read_uint8())
        self.modifications = inputStream.read_uint8()
        self.objectType = ObjectType.parse(inputStream)
        self.objectLocation.parse(inputStream)
        self.objectOrientation.parse(inputStream)
        self.specificObjectAppearance = inputStream.read_uint32()
        self.generalObjectAppearance = inputStream.read_uint16()
        self.padding1 = inputStream.read_uint16()
        self.requesterID = SimulationAddress.parse(inputStream)
        self.receivingID = SimulationAddress.parse(inputStream)
        self.pad2 = inputStream.read_uint32()


@dataclass(slots=True)
class LinearObjectStatePdu(SyntheticEnvironmentFamilyPdu):
    """§7.10.5 Linear Object State PDU

    Used to communicate detailed information about the addition/modification
    of a synthetic environment object that is geometrically anchored to the
    terrain with one point and has size and orientation.
    """

    pduType: ClassVar[int] = 44  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "forceID": 6,
    }

    objectID: ObjectIdentifier = field(default_factory=ObjectIdentifier)
    referencedObjectID: ObjectIdentifier = field(default_factory=ObjectIdentifier)
    updateNumber: uint16 = 0
    forceID: enum8 = 0  # [UID 6]
    requesterID: SimulationAddress = field(default_factory=SimulationAddress)
    receivingID: SimulationAddress = field(default_factory=SimulationAddress)
    objectType: ObjectType = field(default_factory=ObjectType)
    linearSegmentParameters: list[LinearSegmentParameter] = field(default_factory=list)

    @property
    def numberOfLinearSegments(self) -> uint8:
        """number of linear segment parameters."""
        return len(self.linearSegmentParameters)

    def _marshalledBodySize(self) -> int:
        return (
            self.objectID.marshalledSize()
            + self.referencedObjectID.marshalledSize()
            + 2
            + 1
            + 1
            + self.requesterID.marshalledSize()
            + self.receivingID.marshalledSize()
            + self.objectType.marshalledSize()
            + sum(item.marshalledSize() for item in self.linearSegmentParameters)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.objectID.serialize(outputStream)
        self.referencedObjectID.serialize(outputStream)
        outputStream.write_uint16(self.updateNumber)
        outputStream.write_uint8(self.forceID)
        outputStream.write_uint8(self.numberOfLinearSegments)
        self.requesterID.serialize(outputStream)
        self.receivingID.serialize(outputStream)
        self.objectType.serialize(outputStream)
        for item in self.linearSegmentParameters:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.objectID = ObjectIdentifier.parse(inputStream)
        self.referencedObjectID = ObjectIdentifier.parse(inputStream)
        self.updateNumber = inputStream.read_uint16()
        self.forceID = rich_or_int(6, inputStream.read_uint8())
        numberOfLinearSegments = inputStream.read_uint8()
        self.requesterID = SimulationAddress.parse(inputStream)
        self.receivingID = SimulationAddress.parse(inputStream)
        self.objectType = ObjectType.parse(inputStream)
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.linearSegmentParameters = [
            LinearSegmentParameter.parseFrom(inputStream)
            for _ in range(numberOfLinearSegments)
        ]


@dataclass(slots=True)
class ArealObjectStatePdu(SyntheticEnvironmentFamilyPdu):
    """§7.10.6 Areal Object State PDU

    Used to communicate detailed information about the addition/modification
    of a synthetic environment object that is geometrically anchored to the
    terrain with a set of three or more points that come to a closure.
    """

    pduType: ClassVar[int] = 45  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "forceID": 6,
    }

    objectID: ObjectIdentifier = field(default_factory=ObjectIdentifier)
    referencedObjectID: ObjectIdentifier = field(default_factory=ObjectIdentifier)
    updateNumber: uint16 = 0
    forceID: enum8 = 0  # [UID 6]
    modifications: uint8 = 0  # [UID 242]
    objectType: ObjectType = field(default_factory=ObjectType)
    specificObjectAppearance: uint32 = 0
    generalObjectAppearance: uint16 = 0
    requesterID: SimulationAddress = field(default_factory=SimulationAddress)
    receivingID: SimulationAddress = field(default_factory=SimulationAddress)
    objectLocation: list[Vector3Double] = field(default_factory=list)

    @property
    def numberOfPoints(self) -> uint16:
        """Number of points."""
        return len(self.objectLocation)

    def _marshalledBodySize(self) -> int:
        return (
            self.objectID.marshalledSize()
            + self.referencedObjectID.marshalledSize()
            + 2
            + 1
            + 1
            + self.objectType.marshalledSize()
            + 4
            + 2
            + 2
            + self.requesterID.marshalledSize()
            + self.receivingID.marshalledSize()
            + sum(item.marshalledSize() for item in self.objectLocation)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.objectID.serialize(outputStream)
        self.referencedObjectID.serialize(outputStream)
        outputStream.write_uint16(self.updateNumber)
        outputStream.write_uint8(self.forceID)
        outputStream.write_uint8(int(self.modifications))
        self.objectType.serialize(outputStream)
        outputStream.write_uint32(self.specificObjectAppearance)
        outputStream.write_uint16(self.generalObjectAppearance)
        outputStream.write_uint16(self.numberOfPoints)
        self.requesterID.serialize(outputStream)
        self.receivingID.serialize(outputStream)
        for item in self.objectLocation:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.objectID = ObjectIdentifier.parse(inputStream)
        self.referencedObjectID = ObjectIdentifier.parse(inputStream)
        self.updateNumber = inputStream.read_uint16()
        self.forceID = rich_or_int(6, inputStream.read_uint8())
        self.modifications = inputStream.read_uint8()
        self.objectType = ObjectType.parse(inputStream)
        self.specificObjectAppearance = inputStream.read_uint32()
        self.generalObjectAppearance = inputStream.read_uint16()
        numberOfPoints = inputStream.read_uint16()
        self.requesterID = SimulationAddress.parse(inputStream)
        self.receivingID = SimulationAddress.parse(inputStream)
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.objectLocation = [
            Vector3Double.parseFrom(inputStream) for _ in range(numberOfPoints)
        ]
