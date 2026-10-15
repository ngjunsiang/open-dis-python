"""Logistics family (IEEE 1278.1-2012 §7.4) — target-state PDUs.

Wire ground truth: submodules/open-dis-spec-xml/xml/LogisticsFamilyPdus.xml.
Service Request, Resupply Offer/Received/Cancel, Repair Complete/Response,
and the §6.2.86 Supply Quantity record.
"""

from dataclasses import dataclass, field
from typing import ClassVar

from opendis.enum_registry import rich_or_int
from opendis.record.common import EntityIdentifier, EntityType
from opendis.record.pdu import Pdu
from opendis.stream import DataInputStream, DataOutputStream
from opendis.types import enum8, enum16, float32, uint8, uint16

__all__ = [
    "LogisticsFamilyPdu",
    "RepairCompletePdu",
    "RepairResponsePdu",
    "ResupplyCancelPdu",
    "ResupplyOfferPdu",
    "ResupplyReceivedPdu",
    "ServiceRequestPdu",
    "SupplyQuantity",
]


@dataclass(slots=True)
class LogisticsFamilyPdu(Pdu):
    """§7.4 Logistics family PDU

    Abstract superclass for logistics PDUs.

    Thin family marker — per-class identity lives in the
    ``pduType``/``protocolFamily`` ClassVars; family metadata for middleware
    lives in ``PDU_FAMILIES`` (opendis.record.factory).
    """

    protocolFamily: ClassVar[int] = 3  # [UID 5] Logistics


@dataclass(slots=True)
class SupplyQuantity:
    """§6.2.86 Supply Quantity record

    A supply, and the amount of that supply.
    """

    supplyType: EntityType = field(default_factory=EntityType)
    quantity: float32 = 0.0

    def marshalledSize(self) -> int:
        return self.supplyType.marshalledSize() + 4

    def serialize(self, outputStream: DataOutputStream) -> None:
        self.supplyType.serialize(outputStream)
        outputStream.write_float32(self.quantity)

    def parse(self, inputStream: DataInputStream) -> None:
        self.supplyType = EntityType.parse(inputStream)
        self.quantity = inputStream.read_float32()

    @classmethod
    def parseFrom(cls, inputStream: DataInputStream) -> "SupplyQuantity":
        """Construct a new record from the stream (list-parse helper; the
        mutating ``parse`` above satisfies the Record protocol)."""
        item = cls()
        item.parse(inputStream)
        return item


@dataclass(slots=True)
class ServiceRequestPdu(LogisticsFamilyPdu):
    """§7.4.2 Service Request PDU

    Communicate information associated with one entity requesting a service
    from another.
    """

    pduType: ClassVar[int] = 5  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "serviceTypeRequested": 63,
    }

    requestingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    servicingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    serviceTypeRequested: enum8 = 0  # [UID 63]
    supplies: list[SupplyQuantity] = field(default_factory=list)
    # Padding ruling: explicit attribute, out of __init__ (zero by default,
    # holds the wire value after parse so odd pads round-trip byte-exact).
    padding1: uint16 = field(init=False, default=0)

    @property
    def numberOfSupplyTypes(self) -> uint8:
        """How many requested."""
        return len(self.supplies)

    def _marshalledBodySize(self) -> int:
        return (
            self.requestingEntityID.marshalledSize()
            + self.servicingEntityID.marshalledSize()
            + 1
            + 1
            + 2
            + sum(item.marshalledSize() for item in self.supplies)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.requestingEntityID.serialize(outputStream)
        self.servicingEntityID.serialize(outputStream)
        outputStream.write_uint8(self.serviceTypeRequested)
        outputStream.write_uint8(self.numberOfSupplyTypes)
        outputStream.write_uint16(self.padding1)
        for item in self.supplies:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.requestingEntityID = EntityIdentifier.parse(inputStream)
        self.servicingEntityID = EntityIdentifier.parse(inputStream)
        self.serviceTypeRequested = rich_or_int(63, inputStream.read_uint8())
        numberOfSupplyTypes = inputStream.read_uint8()
        self.padding1 = inputStream.read_uint16()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.supplies = [
            SupplyQuantity.parseFrom(inputStream) for _ in range(numberOfSupplyTypes)
        ]


@dataclass(slots=True)
class ResupplyOfferPdu(LogisticsFamilyPdu):
    """§7.4.3 Resupply Offer PDU

    Communicate the offer of supplies by a supplying entity to a receiving
    entity.
    """

    pduType: ClassVar[int] = 6  # [UID 4]

    receivingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    supplyingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    supplies: list[SupplyQuantity] = field(default_factory=list)
    padding1: uint8 = field(init=False, default=0)
    padding2: uint16 = field(init=False, default=0)

    @property
    def numberOfSupplyTypes(self) -> uint8:
        """How many supplies types are being offered."""
        return len(self.supplies)

    def _marshalledBodySize(self) -> int:
        return (
            self.receivingEntityID.marshalledSize()
            + self.supplyingEntityID.marshalledSize()
            + 1
            + 1
            + 2
            + sum(item.marshalledSize() for item in self.supplies)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.receivingEntityID.serialize(outputStream)
        self.supplyingEntityID.serialize(outputStream)
        outputStream.write_uint8(self.numberOfSupplyTypes)
        outputStream.write_uint8(self.padding1)
        outputStream.write_uint16(self.padding2)
        for item in self.supplies:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.receivingEntityID = EntityIdentifier.parse(inputStream)
        self.supplyingEntityID = EntityIdentifier.parse(inputStream)
        numberOfSupplyTypes = inputStream.read_uint8()
        self.padding1 = inputStream.read_uint8()
        self.padding2 = inputStream.read_uint16()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.supplies = [
            SupplyQuantity.parseFrom(inputStream) for _ in range(numberOfSupplyTypes)
        ]


@dataclass(slots=True)
class ResupplyReceivedPdu(LogisticsFamilyPdu):
    """§7.4.4 Resupply Received PDU

    Used to acknowledge the receipt of supplies by the receiving entity.
    """

    pduType: ClassVar[int] = 7  # [UID 4]

    receivingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    supplyingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    supplies: list[SupplyQuantity] = field(default_factory=list)
    padding1: uint8 = field(init=False, default=0)
    padding2: uint16 = field(init=False, default=0)

    @property
    def numberOfSupplyTypes(self) -> uint8:
        """How many supplies are taken by receiving entity."""
        return len(self.supplies)

    def _marshalledBodySize(self) -> int:
        return (
            self.receivingEntityID.marshalledSize()
            + self.supplyingEntityID.marshalledSize()
            + 1
            + 1
            + 2
            + sum(item.marshalledSize() for item in self.supplies)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.receivingEntityID.serialize(outputStream)
        self.supplyingEntityID.serialize(outputStream)
        outputStream.write_uint8(self.numberOfSupplyTypes)
        outputStream.write_uint8(self.padding1)
        outputStream.write_uint16(self.padding2)
        for item in self.supplies:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.receivingEntityID = EntityIdentifier.parse(inputStream)
        self.supplyingEntityID = EntityIdentifier.parse(inputStream)
        numberOfSupplyTypes = inputStream.read_uint8()
        self.padding1 = inputStream.read_uint8()
        self.padding2 = inputStream.read_uint16()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.supplies = [
            SupplyQuantity.parseFrom(inputStream) for _ in range(numberOfSupplyTypes)
        ]


@dataclass(slots=True)
class ResupplyCancelPdu(LogisticsFamilyPdu):
    """§7.4.5 Resupply Cancel PDU

    Used to communicate the canceling of a resupply service provided through
    logistics support.
    """

    pduType: ClassVar[int] = 8  # [UID 4]

    receivingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    supplyingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)

    def _marshalledBodySize(self) -> int:
        return (
            self.receivingEntityID.marshalledSize()
            + self.supplyingEntityID.marshalledSize()
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.receivingEntityID.serialize(outputStream)
        self.supplyingEntityID.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.receivingEntityID = EntityIdentifier.parse(inputStream)
        self.supplyingEntityID = EntityIdentifier.parse(inputStream)


@dataclass(slots=True)
class RepairCompletePdu(LogisticsFamilyPdu):
    """§7.4.6 Repair Complete PDU

    Used by the repairing entity to communicate the repair that has been
    performed for the entity that requested repair service.
    """

    pduType: ClassVar[int] = 9  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "repair": 64,
    }

    receivingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    repairingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    repair: enum16 = 0  # [UID 64]
    padding4: uint16 = field(init=False, default=0)

    def _marshalledBodySize(self) -> int:
        return (
            self.receivingEntityID.marshalledSize()
            + self.repairingEntityID.marshalledSize()
            + 2
            + 2
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.receivingEntityID.serialize(outputStream)
        self.repairingEntityID.serialize(outputStream)
        outputStream.write_uint16(self.repair)
        outputStream.write_uint16(self.padding4)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.receivingEntityID = EntityIdentifier.parse(inputStream)
        self.repairingEntityID = EntityIdentifier.parse(inputStream)
        self.repair = rich_or_int(64, inputStream.read_uint16())
        self.padding4 = inputStream.read_uint16()


@dataclass(slots=True)
class RepairResponsePdu(LogisticsFamilyPdu):
    """§7.4.7 Repair Response PDU

    used by the receiving entity to acknowledge the receipt of a Repair
    Complete PDU.
    """

    pduType: ClassVar[int] = 10  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "repairResult": 65,
    }

    receivingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    repairingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    repairResult: enum8 = 0  # [UID 65]
    padding1: uint8 = field(init=False, default=0)
    padding2: uint16 = field(init=False, default=0)

    def _marshalledBodySize(self) -> int:
        return (
            self.receivingEntityID.marshalledSize()
            + self.repairingEntityID.marshalledSize()
            + 1
            + 1
            + 2
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.receivingEntityID.serialize(outputStream)
        self.repairingEntityID.serialize(outputStream)
        outputStream.write_uint8(self.repairResult)
        outputStream.write_uint8(self.padding1)
        outputStream.write_uint16(self.padding2)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.receivingEntityID = EntityIdentifier.parse(inputStream)
        self.repairingEntityID = EntityIdentifier.parse(inputStream)
        self.repairResult = rich_or_int(65, inputStream.read_uint8())
        self.padding1 = inputStream.read_uint8()
        self.padding2 = inputStream.read_uint16()
