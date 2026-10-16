"""Simulation Management with Reliability family (IEEE 1278.1-2012
§5.12.4) — target-state PDUs.

Wire ground truth: submodules/open-dis-spec-xml/xml/SimulationManagementWithReliabilityFamilyPdus.xml.
Each PDU pairs a §5.6 twin with a reliability-service level. Per the
aliasFor ruling the descriptive name is canonical and the abbreviation
is a plain module-level alias (e.g. ``CreateEntityRPdu =
CreateEntityReliablePdu``).

Python-side deltas from the XML (sample-review rulings): originator/
receiver keep the exemplar's EntityIdentifier shape/names (same 6-byte
wire field, §6.2.81); Record Query-R carries a flat datum-ID list and
Record-R/Set Record-R carry flat record-set lists — the XML wraps each
in an extra RecordQuerySpecification/RecordSpecification layer the
standard's §5.12.4.14–16 tables do not have.
"""

from dataclasses import dataclass, field
from typing import ClassVar

from opendis.bitfields import StopFreezeFrozenBehavior
from opendis.enum_registry import rich_or_int
from opendis.record.common import ClockTime, EntityIdentifier
from opendis.record.pdu import Pdu
from opendis.record.simulation_management import FixedDatum, VariableDatum
from opendis.stream import DataInputStream, DataOutputStream
from opendis.types import enum8, enum16, enum32, uint8, uint16, uint32

__all__ = [
    "AcknowledgeRPdu",
    "AcknowledgeReliablePdu",
    "ActionRequestRPdu",
    "ActionRequestReliablePdu",
    "ActionResponseRPdu",
    "ActionResponseReliablePdu",
    "CommentRPdu",
    "CommentReliablePdu",
    "CreateEntityRPdu",
    "CreateEntityReliablePdu",
    "DataQueryRPdu",
    "DataQueryReliablePdu",
    "DataRPdu",
    "DataReliablePdu",
    "EventReportRPdu",
    "EventReportReliablePdu",
    "RecordQueryRPdu",
    "RecordQueryReliablePdu",
    "RecordRPdu",
    "RecordReliablePdu",
    "RecordSpecificationElement",
    "RemoveEntityRPdu",
    "RemoveEntityReliablePdu",
    "SetDataRPdu",
    "SetDataReliablePdu",
    "SetRecordRPdu",
    "SetRecordReliablePdu",
    "SimulationManagementWithReliabilityFamilyPdu",
    "StartResumeRPdu",
    "StartResumeReliablePdu",
    "StopFreezeRPdu",
    "StopFreezeReliablePdu",
]


def _padTo64(byteCount: int) -> int:
    """Pad bytes needed to bring a datagram to a 64-bit boundary."""
    return (8 - byteCount % 8) % 8


@dataclass(slots=True)
class SimulationManagementWithReliabilityFamilyPdu(Pdu):
    """Simulation Management with Reliability PDUs with reliability service
    levels in a DIS exercise are an alternative to the Simulation Management
    PDUs, and may or may not be required for participation in an DIS
    exercise,.

    Not a thin marker: the §6.2.82 header fields (EntityIdentifier-shaped
    per the sample-review ruling) plus the reliability-service conventions
    of the -R family.
    """

    protocolFamily: ClassVar[int] = 10  # [UID 5] Simulation Management with Reliability

    originatingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    receivingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)

    def _marshalledBodySize(self) -> int:
        return (
            self.originatingEntityID.marshalledSize()
            + self.receivingEntityID.marshalledSize()
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.originatingEntityID.serialize(outputStream)
        self.receivingEntityID.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.originatingEntityID = EntityIdentifier.parse(inputStream)
        self.receivingEntityID = EntityIdentifier.parse(inputStream)


@dataclass(slots=True)
class RecordSpecificationElement:
    """Synthetic record, made up from §6.2.73. This is used to achieve a
    repeating variable list element.<p>recordLength, recordCount and
    recordValues must be set by hand so the.

    One element of a §6.2.73 Record Specification: a block of same-typed
    records. ``recordValues`` is the concatenated block as ``bytes`` (byte
    granularity — bit lengths not divisible by 8 are unsupported, same
    ruling as VariableDatum); the set is padded to a 64-bit boundary by the
    packer.
    """

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "recordID": 66,
    }

    recordID: enum32 = 0  # [UID 66]
    recordSetSerialNumber: uint32 = 0
    recordLength: uint16 = 0
    recordCount: uint16 = 0
    recordValues: bytes = b""
    # Padding ruling: explicit attribute, out of __init__ (zero by default,
    # holds the wire value after parse so odd pads round-trip byte-exact).
    padding: uint32 = field(init=False, default=0)

    def marshalledSize(self):
        prefix = 4 + 4 + 4 + 2 + 2
        return prefix + len(self.recordValues) + self._padTo64(prefix)

    def serialize(self, outputStream: DataOutputStream):
        outputStream.write_uint32(self.recordID)
        outputStream.write_uint32(self.recordSetSerialNumber)
        outputStream.write_uint32(self.padding)
        outputStream.write_uint16(self.recordLength)
        outputStream.write_uint16(self.recordCount)
        outputStream.write_bytes(self.recordValues)
        padding = self._padTo64(14 + len(self.recordValues))
        if padding:
            outputStream.write_bytes(b"\x00" * padding)

    def parse(self, inputStream: DataInputStream):
        self.recordID = rich_or_int(66, inputStream.read_uint32())
        self.recordSetSerialNumber = inputStream.read_uint32()
        self.padding = inputStream.read_uint32()
        self.recordLength = inputStream.read_uint16()
        self.recordCount = inputStream.read_uint16()
        valueBytes = self.recordLength * self.recordCount // 8
        self.recordValues = inputStream.read_bytes(valueBytes)
        padding = self._padTo64(14 + valueBytes)
        if padding:
            inputStream.read_bytes(padding)

    @staticmethod
    def _padTo64(byteCount: int) -> int:
        return (8 - byteCount % 8) % 8

    @classmethod
    def parseFrom(cls, inputStream: DataInputStream) -> "RecordSpecificationElement":
        """Construct a new record from the stream (list-parse helper; the
        mutating ``parse`` above satisfies the Record protocol)."""
        item = cls()
        item.parse(inputStream)
        return item


@dataclass(slots=True)
class CreateEntityReliablePdu(SimulationManagementWithReliabilityFamilyPdu):
    """§5.12.4.2 Create Entity-R PDU

    Serves the same function as the Create Entity PDU but with the addition
    of reliability service levels. Canonical descriptive name;
    CreateEntityRPdu is an alias.
    """

    pduType: ClassVar[int] = 51  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "requiredReliabilityService": 74,
    }

    requiredReliabilityService: enum8 = 0  # [UID 74]
    requestID: uint32 = 0
    pad1: uint8 = field(init=False, default=0)
    pad2: uint16 = field(init=False, default=0)

    def _marshalledBodySize(self) -> int:
        return (
            super(CreateEntityReliablePdu, self)._marshalledBodySize() + 1 + 1 + 2 + 4
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(CreateEntityReliablePdu, self)._serializeBody(outputStream)
        outputStream.write_uint8(self.requiredReliabilityService)
        outputStream.write_uint8(self.pad1)
        outputStream.write_uint16(self.pad2)
        outputStream.write_uint32(self.requestID)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(CreateEntityReliablePdu, self)._parseBody(inputStream)
        self.requiredReliabilityService = rich_or_int(74, inputStream.read_uint8())
        self.pad1 = inputStream.read_uint8()
        self.pad2 = inputStream.read_uint16()
        self.requestID = inputStream.read_uint32()


# generator: aliasFor elements — one class plus a name assignment;
# descriptive name canonical, abbreviation aliased
CreateEntityRPdu = CreateEntityReliablePdu


@dataclass(slots=True)
class RemoveEntityReliablePdu(SimulationManagementWithReliabilityFamilyPdu):
    """§5.12.4.3 Remove Entity-R PDU

    Contains the same information as found in the Remove Entity PDU with the
    addition of the level of reliability service to be used for the removal
    action being requested. Canonical descriptive name; RemoveEntityRPdu is
    an alias.
    """

    pduType: ClassVar[int] = 52  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "requiredReliabilityService": 74,
    }

    requiredReliabilityService: enum8 = 0  # [UID 74]
    requestID: uint32 = 0
    pad1: uint8 = field(init=False, default=0)
    pad2: uint16 = field(init=False, default=0)

    def _marshalledBodySize(self) -> int:
        return (
            super(RemoveEntityReliablePdu, self)._marshalledBodySize() + 1 + 1 + 2 + 4
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(RemoveEntityReliablePdu, self)._serializeBody(outputStream)
        outputStream.write_uint8(self.requiredReliabilityService)
        outputStream.write_uint8(self.pad1)
        outputStream.write_uint16(self.pad2)
        outputStream.write_uint32(self.requestID)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(RemoveEntityReliablePdu, self)._parseBody(inputStream)
        self.requiredReliabilityService = rich_or_int(74, inputStream.read_uint8())
        self.pad1 = inputStream.read_uint8()
        self.pad2 = inputStream.read_uint16()
        self.requestID = inputStream.read_uint32()


RemoveEntityRPdu = RemoveEntityReliablePdu


@dataclass(slots=True)
class StartResumeReliablePdu(SimulationManagementWithReliabilityFamilyPdu):
    """§5.12.4.4 Start/Resume-R PDU

    Serves the same function as the Start/Resume PDU but with the addition
    of reliability service levels. Canonical descriptive name;
    StartResumeRPdu is an alias.
    """

    pduType: ClassVar[int] = 53  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "requiredReliabilityService": 74,
    }

    realWorldTime: ClockTime = field(default_factory=ClockTime)
    simulationTime: ClockTime = field(default_factory=ClockTime)
    requiredReliabilityService: enum8 = 0  # [UID 74]
    requestID: uint32 = 0
    pad1: uint8 = field(init=False, default=0)
    pad2: uint16 = field(init=False, default=0)

    def _marshalledBodySize(self) -> int:
        return (
            super(StartResumeReliablePdu, self)._marshalledBodySize()
            + self.realWorldTime.marshalledSize()
            + self.simulationTime.marshalledSize()
            + 1
            + 1
            + 2
            + 4
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(StartResumeReliablePdu, self)._serializeBody(outputStream)
        self.realWorldTime.serialize(outputStream)
        self.simulationTime.serialize(outputStream)
        outputStream.write_uint8(self.requiredReliabilityService)
        outputStream.write_uint8(self.pad1)
        outputStream.write_uint16(self.pad2)
        outputStream.write_uint32(self.requestID)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(StartResumeReliablePdu, self)._parseBody(inputStream)
        self.realWorldTime.parse(inputStream)
        self.simulationTime.parse(inputStream)
        self.requiredReliabilityService = rich_or_int(74, inputStream.read_uint8())
        self.pad1 = inputStream.read_uint8()
        self.pad2 = inputStream.read_uint16()
        self.requestID = inputStream.read_uint32()


StartResumeRPdu = StartResumeReliablePdu


@dataclass(slots=True)
class StopFreezeReliablePdu(SimulationManagementWithReliabilityFamilyPdu):
    """§5.12.4.5 Stop/Freeze-R PDU

    Serves the same function as the Stop/Freeze PDU (see 5.6.5.5.1) but with
    the addition of reliability service levels. Canonical descriptive name;
    StopFreezeRPdu is an alias.
    """

    pduType: ClassVar[int] = 54  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "reason": 67,
        "requiredReliabilityService": 74,
    }

    realWorldTime: ClockTime = field(default_factory=ClockTime)
    reason: enum8 = 0  # [UID 67]
    frozenBehavior: uint8 = 0  # [UID 68] or the view
    requiredReliabilityService: enum8 = 0  # [UID 74]
    requestID: uint32 = 0
    pad1: uint8 = field(init=False, default=0)

    def _marshalledBodySize(self) -> int:
        return (
            super(StopFreezeReliablePdu, self)._marshalledBodySize()
            + self.realWorldTime.marshalledSize()
            + 1
            + 1
            + 1
            + 1
            + 4
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(StopFreezeReliablePdu, self)._serializeBody(outputStream)
        self.realWorldTime.serialize(outputStream)
        outputStream.write_uint8(self.reason)
        outputStream.write_uint8(int(self.frozenBehavior))
        outputStream.write_uint8(self.requiredReliabilityService)
        outputStream.write_uint8(self.pad1)
        outputStream.write_uint32(self.requestID)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(StopFreezeReliablePdu, self)._parseBody(inputStream)
        self.realWorldTime.parse(inputStream)
        self.reason = rich_or_int(67, inputStream.read_uint8())
        self.frozenBehavior = StopFreezeFrozenBehavior(inputStream.read_uint8())
        self.requiredReliabilityService = rich_or_int(74, inputStream.read_uint8())
        self.pad1 = inputStream.read_uint8()
        self.requestID = inputStream.read_uint32()


StopFreezeRPdu = StopFreezeReliablePdu


@dataclass(slots=True)
class AcknowledgeReliablePdu(SimulationManagementWithReliabilityFamilyPdu):
    """§5.12.4.6 Acknowledge-R PDU

    Serves the same function as the Acknowledge PDU but is used to
    acknowledge the receipt of a Create Entity-R PDU, a Remove Entity-R PDU,
    a Start/Resume-R PDU, or a Stop/Freeze-R PDU. Canonical descriptive
    name; AcknowledgeRPdu is an alias.
    """

    pduType: ClassVar[int] = 55  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "acknowledgeFlag": 69,
        "responseFlag": 70,
    }

    acknowledgeFlag: enum16 = 0  # [UID 69]
    responseFlag: enum16 = 0  # [UID 70]
    requestID: uint32 = 0

    def _marshalledBodySize(self) -> int:
        return super(AcknowledgeReliablePdu, self)._marshalledBodySize() + 2 + 2 + 4

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(AcknowledgeReliablePdu, self)._serializeBody(outputStream)
        outputStream.write_uint16(self.acknowledgeFlag)
        outputStream.write_uint16(self.responseFlag)
        outputStream.write_uint32(self.requestID)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(AcknowledgeReliablePdu, self)._parseBody(inputStream)
        self.acknowledgeFlag = rich_or_int(69, inputStream.read_uint16())
        self.responseFlag = rich_or_int(70, inputStream.read_uint16())
        self.requestID = inputStream.read_uint32()


AcknowledgeRPdu = AcknowledgeReliablePdu


@dataclass(slots=True)
class ActionRequestReliablePdu(SimulationManagementWithReliabilityFamilyPdu):
    """§5.12.4.7 Action Request-R PDU

    Serves the same function as the Action Request PDU but with the addition
    of reliability service levels. Canonical descriptive name;
    ActionRequestRPdu is an alias.
    """

    pduType: ClassVar[int] = 56  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "requiredReliabilityService": 74,
        "actionID": 71,
    }

    requiredReliabilityService: enum8 = 0  # [UID 74]
    requestID: uint32 = 0
    actionID: enum32 = 0  # [UID 71]
    fixedDatumRecords: list[FixedDatum] = field(default_factory=list)
    variableDatumRecords: list[VariableDatum] = field(default_factory=list)
    pad1: uint8 = field(init=False, default=0)
    pad2: uint16 = field(init=False, default=0)

    @property
    def numberOfFixedDatumRecords(self) -> uint32:
        """Fixed datum record count."""
        return len(self.fixedDatumRecords)

    @property
    def numberOfVariableDatumRecords(self) -> uint32:
        """variable datum record count."""
        return len(self.variableDatumRecords)

    def _marshalledBodySize(self) -> int:
        return (
            super(ActionRequestReliablePdu, self)._marshalledBodySize()
            + 1
            + 1
            + 2
            + 4
            + 4
            + 4
            + 4
            + sum(item.marshalledSize() for item in self.fixedDatumRecords)
            + sum(item.marshalledSize() for item in self.variableDatumRecords)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(ActionRequestReliablePdu, self)._serializeBody(outputStream)
        outputStream.write_uint8(self.requiredReliabilityService)
        outputStream.write_uint8(self.pad1)
        outputStream.write_uint16(self.pad2)
        outputStream.write_uint32(self.requestID)
        outputStream.write_uint32(self.actionID)
        outputStream.write_uint32(self.numberOfFixedDatumRecords)
        outputStream.write_uint32(self.numberOfVariableDatumRecords)
        for item in self.fixedDatumRecords:
            item.serialize(outputStream)
        for item in self.variableDatumRecords:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(ActionRequestReliablePdu, self)._parseBody(inputStream)
        self.requiredReliabilityService = rich_or_int(74, inputStream.read_uint8())
        self.pad1 = inputStream.read_uint8()
        self.pad2 = inputStream.read_uint16()
        self.requestID = inputStream.read_uint32()
        self.actionID = rich_or_int(71, inputStream.read_uint32())
        numberOfFixedDatumRecords = inputStream.read_uint32()
        numberOfVariableDatumRecords = inputStream.read_uint32()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.fixedDatumRecords = [
            FixedDatum.parseFrom(inputStream) for _ in range(numberOfFixedDatumRecords)
        ]
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.variableDatumRecords = [
            VariableDatum.parseFrom(inputStream)
            for _ in range(numberOfVariableDatumRecords)
        ]


ActionRequestRPdu = ActionRequestReliablePdu


@dataclass(slots=True)
class ActionResponseReliablePdu(SimulationManagementWithReliabilityFamilyPdu):
    """§5.12.4.8 Action Response-R PDU

    Serves the same function as the Action Response PDU (see 5.6.5.8.1) but
    is used to acknowledge the receipt of an Action Request-R PDU. Canonical
    descriptive name; ActionResponseRPdu is an alias.
    """

    pduType: ClassVar[int] = 57  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "responseStatus": 72,
    }

    requestID: uint32 = 0
    responseStatus: enum32 = 0  # [UID 72]
    fixedDatumRecords: list[FixedDatum] = field(default_factory=list)
    variableDatumRecords: list[VariableDatum] = field(default_factory=list)

    @property
    def numberOfFixedDatumRecords(self) -> uint32:
        """Fixed datum record count."""
        return len(self.fixedDatumRecords)

    @property
    def numberOfVariableDatumRecords(self) -> uint32:
        """variable datum record count."""
        return len(self.variableDatumRecords)

    def _marshalledBodySize(self) -> int:
        return (
            super(ActionResponseReliablePdu, self)._marshalledBodySize()
            + 4
            + 4
            + 4
            + 4
            + sum(item.marshalledSize() for item in self.fixedDatumRecords)
            + sum(item.marshalledSize() for item in self.variableDatumRecords)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(ActionResponseReliablePdu, self)._serializeBody(outputStream)
        outputStream.write_uint32(self.requestID)
        outputStream.write_uint32(self.responseStatus)
        outputStream.write_uint32(self.numberOfFixedDatumRecords)
        outputStream.write_uint32(self.numberOfVariableDatumRecords)
        for item in self.fixedDatumRecords:
            item.serialize(outputStream)
        for item in self.variableDatumRecords:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(ActionResponseReliablePdu, self)._parseBody(inputStream)
        self.requestID = inputStream.read_uint32()
        self.responseStatus = rich_or_int(72, inputStream.read_uint32())
        numberOfFixedDatumRecords = inputStream.read_uint32()
        numberOfVariableDatumRecords = inputStream.read_uint32()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.fixedDatumRecords = [
            FixedDatum.parseFrom(inputStream) for _ in range(numberOfFixedDatumRecords)
        ]
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.variableDatumRecords = [
            VariableDatum.parseFrom(inputStream)
            for _ in range(numberOfVariableDatumRecords)
        ]


ActionResponseRPdu = ActionResponseReliablePdu


@dataclass(slots=True)
class DataQueryReliablePdu(SimulationManagementWithReliabilityFamilyPdu):
    """§5.12.4.9 Data Query-R PDU

    Serves the same function as the Data Query PDU but with the addition of
    reliability service levels. Canonical descriptive name; DataQueryRPdu is
    an alias.
    """

    pduType: ClassVar[int] = 58  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "requiredReliabilityService": 74,
    }

    requiredReliabilityService: enum8 = 0  # [UID 74]
    requestID: uint32 = 0
    timeInterval: uint32 = 0
    fixedDatumIDs: list[enum32] = field(default_factory=list)
    variableDatumIDs: list[enum32] = field(default_factory=list)
    pad1: uint8 = field(init=False, default=0)
    pad2: uint16 = field(init=False, default=0)

    @property
    def numberOfFixedDatumIDs(self) -> uint32:
        """Fixed datum record count."""
        return len(self.fixedDatumIDs)

    @property
    def numberOfVariableDatumIDs(self) -> uint32:
        """variable datum record count."""
        return len(self.variableDatumIDs)

    def _marshalledBodySize(self) -> int:
        return (
            super(DataQueryReliablePdu, self)._marshalledBodySize()
            + 1
            + 1
            + 2
            + 4
            + 4
            + 4
            + 4
            + 4 * len(self.fixedDatumIDs)
            + 4 * len(self.variableDatumIDs)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(DataQueryReliablePdu, self)._serializeBody(outputStream)
        outputStream.write_uint8(self.requiredReliabilityService)
        outputStream.write_uint8(self.pad1)
        outputStream.write_uint16(self.pad2)
        outputStream.write_uint32(self.requestID)
        outputStream.write_uint32(self.timeInterval)
        outputStream.write_uint32(self.numberOfFixedDatumIDs)
        outputStream.write_uint32(self.numberOfVariableDatumIDs)
        for item in self.fixedDatumIDs:
            outputStream.write_uint32(item)
        for item in self.variableDatumIDs:
            outputStream.write_uint32(item)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(DataQueryReliablePdu, self)._parseBody(inputStream)
        self.requiredReliabilityService = rich_or_int(74, inputStream.read_uint8())
        self.pad1 = inputStream.read_uint8()
        self.pad2 = inputStream.read_uint16()
        self.requestID = inputStream.read_uint32()
        self.timeInterval = inputStream.read_uint32()
        numberOfFixedDatumIDs = inputStream.read_uint32()
        numberOfVariableDatumIDs = inputStream.read_uint32()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.fixedDatumIDs = [
            rich_or_int(66, inputStream.read_uint32())
            for _ in range(numberOfFixedDatumIDs)
        ]
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.variableDatumIDs = [
            rich_or_int(66, inputStream.read_uint32())
            for _ in range(numberOfVariableDatumIDs)
        ]


DataQueryRPdu = DataQueryReliablePdu


@dataclass(slots=True)
class SetDataReliablePdu(SimulationManagementWithReliabilityFamilyPdu):
    """§5.12.4.10 Set Data-R PDU

    Serves the same function as the Set Data PDU but with the addition of
    reliability service levels. Canonical descriptive name; SetDataRPdu is
    an alias.
    """

    pduType: ClassVar[int] = 59  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "requiredReliabilityService": 74,
    }

    requiredReliabilityService: enum8 = 0  # [UID 74]
    requestID: uint32 = 0
    fixedDatumRecords: list[FixedDatum] = field(default_factory=list)
    variableDatumRecords: list[VariableDatum] = field(default_factory=list)
    pad1: uint8 = field(init=False, default=0)
    pad2: uint16 = field(init=False, default=0)

    @property
    def numberOfFixedDatumRecords(self) -> uint32:
        """Fixed datum record count."""
        return len(self.fixedDatumRecords)

    @property
    def numberOfVariableDatumRecords(self) -> uint32:
        """variable datum record count."""
        return len(self.variableDatumRecords)

    def _marshalledBodySize(self) -> int:
        return (
            super(SetDataReliablePdu, self)._marshalledBodySize()
            + 1
            + 1
            + 2
            + 4
            + 4
            + 4
            + sum(item.marshalledSize() for item in self.fixedDatumRecords)
            + sum(item.marshalledSize() for item in self.variableDatumRecords)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(SetDataReliablePdu, self)._serializeBody(outputStream)
        outputStream.write_uint8(self.requiredReliabilityService)
        outputStream.write_uint8(self.pad1)
        outputStream.write_uint16(self.pad2)
        outputStream.write_uint32(self.requestID)
        outputStream.write_uint32(self.numberOfFixedDatumRecords)
        outputStream.write_uint32(self.numberOfVariableDatumRecords)
        for item in self.fixedDatumRecords:
            item.serialize(outputStream)
        for item in self.variableDatumRecords:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(SetDataReliablePdu, self)._parseBody(inputStream)
        self.requiredReliabilityService = rich_or_int(74, inputStream.read_uint8())
        self.pad1 = inputStream.read_uint8()
        self.pad2 = inputStream.read_uint16()
        self.requestID = inputStream.read_uint32()
        numberOfFixedDatumRecords = inputStream.read_uint32()
        numberOfVariableDatumRecords = inputStream.read_uint32()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.fixedDatumRecords = [
            FixedDatum.parseFrom(inputStream) for _ in range(numberOfFixedDatumRecords)
        ]
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.variableDatumRecords = [
            VariableDatum.parseFrom(inputStream)
            for _ in range(numberOfVariableDatumRecords)
        ]


SetDataRPdu = SetDataReliablePdu


@dataclass(slots=True)
class DataReliablePdu(SimulationManagementWithReliabilityFamilyPdu):
    """§5.12.4.11 Data-R PDU

    Serves the same function as the Data PDU but with the addition of
    reliability service levels and is used in response to a Data Query-R
    PDU, a Data-R PDU, or a Set Data-R PDU. Canonical descriptive name;
    DataRPdu is an alias.
    """

    pduType: ClassVar[int] = 60  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "requiredReliabilityService": 74,
    }

    requestID: uint32 = 0
    requiredReliabilityService: enum8 = 0  # [UID 74]
    fixedDatumRecords: list[FixedDatum] = field(default_factory=list)
    variableDatumRecords: list[VariableDatum] = field(default_factory=list)
    pad1: uint8 = field(init=False, default=0)
    pad2: uint16 = field(init=False, default=0)

    @property
    def numberOfFixedDatumRecords(self) -> uint32:
        """Fixed datum record count."""
        return len(self.fixedDatumRecords)

    @property
    def numberOfVariableDatumRecords(self) -> uint32:
        """variable datum record count."""
        return len(self.variableDatumRecords)

    def _marshalledBodySize(self) -> int:
        return (
            super(DataReliablePdu, self)._marshalledBodySize()
            + 4
            + 1
            + 1
            + 2
            + 4
            + 4
            + sum(item.marshalledSize() for item in self.fixedDatumRecords)
            + sum(item.marshalledSize() for item in self.variableDatumRecords)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(DataReliablePdu, self)._serializeBody(outputStream)
        outputStream.write_uint32(self.requestID)
        outputStream.write_uint8(self.requiredReliabilityService)
        outputStream.write_uint8(self.pad1)
        outputStream.write_uint16(self.pad2)
        outputStream.write_uint32(self.numberOfFixedDatumRecords)
        outputStream.write_uint32(self.numberOfVariableDatumRecords)
        for item in self.fixedDatumRecords:
            item.serialize(outputStream)
        for item in self.variableDatumRecords:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(DataReliablePdu, self)._parseBody(inputStream)
        self.requestID = inputStream.read_uint32()
        self.requiredReliabilityService = rich_or_int(74, inputStream.read_uint8())
        self.pad1 = inputStream.read_uint8()
        self.pad2 = inputStream.read_uint16()
        numberOfFixedDatumRecords = inputStream.read_uint32()
        numberOfVariableDatumRecords = inputStream.read_uint32()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.fixedDatumRecords = [
            FixedDatum.parseFrom(inputStream) for _ in range(numberOfFixedDatumRecords)
        ]
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.variableDatumRecords = [
            VariableDatum.parseFrom(inputStream)
            for _ in range(numberOfVariableDatumRecords)
        ]


DataRPdu = DataReliablePdu


@dataclass(slots=True)
class EventReportReliablePdu(SimulationManagementWithReliabilityFamilyPdu):
    """§5.12.4.12 Event Report-R PDU

    Contains the same information as found in the Event Report PDU.
    Canonical descriptive name; EventReportRPdu is an alias.
    """

    pduType: ClassVar[int] = 61  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "eventType": 73,
    }

    eventType: enum32 = 0  # [UID 73]
    fixedDatumRecords: list[FixedDatum] = field(default_factory=list)
    variableDatumRecords: list[VariableDatum] = field(default_factory=list)
    pad1: uint32 = field(init=False, default=0)

    @property
    def numberOfFixedDatumRecords(self) -> uint32:
        """Fixed datum record count."""
        return len(self.fixedDatumRecords)

    @property
    def numberOfVariableDatumRecords(self) -> uint32:
        """variable datum record count."""
        return len(self.variableDatumRecords)

    def _marshalledBodySize(self) -> int:
        return (
            super(EventReportReliablePdu, self)._marshalledBodySize()
            + 4
            + 4
            + 4
            + 4
            + sum(item.marshalledSize() for item in self.fixedDatumRecords)
            + sum(item.marshalledSize() for item in self.variableDatumRecords)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(EventReportReliablePdu, self)._serializeBody(outputStream)
        outputStream.write_uint32(self.eventType)
        outputStream.write_uint32(self.pad1)
        outputStream.write_uint32(self.numberOfFixedDatumRecords)
        outputStream.write_uint32(self.numberOfVariableDatumRecords)
        for item in self.fixedDatumRecords:
            item.serialize(outputStream)
        for item in self.variableDatumRecords:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(EventReportReliablePdu, self)._parseBody(inputStream)
        self.eventType = rich_or_int(73, inputStream.read_uint32())
        self.pad1 = inputStream.read_uint32()
        numberOfFixedDatumRecords = inputStream.read_uint32()
        numberOfVariableDatumRecords = inputStream.read_uint32()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.fixedDatumRecords = [
            FixedDatum.parseFrom(inputStream) for _ in range(numberOfFixedDatumRecords)
        ]
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.variableDatumRecords = [
            VariableDatum.parseFrom(inputStream)
            for _ in range(numberOfVariableDatumRecords)
        ]


EventReportRPdu = EventReportReliablePdu


@dataclass(slots=True)
class CommentReliablePdu(SimulationManagementWithReliabilityFamilyPdu):
    """§5.12.4.13 Comment-R PDU

    Serves the same function as the Comment PDU. Canonical descriptive name;
    CommentRPdu is an alias.

    The fixed datum count is not used by this PDU (shall be zero); the list
    is kept so malformed-but-parseable datagrams still round-trip byte-
    exact.
    """

    pduType: ClassVar[int] = 62  # [UID 4]

    variableDatumRecords: list[VariableDatum] = field(default_factory=list)
    fixedDatumRecords: list[FixedDatum] = field(default_factory=list)

    @property
    def numberOfFixedDatumRecords(self) -> uint32:
        """Fixed datum record count, not used in this Pdu."""
        return len(self.fixedDatumRecords)

    @property
    def numberOfVariableDatumRecords(self) -> uint32:
        """variable datum record count."""
        return len(self.variableDatumRecords)

    def _marshalledBodySize(self) -> int:
        return (
            super(CommentReliablePdu, self)._marshalledBodySize()
            + 4
            + 4
            + sum(item.marshalledSize() for item in self.variableDatumRecords)
            + sum(item.marshalledSize() for item in self.fixedDatumRecords)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(CommentReliablePdu, self)._serializeBody(outputStream)
        outputStream.write_uint32(self.numberOfFixedDatumRecords)
        outputStream.write_uint32(self.numberOfVariableDatumRecords)
        for item in self.variableDatumRecords:
            item.serialize(outputStream)
        for item in self.fixedDatumRecords:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(CommentReliablePdu, self)._parseBody(inputStream)
        numberOfFixedDatumRecords = inputStream.read_uint32()
        numberOfVariableDatumRecords = inputStream.read_uint32()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.variableDatumRecords = [
            VariableDatum.parseFrom(inputStream)
            for _ in range(numberOfVariableDatumRecords)
        ]
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.fixedDatumRecords = [
            FixedDatum.parseFrom(inputStream) for _ in range(numberOfFixedDatumRecords)
        ]


CommentRPdu = CommentReliablePdu


@dataclass(slots=True)
class RecordReliablePdu(SimulationManagementWithReliabilityFamilyPdu):
    """§5.12.4.16 Record-R PDU

    Used to respond to a Record Query-R PDU or a Set Record-R PDU. It is
    used to provide information requested in a Record Query-R PDU, to
    confirm the information received in a Set Record-R PDU, and to confirm
    the receipt of a periodic or unsolicited Record-R PDU when the
    acknowledged service level is used. Canonical descriptive name;
    RecordRPdu is an alias.
    """

    pduType: ClassVar[int] = 63  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "requiredReliabilityService": 74,
        "eventType": 333,
    }

    requestID: uint32 = 0
    requiredReliabilityService: enum8 = 0  # [UID 74]
    eventType: enum16 = 0  # [UID 333]
    responseSerialNumber: uint32 = 0
    recordSets: list[RecordSpecificationElement] = field(default_factory=list)
    pad1: uint8 = field(init=False, default=0)

    @property
    def numberOfRecordSets(self) -> uint32:
        """Number of record sets in list."""
        return len(self.recordSets)

    def _marshalledBodySize(self) -> int:
        return (
            super(RecordReliablePdu, self)._marshalledBodySize()
            + 4
            + 1
            + 1
            + 2
            + 4
            + 4
            + sum(item.marshalledSize() for item in self.recordSets)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(RecordReliablePdu, self)._serializeBody(outputStream)
        outputStream.write_uint32(self.requestID)
        outputStream.write_uint8(self.requiredReliabilityService)
        outputStream.write_uint8(self.pad1)
        outputStream.write_uint16(self.eventType)
        outputStream.write_uint32(self.responseSerialNumber)
        outputStream.write_uint32(self.numberOfRecordSets)
        for item in self.recordSets:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(RecordReliablePdu, self)._parseBody(inputStream)
        self.requestID = inputStream.read_uint32()
        self.requiredReliabilityService = rich_or_int(74, inputStream.read_uint8())
        self.pad1 = inputStream.read_uint8()
        self.eventType = rich_or_int(333, inputStream.read_uint16())
        self.responseSerialNumber = inputStream.read_uint32()
        numberOfRecordSets = inputStream.read_uint32()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.recordSets = [
            RecordSpecificationElement.parseFrom(inputStream)
            for _ in range(numberOfRecordSets)
        ]


RecordRPdu = RecordReliablePdu


@dataclass(slots=True)
class SetRecordReliablePdu(SimulationManagementWithReliabilityFamilyPdu):
    """§5.12.4.15 Set Record-R PDU

    Used to set or change certain parameter values. These parameter values
    are contained within a record format as compared to the datum format
    used in the Set Data-R PDU. Canonical descriptive name; SetRecordRPdu is
    an alias.
    """

    pduType: ClassVar[int] = 64  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "requiredReliabilityService": 74,
    }

    requestID: uint32 = 0
    requiredReliabilityService: enum8 = 0  # [UID 74]
    recordSets: list[RecordSpecificationElement] = field(default_factory=list)
    pad1: uint8 = field(init=False, default=0)
    pad2: uint16 = field(init=False, default=0)
    pad3: uint32 = field(init=False, default=0)

    @property
    def numberOfRecordSets(self) -> uint32:
        """Number of record sets in list."""
        return len(self.recordSets)

    def _marshalledBodySize(self) -> int:
        return (
            super(SetRecordReliablePdu, self)._marshalledBodySize()
            + 4
            + 1
            + 1
            + 2
            + 4
            + 4
            + sum(item.marshalledSize() for item in self.recordSets)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(SetRecordReliablePdu, self)._serializeBody(outputStream)
        outputStream.write_uint32(self.requestID)
        outputStream.write_uint8(self.requiredReliabilityService)
        outputStream.write_uint8(self.pad1)
        outputStream.write_uint16(self.pad2)
        outputStream.write_uint32(self.pad3)
        outputStream.write_uint32(self.numberOfRecordSets)
        for item in self.recordSets:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(SetRecordReliablePdu, self)._parseBody(inputStream)
        self.requestID = inputStream.read_uint32()
        self.requiredReliabilityService = rich_or_int(74, inputStream.read_uint8())
        self.pad1 = inputStream.read_uint8()
        self.pad2 = inputStream.read_uint16()
        self.pad3 = inputStream.read_uint32()
        numberOfRecordSets = inputStream.read_uint32()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.recordSets = [
            RecordSpecificationElement.parseFrom(inputStream)
            for _ in range(numberOfRecordSets)
        ]


SetRecordRPdu = SetRecordReliablePdu


@dataclass(slots=True)
class RecordQueryReliablePdu(SimulationManagementWithReliabilityFamilyPdu):
    """§5.12.4.14 Record Query-R PDU

    Used to communicate a request for data in record format. Canonical
    descriptive name; RecordQueryRPdu is an alias.
    """

    pduType: ClassVar[int] = 65  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "requiredReliabilityService": 74,
        "eventType": 334,
    }

    requestID: uint32 = 0
    requiredReliabilityService: enum8 = 0  # [UID 74]
    eventType: enum16 = 0  # [UID 334]
    time: uint32 = 0
    recordIDs: list[enum32] = field(default_factory=list)
    pad1: uint8 = field(init=False, default=0)

    @property
    def numberOfRecords(self) -> uint32:
        """numberOfRecords."""
        return len(self.recordIDs)

    def _marshalledBodySize(self) -> int:
        return (
            super(RecordQueryReliablePdu, self)._marshalledBodySize()
            + 4
            + 1
            + 1
            + 2
            + 4
            + 4
            + 4 * len(self.recordIDs)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(RecordQueryReliablePdu, self)._serializeBody(outputStream)
        outputStream.write_uint32(self.requestID)
        outputStream.write_uint8(self.requiredReliabilityService)
        outputStream.write_uint8(self.pad1)
        outputStream.write_uint16(self.eventType)
        outputStream.write_uint32(self.time)
        outputStream.write_uint32(self.numberOfRecords)
        for item in self.recordIDs:
            outputStream.write_uint32(item)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(RecordQueryReliablePdu, self)._parseBody(inputStream)
        self.requestID = inputStream.read_uint32()
        self.requiredReliabilityService = rich_or_int(74, inputStream.read_uint8())
        self.pad1 = inputStream.read_uint8()
        self.eventType = rich_or_int(334, inputStream.read_uint16())
        self.time = inputStream.read_uint32()
        numberOfRecords = inputStream.read_uint32()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.recordIDs = [
            rich_or_int(66, inputStream.read_uint32()) for _ in range(numberOfRecords)
        ]


RecordQueryRPdu = RecordQueryReliablePdu
