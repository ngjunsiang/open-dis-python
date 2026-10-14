"""Information Operations family (IEEE 1278.1-2012 §5.13/§7.12)
— target-state PDUs.

Wire ground truth: xml-fixed/InformationOperationsFamilyPdus.xml. IO
Action and IO Report PDUs; the IO records (§6.2.48) use the uid-66
Standard Variable record format, so they ride the registry — known
record types decode, unknown ones stay raw bytes byte-exact.
"""

from dataclasses import dataclass, field
from typing import ClassVar

from opendis.enum_registry import rich_or_int
from opendis.record.common import EntityIdentifier
from opendis.record.pdu import Pdu
from opendis.stream import DataInputStream, DataOutputStream
from opendis.types import enum8, enum16, uint8, uint16, uint32

__all__ = [
    "InformationOperationsActionPdu",
    "InformationOperationsFamilyPdu",
    "InformationOperationsReportPdu",
]


@dataclass(slots=True)
class InformationOperationsFamilyPdu(Pdu):
    """Section 5.13 base for IO PDUs: the PDU header plus the
    originating simulation ID."""

    protocolFamily: ClassVar[int] = 13  # [UID 5]

    originatingSimID: EntityIdentifier = field(default_factory=EntityIdentifier)

    def _marshalledBodySize(self) -> int:
        return self.originatingSimID.marshalledSize()

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.originatingSimID.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.originatingSimID = EntityIdentifier.parse(inputStream)


@dataclass(slots=True)
class InformationOperationsActionPdu(InformationOperationsFamilyPdu):
    """Section 5.13.3 IO Action PDU

    Communicates an IO attack or its effects on one or more target
    entities. Base PDU size is 56 bytes plus IO records."""

    pduType: ClassVar[int] = 70  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "IOWarfareType": 285,
        "IOSimulationSource": 286,
        "IOActionType": 287,
        "IOActionPhase": 288,
    }

    receivingSimID: EntityIdentifier = field(default_factory=EntityIdentifier)
    requestID: uint32 = 0
    IOWarfareType: enum16 = 0  # [UID 285]
    IOSimulationSource: enum16 = 0  # [UID 286]
    IOActionType: enum16 = 0  # [UID 287]
    IOActionPhase: enum16 = 0  # [UID 288]
    ioAttackerID: EntityIdentifier = field(default_factory=EntityIdentifier)
    ioPrimaryTargetID: EntityIdentifier = field(default_factory=EntityIdentifier)
    ioRecords: list = field(default_factory=list)

    padding1: uint32 = field(init=False, default=0)
    padding2: uint16 = field(init=False, default=0)

    @property
    def numberOfIORecords(self) -> uint16:
        return len(self.ioRecords)

    def _marshalledBodySize(self) -> int:
        return (super(InformationOperationsActionPdu,
                      self)._marshalledBodySize()
                + self.receivingSimID.marshalledSize()
                + 4 + 2 + 2 + 2 + 2 + 4
                + self.ioAttackerID.marshalledSize()
                + self.ioPrimaryTargetID.marshalledSize()
                + 2 + 2
                + sum(r.marshalledSize() for r in self.ioRecords))

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(InformationOperationsActionPdu, self)._serializeBody(outputStream)
        self.receivingSimID.serialize(outputStream)
        outputStream.write_uint32(self.requestID)
        outputStream.write_uint16(self.IOWarfareType)
        outputStream.write_uint16(self.IOSimulationSource)
        outputStream.write_uint16(self.IOActionType)
        outputStream.write_uint16(self.IOActionPhase)
        outputStream.write_uint32(self.padding1)
        self.ioAttackerID.serialize(outputStream)
        self.ioPrimaryTargetID.serialize(outputStream)
        outputStream.write_uint16(self.padding2)
        outputStream.write_uint16(self.numberOfIORecords)
        for record in self.ioRecords:
            record.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        from opendis.record import parseStandardVariableRecord
        super(InformationOperationsActionPdu, self)._parseBody(inputStream)
        self.receivingSimID = EntityIdentifier.parse(inputStream)
        self.requestID = inputStream.read_uint32()
        self.IOWarfareType = rich_or_int(285, inputStream.read_uint16())
        self.IOSimulationSource = rich_or_int(286, inputStream.read_uint16())
        self.IOActionType = rich_or_int(287, inputStream.read_uint16())
        self.IOActionPhase = rich_or_int(288, inputStream.read_uint16())
        self.padding1 = inputStream.read_uint32()
        self.ioAttackerID = EntityIdentifier.parse(inputStream)
        self.ioPrimaryTargetID = EntityIdentifier.parse(inputStream)
        self.padding2 = inputStream.read_uint16()
        numberOfIORecords = inputStream.read_uint16()
        self.ioRecords = [
            parseStandardVariableRecord(inputStream)
            for _ in range(numberOfIORecords)
        ]


@dataclass(slots=True)
class InformationOperationsReportPdu(InformationOperationsFamilyPdu):
    """Section 5.13.4 IO Report PDU

    Communicates the effects of an IO attack on one or more target
    entities. Base PDU size is 40 bytes plus IO records."""

    pduType: ClassVar[int] = 71  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "ioSimSource": 286,
        "ioReportType": 289,
    }

    ioSimSource: enum16 = 0  # [UID 286]
    ioReportType: enum8 = 0  # [UID 289]
    ioAttackerID: EntityIdentifier = field(default_factory=EntityIdentifier)
    ioPrimaryTargetID: EntityIdentifier = field(default_factory=EntityIdentifier)
    ioRecords: list = field(default_factory=list)

    padding1: uint8 = field(init=False, default=0)
    padding2: uint16 = field(init=False, default=0)
    padding3: uint16 = field(init=False, default=0)

    @property
    def numberOfIORecords(self) -> uint16:
        return len(self.ioRecords)

    def _marshalledBodySize(self) -> int:
        return (super(InformationOperationsReportPdu,
                      self)._marshalledBodySize()
                + 2 + 1 + 1
                + self.ioAttackerID.marshalledSize()
                + self.ioPrimaryTargetID.marshalledSize()
                + 2 + 2 + 2
                + sum(r.marshalledSize() for r in self.ioRecords))

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        super(InformationOperationsReportPdu, self)._serializeBody(outputStream)
        outputStream.write_uint16(self.ioSimSource)
        outputStream.write_uint8(self.ioReportType)
        outputStream.write_uint8(self.padding1)
        self.ioAttackerID.serialize(outputStream)
        self.ioPrimaryTargetID.serialize(outputStream)
        outputStream.write_uint16(self.padding2)
        outputStream.write_uint16(self.padding3)
        outputStream.write_uint16(self.numberOfIORecords)
        for record in self.ioRecords:
            record.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        from opendis.record import parseStandardVariableRecord
        super(InformationOperationsReportPdu, self)._parseBody(inputStream)
        self.ioSimSource = rich_or_int(286, inputStream.read_uint16())
        self.ioReportType = rich_or_int(289, inputStream.read_uint8())
        self.padding1 = inputStream.read_uint8()
        self.ioAttackerID = EntityIdentifier.parse(inputStream)
        self.ioPrimaryTargetID = EntityIdentifier.parse(inputStream)
        self.padding2 = inputStream.read_uint16()
        self.padding3 = inputStream.read_uint16()
        numberOfIORecords = inputStream.read_uint16()
        self.ioRecords = [
            parseStandardVariableRecord(inputStream)
            for _ in range(numberOfIORecords)
        ]
