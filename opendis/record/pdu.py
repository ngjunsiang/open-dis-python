"""PDU layer shared types: composed header, Pdu base, UnrecognizedPdu.

Design: docs/design/dis7-representation.md §3.1 (composition over
inheritance), §3.2 (UnrecognizedPdu), §3.7 (timestamp/length semantics).

Wire order of the 12-byte PDU Header (IEEE 1278.1-2012 §6.2.66 Table 98,
big-endian): Protocol Version, Exercise ID, PDU Type, Protocol Family,
Timestamp (u32), **Length (u16), PDU Status (u8), Padding (u8)** — the
length field precedes the status/padding pair. (The DIS 6 16-bit trailing
padding was split into status + padding; the length stayed at offset 8.)
"""

import io
import logging
import struct
from dataclasses import dataclass, field
from typing import ClassVar

from opendis.stream import DataInputStream, DataOutputStream
from opendis.timestamp import Timestamp
from opendis.types import enum8, uint8, uint16, uint32

__all__ = ["Pdu", "PduHeader", "UnrecognizedPdu"]

_logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PduHeader:
    """Section 6.2.66 PDU Header record

    The header is 12 contiguous bytes packed by one precompiled
    ``struct.Struct`` call instead of eight sequential stream reads. The
    padding byte and the length are not instance state: the pad belongs to
    the packer and the length is derived from ``marshalledSize()``. The
    wire length seen at parse is kept (underscored) as evidence for
    header-vs-body validation.

    # generator: _wireLength is parse evidence, not state; serialize takes
    # the PDU length as an argument because only the whole PDU knows it.
    """

    # (version, exercise, type, family, timestamp, length, status, pad)
    _STRUCT: ClassVar = struct.Struct(">BBBBIHBB")

    protocolVersion: enum8 = 7  # [UID 3] IEEE 1278.1-2012
    exerciseID: uint8 = 0
    pduType: enum8 = 0  # [UID 4]
    protocolFamily: enum8 = 0  # [UID 5]
    timestamp: Timestamp = field(default_factory=Timestamp.now)
    pduStatus: uint8 = 0  # §6.2.67; Live Entity headers use subprotocolNumber

    _wireLength: int = field(default=0, init=False, repr=False)
    # Padding ruling: explicit attribute, out of __init__ (zero by default,
    # holds the wire value after parse so odd pads round-trip byte-exact).
    padding: uint8 = field(init=False, default=0)

    def marshalledSize(self) -> int:
        return 12

    def serialize(self, outputStream: DataOutputStream, length: int) -> None:
        outputStream.write_bytes(
            self._STRUCT.pack(self.protocolVersion, self.exerciseID,
                              self.pduType, self.protocolFamily,
                              self.timestamp.raw, length, self.pduStatus,
                              self.padding))

    @classmethod
    def parse(cls, inputStream: DataInputStream) -> "PduHeader":
        ver, ex, typ, fam, ts, length, status, pad = \
            cls._STRUCT.unpack(inputStream.read_bytes(12))
        header = cls(ver, ex, typ, fam, Timestamp(ts), status)
        header._wireLength = length
        header.padding = pad
        return header


@dataclass(slots=True)
class Pdu:
    """Base class for type identity, dispatch, and the composed header.

    ``pduType``, ``protocolFamily`` and ``protocolVersion`` are class-level
    constants on each concrete PDU (PR #51 convention); the header carries
    the wire evidence, which can legitimately differ (e.g. a DIS 6
    datagram parsed into DIS 7 classes re-serializes byte-exact). The
    delegating properties below keep ``pdu.exerciseID`` and friends
    indistinguishable from flat attributes at the call site.
    """

    header: PduHeader = field(default_factory=PduHeader)

    protocolVersion: ClassVar[int] = 7  # [UID 3]
    pduType: ClassVar[int] = 0  # [UID 4]
    protocolFamily: ClassVar[int] = 0  # [UID 5]

    # generator: a default-constructed header adopts the class identity
    # (pduType 0 is not a valid PDU type, so it is a safe "unset" marker);
    # a parsed header keeps the wire evidence instead.
    def __post_init__(self) -> None:
        if self.header.pduType == 0:
            self.header.pduType = self.pduType
            self.header.protocolFamily = self.protocolFamily
            self.header.protocolVersion = self.protocolVersion

    @property
    def exerciseID(self) -> uint8:
        return self.header.exerciseID

    @exerciseID.setter
    def exerciseID(self, value: uint8) -> None:
        self.header.exerciseID = value

    @property
    def timestamp(self) -> Timestamp:
        return self.header.timestamp

    @timestamp.setter
    def timestamp(self, value: Timestamp) -> None:
        self.header.timestamp = value

    @property
    def pduStatus(self) -> uint8:
        return self.header.pduStatus

    @pduStatus.setter
    def pduStatus(self, value: uint8) -> None:
        self.header.pduStatus = value

    @property
    def length(self) -> int:
        """Length in bytes of the PDU including the header — always derived
        (leif81's ruling on #11), never stored as user-settable state."""
        return self.marshalledSize()

    def marshalledSize(self) -> int:
        return 12 + self._marshalledBodySize()

    def serialize(self, outputStream: DataOutputStream) -> None:
        # Length computed first so the header can be written in one struct
        # call even on non-seekable streams.
        self.header.serialize(outputStream, self.marshalledSize())
        self._serializeBody(outputStream)

    def parse(self, inputStream: DataInputStream) -> None:
        self.header = PduHeader.parse(inputStream)
        if self.header.pduType != self.pduType:
            _logger.warning(
                "%s parsed a datagram whose pduType is %s",
                type(self).__name__, self.header.pduType)
        self._parseBody(inputStream)
        # Evidence-only check, after the body is populated.
        if self.header._wireLength != self.marshalledSize():
            _logger.debug(
                "%s wire length %s != computed %s",
                type(self).__name__,
                self.header._wireLength, self.marshalledSize())

    def to_bytes(self) -> bytes:
        """Serialize the PDU to bytes."""
        buffer = io.BytesIO()
        self.serialize(DataOutputStream(buffer))
        return buffer.getvalue()

    @classmethod
    def from_bytes(cls, data: bytes) -> "Pdu":
        """Parse a datagram into the right PDU class via the factory."""
        from opendis.record.factory import createPdu
        return createPdu(data)

    # -- concrete classes implement these three -------------------------

    def _marshalledBodySize(self) -> int:
        raise NotImplementedError

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        raise NotImplementedError

    def _parseBody(self, inputStream: DataInputStream) -> None:
        raise NotImplementedError


class UnrecognizedPdu(Pdu):
    """A datagram whose pduType has no decoder (design §3.2).

    Holds the fully parsed header (best effort — a newer protocol version
    may lay the header out differently) plus the raw payload, and
    re-serializes byte-exact by replaying the original header bytes, so
    forwarders and loggers are lossless.

    # generator: keeping the raw header bytes (not just parsed fields) is
    # what guarantees byte-exact re-serialization for unknown versions.
    """

    __slots__ = ("rawHeader", "rawPayload")

    def __init__(self, rawHeader: bytes = b"", rawPayload: bytes = b"") -> None:
        self.rawHeader = rawHeader
        self.rawPayload = rawPayload
        self.header = PduHeader()
        if len(rawHeader) >= 12:
            try:
                self.header = PduHeader.parse(
                    DataInputStream(io.BytesIO(rawHeader)))
            except struct.error:
                pass  # keep the zero header; the raw bytes are the truth

    def marshalledSize(self) -> int:
        return len(self.rawHeader) + len(self.rawPayload)

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_bytes(self.rawHeader)
        outputStream.write_bytes(self.rawPayload)

    def _marshalledBodySize(self) -> int:
        return len(self.rawPayload)

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        raise NotImplementedError("UnrecognizedPdu.serialize writes raw bytes")

    def _parseBody(self, inputStream: DataInputStream) -> None:
        raise NotImplementedError("UnrecognizedPdu is built by the factory")

    def __repr__(self) -> str:
        return (f"UnrecognizedPdu(pduType={self.header.pduType}, "
                f"protocolVersion={self.header.protocolVersion}, "
                f"exerciseID={self.header.exerciseID}, "
                f"length={len(self.rawHeader) + len(self.rawPayload)}, "
                f"rawPayload={self.rawPayload!r})")
