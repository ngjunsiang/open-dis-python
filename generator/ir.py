"""Typed intermediate representation between the XML spec and the emitter.

Every semantic decision the emitter needs is made before emission — the
emitter only lays out text (ruled architecture, 2026-10-14). Shapes the
common-record slice does not exercise yet (lists, pads, bitfield refs)
exist as explicit Unsupported placeholders so encountering one fails
loudly at resolve time instead of emitting wrong code silently.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from xml.etree.ElementTree import Element

PRIM_BITS: dict[str, int] = {
    "uint8": 8,
    "uint16": 16,
    "uint32": 32,
    "uint64": 64,
    "int8": 8,
    "int16": 16,
    "int32": 32,
    "int64": 64,
    "float32": 32,
    "float64": 64,
}

ENUM_ANN: dict[int, str] = {8: "enum8", 16: "enum16", 32: "enum32"}


@dataclass(frozen=True)
class Primitive:
    type: str
    default: str | None = None


@dataclass(frozen=True)
class EnumRef:
    """A sisoenum-typed field; ``uid`` is None only for unknown shapes."""

    uid: int | None
    size: int  # bits
    enum_type: str | None = None
    when: str | None = None  # variant guard; None marks the default member
    default: str | None = None  # raw XML symbol, e.g. "PlatformDomain.OTHER"


@dataclass(frozen=True)
class ClassRef:
    target: str  # canonical Python class name
    when: str | None = None


@dataclass(frozen=True)
class FixedBytes:
    """A fixed-length primitivelist without a count field (e.g. marking)."""

    length: int  # bytes
    could_be_string: bool = False


@dataclass(frozen=True)
class Unsupported:
    """A construct this generator version does not handle — fail loud."""

    summary: str


@dataclass(frozen=True)
class VariantGroup:
    """An attribute holding competing type children of one tag.

    Semantics pinned by check_consistency.py: per child tag, exactly ONE
    member of a when-carrying group is present — the first whose when=
    is true, else the no-when default. The default/full shape is declared
    LAST (ruled ordering so legacy SAX parsers degrade correctly).
    """

    tag: str
    members: tuple


Shape = Primitive | EnumRef | ClassRef | FixedBytes | Unsupported | VariantGroup


@dataclass(frozen=True)
class Attribute:
    name: str
    comment: str | None
    shape: Shape
    present_if: str | None = None


@dataclass
class RecordClass:
    name: str
    comment: str | None
    attributes: list[Attribute]
    frozen: bool = False
    xml: Element | None = dc_field(default=None, repr=False, compare=False)
