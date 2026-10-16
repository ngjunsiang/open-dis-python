"""Simulation Management family (IEEE 1278.1-2012 §7.5) — datum showcase.

Wire ground truth: submodules/open-dis-spec-xml/xml/SimulationManagementFamilyPdus.xml.
DataPdu with FixedDatum records and VariableDatum records whose payloads
are ``bytes`` (never per-byte lists), 64-bit padding computed by the
packer, and a typed uid-66 decoder path through the existing
StandardVariableRecord registry (opendis/record/__init__.py).

Python-side deltas from the XML (sample-review rulings): the base's
originator/receiver fields are EntityIdentifier-shaped
``originatingEntityID``/``receivingEntityID`` (the XML's
SimulationIdentifier classRef is the same 6-byte wire shape, §6.2.81);
Data Query carries datum-ID lists (u32 each, §7.5.9), not FixedDatum
records; datum list field names are fixedDatumRecords/variableDatumRecords
uniformly (the XML mixes fixedDatums/variableDatums spellings).
"""

import io
from dataclasses import dataclass, field
from typing import ClassVar

from opendis.bitfields import StopFreezeFrozenBehavior
from opendis.enum_registry import rich_or_int
from opendis.record.base import StandardVariableRecord
from opendis.record.common import ClockTime, EntityIdentifier
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


def _padTo64(byteCount: int) -> int:
    """Pad bytes needed to bring a datagram to a 64-bit boundary."""
    return (8 - byteCount % 8) % 8


@dataclass(slots=True)
class FixedDatum:
    """§6.2.37 Fixed Datum record

    Fixed Datum Record.
    """

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "fixedDatumID": 66,
    }

    fixedDatumID: enum32 = 0  # [UID 66]
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
        """Construct a new record from the stream (list-parse helper; the
        mutating ``parse`` above satisfies the Record protocol)."""
        item = cls()
        item.parse(inputStream)
        return item


def _paddedDatumSize(byteCount: int) -> int:
    """Datum fields are padded at the end to a multiple of 64 bits."""
    remainder = byteCount % 8
    if remainder:
        byteCount += 8 - remainder
    return byteCount


@dataclass(slots=True)
class VariableDatum:
    """§6.2.93 Variable Datum record

    The variable datum type, the datum length, and the value for that
    variable datum type.

    ``variableData`` is the raw payload as ``bytes``;
    ``variableDatumLength`` (in bits) is derived at serialize time and the
    64-bit padding is computed by the packer — neither is user-settable
    state.

    # generator: payload carries the complete serialized record when the
    # datum ID is a uid-66 record type, so a known record re-serializes
    # standalone and an unknown one stays raw bytes (forward compat).
    """

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "variableDatumID": 66,
    }

    variableDatumID: enum32 = 0  # [UID 66]
    variableData: bytes = b""

    @property
    def variableDatumLength(self) -> uint32:
        """Length, IN BITS, of the variable datum."""
        return len(self.variableData) * 8

    def marshalledSize(self):
        return 8 + _paddedDatumSize(len(self.variableData))

    def serialize(self, outputStream: DataOutputStream):
        outputStream.write_uint32(self.variableDatumID)
        outputStream.write_uint32(self.variableDatumLength)
        outputStream.write_bytes(self.variableData)
        padding = _paddedDatumSize(len(self.variableData)) - len(self.variableData)
        if padding:
            outputStream.write_bytes(b"\x00" * padding)

    def parse(self, inputStream: DataInputStream):
        self.variableDatumID = rich_or_int(66, inputStream.read_uint32())
        variableDatumLength = inputStream.read_uint32()
        self.variableData = inputStream.read_bytes(variableDatumLength // 8)
        padding = _paddedDatumSize(len(self.variableData)) - len(self.variableData)
        if padding:
            inputStream.read_bytes(padding)

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

    @classmethod
    def parseFrom(cls, inputStream: DataInputStream) -> "VariableDatum":
        """Construct a new record from the stream (list-parse helper; the
        mutating ``parse`` above satisfies the Record protocol)."""
        item = cls()
        item.parse(inputStream)
        return item


@dataclass(slots=True)
class SimulationManagementFamilyPdu(Pdu):
    """§7.5 Simulation Management family PDU

    First part of a simulation management (SIMAN) PDU and SIMAN-Reliability
    (SIMAN-R) PDU.

    Not a thin marker: carries the §6.2.82 Simulation Management PDU header
    fields (originating and receiving entity IDs, EntityIdentifier-shaped
    per the sample-review ruling).
    """

    protocolFamily: ClassVar[int] = 5  # [UID 5] Simulation Management

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
class DataPdu(SimulationManagementFamilyPdu):
    """§7.5.11 Data PDU

    Information issued in response to a Data Query PDU or Set Data PDU.
    §5.6.5.11.
    """

    pduType: ClassVar[int] = 20  # [UID 4]

    requestID: uint32 = 0
    fixedDatumRecords: list[FixedDatum] = field(default_factory=list)
    variableDatumRecords: list[VariableDatum] = field(default_factory=list)
    # Padding ruling: explicit attribute, out of __init__ (zero by default,
    # holds the wire value after parse so odd pads round-trip byte-exact).
    padding1: uint32 = field(init=False, default=0)

    @property
    def numberOfFixedDatumRecords(self) -> uint32:
        """Number of fixed datum records."""
        return len(self.fixedDatumRecords)

    @property
    def numberOfVariableDatumRecords(self) -> uint32:
        """Number of variable datum records, handled automatically by marshaller at
        run time (and not modifiable by end-user programmers).
        """
        return len(self.variableDatumRecords)

    def _marshalledBodySize(self) -> int:
        return (
            super(DataPdu, self)._marshalledBodySize()
            + 4
            + 4
            + 4
            + 4
            + sum(item.marshalledSize() for item in self.fixedDatumRecords)
            + sum(item.marshalledSize() for item in self.variableDatumRecords)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(DataPdu, self)._serializeBody(outputStream)
        outputStream.write_uint32(self.requestID)
        outputStream.write_uint32(self.padding1)
        outputStream.write_uint32(self.numberOfFixedDatumRecords)
        outputStream.write_uint32(self.numberOfVariableDatumRecords)
        for item in self.fixedDatumRecords:
            item.serialize(outputStream)
        for item in self.variableDatumRecords:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(DataPdu, self)._parseBody(inputStream)
        self.requestID = inputStream.read_uint32()
        self.padding1 = inputStream.read_uint32()
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


@dataclass(slots=True)
class CreateEntityPdu(SimulationManagementFamilyPdu):
    """§7.5.2 Create Entity PDU

    The creation of a new entity shall be communicated using a Create Entity
    PDU. See §5.6.5.2.
    """

    pduType: ClassVar[int] = 11  # [UID 4]

    requestID: uint32 = 0

    def _marshalledBodySize(self) -> int:
        return super(CreateEntityPdu, self)._marshalledBodySize() + 4

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(CreateEntityPdu, self)._serializeBody(outputStream)
        outputStream.write_uint32(self.requestID)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(CreateEntityPdu, self)._parseBody(inputStream)
        self.requestID = inputStream.read_uint32()


@dataclass(slots=True)
class RemoveEntityPdu(SimulationManagementFamilyPdu):
    """§7.5.3 Remove Entity PDU

    The removal of an entity from an exercise shall be communicated with a
    Remove Entity PDU. See §5.6.5.3.
    """

    pduType: ClassVar[int] = 12  # [UID 4]

    requestID: uint32 = 0

    def _marshalledBodySize(self) -> int:
        return super(RemoveEntityPdu, self)._marshalledBodySize() + 4

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(RemoveEntityPdu, self)._serializeBody(outputStream)
        outputStream.write_uint32(self.requestID)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(RemoveEntityPdu, self)._parseBody(inputStream)
        self.requestID = inputStream.read_uint32()


@dataclass(slots=True)
class StartResumePdu(SimulationManagementFamilyPdu):
    """§7.5.4 Start/Resume PDU

    The Start/Resume of an entity/exercise shall be communicated using a
    Start/Resume PDU. See §5.6.5.4.
    """

    pduType: ClassVar[int] = 13  # [UID 4]

    realWorldTime: ClockTime = field(default_factory=ClockTime)
    simulationTime: ClockTime = field(default_factory=ClockTime)
    requestID: uint32 = 0

    def _marshalledBodySize(self) -> int:
        return (
            super(StartResumePdu, self)._marshalledBodySize()
            + self.realWorldTime.marshalledSize()
            + self.simulationTime.marshalledSize()
            + 4
        )

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
    """§7.5.5 Stop/Freeze PDU

    The stopping or freezing of an entity/exercise shall be communicated
    using a Stop/Freeze PDU. See §5.6.5.5.
    """

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
        return (
            super(StopFreezePdu, self)._marshalledBodySize()
            + self.realWorldTime.marshalledSize()
            + 1
            + 1
            + 2
            + 4
        )

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
        self.frozenBehavior = StopFreezeFrozenBehavior(inputStream.read_uint8())
        self.padding1 = inputStream.read_uint16()
        self.requestID = inputStream.read_uint32()


@dataclass(slots=True)
class AcknowledgePdu(SimulationManagementFamilyPdu):
    """§7.5.6 Acknowledge PDU

    Acknowledges the receipt of a Start/Resume PDU, Stop/Freeze PDU, Create
    Entity PDU, or Remove Entity PDU. See §5.6.5.6.
    """

    pduType: ClassVar[int] = 15  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "acknowledgeFlag": 69,
        "responseFlag": 70,
    }

    acknowledgeFlag: enum16 = 0  # [UID 69]
    responseFlag: enum16 = 0  # [UID 70]
    requestID: uint32 = 0

    def _marshalledBodySize(self) -> int:
        return super(AcknowledgePdu, self)._marshalledBodySize() + 2 + 2 + 4

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
class ActionRequestPdu(SimulationManagementFamilyPdu):
    """§7.5.7 Action Request PDU

    A request from a Simulation Manager (SM) to a managed entity to perform
    a specified action. See §5.6.5.7.
    """

    pduType: ClassVar[int] = 16  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "actionID": 71,
    }

    requestID: uint32 = 0
    actionID: enum32 = 0  # [UID 71]
    fixedDatumRecords: list[FixedDatum] = field(default_factory=list)
    variableDatumRecords: list[VariableDatum] = field(default_factory=list)

    @property
    def numberOfFixedDatumRecords(self) -> uint32:
        """Number of fixed datum records."""
        return len(self.fixedDatumRecords)

    @property
    def numberOfVariableDatumRecords(self) -> uint32:
        """Number of variable datum records, handled automatically by marshaller at
        run time (and not modifiable by end-user programmers).
        """
        return len(self.variableDatumRecords)

    def _marshalledBodySize(self) -> int:
        return (
            super(ActionRequestPdu, self)._marshalledBodySize()
            + 4
            + 4
            + 4
            + 4
            + sum(item.marshalledSize() for item in self.fixedDatumRecords)
            + sum(item.marshalledSize() for item in self.variableDatumRecords)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(ActionRequestPdu, self)._serializeBody(outputStream)
        outputStream.write_uint32(self.requestID)
        outputStream.write_uint32(self.actionID)
        outputStream.write_uint32(self.numberOfFixedDatumRecords)
        outputStream.write_uint32(self.numberOfVariableDatumRecords)
        for item in self.fixedDatumRecords:
            item.serialize(outputStream)
        for item in self.variableDatumRecords:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(ActionRequestPdu, self)._parseBody(inputStream)
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


@dataclass(slots=True)
class ActionResponsePdu(SimulationManagementFamilyPdu):
    """§7.5.8 Action Response PDU

    When an entity receives an Action Request PDU, that entity shall
    acknowledge the receipt of the Action Request PDU with an Action
    Response PDU. See §5.6.5.8.
    """

    pduType: ClassVar[int] = 17  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "requestStatus": 72,
    }

    requestID: uint32 = 0
    requestStatus: enum32 = 0  # [UID 72]
    fixedDatumRecords: list[FixedDatum] = field(default_factory=list)
    variableDatumRecords: list[VariableDatum] = field(default_factory=list)

    @property
    def numberOfFixedDatumRecords(self) -> uint32:
        """Number of fixed datum records."""
        return len(self.fixedDatumRecords)

    @property
    def numberOfVariableDatumRecords(self) -> uint32:
        """Number of variable datum records, handled automatically by marshaller at
        run time (and not modifiable by end-user programmers).
        """
        return len(self.variableDatumRecords)

    def _marshalledBodySize(self) -> int:
        return (
            super(ActionResponsePdu, self)._marshalledBodySize()
            + 4
            + 4
            + 4
            + 4
            + sum(item.marshalledSize() for item in self.fixedDatumRecords)
            + sum(item.marshalledSize() for item in self.variableDatumRecords)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(ActionResponsePdu, self)._serializeBody(outputStream)
        outputStream.write_uint32(self.requestID)
        outputStream.write_uint32(self.requestStatus)
        outputStream.write_uint32(self.numberOfFixedDatumRecords)
        outputStream.write_uint32(self.numberOfVariableDatumRecords)
        for item in self.fixedDatumRecords:
            item.serialize(outputStream)
        for item in self.variableDatumRecords:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(ActionResponsePdu, self)._parseBody(inputStream)
        self.requestID = inputStream.read_uint32()
        self.requestStatus = rich_or_int(72, inputStream.read_uint32())
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


@dataclass(slots=True)
class DataQueryPdu(SimulationManagementFamilyPdu):
    """§7.5.9 Data Query PDU

    A request for data from an entity shall be communicated by issuing a
    Data Query PDU. See §5.6.5.9.
    """

    pduType: ClassVar[int] = 18  # [UID 4]

    requestID: uint32 = 0
    timeInterval: uint32 = 0
    fixedDatumIDs: list[enum32] = field(default_factory=list)
    variableDatumIDs: list[enum32] = field(default_factory=list)

    @property
    def numberOfFixedDatumIDs(self) -> uint32:
        """Number of fixed datum records."""
        return len(self.fixedDatumIDs)

    @property
    def numberOfVariableDatumIDs(self) -> uint32:
        """Number of variable datum records, handled automatically by marshaller at
        run time (and not modifiable by end-user programmers).
        """
        return len(self.variableDatumIDs)

    def _marshalledBodySize(self) -> int:
        return (
            super(DataQueryPdu, self)._marshalledBodySize()
            + 4
            + 4
            + 4
            + 4
            + 4 * len(self.fixedDatumIDs)
            + 4 * len(self.variableDatumIDs)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(DataQueryPdu, self)._serializeBody(outputStream)
        outputStream.write_uint32(self.requestID)
        outputStream.write_uint32(self.timeInterval)
        outputStream.write_uint32(self.numberOfFixedDatumIDs)
        outputStream.write_uint32(self.numberOfVariableDatumIDs)
        for item in self.fixedDatumIDs:
            outputStream.write_uint32(item)
        for item in self.variableDatumIDs:
            outputStream.write_uint32(item)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(DataQueryPdu, self)._parseBody(inputStream)
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


@dataclass(slots=True)
class SetDataPdu(SimulationManagementFamilyPdu):
    """§7.5.10 Set Data PDU

    Initializing or changing internal state information shall be
    communicated using a Set Data PDU. See §5.6.5.10.
    """

    pduType: ClassVar[int] = 19  # [UID 4]

    requestID: uint32 = 0
    fixedDatumRecords: list[FixedDatum] = field(default_factory=list)
    variableDatumRecords: list[VariableDatum] = field(default_factory=list)
    padding1: uint32 = field(init=False, default=0)

    @property
    def numberOfFixedDatumRecords(self) -> uint32:
        """Number of fixed datum records."""
        return len(self.fixedDatumRecords)

    @property
    def numberOfVariableDatumRecords(self) -> uint32:
        """Number of variable datum records, handled automatically by marshaller at
        run time (and not modifiable by end-user programmers).
        """
        return len(self.variableDatumRecords)

    def _marshalledBodySize(self) -> int:
        return (
            super(SetDataPdu, self)._marshalledBodySize()
            + 4
            + 4
            + 4
            + 4
            + sum(item.marshalledSize() for item in self.fixedDatumRecords)
            + sum(item.marshalledSize() for item in self.variableDatumRecords)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(SetDataPdu, self)._serializeBody(outputStream)
        outputStream.write_uint32(self.requestID)
        outputStream.write_uint32(self.padding1)
        outputStream.write_uint32(self.numberOfFixedDatumRecords)
        outputStream.write_uint32(self.numberOfVariableDatumRecords)
        for item in self.fixedDatumRecords:
            item.serialize(outputStream)
        for item in self.variableDatumRecords:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(SetDataPdu, self)._parseBody(inputStream)
        self.requestID = inputStream.read_uint32()
        self.padding1 = inputStream.read_uint32()
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


@dataclass(slots=True)
class EventReportPdu(SimulationManagementFamilyPdu):
    """§7.5.12 Event Report PDU

    A managed entity shall report the occurrence of a significant event to
    the simulation manager (SM) using an Event Report PDU. See §5.6.5.12.
    """

    pduType: ClassVar[int] = 21  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "eventType": 73,
    }

    eventType: enum32 = 0  # [UID 73]
    fixedDatumRecords: list[FixedDatum] = field(default_factory=list)
    variableDatumRecords: list[VariableDatum] = field(default_factory=list)
    padding1: uint32 = field(init=False, default=0)

    @property
    def numberOfFixedDatumRecords(self) -> uint32:
        """Number of fixed datum records."""
        return len(self.fixedDatumRecords)

    @property
    def numberOfVariableDatumRecords(self) -> uint32:
        """Number of variable datum records, handled automatically by marshaller at
        run time (and not modifiable by end-user programmers).
        """
        return len(self.variableDatumRecords)

    def _marshalledBodySize(self) -> int:
        return (
            super(EventReportPdu, self)._marshalledBodySize()
            + 4
            + 4
            + 4
            + 4
            + sum(item.marshalledSize() for item in self.fixedDatumRecords)
            + sum(item.marshalledSize() for item in self.variableDatumRecords)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(EventReportPdu, self)._serializeBody(outputStream)
        outputStream.write_uint32(self.eventType)
        outputStream.write_uint32(self.padding1)
        outputStream.write_uint32(self.numberOfFixedDatumRecords)
        outputStream.write_uint32(self.numberOfVariableDatumRecords)
        for item in self.fixedDatumRecords:
            item.serialize(outputStream)
        for item in self.variableDatumRecords:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(EventReportPdu, self)._parseBody(inputStream)
        self.eventType = rich_or_int(73, inputStream.read_uint32())
        self.padding1 = inputStream.read_uint32()
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


@dataclass(slots=True)
class CommentPdu(SimulationManagementFamilyPdu):
    """§7.5.13 Comment PDU

    Used to enter arbitrary messages (character strings, for example). See
    §5.6.5.13.

    The fixed datum count is not used by this PDU (shall be zero); the list
    is kept so malformed-but-parseable datagrams still round-trip byte-
    exact.
    """

    pduType: ClassVar[int] = 22  # [UID 4]

    variableDatumRecords: list[VariableDatum] = field(default_factory=list)
    fixedDatumRecords: list[FixedDatum] = field(default_factory=list)

    @property
    def numberOfFixedDatumRecords(self) -> uint32:
        """Number of fixed datum records, not used in this Pdu."""
        return len(self.fixedDatumRecords)

    @property
    def numberOfVariableDatumRecords(self) -> uint32:
        """Number of variable datum records, handled automatically by marshaller at
        run time (and not modifiable by end-user programmers).
        """
        return len(self.variableDatumRecords)

    def _marshalledBodySize(self) -> int:
        return (
            super(CommentPdu, self)._marshalledBodySize()
            + 4
            + 4
            + sum(item.marshalledSize() for item in self.variableDatumRecords)
            + sum(item.marshalledSize() for item in self.fixedDatumRecords)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(CommentPdu, self)._serializeBody(outputStream)
        outputStream.write_uint32(self.numberOfFixedDatumRecords)
        outputStream.write_uint32(self.numberOfVariableDatumRecords)
        for item in self.variableDatumRecords:
            item.serialize(outputStream)
        for item in self.fixedDatumRecords:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        super(CommentPdu, self)._parseBody(inputStream)
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
