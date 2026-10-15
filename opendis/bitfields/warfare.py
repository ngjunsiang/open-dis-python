"""Warfare-family bitfield view classes (see package docstring)."""

from typing import ClassVar

from opendis.bitfields.base import BitfieldView

__all__ = ["DEFireFlags"]


class DEFireFlags(BitfieldView):
    """SISO-REF-010 [UID 313] DE Fire Flags — §7.3.4 Directed Energy Fire
    PDU, 16-bit Boolean field.

    Bits 2–15 are reserved; they survive round-trips untouched.
    """

    _WIDTH: ClassVar[int] = 16
    _FIELDS: ClassVar[tuple[tuple[str, int, int, int | None], ...]] = (
        ("weaponOn", 0, 1, None),
        ("stateUpdateFlag", 1, 1, 374),
    )

    @property
    def weaponOn(self) -> bool:
        return self._getBit(0)

    @weaponOn.setter
    def weaponOn(self, on: bool) -> None:
        self._setBit(0, on)

    @property
    def stateUpdateFlag(self) -> bool:
        return self._getBit(1)

    @stateUpdateFlag.setter
    def stateUpdateFlag(self, on: bool) -> None:
        self._setBit(1, on)
