"""Simulation Management family (IEEE 1278.1-2012 §5.6) — datum showcase.

DataPdu with FixedDatum records and VariableDatum records whose payloads
are ``bytes`` (never per-byte lists), 64-bit padding computed by the
packer, and a typed uid-66 decoder path through the existing
StandardVariableRecord registry (opendis/record/__init__.py).
"""

import io
from dataclasses import dataclass, field
from typing import ClassVar

from opendis.enum_registry import rich_or_int
from opendis.record.base import StandardVariableRecord
from opendis.record.common import EntityIdentifier
from opendis.record.pdu import Pdu
from opendis.stream import DataInputStream, DataOutputStream
from opendis.types import enum8, enum16, enum32, uint8, uint16, uint32

__all__ = [
    "AcknowledgePdu",
    "ActionRequestPdu",
    "ActionResponsePdu",
    "CommentPdu",
    "CreateEntityPdu",
    "DataPdu",
    "DataQueryPdu",
    "EventReportPdu",
    "FixedDatum",
    "RemoveEntityPdu",
    "SetDataPdu",
    "SimulationManagementFamilyPdu",
    "StartResumePdu",
    "StopFreezePdu",
    "VariableDatum",
]


@dataclass(slots=True)
class FixedDatum:
    """Section 6.2.37 Fixed Datum record

    The fixed datum type, and a 32-bit value for that fixed datum type.
    """

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "fixedDatumID": 66,
    }

    fixedDatumID: enum32 = 0  # [UID 66] Variable Record Type
    fixedDatumValue: uint32 = 0

    def marshalledSize(self) -> int:
        return 8

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint32(self.fixedDatumID)
        outputStream.write_uint32(self.fixedDatumValue)

    def parse(self, inputStream: DataInputStream) -> None:
        self.fixedDatumID = rich_or_int(66, inputStream.read_uint32())
        self.fixedDatumValue = inputStream.read_uint32()

    @classmethod
    def parseFrom(cls, inputStream: DataInputStream) -> "FixedDatum":
        """Construct a new record from the stream (list-parse helper)."""
        fd = cls()
        fd.parse(inputStream)
        return fd


def _paddedDatumSize(byteCount: int) -> int:
    """Datum fields are padded at the end to a multiple of 64 bits."""
    remainder = byteCount % 8
    if remainder:
        byteCount += 8 - remainder
    return byteCount


@dataclass(slots=True)
class VariableDatum:
    """Section 6.2.93 Variable Datum record

    The variable datum type, the datum length in bits, and the value for
    that variable datum type. ``variableData`` is the raw payload as
    ``bytes``; ``variableDatumLength`` (in bits) is derived at serialize
    time and the 64-bit padding is computed by the packer — neither is
    user-settable state.

    # generator: payload carries the complete serialized record when the
    # datum ID is a uid-66 record type, so a known record re-serializes
    # standalone and an unknown one stays raw bytes (forward compat).
    """

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "variableDatumID": 66,
    }

    variableDatumID: enum32 = 0  # [UID 66] Variable Record Type
    variableData: bytes = b""

    @property
    def variableDatumLength(self) -> uint32:
        """Length, IN BITS, of the variable datum — derived from the
        payload, never stored."""
        return len(self.variableData) * 8

    def marshalledSize(self) -> int:
        return 8 + _paddedDatumSize(len(self.variableData))

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint32(self.variableDatumID)
        outputStream.write_uint32(self.variableDatumLength)
        outputStream.write_bytes(self.variableData)
        padding = _paddedDatumSize(len(self.variableData)) - len(self.variableData)
        if padding:
            outputStream.write_bytes(b"\x00" * padding)

    def parse(self,
              inputStream: DataInputStream,
              bytelength: int | None = None) -> None:
        self.variableDatumID = rich_or_int(66, inputStream.read_uint32())
        variableDatumLength = inputStream.read_uint32()
        self.variableData = inputStream.read_bytes(variableDatumLength // 8)
        padding = _paddedDatumSize(len(self.variableData)) - len(self.variableData)
        if padding:
            inputStream.read_bytes(padding)

    @classmethod
    def parseFrom(cls, inputStream: DataInputStream) -> "VariableDatum":
        """Construct a new record from the stream (list-parse helper)."""
        vd = cls()
        vd.parse(inputStream)
        return vd

    @property
    def decodedRecord(self) -> StandardVariableRecord | None:
        """The typed record for this datum, via the StandardVariableRecord
        registry keyed on uid 66 — or None when the record type (or a
        decoder for it) is unknown, leaving the raw bytes authoritative.

        # generator: typed uid-66 decoder wiring; unknown record types
        # degrade to raw bytes rather than raising.
        """
        from opendis.record import (
            getStandardVariableClass,
            isKnownStandardVariableRecord,
        )
        recordType = int(self.variableDatumID)
        if not isKnownStandardVariableRecord(recordType):
            return None
        try:
            stream = DataInputStream(io.BytesIO(self.variableData))
            headerType = stream.read_uint32()
            if headerType != recordType:
                return None
            bytelength = stream.read_uint16()
            record = getStandardVariableClass(recordType)()
            record.parse(stream, bytelength)
            return record
        except Exception:
            # Payload did not parse as this record type; the raw bytes
            # remain the truth (tolerance rule).
            return None


@dataclass(slots=True)
class SimulationManagementFamilyPdu(Pdu):
    """Section 5.6 marker; carries the §6.2.82 Simulation Management PDU
    Header fields (originating and receiving entity IDs)."""

    protocolFamily: ClassVar[int] = 5  # [UID 5]

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
class DataPdu(SimulationManagementFamilyPdu):
    """Section 7.5.11 Data PDU

    Information issued in response to a Data Query PDU or Set Data PDU.
    The request ID is followed by four pad bytes (packer-computed) and the
    fixed and variable datum lists; both counts are ``len()`` properties
    written at serialize time.
    """

    pduType: ClassVar[int] = 20  # [UID 4]

    requestID: uint32 = 0
    padding1: uint32 = field(init=False, default=0)
    fixedDatumRecords: list[FixedDatum] = field(default_factory=list)
    variableDatumRecords: list[VariableDatum] = field(default_factory=list)

    @property
    def numberOfFixedDatumRecords(self) -> uint32:
        return len(self.fixedDatumRecords)

    @property
    def numberOfVariableDatumRecords(self) -> uint32:
        return len(self.variableDatumRecords)

    # generator: two-arg super() — zero-arg super()'s __class__ cell points
    # at the pre-slots class when @dataclass(slots=True) recreates it
    def _marshalledBodySize(self) -> int:
        return (super(DataPdu, self)._marshalledBodySize()
                + 4 + 4  # requestID + padding1
                + 4 + 4  # counts
                + sum(fd.marshalledSize() for fd in self.fixedDatumRecords)
                + sum(vd.marshalledSize() for vd in self.variableDatumRecords))

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(DataPdu, self)._serializeBody(outputStream)
        outputStream.write_uint32(self.requestID)
        outputStream.write_uint32(self.padding1)
        outputStream.write_uint32(self.numberOfFixedDatumRecords)
        outputStream.write_uint32(self.numberOfVariableDatumRecords)
        for anObj in self.fixedDatumRecords:
            anObj.serialize(outputStream)
        for anObj in self.variableDatumRecords:
            anObj.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(DataPdu, self)._parseBody(inputStream)
        self.requestID = inputStream.read_uint32()
        self.padding1 = inputStream.read_uint32()
        numberOfFixedDatumRecords = inputStream.read_uint32()
        numberOfVariableDatumRecords = inputStream.read_uint32()
        self.fixedDatumRecords = [
            self._parseFixedDatum(inputStream)
            for _ in range(numberOfFixedDatumRecords)
        ]
        self.variableDatumRecords = [
            self._parseVariableDatum(inputStream)
            for _ in range(numberOfVariableDatumRecords)
        ]

    @staticmethod
    def _parseFixedDatum(inputStream: DataInputStream) -> FixedDatum:
        fd = FixedDatum()
        fd.parse(inputStream)
        return fd

    @staticmethod
    def _parseVariableDatum(inputStream: DataInputStream) -> VariableDatum:
        vd = VariableDatum()
        vd.parse(inputStream)
        return vd


# ---------------------------------------------------------------------------
# Remaining Simulation Management PDUs (§7.5) in the target-state style.
# Wire ground truth: xml-fixed/SimulationManagementFamilyPdus.xml.
#
# XML deltas applied deliberately (see docs/design/sample-review.md):
# - the base's 48-bit originator/receiver fields keep the exemplar's
#   EntityIdentifier shape/names (originatingEntityID/receivingEntityID);
#   the XML's SimulationIdentifier classRef is the same 6-byte wire shape
#   (§6.2.81 — the field may hold either form).
# - Data Query carries datum ID lists (u32 each, §7.5.9), not FixedDatum
#   records — the XML's objectlist classRef is wrong there.
# - datum list field names are fixedDatumRecords/variableDatumRecords
#   uniformly (the XML mixes fixedDatums/variableDatums spellings).
# ---------------------------------------------------------------------------

from opendis.bitfields import StopFreezeFrozenBehavior  # noqa: E402
from opendis.record.common import ClockTime  # noqa: E402


class _DatumListsMixin:
    """Shared Datum Specification tail (§5.6.7): two u32 counts, fixed
    datum records, variable datum records. Hosts declare the two list
    fields; counts are always derived."""

    @property
    def numberOfFixedDatumRecords(self) -> uint32:
        return len(self.fixedDatumRecords)

    @property
    def numberOfVariableDatumRecords(self) -> uint32:
        return len(self.variableDatumRecords)

    def _datumTailSize(self) -> int:
        return (4 + 4
                + sum(fd.marshalledSize() for fd in self.fixedDatumRecords)
                + sum(vd.marshalledSize() for vd in self.variableDatumRecords))

    def _serializeDatumTail(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint32(self.numberOfFixedDatumRecords)
        outputStream.write_uint32(self.numberOfVariableDatumRecords)
        for fd in self.fixedDatumRecords:
            fd.serialize(outputStream)
        for vd in self.variableDatumRecords:
            vd.serialize(outputStream)

    def _parseDatumTail(self, inputStream: DataInputStream) -> None:
        numberOfFixedDatumRecords = inputStream.read_uint32()
        numberOfVariableDatumRecords = inputStream.read_uint32()
        self.fixedDatumRecords = [
            FixedDatum.parseFrom(inputStream)
            for _ in range(numberOfFixedDatumRecords)
        ]
        self.variableDatumRecords = [
            VariableDatum.parseFrom(inputStream)
            for _ in range(numberOfVariableDatumRecords)
        ]


@dataclass(slots=True)
class CreateEntityPdu(SimulationManagementFamilyPdu):
    """Section 7.5.2 Create Entity PDU

    Communicates the creation of a new entity. Total PDU size is 28
    bytes."""

    pduType: ClassVar[int] = 11  # [UID 4]

    requestID: uint32 = 0

    def _marshalledBodySize(self) -> int:
        return (super(CreateEntityPdu, self)._marshalledBodySize() + 4)

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(CreateEntityPdu, self)._serializeBody(outputStream)
        outputStream.write_uint32(self.requestID)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(CreateEntityPdu, self)._parseBody(inputStream)
        self.requestID = inputStream.read_uint32()


@dataclass(slots=True)
class RemoveEntityPdu(SimulationManagementFamilyPdu):
    """Section 7.5.3 Remove Entity PDU

    Communicates the removal of an entity from an exercise. Total PDU
    size is 28 bytes."""

    pduType: ClassVar[int] = 12  # [UID 4]

    requestID: uint32 = 0

    def _marshalledBodySize(self) -> int:
        return (super(RemoveEntityPdu, self)._marshalledBodySize() + 4)

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(RemoveEntityPdu, self)._serializeBody(outputStream)
        outputStream.write_uint32(self.requestID)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(RemoveEntityPdu, self)._parseBody(inputStream)
        self.requestID = inputStream.read_uint32()


@dataclass(slots=True)
class StartResumePdu(SimulationManagementFamilyPdu):
    """Section 7.5.4 Start/Resume PDU

    Communicates the start/resume of an entity or exercise. Total PDU
    size is 44 bytes."""

    pduType: ClassVar[int] = 13  # [UID 4]

    realWorldTime: ClockTime = field(default_factory=ClockTime)
    simulationTime: ClockTime = field(default_factory=ClockTime)
    requestID: uint32 = 0

    def _marshalledBodySize(self) -> int:
        return (super(StartResumePdu, self)._marshalledBodySize()
                + self.realWorldTime.marshalledSize()
                + self.simulationTime.marshalledSize()
                + 4)

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(StartResumePdu, self)._serializeBody(outputStream)
        self.realWorldTime.serialize(outputStream)
        self.simulationTime.serialize(outputStream)
        outputStream.write_uint32(self.requestID)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(StartResumePdu, self)._parseBody(inputStream)
        self.realWorldTime.parse(inputStream)
        self.simulationTime.parse(inputStream)
        self.requestID = inputStream.read_uint32()


@dataclass(slots=True)
class StopFreezePdu(SimulationManagementFamilyPdu):
    """Section 7.5.5 Stop/Freeze PDU

    Communicates the stopping or freezing of an entity or exercise.
    ``frozenBehavior`` holds the raw uint8 until parsed, then the
    [UID 68] view. Total PDU size is 40 bytes."""

    pduType: ClassVar[int] = 14  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "reason": 67,
    }

    realWorldTime: ClockTime = field(default_factory=ClockTime)
    reason: enum8 = 0  # [UID 67]
    frozenBehavior: uint8 = 0  # [UID 68] or the view
    requestID: uint32 = 0

    padding1: uint16 = field(init=False, default=0)

    def _marshalledBodySize(self) -> int:
        return (super(StopFreezePdu, self)._marshalledBodySize()
                + self.realWorldTime.marshalledSize()
                + 1 + 1 + 2 + 4)

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(StopFreezePdu, self)._serializeBody(outputStream)
        self.realWorldTime.serialize(outputStream)
        outputStream.write_uint8(self.reason)
        outputStream.write_uint8(int(self.frozenBehavior))
        outputStream.write_uint16(self.padding1)
        outputStream.write_uint32(self.requestID)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(StopFreezePdu, self)._parseBody(inputStream)
        self.realWorldTime.parse(inputStream)
        self.reason = rich_or_int(67, inputStream.read_uint8())
        self.frozenBehavior = StopFreezeFrozenBehavior(
            inputStream.read_uint8())
        self.padding1 = inputStream.read_uint16()
        self.requestID = inputStream.read_uint32()


@dataclass(slots=True)
class AcknowledgePdu(SimulationManagementFamilyPdu):
    """Section 7.5.6 Acknowledge PDU

    Acknowledges receipt of a Start/Resume, Stop/Freeze, Create Entity,
    or Remove Entity PDU. Total PDU size is 32 bytes."""

    pduType: ClassVar[int] = 15  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "acknowledgeFlag": 69,
        "responseFlag": 70,
    }

    acknowledgeFlag: enum16 = 0  # [UID 69]
    responseFlag: enum16 = 0  # [UID 70]
    requestID: uint32 = 0

    def _marshalledBodySize(self) -> int:
        return (super(AcknowledgePdu, self)._marshalledBodySize()
                + 2 + 2 + 4)

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(AcknowledgePdu, self)._serializeBody(outputStream)
        outputStream.write_uint16(self.acknowledgeFlag)
        outputStream.write_uint16(self.responseFlag)
        outputStream.write_uint32(self.requestID)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(AcknowledgePdu, self)._parseBody(inputStream)
        self.acknowledgeFlag = rich_or_int(69, inputStream.read_uint16())
        self.responseFlag = rich_or_int(70, inputStream.read_uint16())
        self.requestID = inputStream.read_uint32()


@dataclass(slots=True)
class ActionRequestPdu(_DatumListsMixin, SimulationManagementFamilyPdu):
    """Section 7.5.7 Action Request PDU

    A request from a simulation manager to a managed entity to perform a
    specified action, carrying a Datum Specification."""

    pduType: ClassVar[int] = 16  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "actionID": 71,
    }

    requestID: uint32 = 0
    actionID: enum32 = 0  # [UID 71]
    fixedDatumRecords: list[FixedDatum] = field(default_factory=list)
    variableDatumRecords: list[VariableDatum] = field(default_factory=list)

    def _marshalledBodySize(self) -> int:
        return (super(ActionRequestPdu, self)._marshalledBodySize()
                + 4 + 4 + self._datumTailSize())

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(ActionRequestPdu, self)._serializeBody(outputStream)
        outputStream.write_uint32(self.requestID)
        outputStream.write_uint32(self.actionID)
        self._serializeDatumTail(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(ActionRequestPdu, self)._parseBody(inputStream)
        self.requestID = inputStream.read_uint32()
        self.actionID = rich_or_int(71, inputStream.read_uint32())
        self._parseDatumTail(inputStream)


@dataclass(slots=True)
class ActionResponsePdu(_DatumListsMixin, SimulationManagementFamilyPdu):
    """Section 7.5.8 Action Response PDU

    Acknowledges an Action Request PDU, carrying a Datum Specification."""

    pduType: ClassVar[int] = 17  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "requestStatus": 72,
    }

    requestID: uint32 = 0
    requestStatus: enum32 = 0  # [UID 72]
    fixedDatumRecords: list[FixedDatum] = field(default_factory=list)
    variableDatumRecords: list[VariableDatum] = field(default_factory=list)

    def _marshalledBodySize(self) -> int:
        return (super(ActionResponsePdu, self)._marshalledBodySize()
                + 4 + 4 + self._datumTailSize())

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(ActionResponsePdu, self)._serializeBody(outputStream)
        outputStream.write_uint32(self.requestID)
        outputStream.write_uint32(self.requestStatus)
        self._serializeDatumTail(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(ActionResponsePdu, self)._parseBody(inputStream)
        self.requestID = inputStream.read_uint32()
        self.requestStatus = rich_or_int(72, inputStream.read_uint32())
        self._parseDatumTail(inputStream)


@dataclass(slots=True)
class DataQueryPdu(SimulationManagementFamilyPdu):
    """Section 7.5.9 Data Query PDU

    A request for data from an entity. The lists carry datum IDs (u32
    each, [UID 66]), not datum records — the query names the datums it
    wants (§7.5.9). Total PDU size is 40 + 4·n bytes."""

    pduType: ClassVar[int] = 18  # [UID 4]

    requestID: uint32 = 0
    timeInterval: uint32 = 0
    fixedDatumIDs: list[enum32] = field(default_factory=list)
    variableDatumIDs: list[enum32] = field(default_factory=list)

    @property
    def numberOfFixedDatumIDs(self) -> uint32:
        return len(self.fixedDatumIDs)

    @property
    def numberOfVariableDatumIDs(self) -> uint32:
        return len(self.variableDatumIDs)

    def _marshalledBodySize(self) -> int:
        return (super(DataQueryPdu, self)._marshalledBodySize()
                + 4 + 4 + 4 + 4
                + 4 * len(self.fixedDatumIDs)
                + 4 * len(self.variableDatumIDs))

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(DataQueryPdu, self)._serializeBody(outputStream)
        outputStream.write_uint32(self.requestID)
        outputStream.write_uint32(self.timeInterval)
        outputStream.write_uint32(self.numberOfFixedDatumIDs)
        outputStream.write_uint32(self.numberOfVariableDatumIDs)
        for datumID in self.fixedDatumIDs:
            outputStream.write_uint32(datumID)
        for datumID in self.variableDatumIDs:
            outputStream.write_uint32(datumID)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(DataQueryPdu, self)._parseBody(inputStream)
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


@dataclass(slots=True)
class SetDataPdu(_DatumListsMixin, SimulationManagementFamilyPdu):
    """Section 7.5.10 Set Data PDU

    Initializes or changes internal state information, carrying a Datum
    Specification."""

    pduType: ClassVar[int] = 19  # [UID 4]

    requestID: uint32 = 0
    fixedDatumRecords: list[FixedDatum] = field(default_factory=list)
    variableDatumRecords: list[VariableDatum] = field(default_factory=list)

    padding1: uint32 = field(init=False, default=0)

    def _marshalledBodySize(self) -> int:
        return (super(SetDataPdu, self)._marshalledBodySize()
                + 4 + 4 + self._datumTailSize())

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(SetDataPdu, self)._serializeBody(outputStream)
        outputStream.write_uint32(self.requestID)
        outputStream.write_uint32(self.padding1)
        self._serializeDatumTail(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(SetDataPdu, self)._parseBody(inputStream)
        self.requestID = inputStream.read_uint32()
        self.padding1 = inputStream.read_uint32()
        self._parseDatumTail(inputStream)


@dataclass(slots=True)
class EventReportPdu(_DatumListsMixin, SimulationManagementFamilyPdu):
    """Section 7.5.12 Event Report PDU

    A managed entity reports the occurrence of a significant event to
    the simulation manager, carrying a Datum Specification."""

    pduType: ClassVar[int] = 21  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "eventType": 73,
    }

    eventType: enum32 = 0  # [UID 73]
    fixedDatumRecords: list[FixedDatum] = field(default_factory=list)
    variableDatumRecords: list[VariableDatum] = field(default_factory=list)

    padding1: uint32 = field(init=False, default=0)

    def _marshalledBodySize(self) -> int:
        return (super(EventReportPdu, self)._marshalledBodySize()
                + 4 + 4 + self._datumTailSize())

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(EventReportPdu, self)._serializeBody(outputStream)
        outputStream.write_uint32(self.eventType)
        outputStream.write_uint32(self.padding1)
        self._serializeDatumTail(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(EventReportPdu, self)._parseBody(inputStream)
        self.eventType = rich_or_int(73, inputStream.read_uint32())
        self.padding1 = inputStream.read_uint32()
        self._parseDatumTail(inputStream)


@dataclass(slots=True)
class CommentPdu(_DatumListsMixin, SimulationManagementFamilyPdu):
    """Section 7.5.13 Comment PDU

    Used to enter arbitrary messages (character strings, for example)
    via variable datums. The fixed datum count is not used by this PDU
    (shall be zero); the list is kept so malformed-but-parseable
    datagrams still round-trip byte-exact."""

    pduType: ClassVar[int] = 22  # [UID 4]

    fixedDatumRecords: list[FixedDatum] = field(default_factory=list)
    variableDatumRecords: list[VariableDatum] = field(default_factory=list)

    def _marshalledBodySize(self) -> int:
        return (super(CommentPdu, self)._marshalledBodySize()
                + self._datumTailSize())

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(CommentPdu, self)._serializeBody(outputStream)
        self._serializeDatumTail(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(CommentPdu, self)._parseBody(inputStream)
        self._parseDatumTail(inputStream)
