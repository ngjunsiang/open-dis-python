"""Synthetic Environment family (IEEE 1278.1-2012 §7.10) — target-state PDUs.

Wire ground truth: submodules/open-dis-spec-xml/xml/SyntheticEnvironmentFamilyPdus.xml.
Environmental Process, Gridded Data, Point/Linear/Areal Object State,
plus the Object Type/Identifier records, Linear Segment Parameter, and
the generic Environment record (opaque geometry, typed decoders
deferred). The Gridded Data PDU (type 42) carries the §6.2.40 grid-axis
descriptors (fixed/variable dispatch) and the §6.2.41 Grid Data records
(representation types 0-2; the XML declares exactly those three).

Python-side deltas from the XML (sample-review rulings): the bitfield-
mapped appearance/modification fields (uids 229, 240, 242, 249) stay raw
integers (the 2026-10-16 viewable-primitive ruling: rich presentation
belongs to the optional plugin layer); the grid-data record count is
derived per Table 192 (the XML's countFieldName is an upstream bug).
"""

from dataclasses import dataclass, field
from typing import ClassVar

from opendis.enum_registry import rich_or_int
from opendis.record.common import (
    ClockTime,
    EntityIdentifier,
    EntityType,
    EulerAngles,
    SimulationAddress,
    Vector3Double,
)
from opendis.record.pdu import Pdu
from opendis.stream import DataInputStream, DataOutputStream
from opendis.types import enum8, enum16, enum32, float32, float64, uint8, uint16, uint32

__all__ = [
    "ArealObjectStatePdu",
    "EnvironmentRecord",
    "EnvironmentalProcessPdu",
    "GridAxisDescriptorFixed",
    "GridAxisDescriptorVariable",
    "GridDataType0",
    "GridDataType1",
    "GridDataType2",
    "GriddedDataPdu",
    "LinearObjectStatePdu",
    "LinearSegmentParameter",
    "ObjectIdentifier",
    "ObjectType",
    "PointObjectStatePdu",
    "SyntheticEnvironmentFamilyPdu",
]


def _padTo16(byteCount: int) -> int:
    """Pad bytes needed to bring a datagram to a 16-bit boundary."""
    return (2 - byteCount % 2) % 2


def _padTo32(byteCount: int) -> int:
    """Pad bytes needed to bring a datagram to a 32-bit boundary."""
    return (4 - byteCount % 4) % 4


def _padTo64(byteCount: int) -> int:
    """Pad bytes needed to bring a datagram to a 64-bit boundary."""
    return (8 - byteCount % 8) % 8


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
class GridAxisDescriptorFixed:
    """§6.2.40

    Grid axis record for fixed data.
    """

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "axisType": 377,
    }

    domainInitialXi: float64 = 0.0
    domainFinalXi: float64 = 0.0
    domainPointsXi: uint16 = 0
    interleafFactor: uint8 = 0
    axisType: enum8 = 0  # [UID 377]
    numberOfPointsOnXiAxis: uint16 = 0
    initialIndex: uint16 = 0

    def marshalledSize(self) -> int:
        return 24

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_float64(self.domainInitialXi)
        outputStream.write_float64(self.domainFinalXi)
        outputStream.write_uint16(self.domainPointsXi)
        outputStream.write_uint8(self.interleafFactor)
        outputStream.write_uint8(self.axisType)
        outputStream.write_uint16(self.numberOfPointsOnXiAxis)
        outputStream.write_uint16(self.initialIndex)

    def parse(self, inputStream: DataInputStream) -> None:
        self.domainInitialXi = inputStream.read_float64()
        self.domainFinalXi = inputStream.read_float64()
        self.domainPointsXi = inputStream.read_uint16()
        self.interleafFactor = inputStream.read_uint8()
        self.axisType = rich_or_int(377, inputStream.read_uint8())
        self.numberOfPointsOnXiAxis = inputStream.read_uint16()
        self.initialIndex = inputStream.read_uint16()

    @classmethod
    def parseFrom(cls, inputStream: DataInputStream) -> "GridAxisDescriptorFixed":
        """Construct a new record from the stream (list-parse helper; the
        mutating ``parse`` above satisfies the Record protocol)."""
        item = cls()
        item.parse(inputStream)
        return item


@dataclass(slots=True)
class GridAxisDescriptorVariable:
    """§6.2.40

    Grid axis descriptor for variable spacing axis data.
    """

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "axisType": 377,
    }

    domainInitialXi: float64 = 0.0
    domainFinalXi: float64 = 0.0
    domainPointsXi: uint16 = 0
    interleafFactor: uint8 = 0
    axisType: enum8 = 0  # [UID 377]
    initialIndex: uint16 = 0
    coordinateScaleXi: float64 = 0.0
    coordinateOffsetXi: float64 = 0.0
    xiValues: list[uint16] = field(default_factory=list)

    @property
    def numberOfPointsOnXiAxis(self) -> uint16:
        """Number of grid locations along Xi axis (derived from xiValues)."""
        return len(self.xiValues)

    def _unpaddedBodySize(self) -> int:
        return 8 + 8 + 2 + 1 + 1 + 2 + 2 + 8 + 8 + 2 * len(self.xiValues)

    def marshalledSize(self) -> int:
        return self._unpaddedBodySize() + _padTo64(self._unpaddedBodySize())

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_float64(self.domainInitialXi)
        outputStream.write_float64(self.domainFinalXi)
        outputStream.write_uint16(self.domainPointsXi)
        outputStream.write_uint8(self.interleafFactor)
        outputStream.write_uint8(self.axisType)
        outputStream.write_uint16(self.numberOfPointsOnXiAxis)
        outputStream.write_uint16(self.initialIndex)
        outputStream.write_float64(self.coordinateScaleXi)
        outputStream.write_float64(self.coordinateOffsetXi)
        for item in self.xiValues:
            outputStream.write_uint16(item)
        padding = _padTo64(0 + self._unpaddedBodySize())
        if padding:
            outputStream.write_bytes(b"\x00" * padding)

    def parse(self, inputStream: DataInputStream) -> None:
        self.domainInitialXi = inputStream.read_float64()
        self.domainFinalXi = inputStream.read_float64()
        self.domainPointsXi = inputStream.read_uint16()
        self.interleafFactor = inputStream.read_uint8()
        self.axisType = rich_or_int(377, inputStream.read_uint8())
        numberOfPointsOnXiAxis = inputStream.read_uint16()
        self.initialIndex = inputStream.read_uint16()
        self.coordinateScaleXi = inputStream.read_float64()
        self.coordinateOffsetXi = inputStream.read_float64()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.xiValues = [
            inputStream.read_uint16() for _ in range(numberOfPointsOnXiAxis)
        ]
        padding = _padTo64(0 + self._unpaddedBodySize())
        if padding:
            inputStream.read_bytes(padding)


@dataclass(slots=True)
class GridDataType0:
    """6.2.41, table 68."""

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "sampleType": 246,
        "dataRepresentation": 247,
    }

    sampleType: enum16 = 0  # [UID 246]
    dataRepresentation: enum16 = 0  # [UID 247]
    dataValues: list[uint8] = field(default_factory=list)

    @property
    def numberOfBytes(self) -> uint16:
        """numberOfBytes"""
        return len(self.dataValues)

    def _unpaddedBodySize(self) -> int:
        return 2 + 2 + 2 + len(self.dataValues)

    def marshalledSize(self) -> int:
        return self._unpaddedBodySize() + _padTo16(self._unpaddedBodySize())

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.sampleType)
        outputStream.write_uint16(self.dataRepresentation)
        outputStream.write_uint16(self.numberOfBytes)
        for item in self.dataValues:
            outputStream.write_uint8(item)
        padding = _padTo16(0 + self._unpaddedBodySize())
        if padding:
            outputStream.write_bytes(b"\x00" * padding)

    def parse(self, inputStream: DataInputStream) -> None:
        self.sampleType = rich_or_int(246, inputStream.read_uint16())
        self.dataRepresentation = rich_or_int(247, inputStream.read_uint16())
        numberOfBytes = inputStream.read_uint16()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.dataValues = [inputStream.read_uint8() for _ in range(numberOfBytes)]
        padding = _padTo16(0 + self._unpaddedBodySize())
        if padding:
            inputStream.read_bytes(padding)


@dataclass(slots=True)
class GridDataType1:
    """6.2.41, table 69."""

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "sampleType": 246,
        "dataRepresentation": 247,
    }

    sampleType: enum16 = 0  # [UID 246]
    dataRepresentation: enum16 = 0  # [UID 247]
    fieldScale: float32 = 0.0
    fieldOffset: float32 = 0.0
    dataValues: list[uint16] = field(default_factory=list)

    @property
    def numberOfValues(self) -> uint16:
        """numberOfValues"""
        return len(self.dataValues)

    def _unpaddedBodySize(self) -> int:
        return 2 + 2 + 4 + 4 + 2 + 2 * len(self.dataValues)

    def marshalledSize(self) -> int:
        return self._unpaddedBodySize() + _padTo32(self._unpaddedBodySize())

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.sampleType)
        outputStream.write_uint16(self.dataRepresentation)
        outputStream.write_float32(self.fieldScale)
        outputStream.write_float32(self.fieldOffset)
        outputStream.write_uint16(self.numberOfValues)
        for item in self.dataValues:
            outputStream.write_uint16(item)
        padding = _padTo32(0 + self._unpaddedBodySize())
        if padding:
            outputStream.write_bytes(b"\x00" * padding)

    def parse(self, inputStream: DataInputStream) -> None:
        self.sampleType = rich_or_int(246, inputStream.read_uint16())
        self.dataRepresentation = rich_or_int(247, inputStream.read_uint16())
        self.fieldScale = inputStream.read_float32()
        self.fieldOffset = inputStream.read_float32()
        numberOfValues = inputStream.read_uint16()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.dataValues = [inputStream.read_uint16() for _ in range(numberOfValues)]
        padding = _padTo32(0 + self._unpaddedBodySize())
        if padding:
            inputStream.read_bytes(padding)


@dataclass(slots=True)
class GridDataType2:
    """6.2.41, table 70."""

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "sampleType": 246,
        "dataRepresentation": 247,
    }

    sampleType: enum16 = 0  # [UID 246]
    dataRepresentation: enum16 = 0  # [UID 247]
    dataValues: list[float32] = field(default_factory=list)
    padding: uint16 = field(init=False, default=0)

    @property
    def numberOfValues(self) -> uint16:
        """numberOfValues"""
        return len(self.dataValues)

    def marshalledSize(self) -> int:
        return 2 + 2 + 2 + 2 + 4 * len(self.dataValues)

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.sampleType)
        outputStream.write_uint16(self.dataRepresentation)
        outputStream.write_uint16(self.numberOfValues)
        outputStream.write_uint16(self.padding)
        for item in self.dataValues:
            outputStream.write_float32(item)

    def parse(self, inputStream: DataInputStream) -> None:
        self.sampleType = rich_or_int(246, inputStream.read_uint16())
        self.dataRepresentation = rich_or_int(247, inputStream.read_uint16())
        numberOfValues = inputStream.read_uint16()
        self.padding = inputStream.read_uint16()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.dataValues = [inputStream.read_float32() for _ in range(numberOfValues)]


@dataclass(slots=True)
class GriddedDataPdu(SyntheticEnvironmentFamilyPdu):
    """§7.10.3 Gridded Data PDU

    Used to communicate information about global, spatially varying
    environmental effects.

    The grid-data record count is derived: G = vectorDimension x the product
    of the per-axis point counts (Table 192) — the XML's
    countFieldName="numberOfGridAxes" on the list is an upstream bug. Axis
    descriptors dispatch on their trailing axisType byte ([UID 377]); grid
    data records on dataRepresentation ([UID 247], formats 0-2 per §6.2.41).
    """

    pduType: ClassVar[int] = 42  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "coordinateSystem": 244,
        "constantGrid": 245,
    }

    environmentalSimulationApplicationID: EntityIdentifier = field(
        default_factory=EntityIdentifier
    )
    fieldNumber: uint16 = 0
    pduNumber: uint16 = 0
    pduTotal: uint16 = 0
    coordinateSystem: enum16 = 0  # [UID 244]
    constantGrid: enum8 = 0  # [UID 245]
    environmentType: EntityType = field(default_factory=EntityType)
    orientation: EulerAngles = field(default_factory=EulerAngles)
    sampleTime: ClockTime = field(default_factory=ClockTime)
    totalValues: uint32 = 0
    vectorDimension: uint8 = 0
    gridAxisDescriptors: list[GridAxisDescriptorFixed] = field(default_factory=list)
    gridDataRecords: list[GridDataType0 | GridDataType1 | GridDataType2] = field(
        default_factory=list
    )
    padding1: uint8 = field(init=False, default=0)
    padding2: uint16 = field(init=False, default=0)

    @property
    def numberOfGridAxes(self) -> uint8:
        """number of grid axes for the environmental data."""
        return len(self.gridAxisDescriptors)

    def _marshalledBodySize(self):
        return (
            6
            + 2
            + 2
            + 2
            + 2
            + 1
            + 1
            + self.environmentType.marshalledSize()
            + self.orientation.marshalledSize()
            + self.sampleTime.marshalledSize()
            + 4
            + 1
            + 1
            + 2
            + sum(axis.marshalledSize() for axis in self.gridAxisDescriptors)
            + sum(record.marshalledSize() for record in self.gridDataRecords)
        )

    def _serializeBody(self, outputStream: DataOutputStream):
        self.environmentalSimulationApplicationID.serialize(outputStream)
        outputStream.write_uint16(self.fieldNumber)
        outputStream.write_uint16(self.pduNumber)
        outputStream.write_uint16(self.pduTotal)
        outputStream.write_uint16(self.coordinateSystem)
        outputStream.write_uint8(self.numberOfGridAxes)
        outputStream.write_uint8(self.constantGrid)
        self.environmentType.serialize(outputStream)
        self.orientation.serialize(outputStream)
        self.sampleTime.serialize(outputStream)
        outputStream.write_uint32(self.totalValues)
        outputStream.write_uint8(self.vectorDimension)
        outputStream.write_uint8(self.padding1)
        outputStream.write_uint16(self.padding2)
        for axis in self.gridAxisDescriptors:
            axis.serialize(outputStream)
        for record in self.gridDataRecords:
            record.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream):
        self.environmentalSimulationApplicationID = EntityIdentifier.parse(inputStream)
        self.fieldNumber = inputStream.read_uint16()
        self.pduNumber = inputStream.read_uint16()
        self.pduTotal = inputStream.read_uint16()
        self.coordinateSystem = rich_or_int(244, inputStream.read_uint16())
        numberOfGridAxes = inputStream.read_uint8()
        self.constantGrid = rich_or_int(245, inputStream.read_uint8())
        self.environmentType = EntityType.parse(inputStream)
        self.orientation.parse(inputStream)
        self.sampleTime.parse(inputStream)
        self.totalValues = inputStream.read_uint32()
        self.vectorDimension = inputStream.read_uint8()
        self.padding1 = inputStream.read_uint8()
        self.padding2 = inputStream.read_uint16()
        # generator: axis descriptors dispatch on their trailing axisType byte
        # ([UID 377]: 0 = regular/fixed, 1 = irregular/variable) — the XML's
        # initialClass hint carries no wire semantics
        self.gridAxisDescriptors = []
        for _ in range(numberOfGridAxes):
            domainInitialXi = inputStream.read_float64()
            domainFinalXi = inputStream.read_float64()
            domainPointsXi = inputStream.read_uint16()
            interleafFactor = inputStream.read_uint8()
            axisType = inputStream.read_uint8()
            if int(axisType) == 1:
                axis = GridAxisDescriptorVariable(
                    domainInitialXi,
                    domainFinalXi,
                    domainPointsXi,
                    interleafFactor,
                    axisType,
                )
                numberOfPointsOnXiAxis = inputStream.read_uint16()
                axis.initialIndex = inputStream.read_uint16()
                axis.coordinateScaleXi = inputStream.read_float64()
                axis.coordinateOffsetXi = inputStream.read_float64()
                axis.xiValues = [
                    inputStream.read_uint16() for _ in range(numberOfPointsOnXiAxis)
                ]
                padding = _padTo64(40 + 2 * len(axis.xiValues))
                if padding:
                    inputStream.read_bytes(padding)
            else:
                axis = GridAxisDescriptorFixed(
                    domainInitialXi,
                    domainFinalXi,
                    domainPointsXi,
                    interleafFactor,
                    axisType,
                )
                axis.numberOfPointsOnXiAxis = inputStream.read_uint16()
                axis.initialIndex = inputStream.read_uint16()
            self.gridAxisDescriptors.append(axis)
        # generator: Table 192's G = V x product of the per-axis point counts —
        # the record count is derived, not stored (the XML's
        # countFieldName="numberOfGridAxes" is an upstream bug)
        dataCount = self.vectorDimension
        for axis in self.gridAxisDescriptors:
            dataCount *= axis.numberOfPointsOnXiAxis
        self.gridDataRecords = []
        for _ in range(dataCount):
            sampleType = inputStream.read_uint16()
            dataRepresentation = inputStream.read_uint16()
            # generator: representation types 3-6 have no record format
            # (§6.2.41 defines 0-2 only); stop before misparsing the rest
            if int(dataRepresentation) == 0:
                record = GridDataType0(sampleType, dataRepresentation)
                numberOfBytes = inputStream.read_uint16()
                record.dataValues = [
                    inputStream.read_uint8() for _ in range(numberOfBytes)
                ]
                padding = _padTo16(6 + len(record.dataValues))
                if padding:
                    inputStream.read_bytes(padding)
            elif int(dataRepresentation) == 1:
                record = GridDataType1(sampleType, dataRepresentation)
                record.fieldScale = inputStream.read_float32()
                record.fieldOffset = inputStream.read_float32()
                numberOfValues = inputStream.read_uint16()
                record.dataValues = [
                    inputStream.read_uint16() for _ in range(numberOfValues)
                ]
                padding = _padTo32(10 + 2 * len(record.dataValues))
                if padding:
                    inputStream.read_bytes(padding)
            elif int(dataRepresentation) == 2:
                record = GridDataType2(sampleType, dataRepresentation)
                numberOfValues = inputStream.read_uint16()
                record.padding = inputStream.read_uint16()
                record.dataValues = [
                    inputStream.read_float32() for _ in range(numberOfValues)
                ]
            else:
                break
            self.gridDataRecords.append(record)


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
