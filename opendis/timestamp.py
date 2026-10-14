"""Timestamp value object for the DIS PDU header (IEEE 1278.1-2012 §6.2.88).

The timestamp is a 32-bit value: bit 0 is the absolute/relative time type
flag and the most significant 31 bits hold the time — a count of
3600/2^31-second units (≈1.67638063 µs) past the start of the hour,
wrapping every hour. Keeping ``raw`` as the stored state makes round-trips
exact; the derived properties carry the domain knowledge.
"""

from dataclasses import dataclass
import time

__all__ = ["Timestamp"]

_UNITS_PER_HOUR = 1 << 31
_SECONDS_PER_UNIT = 3600.0 / _UNITS_PER_HOUR


@dataclass(frozen=True, slots=True)
class Timestamp:
    """IEEE 1278.1-2012 §6.2.88 Timestamp.

    Frozen so it is hashable and safe to keep on entity-state histories.
    The wire layer is unchanged: pack writes ``timestamp.raw``, parse does
    ``Timestamp(read_uint32())``.
    """

    raw: int = 0

    @property
    def isAbsolute(self) -> bool:
        """True when the timestamp is absolute (referenced to UTC hour)."""
        return bool(self.raw & 1)

    @property
    def secondsPastHour(self) -> float:
        """Seconds since the start of the hour, in [0, 3600)."""
        return (self.raw >> 1) * _SECONDS_PER_UNIT

    @classmethod
    def fromSeconds(cls, seconds: float, *, absolute: bool = True) -> "Timestamp":
        """Build a timestamp from seconds past the hour.

        Values outside [0, 3600) wrap modulo one hour, mirroring the wire
        representation.
        """
        units = round((seconds % 3600.0) / _SECONDS_PER_UNIT) % _UNITS_PER_HOUR
        return cls((units << 1) | int(absolute))

    @classmethod
    def now(cls, *, absolute: bool = True) -> "Timestamp":
        """Build a timestamp from the current wall-clock time of day."""
        return cls.fromSeconds(time.time() % 3600.0, absolute=absolute)

    def deltaSince(self, other: "Timestamp") -> float:
        """Seconds from ``other`` to ``self``, correct across the hourly wrap.

        The result lies in [0, 3600): a ``self`` slightly *before* ``other``
        yields a value slightly under 3600. Assumes both timestamps share
        their time type (both absolute or both relative).
        """
        units = ((self.raw >> 1) - (other.raw >> 1)) % _UNITS_PER_HOUR
        return units * _SECONDS_PER_UNIT
