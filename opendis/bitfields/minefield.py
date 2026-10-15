"""Minefield-family bitfield view classes (see package docstring)."""

from typing import ClassVar

from opendis.bitfields.base import BitfieldView

__all__ = ["MinefieldStateAppearance"]


class MinefieldStateAppearance(BitfieldView):
    """SISO-REF-010 [UID 190] Minefield State-Appearance Bit Map — §7.9.2
    Minefield State PDU, 16-bit field.

    Bits 4–12 and 14–15 are reserved; they survive round-trips
    untouched.
    """

    _WIDTH: ClassVar[int] = 16
    _FIELDS: ClassVar[tuple[tuple[str, int, int, int | None], ...]] = (
        ("minefieldType", 0, 2, 418),
        ("activeStatus", 2, 1, 419),
        ("lane", 3, 1, 420),
        ("state", 13, 1, 421),
    )

    @property
    def minefieldType(self) -> int:
        """[UID 418] Minefield Appearance-Minefield Type."""
        return self._getBits(0, 2, 418)

    @minefieldType.setter
    def minefieldType(self, value: int) -> None:
        self._setBits(0, 2, value)

    @property
    def activeStatus(self) -> bool:
        return self._getBit(2)

    @activeStatus.setter
    def activeStatus(self, on: bool) -> None:
        self._setBit(2, on)

    @property
    def lane(self) -> bool:
        return self._getBit(3)

    @lane.setter
    def lane(self, on: bool) -> None:
        self._setBit(3, on)

    @property
    def state(self) -> bool:
        return self._getBit(13)

    @state.setter
    def state(self, on: bool) -> None:
        self._setBit(13, on)
