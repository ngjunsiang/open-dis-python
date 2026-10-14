"""Base classes for all Record types.

Parse-style split (ruled 2026-10-14): mutable records satisfy ``Record``
(repopulating instance ``parse``); frozen records satisfy ``FrozenRecord``
(``parse`` is a classmethod returning a new instance — frozen dataclasses
cannot be repopulated in place, and re-parsing into a shared instance is
the PR #49 corruption pattern). ``Serializable`` is the narrow
serialize-only type both styles satisfy. Note ``runtime_checkable``
conformance cannot distinguish the two parse styles at runtime (both
provide a ``parse`` attribute) — static checkers can.
"""

__all__ = [
    "FrozenRecord",
    "Record",
    "Serializable",
    "StandardVariableRecord",
    "VariableRecord",
]

from abc import abstractmethod
from typing import Any, Protocol, TypeGuard, runtime_checkable

from opendis.stream import DataInputStream, DataOutputStream
from opendis.types import enum32


@runtime_checkable
class Serializable(Protocol):
    """Records that can size and serialize themselves, regardless of how
    they parse (the narrow type for middleware that only writes PDUs)."""

    @abstractmethod
    def marshalledSize(self) -> int:
        """Return the size (in bytes) of the record when serialized."""

    @abstractmethod
    def serialize(self, outputStream: DataOutputStream) -> None:
        """Serialize the record to the output stream."""


@runtime_checkable
class Record(Serializable, Protocol):
    """Base class for all Record types with fixed sizes; ``parse``
    repopulates an existing instance (mutable records)."""

    @abstractmethod
    def parse(self, inputStream: DataInputStream) -> None:
        """Parse the record from the input stream."""


@runtime_checkable
class FrozenRecord(Serializable, Protocol):
    """Base class for frozen record types; ``parse`` is a classmethod
    that constructs and returns a new instance."""

    @classmethod
    @abstractmethod
    def parse(cls, inputStream: DataInputStream) -> "FrozenRecord":
        """Construct a new record from the input stream."""


@runtime_checkable
class VariableRecord(Serializable, Protocol):
    """Base class for all Record types with variable sizes."""

    @staticmethod
    def is_positive_int(value: Any) -> TypeGuard[int]:
        """Check if a value is a positive integer."""
        return isinstance(value, int) and value >= 0

    @abstractmethod
    def parse(self,
              inputStream: DataInputStream,
              bytelength: int | None = None) -> None:
        """Parse the record from the input stream.

        If bytelength is provided, it indicates the expected length of the record. Some records may require this information to parse correctly.
        """
        if bytelength is not None and not self.is_positive_int(bytelength):
            raise ValueError(
                f"bytelength must be a non-negative integer, got {bytelength!r}"
            )
        # TODO: Implement padding handling


class StandardVariableRecord(VariableRecord):
    """6.2.83 Standard Variable (SV) Record

    This base class defines the interface for DIS records with variable sizes.
    First SV record of a Standard Variable Specification record shall start on
    a 64-bit boundary.
    Padding shall be explicitly included in each record as necessary to make
    the record length a multiple of 8 octets (64 bits) so that the following
    record is automatically aligned. The record length requirement may be
    achieved by placing padding fields anywhere in the SV record as deemed appropriate, not necessarily at the end of the record.
    """
    recordType: enum32  # [UID 66]

    @staticmethod
    def is_positive_int(value: Any) -> TypeGuard[int]:
        """Check if a value is a positive integer."""
        return isinstance(value, int) and value >= 0

    @property
    def recordLength(self) -> int:
        return self.marshalledSize()

    @abstractmethod
    def serialize(self, outputStream: DataOutputStream) -> None:
        """Serialize the record to the output stream.

        The record header (recordType u32 + recordLength u16, see 6.2.83)
        is written by each subclass before its own fields.
        """

    @abstractmethod
    def parse(self,  # pyright: ignore [reportIncompatibleMethodOverride]
              inputStream: DataInputStream,
              bytelength: int) -> None:
        """Parse the record from the input stream.

        If bytelength is provided, it indicates the expected length of the record. Some records may require this information to parse correctly.
        Assume that recordType and recordLength have already been read from the
        stream.
        recordLength will usually be passed to this method to assist in parsing.
        """
        # Validate bytelength
        super().parse(inputStream, bytelength)
        if not bytelength % 8 == 0:
            raise ValueError(
                f"bytelength must be a multiple of 8, got {bytelength!r}"
            )
        # TODO: Implement padding handling
