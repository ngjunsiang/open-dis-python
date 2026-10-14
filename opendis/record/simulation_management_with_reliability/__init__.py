"""Simulation Management with Reliability family (IEEE 1278.1-2012
§5.12.4) — target-state PDUs.

Wire ground truth: xml-fixed/SimulationManagementWithReliabilityFamilyPdus.xml.
Each PDU pairs a §5.6 twin with a reliability-service level. Per the
aliasFor ruling the descriptive name is canonical and the abbreviation
is a plain module-level alias (e.g. ``CreateEntityRPdu =
CreateEntityReliablePdu``).

XML deltas applied deliberately (see docs/design/sample-review.md):
- originator/receiver keep the exemplar's EntityIdentifier
  shape/names (same 6-byte wire field, §6.2.81).
- Record Query-R carries a flat datum-ID list; Record-R/Set Record-R
  carry a flat record-set list — the XML wraps each in an extra
  RecordQuerySpecification/RecordSpecification layer the standard's
  §5.12.4.14–16 tables do not have.
"""

from dataclasses import dataclass, field
from typing import ClassVar

from opendis.bitfields import StopFreezeFrozenBehavior
from opendis.enum_registry import rich_or_int
from opendis.record.common import ClockTime, EntityIdentifier
from opendis.record.pdu import Pdu
from opendis.record.simulation_management import (
    FixedDatum,
    VariableDatum,
    _DatumListsMixin,
)
from opendis.stream import DataInputStream, DataOutputStream
from opendis.types import enum8, enum16, enum32, uint8, uint16, uint32

__all__ = [
    "AcknowledgeReliablePdu",
    "ActionRequestReliablePdu",
    "ActionResponseReliablePdu",
    "CommentReliablePdu",
    "CreateEntityReliablePdu",
    "DataQueryReliablePdu",
    "DataReliablePdu",
    "EventReportReliablePdu",
    "RecordQueryReliablePdu",
    "RecordReliablePdu",
    "RecordSpecificationElement",
    "RemoveEntityReliablePdu",
    "SetDataReliablePdu",
    "SetRecordReliablePdu",
    "SimulationManagementWithReliabilityFamilyPdu",
    "StartResumeReliablePdu",
    "StopFreezeReliablePdu",
]


@dataclass(slots=True)
class SimulationManagementWithReliabilityFamilyPdu(Pdu):
    """§5.12.4 base: Simulation Management PDU header fields plus the
    reliability-service conventions of the -R family."""

    protocolFamily: ClassVar[int] = 10  # [UID 5]

    originatingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    receivingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)

    def _marshalledBodySize(self) -> int:
        return (self.originatingEntityID.marshalledSize()
                + self.receivingEntityID.marshalledSize())

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.originatingEntityID.serialize(outputStream)
        self.receivingEntityID.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.originatingEntityID = EntityIdentifier.parse(inputStream)
        self.receivingEntityID = EntityIdentifier.parse(inputStream)


@dataclass(slots=True)
class RecordSpecificationElement:
    """Section 6.2.73 Record Set (one element of a Record Specification)

    A block of same-typed records: record ID, serial number, the length
    of ONE record in bits, how many records, then the concatenated
    record values (byte granularity — bit lengths not divisible by 8
    are unsupported, same ruling as VariableDatum). The set is padded to
    a 64-bit boundary by the packer."""

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "recordID": 66,
    }

    recordID: enum32 = 0  # [UID 66] Variable Record Type
    recordSetSerialNumber: uint32 = 0
    recordLength: uint16 = 0  # bits, per record
    recordCount: uint16 = 0
    recordValues: bytes = b""

    padding: uint32 = field(init=False, default=0)

    def marshalledSize(self) -> int:
        prefix = 4 + 4 + 4 + 2 + 2
        return prefix + len(self.recordValues) + self._padTo64(prefix)

    @staticmethod
    def _padTo64(byteCount: int) -> int:
        return (8 - byteCount % 8) % 8

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint32(self.recordID)
        outputStream.write_uint32(self.recordSetSerialNumber)
        outputStream.write_uint32(self.padding)
        outputStream.write_uint16(self.recordLength)
        outputStream.write_uint16(self.recordCount)
        outputStream.write_bytes(self.recordValues)
        padding = self._padTo64(14 + len(self.recordValues))
        if padding:
            outputStream.write_bytes(b"\x00" * padding)

    def parse(self, inputStream: DataInputStream) -> None:
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

    @classmethod
    def parseFrom(cls, inputStream: DataInputStream) -> "RecordSpecificationElement":
        """Construct a new record set from the stream (list-parse helper)."""
        record = cls()
        record.parse(inputStream)
        return record


@dataclass(slots=True)
class CreateEntityReliablePdu(SimulationManagementWithReliabilityFamilyPdu):
    """§5.12.4.2 Create Entity-R PDU — Create Entity with reliability
    service levels. Total PDU size is 32 bytes."""

    pduType: ClassVar[int] = 51  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "requiredReliabilityService": 74,
    }

    requiredReliabilityService: enum8 = 0  # [UID 74]
    requestID: uint32 = 0

    pad1: uint8 = field(init=False, default=0)
    pad2: uint16 = field(init=False, default=0)

    def _marshalledBodySize(self) -> int:
        return (super(CreateEntityReliablePdu, self)._marshalledBodySize()
                + 1 + 1 + 2 + 4)

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(CreateEntityReliablePdu, self)._serializeBody(outputStream)
        outputStream.write_uint8(self.requiredReliabilityService)
        outputStream.write_uint8(self.pad1)
        outputStream.write_uint16(self.pad2)
        outputStream.write_uint32(self.requestID)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(CreateEntityReliablePdu, self)._parseBody(inputStream)
        self.requiredReliabilityService = rich_or_int(
            74, inputStream.read_uint8())
        self.pad1 = inputStream.read_uint8()
        self.pad2 = inputStream.read_uint16()
        self.requestID = inputStream.read_uint32()


# generator: aliasFor elements — one class plus a name assignment;
# descriptive name canonical, abbreviation aliased
CreateEntityRPdu = CreateEntityReliablePdu


@dataclass(slots=True)
class RemoveEntityReliablePdu(SimulationManagementWithReliabilityFamilyPdu):
    """§5.12.4.3 Remove Entity-R PDU. Total PDU size is 32 bytes."""

    pduType: ClassVar[int] = 52  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "requiredReliabilityService": 74,
    }

    requiredReliabilityService: enum8 = 0  # [UID 74]
    requestID: uint32 = 0

    pad1: uint8 = field(init=False, default=0)
    pad2: uint16 = field(init=False, default=0)

    def _marshalledBodySize(self) -> int:
        return (super(RemoveEntityReliablePdu, self)._marshalledBodySize()
                + 1 + 1 + 2 + 4)

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(RemoveEntityReliablePdu, self)._serializeBody(outputStream)
        outputStream.write_uint8(self.requiredReliabilityService)
        outputStream.write_uint8(self.pad1)
        outputStream.write_uint16(self.pad2)
        outputStream.write_uint32(self.requestID)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(RemoveEntityReliablePdu, self)._parseBody(inputStream)
        self.requiredReliabilityService = rich_or_int(
            74, inputStream.read_uint8())
        self.pad1 = inputStream.read_uint8()
        self.pad2 = inputStream.read_uint16()
        self.requestID = inputStream.read_uint32()


RemoveEntityRPdu = RemoveEntityReliablePdu


@dataclass(slots=True)
class StartResumeReliablePdu(SimulationManagementWithReliabilityFamilyPdu):
    """§5.12.4.4 Start/Resume-R PDU. Total PDU size is 48 bytes."""

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
        return (super(StartResumeReliablePdu, self)._marshalledBodySize()
                + self.realWorldTime.marshalledSize()
                + self.simulationTime.marshalledSize()
                + 1 + 1 + 2 + 4)

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
        self.requiredReliabilityService = rich_or_int(
            74, inputStream.read_uint8())
        self.pad1 = inputStream.read_uint8()
        self.pad2 = inputStream.read_uint16()
        self.requestID = inputStream.read_uint32()


StartResumeRPdu = StartResumeReliablePdu


@dataclass(slots=True)
class StopFreezeReliablePdu(SimulationManagementWithReliabilityFamilyPdu):
    """§5.12.4.5 Stop/Freeze-R PDU — Stop/Freeze with reliability service
    levels. Total PDU size is 40 bytes."""

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
        return (super(StopFreezeReliablePdu, self)._marshalledBodySize()
                + self.realWorldTime.marshalledSize()
                + 1 + 1 + 1 + 1 + 4)

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
        self.frozenBehavior = StopFreezeFrozenBehavior(
            inputStream.read_uint8())
        self.requiredReliabilityService = rich_or_int(
            74, inputStream.read_uint8())
        self.pad1 = inputStream.read_uint8()
        self.requestID = inputStream.read_uint32()


StopFreezeRPdu = StopFreezeReliablePdu


@dataclass(slots=True)
class AcknowledgeReliablePdu(SimulationManagementWithReliabilityFamilyPdu):
    """§5.12.4.6 Acknowledge-R PDU — acknowledges the -R Create/Remove/
    Start/Stop requests. Total PDU size is 32 bytes."""

    pduType: ClassVar[int] = 55  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "acknowledgeFlag": 69,
        "responseFlag": 70,
    }

    acknowledgeFlag: enum16 = 0  # [UID 69]
    responseFlag: enum16 = 0  # [UID 70]
    requestID: uint32 = 0

    def _marshalledBodySize(self) -> int:
        return (super(AcknowledgeReliablePdu, self)._marshalledBodySize()
                + 2 + 2 + 4)

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
class ActionRequestReliablePdu(_DatumListsMixin,
                               SimulationManagementWithReliabilityFamilyPdu):
    """§5.12.4.7 Action Request-R PDU. Total base PDU size is 44 bytes
    plus datums."""

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

    def _marshalledBodySize(self) -> int:
        return (super(ActionRequestReliablePdu, self)._marshalledBodySize()
                + 1 + 1 + 2 + 4 + 4 + self._datumTailSize())

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(ActionRequestReliablePdu, self)._serializeBody(outputStream)
        outputStream.write_uint8(self.requiredReliabilityService)
        outputStream.write_uint8(self.pad1)
        outputStream.write_uint16(self.pad2)
        outputStream.write_uint32(self.requestID)
        outputStream.write_uint32(self.actionID)
        self._serializeDatumTail(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(ActionRequestReliablePdu, self)._parseBody(inputStream)
        self.requiredReliabilityService = rich_or_int(
            74, inputStream.read_uint8())
        self.pad1 = inputStream.read_uint8()
        self.pad2 = inputStream.read_uint16()
        self.requestID = inputStream.read_uint32()
        self.actionID = rich_or_int(71, inputStream.read_uint32())
        self._parseDatumTail(inputStream)


ActionRequestRPdu = ActionRequestReliablePdu


@dataclass(slots=True)
class ActionResponseReliablePdu(_DatumListsMixin,
                                SimulationManagementWithReliabilityFamilyPdu):
    """§5.12.4.8 Action Response-R PDU. Total base PDU size is 40 bytes
    plus datums."""

    pduType: ClassVar[int] = 57  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "responseStatus": 72,
    }

    requestID: uint32 = 0
    responseStatus: enum32 = 0  # [UID 72]
    fixedDatumRecords: list[FixedDatum] = field(default_factory=list)
    variableDatumRecords: list[VariableDatum] = field(default_factory=list)

    def _marshalledBodySize(self) -> int:
        return (super(ActionResponseReliablePdu, self)._marshalledBodySize()
                + 4 + 4 + self._datumTailSize())

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(ActionResponseReliablePdu, self)._serializeBody(outputStream)
        outputStream.write_uint32(self.requestID)
        outputStream.write_uint32(self.responseStatus)
        self._serializeDatumTail(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(ActionResponseReliablePdu, self)._parseBody(inputStream)
        self.requestID = inputStream.read_uint32()
        self.responseStatus = rich_or_int(72, inputStream.read_uint32())
        self._parseDatumTail(inputStream)


ActionResponseRPdu = ActionResponseReliablePdu


@dataclass(slots=True)
class DataQueryReliablePdu(SimulationManagementWithReliabilityFamilyPdu):
    """§5.12.4.9 Data Query-R PDU — datum ID lists (u32 each), like the
    Data Query PDU. Total base PDU size is 44 bytes plus IDs."""

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
        return len(self.fixedDatumIDs)

    @property
    def numberOfVariableDatumIDs(self) -> uint32:
        return len(self.variableDatumIDs)

    def _marshalledBodySize(self) -> int:
        return (super(DataQueryReliablePdu, self)._marshalledBodySize()
                + 1 + 1 + 2 + 4 + 4 + 4 + 4
                + 4 * len(self.fixedDatumIDs)
                + 4 * len(self.variableDatumIDs))

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(DataQueryReliablePdu, self)._serializeBody(outputStream)
        outputStream.write_uint8(self.requiredReliabilityService)
        outputStream.write_uint8(self.pad1)
        outputStream.write_uint16(self.pad2)
        outputStream.write_uint32(self.requestID)
        outputStream.write_uint32(self.timeInterval)
        outputStream.write_uint32(self.numberOfFixedDatumIDs)
        outputStream.write_uint32(self.numberOfVariableDatumIDs)
        for datumID in self.fixedDatumIDs:
            outputStream.write_uint32(datumID)
        for datumID in self.variableDatumIDs:
            outputStream.write_uint32(datumID)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(DataQueryReliablePdu, self)._parseBody(inputStream)
        self.requiredReliabilityService = rich_or_int(
            74, inputStream.read_uint8())
        self.pad1 = inputStream.read_uint8()
        self.pad2 = inputStream.read_uint16()
        self.requestID = inputStream.read_uint32()
        self.timeInterval = inputStream.read_uint32()
        numberOfFixedDatumIDs = inputStream.read_uint32()
        numberOfVariableDatumIDs = inputStream.read_uint32()
        self.fixedDatumIDs = [
            rich_or_int(66, inputStream.read_uint32())
            for _ in range(numberOfFixedDatumIDs)
        ]
        self.variableDatumIDs = [
            rich_or_int(66, inputStream.read_uint32())
            for _ in range(numberOfVariableDatumIDs)
        ]


DataQueryRPdu = DataQueryReliablePdu


@dataclass(slots=True)
class SetDataReliablePdu(_DatumListsMixin,
                         SimulationManagementWithReliabilityFamilyPdu):
    """§5.12.4.10 Set Data-R PDU. Total base PDU size is 40 bytes plus
    datums."""

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

    def _marshalledBodySize(self) -> int:
        return (super(SetDataReliablePdu, self)._marshalledBodySize()
                + 1 + 1 + 2 + 4 + self._datumTailSize())

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(SetDataReliablePdu, self)._serializeBody(outputStream)
        outputStream.write_uint8(self.requiredReliabilityService)
        outputStream.write_uint8(self.pad1)
        outputStream.write_uint16(self.pad2)
        outputStream.write_uint32(self.requestID)
        self._serializeDatumTail(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(SetDataReliablePdu, self)._parseBody(inputStream)
        self.requiredReliabilityService = rich_or_int(
            74, inputStream.read_uint8())
        self.pad1 = inputStream.read_uint8()
        self.pad2 = inputStream.read_uint16()
        self.requestID = inputStream.read_uint32()
        self._parseDatumTail(inputStream)


SetDataRPdu = SetDataReliablePdu


@dataclass(slots=True)
class DataReliablePdu(_DatumListsMixin,
                      SimulationManagementWithReliabilityFamilyPdu):
    """§5.12.4.11 Data-R PDU — response to Data Query-R / Set Data-R.
    Total base PDU size is 40 bytes plus datums."""

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

    def _marshalledBodySize(self) -> int:
        return (super(DataReliablePdu, self)._marshalledBodySize()
                + 4 + 1 + 1 + 2 + self._datumTailSize())

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(DataReliablePdu, self)._serializeBody(outputStream)
        outputStream.write_uint32(self.requestID)
        outputStream.write_uint8(self.requiredReliabilityService)
        outputStream.write_uint8(self.pad1)
        outputStream.write_uint16(self.pad2)
        self._serializeDatumTail(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(DataReliablePdu, self)._parseBody(inputStream)
        self.requestID = inputStream.read_uint32()
        self.requiredReliabilityService = rich_or_int(
            74, inputStream.read_uint8())
        self.pad1 = inputStream.read_uint8()
        self.pad2 = inputStream.read_uint16()
        self._parseDatumTail(inputStream)


DataRPdu = DataReliablePdu


@dataclass(slots=True)
class EventReportReliablePdu(_DatumListsMixin,
                             SimulationManagementWithReliabilityFamilyPdu):
    """§5.12.4.12 Event Report-R PDU. Total base PDU size is 40 bytes
    plus datums."""

    pduType: ClassVar[int] = 61  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "eventType": 73,
    }

    eventType: enum32 = 0  # [UID 73]
    fixedDatumRecords: list[FixedDatum] = field(default_factory=list)
    variableDatumRecords: list[VariableDatum] = field(default_factory=list)

    pad1: uint32 = field(init=False, default=0)

    def _marshalledBodySize(self) -> int:
        return (super(EventReportReliablePdu, self)._marshalledBodySize()
                + 4 + 4 + self._datumTailSize())

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(EventReportReliablePdu, self)._serializeBody(outputStream)
        outputStream.write_uint32(self.eventType)
        outputStream.write_uint32(self.pad1)
        self._serializeDatumTail(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(EventReportReliablePdu, self)._parseBody(inputStream)
        self.eventType = rich_or_int(73, inputStream.read_uint32())
        self.pad1 = inputStream.read_uint32()
        self._parseDatumTail(inputStream)


EventReportRPdu = EventReportReliablePdu


@dataclass(slots=True)
class CommentReliablePdu(_DatumListsMixin,
                         SimulationManagementWithReliabilityFamilyPdu):
    """§5.12.4.13 Comment-R PDU. The fixed datum count is not used by
    this PDU (shall be zero); the list is kept so malformed-but-parseable
    datagrams still round-trip byte-exact. Total base PDU size is 32
    bytes plus datums."""

    pduType: ClassVar[int] = 62  # [UID 4]

    fixedDatumRecords: list[FixedDatum] = field(default_factory=list)
    variableDatumRecords: list[VariableDatum] = field(default_factory=list)

    def _marshalledBodySize(self) -> int:
        return (super(CommentReliablePdu, self)._marshalledBodySize()
                + self._datumTailSize())

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(CommentReliablePdu, self)._serializeBody(outputStream)
        self._serializeDatumTail(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(CommentReliablePdu, self)._parseBody(inputStream)
        self._parseDatumTail(inputStream)


CommentRPdu = CommentReliablePdu


@dataclass(slots=True)
class RecordReliablePdu(SimulationManagementWithReliabilityFamilyPdu):
    """§5.12.4.16 Record-R PDU — responds to Record Query-R / Set
    Record-R with record sets. Total base PDU size is 36 bytes plus
    record sets."""

    pduType: ClassVar[int] = 63  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "requiredReliabilityService": 74,
        "eventType": 333,
    }

    requestID: uint32 = 0
    requiredReliabilityService: enum8 = 0  # [UID 74]
    eventType: enum16 = 0  # [UID 333] Record-R event type
    recordSets: list[RecordSpecificationElement] = field(
        default_factory=list)

    pad1: uint8 = field(init=False, default=0)

    @property
    def numberOfRecordSets(self) -> uint32:
        return len(self.recordSets)

    def _marshalledBodySize(self) -> int:
        return (super(RecordReliablePdu, self)._marshalledBodySize()
                + 4 + 1 + 1 + 2 + 4
                + sum(rs.marshalledSize() for rs in self.recordSets))

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(RecordReliablePdu, self)._serializeBody(outputStream)
        outputStream.write_uint32(self.requestID)
        outputStream.write_uint8(self.requiredReliabilityService)
        outputStream.write_uint8(self.pad1)
        outputStream.write_uint16(self.eventType)
        outputStream.write_uint32(self.numberOfRecordSets)
        for recordSet in self.recordSets:
            recordSet.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(RecordReliablePdu, self)._parseBody(inputStream)
        self.requestID = inputStream.read_uint32()
        self.requiredReliabilityService = rich_or_int(
            74, inputStream.read_uint8())
        self.pad1 = inputStream.read_uint8()
        self.eventType = rich_or_int(333, inputStream.read_uint16())
        numberOfRecordSets = inputStream.read_uint32()
        self.recordSets = [
            RecordSpecificationElement.parseFrom(inputStream)
            for _ in range(numberOfRecordSets)
        ]


RecordRPdu = RecordReliablePdu


@dataclass(slots=True)
class SetRecordReliablePdu(SimulationManagementWithReliabilityFamilyPdu):
    """§5.12.4.15 Set Record-R PDU. Total base PDU size is 40 bytes plus
    record sets."""

    pduType: ClassVar[int] = 64  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "requiredReliabilityService": 74,
    }

    requestID: uint32 = 0
    requiredReliabilityService: enum8 = 0  # [UID 74]
    recordSets: list[RecordSpecificationElement] = field(
        default_factory=list)

    pad1: uint8 = field(init=False, default=0)
    pad2: uint16 = field(init=False, default=0)
    pad3: uint32 = field(init=False, default=0)

    @property
    def numberOfRecordSets(self) -> uint32:
        return len(self.recordSets)

    def _marshalledBodySize(self) -> int:
        return (super(SetRecordReliablePdu, self)._marshalledBodySize()
                + 4 + 1 + 1 + 2 + 4 + 4
                + sum(rs.marshalledSize() for rs in self.recordSets))

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(SetRecordReliablePdu, self)._serializeBody(outputStream)
        outputStream.write_uint32(self.requestID)
        outputStream.write_uint8(self.requiredReliabilityService)
        outputStream.write_uint8(self.pad1)
        outputStream.write_uint16(self.pad2)
        outputStream.write_uint32(self.pad3)
        outputStream.write_uint32(self.numberOfRecordSets)
        for recordSet in self.recordSets:
            recordSet.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(SetRecordReliablePdu, self)._parseBody(inputStream)
        self.requestID = inputStream.read_uint32()
        self.requiredReliabilityService = rich_or_int(
            74, inputStream.read_uint8())
        self.pad1 = inputStream.read_uint8()
        self.pad2 = inputStream.read_uint16()
        self.pad3 = inputStream.read_uint32()
        numberOfRecordSets = inputStream.read_uint32()
        self.recordSets = [
            RecordSpecificationElement.parseFrom(inputStream)
            for _ in range(numberOfRecordSets)
        ]


SetRecordRPdu = SetRecordReliablePdu


@dataclass(slots=True)
class RecordQueryReliablePdu(SimulationManagementWithReliabilityFamilyPdu):
    """§5.12.4.14 Record Query-R PDU — requests data in record format;
    the flat record-ID list is the §6.2.72 Record Query Specification.
    Total base PDU size is 40 bytes plus IDs."""

    pduType: ClassVar[int] = 65  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "requiredReliabilityService": 74,
        "eventType": 334,
    }

    requestID: uint32 = 0
    requiredReliabilityService: enum8 = 0  # [UID 74]
    eventType: enum16 = 0  # [UID 334] Record Query-R event type
    time: uint32 = 0
    recordIDs: list[enum32] = field(default_factory=list)

    pad1: uint8 = field(init=False, default=0)

    @property
    def numberOfRecords(self) -> uint32:
        return len(self.recordIDs)

    def _marshalledBodySize(self) -> int:
        return (super(RecordQueryReliablePdu, self)._marshalledBodySize()
                + 4 + 1 + 1 + 2 + 4 + 4
                + 4 * len(self.recordIDs))

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(RecordQueryReliablePdu, self)._serializeBody(outputStream)
        outputStream.write_uint32(self.requestID)
        outputStream.write_uint8(self.requiredReliabilityService)
        outputStream.write_uint8(self.pad1)
        outputStream.write_uint16(self.eventType)
        outputStream.write_uint32(self.time)
        outputStream.write_uint32(self.numberOfRecords)
        for recordID in self.recordIDs:
            outputStream.write_uint32(recordID)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(RecordQueryReliablePdu, self)._parseBody(inputStream)
        self.requestID = inputStream.read_uint32()
        self.requiredReliabilityService = rich_or_int(
            74, inputStream.read_uint8())
        self.pad1 = inputStream.read_uint8()
        self.eventType = rich_or_int(334, inputStream.read_uint16())
        self.time = inputStream.read_uint32()
        numberOfRecords = inputStream.read_uint32()
        self.recordIDs = [
            rich_or_int(66, inputStream.read_uint32())
            for _ in range(numberOfRecords)
        ]


RecordQueryRPdu = RecordQueryReliablePdu
