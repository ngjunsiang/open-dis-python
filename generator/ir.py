"""Typed intermediate representation between the XML spec and the emitter.

Every semantic decision the emitter needs is made before emission — the
emitter only lays out text (ruled architecture, 2026-10-14). Shapes the
record slices do not exercise yet (pads, counted primitivelists) exist
as explicit Unsupported placeholders so encountering one fails loudly at
resolve time instead of emitting wrong code silently.
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
class BitfieldRef:
    """A sisobitfield wire field: raw uint{size} state, [UID n] rider.

    The PDU holds the plain integer; typed bitfield views are applied
    after parse by curated tails (context-dependent layout selection is
    beyond mechanical generation).
    """

    uid: int
    size: int  # bits


@dataclass(frozen=True)
class ObjectList:
    """A variable-length list of one record class with a count field.

    ``count_field`` names a ``hidden="true"`` primitive declared earlier
    in the same class: it is on the wire but is never instance state —
    the Python side exposes it as a derived ``len()`` property (ruled
    counts-as-length representation).
    """

    element: str  # record class name
    count_field: str


@dataclass(frozen=True)
class PrimitiveList:
    """A variable-length list of one primitive type with a count field.

    Same counts-as-length contract as ObjectList; elements may be rich
    enums when ``element_uid`` is set (Data Query datum-ID lists).
    ``count_expr``/``count_list`` carry the minefield count vocabulary
    (N×M products and per-element count lists) — both are beyond the
    plain count-field form and fail loud in the emitter.
    """

    element: str  # primitive wire type, e.g. "uint16"
    count_field: str
    element_uid: int | None = None
    count_expr: str | None = None
    count_list: str | None = None


@dataclass(frozen=True)
class BytesPayload:
    """A byte payload whose wire length counts BITS.

    The paired hidden count field is derived: ``len(payload) * 8``. The
    2012 standard uses bit counts here (Variable Datum §6.2.93, Signal
    and Intercom Signal §7.7); non-multiple-of-8 counts are unsupported
    (sample-review open question 6 ruling). ``bit_count_field=None``
    marks an expression-sized payload (§6.2.73 record sets): every wire
    method is curated.
    """

    bit_count_field: str | None
    count_is_bits: bool = True  # False: the paired count is in bytes


@dataclass(frozen=True)
class OptionalRecord:
    """A single record that may be absent on the wire (Transmitter's
    Modulation Parameters / Antenna Pattern): ``X | None = None``. The
    wire methods are always curated (presence dispatch is beyond
    mechanical generation)."""

    target: str  # Python class name (usually a hand seam class)


@dataclass(frozen=True)
class CuratedField:
    """A field whose shape is fully curated (annotation + default +
    rider text): the flag-conditional optionals of the LE conditional
    vocabulary. The owning class's wire methods are curated."""

    annotation: str
    default: str
    rider: str | None = None


@dataclass(frozen=True)
class PadToBoundary:
    """An alignment pad computed by the packer, never instance state.

    The exemplar's shape: size/serialize/parse compute the pad from the
    running byte count (unnamed alignment pads stay packer-computed,
    2026-10-14 ruling). Mechanical method emission refuses these classes
    — their wire methods are curated.
    """

    length: int  # bit boundary (32/64)


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


Shape = (
    Primitive
    | EnumRef
    | ClassRef
    | FixedBytes
    | BitfieldRef
    | ObjectList
    | PrimitiveList
    | BytesPayload
    | OptionalRecord
    | CuratedField
    | PadToBoundary
    | Unsupported
    | VariantGroup
)


@dataclass(frozen=True)
class Attribute:
    name: str
    comment: str | None
    shape: Shape
    present_if: str | None = None
    hidden: bool = False  # wire-only count field, derived on the Python side
    count_for: str | None = None  # for hidden counts: the list field sized
    count_bits: bool = False  # hidden count is a bit count (BytesPayload)
    viewable: bool = False  # primitive-bound: parse may attach a curated view
    view: str | None = None  # BitfieldRef: the attached view's local name
    # (uid-keyed lookup over the generated single-layout tables; None on
    # raw fields and the kind/domain-qualified context tables)
    view_binding: str | None = None  # viewable: the absorbed XML class name
    # (EntityAppearance/EntityCapabilities — context layouts keyed by the
    # record's entityType; emits the kind-dispatch parse tail)
    pad: bool = False  # named padding primitive: field(init=False), grouped last


@dataclass
class RecordClass:
    name: str
    comment: str | None
    attributes: list[Attribute]
    frozen: bool = False
    parent: str | None = None  # canonical Python base (None -> plain class)
    is_pdu: bool = False  # lineage reaches a kernel PDU base
    is_sv: bool = False  # uid-66 Standard Variable record (SV_RECORDS):
    # writes its own recordType/recordLength header; frozen parse takes
    # the wire bytelength (§6.2.83)
    # XML-declared identity constants (pduType/protocolFamily from
    # initialValue + class id; uid-66 recordType from the SV signature's
    # defaultValue): (var name, value expr, rider) in emission order
    identity_vars: tuple[tuple[str, str, str | None], ...] = ()
    xml: Element | None = dc_field(default=None, repr=False, compare=False)
