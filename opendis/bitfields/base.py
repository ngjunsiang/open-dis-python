"""Base mechanics for bitfield view classes.

Design: docs/design/dis7-representation.md §3.5. The wire field on the
PDU/record stays a plain ``uint32``/``uint8``; generated view classes sit
on top. Each view holds one ``_value`` int masked to the field width, so
unknown/reserved bits survive round-trips; every accessor touches only its
own mask. Single-bit fields are ``bool`` properties, multi-bit sub-fields
resolve through :func:`opendis.enum_registry.rich_or_int` so they are
plain ``int`` unless an enum provider is active.
"""

from typing import ClassVar

from opendis.enum_registry import rich_or_int

__all__ = ["BitfieldView"]


class BitfieldView:
    """Shared mechanics for stamped bitfield views (one class per layout)."""

    __slots__ = ("_value",)

    _WIDTH: ClassVar[int] = 32
    # (propertyName, shift, width, sisoEnumUid or None) — drive repr; the
    # stamped properties below are the type-checker-visible accessors.
    _FIELDS: ClassVar[tuple[tuple[str, int, int, int | None], ...]] = ()

    def __init__(self, value: int = 0) -> None:
        self._value = int(value) & ((1 << self._WIDTH) - 1)

    @property
    def value(self) -> int:
        """The raw wire value; ``int(view)`` is equivalent."""
        return self._value

    def __int__(self) -> int:
        return self._value

    def __eq__(self, other: object) -> bool:
        return type(self) is type(other) and self._value == other._value

    __hash__ = None  # noqa: B032 - mutable view, unhashable by design

    def __repr__(self) -> str:
        parts = []
        for name, shift, width, uid in self._FIELDS:
            field = (self._value >> shift) & ((1 << width) - 1)
            if width == 1:
                shown: object = bool(field)
            elif uid is not None:
                shown = rich_or_int(uid, field)
            else:
                shown = field
            parts.append(f"{name}={shown!r}")
        return f"{type(self).__name__}({', '.join(parts)})"

    def _getBit(self, shift: int) -> bool:
        return bool((self._value >> shift) & 1)

    def _setBit(self, shift: int, on: bool) -> None:
        if on:
            self._value |= 1 << shift
        else:
            self._value &= ~(1 << shift)

    def _getBits(self, shift: int, width: int, uid: int) -> int:
        return rich_or_int(uid, (self._value >> shift) & ((1 << width) - 1))

    # generator: setter range validation is beyond mechanical layout emission
    def _setBits(self, shift: int, width: int, value: int) -> None:
        value = int(value)
        mask = (1 << width) - 1
        if not 0 <= value <= mask:
            raise ValueError(
                f"{value} does not fit a {width}-bit field "
                f"(expected 0..{mask})"
            )
        self._value = (self._value & ~(mask << shift)) | (value << shift)
