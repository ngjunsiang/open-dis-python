"""Simulation-management bitfield view classes (see package docstring)."""

from typing import ClassVar

from opendis.bitfields.base import BitfieldView

__all__ = ["StopFreezeFrozenBehavior"]


class StopFreezeFrozenBehavior(BitfieldView):
    """SISO-REF-010 [UID 68] Stop/Freeze-Frozen Behavior — §7.5.5 Stop/
    Freeze PDU, 8-bit field.

    Bits 3–7 are reserved; they survive round-trips untouched.
    """

    _WIDTH: ClassVar[int] = 8
    _FIELDS: ClassVar[tuple[tuple[str, int, int, int | None], ...]] = (
        ("runSimulationClock", 0, 1, None),
        ("transmitUpdates", 1, 1, None),
        ("processUpdates", 2, 1, None),
    )

    @property
    def runSimulationClock(self) -> bool:
        return self._getBit(0)

    @runSimulationClock.setter
    def runSimulationClock(self, on: bool) -> None:
        self._setBit(0, on)

    @property
    def transmitUpdates(self) -> bool:
        return self._getBit(1)

    @transmitUpdates.setter
    def transmitUpdates(self, on: bool) -> None:
        self._setBit(1, on)

    @property
    def processUpdates(self) -> bool:
        return self._getBit(2)

    @processUpdates.setter
    def processUpdates(self, on: bool) -> None:
        self._setBit(2, on)
