"""Minefield family (IEEE 1278.1-2012 §7.9) — target-state PDUs (QRP mode).

Wire ground truth: submodules/open-dis-spec-xml/xml/MinefieldFamilyPdus.xml.
Minefield State, Query, Data, and Response NACK.
"""

from dataclasses import dataclass, field
from typing import ClassVar

from opendis.bitfields import MinefieldStateAppearance
from opendis.enum_registry import rich_or_int
from opendis.record.common import (
    EntityIdentifier,
    EntityType,
    EulerAngles,
    SimulationAddress,
    Vector3Double,
    Vector3Float,
)
from opendis.record.pdu import Pdu
from opendis.stream import DataInputStream, DataOutputStream
from opendis.types import enum8, enum16, float32, uint8, uint16, uint32

__all__ = [
    "MineEmplacementTime",
    "MinefieldDataPdu",
    "MinefieldFamilyPdu",
    "MinefieldIdentifier",
    "MinefieldQueryPdu",
    "MinefieldResponseNACKPdu",
    "MinefieldStatePdu",
    "Vector2Float",
]


def _padTo32(byteCount: int) -> int:
    """Pad bytes needed to bring a datagram to a 32-bit boundary."""
    return (4 - byteCount % 4) % 4


@dataclass(frozen=True, slots=True)
class MinefieldIdentifier:
    """§6.2.56 Minefield Identifier record

    The unique designation of a minefield.
    """

    simulationAddress: SimulationAddress = field(default_factory=SimulationAddress)
    minefieldNumber: uint16 = 0

    def marshalledSize(self) -> int:
        return self.simulationAddress.marshalledSize() + 2

    def serialize(self, outputStream: DataOutputStream) -> None:
        self.simulationAddress.serialize(outputStream)
        outputStream.write_uint16(self.minefieldNumber)

    @classmethod
    def parse(cls, inputStream: DataInputStream) -> "MinefieldIdentifier":
        simulationAddress = SimulationAddress.parse(inputStream)
        minefieldNumber = inputStream.read_uint16()
        return cls(simulationAddress, minefieldNumber)


@dataclass(slots=True)
class Vector2Float:
    """Two floating point values, x, y."""

    x: float32 = 0.0
    y: float32 = 0.0

    def marshalledSize(self) -> int:
        return 8

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_float32(self.x)
        outputStream.write_float32(self.y)

    def parse(self, inputStream: DataInputStream) -> None:
        self.x = inputStream.read_float32()
        self.y = inputStream.read_float32()

    @classmethod
    def parseFrom(cls, inputStream: DataInputStream) -> "Vector2Float":
        """Construct a new record from the stream (list-parse helper; the
        mutating ``parse`` above satisfies the Record protocol)."""
        item = cls()
        item.parse(inputStream)
        return item


@dataclass(slots=True)
class MineEmplacementTime:
    """§6.2.14 Mine Emplacement Time record

    simulation time of emplacement of the mine; Clock Time record,.
    """

    hour: uint32 = 0
    timePastTheHour: uint32 = 0

    def marshalledSize(self) -> int:
        return 8

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint32(self.hour)
        outputStream.write_uint32(self.timePastTheHour)

    def parse(self, inputStream: DataInputStream) -> None:
        self.hour = inputStream.read_uint32()
        self.timePastTheHour = inputStream.read_uint32()

    @classmethod
    def parseFrom(cls, inputStream: DataInputStream) -> "MineEmplacementTime":
        """Construct a new record from the stream (list-parse helper; the
        mutating ``parse`` above satisfies the Record protocol)."""
        item = cls()
        item.parse(inputStream)
        return item


@dataclass(slots=True)
class MinefieldFamilyPdu(Pdu):
    """§7.9 Minefield family PDU

    Abstract superclass for PDUs relating to minefields.
    """

    protocolFamily: ClassVar[int] = 8  # [UID 5] Minefield


@dataclass(slots=True)
class MinefieldStatePdu(MinefieldFamilyPdu):
    """§7.9.2 Minefield State PDU

    Communicate information about the minefield, including the location,
    perimeter, and types of mines contained within it.
    """

    pduType: ClassVar[int] = 37  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "forceID": 6,
    }

    minefieldID: MinefieldIdentifier = field(default_factory=MinefieldIdentifier)
    minefieldSequence: uint16 = 0
    forceID: enum8 = 0  # [UID 6]
    minefieldType: EntityType = field(default_factory=EntityType)
    minefieldLocation: Vector3Double = field(default_factory=Vector3Double)
    minefieldOrientation: EulerAngles = field(default_factory=EulerAngles)
    appearance: uint16 = 0  # [UID 190] or the view
    protocolMode: uint16 = 0  # 2-bit protocol mode + 14 reserved bits
    perimeterPoints: list[Vector2Float] = field(default_factory=list)
    mineType: list[EntityType] = field(default_factory=list)

    @property
    def numberOfPerimeterPoints(self) -> uint8:
        """Number of permieter points."""
        return len(self.perimeterPoints)

    @property
    def numberOfMineTypes(self) -> uint16:
        """the number of different mine types employed in the minefield."""
        return len(self.mineType)

    def _marshalledBodySize(self) -> int:
        return (
            self.minefieldID.marshalledSize()
            + 2
            + 1
            + 1
            + self.minefieldType.marshalledSize()
            + 2
            + self.minefieldLocation.marshalledSize()
            + self.minefieldOrientation.marshalledSize()
            + 2
            + 2
            + sum(item.marshalledSize() for item in self.perimeterPoints)
            + sum(item.marshalledSize() for item in self.mineType)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.minefieldID.serialize(outputStream)
        outputStream.write_uint16(self.minefieldSequence)
        outputStream.write_uint8(self.forceID)
        outputStream.write_uint8(self.numberOfPerimeterPoints)
        self.minefieldType.serialize(outputStream)
        outputStream.write_uint16(self.numberOfMineTypes)
        self.minefieldLocation.serialize(outputStream)
        self.minefieldOrientation.serialize(outputStream)
        outputStream.write_uint16(int(self.appearance))
        outputStream.write_uint16(int(self.protocolMode))
        for item in self.perimeterPoints:
            item.serialize(outputStream)
        for item in self.mineType:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.minefieldID = MinefieldIdentifier.parse(inputStream)
        self.minefieldSequence = inputStream.read_uint16()
        self.forceID = rich_or_int(6, inputStream.read_uint8())
        numberOfPerimeterPoints = inputStream.read_uint8()
        self.minefieldType = EntityType.parse(inputStream)
        numberOfMineTypes = inputStream.read_uint16()
        self.minefieldLocation.parse(inputStream)
        self.minefieldOrientation.parse(inputStream)
        self.appearance = MinefieldStateAppearance(inputStream.read_uint16())
        self.protocolMode = inputStream.read_uint16()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.perimeterPoints = [
            Vector2Float.parseFrom(inputStream) for _ in range(numberOfPerimeterPoints)
        ]
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.mineType = [
            EntityType.parse(inputStream) for _ in range(numberOfMineTypes)
        ]


@dataclass(slots=True)
class MinefieldQueryPdu(MinefieldFamilyPdu):
    """§7.9.3 Minefield Query PDU

    Contains information about the requesting entity and the region and mine
    types of interest to the requesting entity.
    """

    pduType: ClassVar[int] = 38  # [UID 4]

    minefieldID: MinefieldIdentifier = field(default_factory=MinefieldIdentifier)
    requestingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    requestID: uint8 = 0
    dataFilter: uint32 = 0
    requestedMineType: EntityType = field(default_factory=EntityType)
    requestedPerimeterPoints: list[Vector2Float] = field(default_factory=list)
    sensorTypes: list[uint16] = field(default_factory=list)
    # Padding ruling: explicit attribute, out of __init__ (zero by default,
    # holds the wire value after parse so odd pads round-trip byte-exact).
    padding: uint8 = field(init=False, default=0)

    @property
    def numberOfPerimeterPoints(self) -> uint8:
        """Number of perimeter points for the minefield."""
        return len(self.requestedPerimeterPoints)

    @property
    def numberOfSensorTypes(self) -> uint8:
        """Number of sensor types."""
        return len(self.sensorTypes)

    def _unpaddedBodySize(self) -> int:
        return (
            self.minefieldID.marshalledSize()
            + self.requestingEntityID.marshalledSize()
            + 1
            + 1
            + 1
            + 1
            + 4
            + self.requestedMineType.marshalledSize()
            + sum(item.marshalledSize() for item in self.requestedPerimeterPoints)
            + 2 * len(self.sensorTypes)
        )

    def _marshalledBodySize(self) -> int:
        return self._unpaddedBodySize() + _padTo32(12 + self._unpaddedBodySize())

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.minefieldID.serialize(outputStream)
        self.requestingEntityID.serialize(outputStream)
        outputStream.write_uint8(self.requestID)
        outputStream.write_uint8(self.numberOfPerimeterPoints)
        outputStream.write_uint8(self.padding)
        outputStream.write_uint8(self.numberOfSensorTypes)
        outputStream.write_uint32(self.dataFilter)
        self.requestedMineType.serialize(outputStream)
        for item in self.requestedPerimeterPoints:
            item.serialize(outputStream)
        for item in self.sensorTypes:
            outputStream.write_uint16(item)
        padding = _padTo32(12 + self._unpaddedBodySize())
        if padding:
            outputStream.write_bytes(b"\x00" * padding)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.minefieldID = MinefieldIdentifier.parse(inputStream)
        self.requestingEntityID = EntityIdentifier.parse(inputStream)
        self.requestID = inputStream.read_uint8()
        numberOfPerimeterPoints = inputStream.read_uint8()
        self.padding = inputStream.read_uint8()
        numberOfSensorTypes = inputStream.read_uint8()
        self.dataFilter = inputStream.read_uint32()
        self.requestedMineType = EntityType.parse(inputStream)
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.requestedPerimeterPoints = [
            Vector2Float.parseFrom(inputStream) for _ in range(numberOfPerimeterPoints)
        ]
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.sensorTypes = [
            inputStream.read_uint16() for _ in range(numberOfSensorTypes)
        ]
        padding = _padTo32(12 + self._unpaddedBodySize())
        if padding:
            inputStream.read_bytes(padding)


@dataclass(slots=True)
class MinefieldDataPdu(MinefieldFamilyPdu):
    """§7.9.4 Minefield Data PDU

    Information about the location and status of a collection of mines in a
    minefield is conveyed through the Minefield Data PDU on an individual
    mine basis.

    Per-mine data in FIELD-major order (Table 189): each conditional per-
    mine list is one contiguous run, present when its dataFilter bit
    (§6.2.16 Table 38) is set. ``mineEntityNumber`` is unconditional; scalar
    detection is N×S (mines × sensor types); the trip-wire section is mine-
    major for its count lists with all vertices pooled at the end
    (§5.10.4.5).

    # generator: presentIf-driven section presence — the conditional
    # vocabulary's reference implementation; absent sections are simply
    # not serialized (empty lists), and marshalledSize consults the
    # filter bits.
    """

    pduType: ClassVar[int] = 39  # [UID 4]

    minefieldID: MinefieldIdentifier = field(default_factory=MinefieldIdentifier)
    requestingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    minefieldSequenceNumber: uint16 = 0
    requestID: uint8 = 0
    pduSequenceNumber: uint8 = 0
    numberOfPdus: uint8 = 0
    dataFilter: uint32 = 0
    mineType: EntityType = field(default_factory=EntityType)
    sensorTypes: list[uint16] = field(default_factory=list)
    mineLocation: list[Vector3Float] = field(default_factory=list)
    groundBurialDepthOffset: list[float32] = field(default_factory=list)
    waterBurialDepthOffset: list[float32] = field(default_factory=list)
    snowBurialDepthOffset: list[float32] = field(default_factory=list)
    mineOrientation: list[EulerAngles] = field(default_factory=list)
    thermalContrast: list[float32] = field(default_factory=list)
    reflectance: list[float32] = field(default_factory=list)
    mineEmplacementTime: list[MineEmplacementTime] = field(default_factory=list)
    mineEntityNumber: list[uint16] = field(default_factory=list)
    fusing: list[enum16] = field(default_factory=list)  # [UID 192]
    scalarDetectionCoefficient: list[uint8] = field(default_factory=list)
    paintScheme: list[enum8] = field(default_factory=list)  # [UID 202]
    numberOfTripDetonationWires: list[uint8] = field(default_factory=list)
    numberOfVertices: list[uint8] = field(default_factory=list)
    vertices: list[Vector3Float] = field(default_factory=list)
    padding: uint8 = field(init=False, default=0)

    @property
    def numberOfMinesInThisPdu(self) -> uint8:
        """how many mines are in this PDU."""
        return len(self.mineLocation)

    @property
    def numberOfSensorTypes(self) -> uint8:
        """how many sensor type are in this PDU."""
        return len(self.sensorTypes)

    # dataFilter bit numbers (§6.2.16 Table 38)
    GROUND: ClassVar[int] = 0
    WATER: ClassVar[int] = 1
    SNOW: ClassVar[int] = 2
    ORIENTATION: ClassVar[int] = 3
    THERMAL: ClassVar[int] = 4
    REFLECTANCE: ClassVar[int] = 5
    EMPLACEMENT: ClassVar[int] = 6
    WIRES: ClassVar[int] = 7
    FUSING: ClassVar[int] = 8
    SCALAR: ClassVar[int] = 9
    PAINT: ClassVar[int] = 10

    def _filter(self, bit: int) -> bool:
        return bool((int(self.dataFilter) >> bit) & 1)

    @property
    def groundPresent(self) -> bool:
        return (
            self._filter(self.GROUND)
            or self._filter(self.WATER)
            or self._filter(self.SNOW)
        )

    @property
    def orientationPresent(self) -> bool:
        return (
            self._filter(self.GROUND)
            or self._filter(self.WATER)
            or self._filter(self.SNOW)
            or self._filter(self.ORIENTATION)
        )

    def _prefixSize(self) -> int:
        return (
            self.minefieldID.marshalledSize()
            + self.requestingEntityID.marshalledSize()
            + 2
            + 1
            + 1
            + 1
            + 1
            + 1
            + 1  # counts + padding
            + 4
            + self.mineType.marshalledSize()
            + 2 * len(self.sensorTypes)
        )

    def _wireVertexCount(self) -> int:
        return sum(self.numberOfVertices)

    def _marshalledBodySize(self):
        n = self.numberOfMinesInThisPdu
        s = self.numberOfSensorTypes
        consumed = 12 + self._prefixSize()
        consumed += _padTo32(consumed)  # padTo32 after sensor types
        consumed += 12 * n  # mineLocation
        if self.groundPresent:
            consumed += 4 * n
        if self._filter(self.WATER):
            consumed += 4 * n
        if self._filter(self.SNOW):
            consumed += 4 * n
        if self.orientationPresent:
            consumed += 12 * n
        if self._filter(self.THERMAL):
            consumed += 4 * n
        if self._filter(self.REFLECTANCE):
            consumed += 4 * n
        if self._filter(self.EMPLACEMENT):
            consumed += 8 * n
        consumed += 2 * n  # mineEntityNumber (unconditional)
        if self._filter(self.FUSING):
            consumed += 2 * n
        if self._filter(self.SCALAR):
            consumed += n * s
        if self._filter(self.PAINT):
            consumed += n
        consumed += _padTo32(consumed)  # padTo32_2
        if self._filter(self.WIRES):
            consumed += n  # per-mine wire counts
            consumed += _padTo32(consumed)  # padTo32_3
            consumed += len(self.numberOfVertices)  # per-wire vertex counts
            consumed += _padTo32(consumed)  # padTo32_4
            consumed += 12 * self._wireVertexCount()
        return consumed - 12

    def _serializeBody(self, outputStream: DataOutputStream):
        n = self.numberOfMinesInThisPdu
        consumed = 12 + self._prefixSize()
        self.minefieldID.serialize(outputStream)
        self.requestingEntityID.serialize(outputStream)
        outputStream.write_uint16(self.minefieldSequenceNumber)
        outputStream.write_uint8(self.requestID)
        outputStream.write_uint8(self.pduSequenceNumber)
        outputStream.write_uint8(self.numberOfPdus)
        outputStream.write_uint8(self.numberOfMinesInThisPdu)
        outputStream.write_uint8(self.numberOfSensorTypes)
        outputStream.write_uint8(self.padding)
        outputStream.write_uint32(self.dataFilter)
        self.mineType.serialize(outputStream)
        for sensorType in self.sensorTypes:
            outputStream.write_uint16(sensorType)

        def pad() -> None:
            nonlocal consumed
            padding = _padTo32(consumed)
            if padding:
                outputStream.write_bytes(b"\x00" * padding)
                consumed += padding

        def writeFloats(values: list) -> None:
            nonlocal consumed
            for value in values:
                outputStream.write_float32(value)
            consumed += 4 * len(values)

        pad()  # padTo32 after sensor types
        for location in self.mineLocation:
            location.serialize(outputStream)
        consumed += 12 * n
        if self.groundPresent:
            writeFloats(self.groundBurialDepthOffset)
        if self._filter(self.WATER):
            writeFloats(self.waterBurialDepthOffset)
        if self._filter(self.SNOW):
            writeFloats(self.snowBurialDepthOffset)
        if self.orientationPresent:
            for orientation in self.mineOrientation:
                orientation.serialize(outputStream)
            consumed += 12 * n
        if self._filter(self.THERMAL):
            writeFloats(self.thermalContrast)
        if self._filter(self.REFLECTANCE):
            writeFloats(self.reflectance)
        if self._filter(self.EMPLACEMENT):
            for time in self.mineEmplacementTime:
                time.serialize(outputStream)
            consumed += 8 * n
        for entityNumber in self.mineEntityNumber:
            outputStream.write_uint16(entityNumber)
        consumed += 2 * n
        if self._filter(self.FUSING):
            for value in self.fusing:
                outputStream.write_uint16(value)
            consumed += 2 * n
        if self._filter(self.SCALAR):
            for value in self.scalarDetectionCoefficient:
                outputStream.write_uint8(value)
            consumed += n * self.numberOfSensorTypes
        if self._filter(self.PAINT):
            for value in self.paintScheme:
                outputStream.write_uint8(value)
            consumed += n
        pad()  # padTo32_2
        if self._filter(self.WIRES):
            for count in self.numberOfTripDetonationWires:
                outputStream.write_uint8(count)
            consumed += n
            pad()  # padTo32_3
            for count in self.numberOfVertices:
                outputStream.write_uint8(count)
            consumed += len(self.numberOfVertices)
            pad()  # padTo32_4
            for vertex in self.vertices:
                vertex.serialize(outputStream)
            consumed += 12 * len(self.vertices)

    def _parseBody(self, inputStream: DataInputStream):
        self.minefieldID = MinefieldIdentifier.parse(inputStream)
        self.requestingEntityID = EntityIdentifier.parse(inputStream)
        self.minefieldSequenceNumber = inputStream.read_uint16()
        self.requestID = inputStream.read_uint8()
        self.pduSequenceNumber = inputStream.read_uint8()
        self.numberOfPdus = inputStream.read_uint8()
        numberOfMinesInThisPdu = inputStream.read_uint8()
        numberOfSensorTypes = inputStream.read_uint8()
        self.padding = inputStream.read_uint8()
        self.dataFilter = inputStream.read_uint32()
        self.mineType = EntityType.parse(inputStream)
        self.sensorTypes = [
            inputStream.read_uint16() for _ in range(numberOfSensorTypes)
        ]
        consumed = 12 + self._prefixSize()

        def pad() -> None:
            nonlocal consumed
            padding = _padTo32(consumed)
            if padding:
                inputStream.read_bytes(padding)
                consumed += padding

        def readFloats(count: int) -> list:
            nonlocal consumed
            values = [inputStream.read_float32() for _ in range(count)]
            consumed += 4 * count
            return values

        pad()  # padTo32 after sensor types
        self.mineLocation = []
        for _ in range(numberOfMinesInThisPdu):
            location = Vector3Float()
            location.parse(inputStream)
            self.mineLocation.append(location)
        consumed += 12 * numberOfMinesInThisPdu
        if self.groundPresent:
            self.groundBurialDepthOffset = readFloats(numberOfMinesInThisPdu)
        if self._filter(self.WATER):
            self.waterBurialDepthOffset = readFloats(numberOfMinesInThisPdu)
        if self._filter(self.SNOW):
            self.snowBurialDepthOffset = readFloats(numberOfMinesInThisPdu)
        if self.orientationPresent:
            self.mineOrientation = []
            for _ in range(numberOfMinesInThisPdu):
                orientation = EulerAngles()
                orientation.parse(inputStream)
                self.mineOrientation.append(orientation)
            consumed += 12 * numberOfMinesInThisPdu
        if self._filter(self.THERMAL):
            self.thermalContrast = readFloats(numberOfMinesInThisPdu)
        if self._filter(self.REFLECTANCE):
            self.reflectance = readFloats(numberOfMinesInThisPdu)
        if self._filter(self.EMPLACEMENT):
            self.mineEmplacementTime = [
                MineEmplacementTime.parseFrom(inputStream)
                for _ in range(numberOfMinesInThisPdu)
            ]
            consumed += 8 * numberOfMinesInThisPdu
        self.mineEntityNumber = [
            inputStream.read_uint16() for _ in range(numberOfMinesInThisPdu)
        ]
        consumed += 2 * numberOfMinesInThisPdu
        if self._filter(self.FUSING):
            self.fusing = [
                inputStream.read_uint16() for _ in range(numberOfMinesInThisPdu)
            ]
            consumed += 2 * numberOfMinesInThisPdu
        if self._filter(self.SCALAR):
            count = numberOfMinesInThisPdu * numberOfSensorTypes
            self.scalarDetectionCoefficient = [
                inputStream.read_uint8() for _ in range(count)
            ]
            consumed += count
        if self._filter(self.PAINT):
            self.paintScheme = [
                inputStream.read_uint8() for _ in range(numberOfMinesInThisPdu)
            ]
            consumed += numberOfMinesInThisPdu
        pad()  # padTo32_2
        if self._filter(self.WIRES):
            self.numberOfTripDetonationWires = [
                inputStream.read_uint8() for _ in range(numberOfMinesInThisPdu)
            ]
            consumed += numberOfMinesInThisPdu
            pad()  # padTo32_3
            wireTotal = sum(self.numberOfTripDetonationWires)
            self.numberOfVertices = [inputStream.read_uint8() for _ in range(wireTotal)]
            consumed += wireTotal
            pad()  # padTo32_4
            self.vertices = []
            for _ in range(self._wireVertexCount()):
                vertex = Vector3Float()
                vertex.parse(inputStream)
                self.vertices.append(vertex)


@dataclass(slots=True)
class MinefieldResponseNACKPdu(MinefieldFamilyPdu):
    """§7.9.5 Minefield Response NACK PDU

    Contains information about the requesting entity and the PDU(s) that
    were not received in response to a query. NACK = Negative
    Acknowledgment.
    """

    pduType: ClassVar[int] = 40  # [UID 4]

    minefieldID: MinefieldIdentifier = field(default_factory=MinefieldIdentifier)
    requestingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    requestID: uint8 = 0
    missingPduSequenceNumbers: list[uint8] = field(default_factory=list)

    @property
    def numberOfMissingPdus(self) -> uint8:
        """how many pdus were missing."""
        return len(self.missingPduSequenceNumbers)

    def _unpaddedBodySize(self) -> int:
        return (
            self.minefieldID.marshalledSize()
            + self.requestingEntityID.marshalledSize()
            + 1
            + 1
            + len(self.missingPduSequenceNumbers)
        )

    def _marshalledBodySize(self) -> int:
        return self._unpaddedBodySize() + _padTo32(12 + self._unpaddedBodySize())

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.minefieldID.serialize(outputStream)
        self.requestingEntityID.serialize(outputStream)
        outputStream.write_uint8(self.requestID)
        outputStream.write_uint8(self.numberOfMissingPdus)
        for item in self.missingPduSequenceNumbers:
            outputStream.write_uint8(item)
        padding = _padTo32(12 + self._unpaddedBodySize())
        if padding:
            outputStream.write_bytes(b"\x00" * padding)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.minefieldID = MinefieldIdentifier.parse(inputStream)
        self.requestingEntityID = EntityIdentifier.parse(inputStream)
        self.requestID = inputStream.read_uint8()
        numberOfMissingPdus = inputStream.read_uint8()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.missingPduSequenceNumbers = [
            inputStream.read_uint8() for _ in range(numberOfMissingPdus)
        ]
        padding = _padTo32(12 + self._unpaddedBodySize())
        if padding:
            inputStream.read_bytes(padding)
