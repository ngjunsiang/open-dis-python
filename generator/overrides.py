"""Python-side curated tables the generator consumes (fail-loud).

The corrected XML carries wire truth. These tables carry the decisions
that are NOT derivable from it:

* module homes — which classes live in which generated module, in what
  order (design §6 new-homes ruling);
* the frozen-identity set (design §3.3 — frozen is a policy choice about
  how a record is used, not a wire property);
* docstring canon — XML comments are untrustworthy (citation drift is
  real: the XML still cites EulerAngles as 6.2.33 and Vector3Float as
  6.2.95), so the exemplar's reviewed prose is the reference text;
* beyond-mechanical members (`# generator:` spots in the exemplar);
* name/shape bindings — e.g. the XML's flat ``EntityID`` (71 classRefs)
  binds to the canonical nested ``EntityIdentifier`` per the ruled
  identifier taxonomy.

Classes absent from these tables get mechanical defaults (mutable,
XML-comment docstring) so growing the family modules needs no edits here
unless a ruling applies.
"""

from __future__ import annotations

# -- module composition ---------------------------------------------------

COMMON_RECORDS = [
    "SimulationAddress",
    "EntityIdentifier",
    "EventIdentifier",
    "EntityType",
    "EulerAngles",
    "Vector3Float",
    "Vector3Double",
    "ClockTime",
    "MunitionDescriptor",
    "EntityMarking",
]

FROZEN_RECORDS = {
    "SimulationAddress",
    "EntityIdentifier",
    "EventIdentifier",
    "EntityType",
}

# XML class name -> canonical Python class. The XML class is NOT emitted;
# every reference to it rebinds to the canonical class.
RECORD_BINDINGS = {
    "EntityID": "EntityIdentifier",
}

# -- docstring canon (exemplar prose, .references/decisions.md rulings) ----

MODULE_DOCSTRINGS = {
    "common": """Common record types used across multiple protocol families.

Target-state DIS 7 representation (design: docs/design/dis7-representation.md
§3.3). Identity types are frozen dataclasses — hashable, usable as dict keys,
and type-sensitive so same-shaped identifiers never compare equal. They parse
constructively (``parse`` returns a new instance) because frozen records
cannot be repopulated in place; mutable value records keep the mutating
``parse`` of the ``Record`` protocol.

# generator: frozen records get constructor-style parse (classmethod);
# mutable records keep mutating parse. Both satisfy the runtime-checkable
# Record protocol, but only the mutating form matches its static signature.
""",
}

DOCSTRINGS = {
    "SimulationAddress": """§6.2.80 Simulation Address record

Simulation designation associated with all object identifiers except
those contained in Live Entity PDUs.""",
    "EntityIdentifier": """§6.2.28 Entity Identifier record

Unique designation of each entity in an event or exercise that is not
contained in a Live Entity PDU. This is the standard 6-byte shape of
the ruled entity-identifier taxonomy; the 4-byte live form (6.2.53)
belongs to the Live Entity family. Frozen: entity-keyed dicts and
Fire → Detonation event correlation must not confuse this with
same-shaped identifiers such as EventIdentifier.""",
    "EventIdentifier": """§6.2.33 Event Identifier record

Identifies an event in the world. Use this format for every PDU EXCEPT
the LiveEntityPdu. Ruled event-identifier taxonomy: this 6-byte shape,
the 4-byte live form (EventIdentifierLiveEntity), a 2-byte
flag-conditional elision, and absent-as-None — parse code may
construct only these named shapes (see .references/decisions.md).""",
    "EntityType": """§6.2.30 Entity Type record

Identifies the type of Entity. The domain field is dual-tabled: its
SISO enumeration is [UID 8] for every entity kind except munitions
(entity kind 2), which use [UID 14] to describe the target's domain
(design §9.4); parse resolves the right table from entityKind, and the
raw field stays a plain integer either way.""",
    "EulerAngles": """§6.2.32 Euler Angles record

Three floating point values representing an orientation, psi, theta,
and phi, aka the euler angles, in radians.
These angles shall be specified with respect to the entity's coordinate
system.""",
    "Vector3Float": """§6.2.96 Vector record

Vector values for entity coordinates, linear acceleration, and linear
velocity shall be represented using a Vector record. This record shall
consist of three fields, each a 32-bit floating point number.
The unit of measure represented by these fields shall depend on the
information represented.""",
    "Vector3Double": """Three 64-bit floating point values, used for entity location.

Ruled 2026-10-14: the XML class name ``Vector3Double`` is canonical —
it is the only 3x-f64 class in the XML (13 classRefs, all location
fields) and the standard's only 3x-f64 record is World Coordinates
(6.2.98; 6.2.97 is Vectoring Nozzle System Data, and an earlier
revision of this docstring wrongly cited it). ``WorldCoordinates`` is
a plain alias below, not a subclass — separate same-shaped classes
would split type-sensitive equality and isinstance across the two
names. The XML-fix session may rename the XML class so the alias
flips direction. The class stays semantics-neutral (x/y/z only);
geodetic helpers live in a separate module (RangeCoordinates.py
precedent).""",
    "ClockTime": """§6.2.14 Clock Time record

Time measurements that surpass one hour. Hour is hours since
0000 h 1 January 1970 UTC; timePastHour is a Timestamp record
(§6.2.88) held as its raw 32-bit value — 64 bits each way the record
is 8 bytes.""",
    "MunitionDescriptor": """§6.2.19.2 Munition Descriptor record

Describes the firing or detonation of a munition: the munition type
plus warhead, fuse, quantity, and rate. The Expendable Descriptor
(§6.2.19.4) shares this slot on the wire with a same-sized shape
(expendable type + 64 bits of padding).""",
    "EntityMarking": """§6.2.29 Entity Marking record

A character set followed by 11 characters of text data. The wire state
is the raw 11 bytes; ``string`` is a NUL-trimmed view that pads on
assignment.

# generator: the str-backed string property (NUL-trimmed, latin-1 to
# stay byte-faithful, truncated to 11 with a logged warning) is
# beyond mechanical generation.""",
}

FIELD_DOCSTRINGS = {
    (
        "SimulationAddress",
        "site",
    ): """A site is defined as a facility, installation, organizational unit or
a geographic location that has one or more simulation applications
capable of participating in a distributed event.""",
    (
        "SimulationAddress",
        "application",
    ): """An application is defined as a software program that is used to
generate and process distributed simulation data including live, virtual
and constructive data.""",
}

# -- class-level constants -------------------------------------------------

CLASS_VARS = {
    "SimulationAddress": [
        ("ALL_SITES", "sym.ALL_SITES"),
        ("ALL_APPLICATIONS", "sym.ALL_APPLIC"),
    ],
    "EntityIdentifier": [
        ("ALL_ENTITIES", "sym.ALL_ENTITIES"),
    ],
}

# -- class tails (the ruled plain alias) --------------------------------------

# Emitted directly after the named class (the exemplar refresh moved the
# alias from module end to directly under Vector3Double).
CLASS_TAILS = {
    "Vector3Double": """# generator: plain alias per the 2026-10-14 ruling — never re-declare as a
# separate class
WorldCoordinates = Vector3Double""",
}

# Variant-uid constant comments (curated prose; REF-010's table names are
# "Platform Domain"/"Munition Domain", the exemplar annotates instead)
VARIANT_UID_COMMENTS = {
    8: "Entity Domain (platforms and non-munition kinds)",
    14: "Entity Domain (munition entities: domain of the target)",
}

# Stamp emitted above a variant field's uid-selection statement
VARIANT_PARSE_NOTES = {
    (
        "EntityType",
        "domain",
    ): """# generator: domain's enum table is kind-dependent (UID 14 for
        # munitions, UID 8 otherwise) — the XML's own TODO #9""",
}

# -- bitfield views -----------------------------------------------------------

# family module -> REF-010 bitfield uids, in definition order (the
# exemplar's set; the remaining appearance variants arrive with their
# consuming families)
BITFIELD_VIEWS = {
    "appearance": [31, 32, 450, 451],
    "minefield": [190],
    "simulation_management": [68],
    "warfare": [313],
}

# View class names where PascalCase(table name) misses the exemplar
BITFIELD_CLASS_NAMES = {
    190: "MinefieldStateAppearance",  # "Minefield State-Appearance Bit Map"
}

# (bitfield uid, REF-010 row name) -> property name where sanitization
# alone misses the exemplar's name
BITFIELD_RENAMES = {
    (31, "Is Smoke Emanating"): "isSmokeEmitting",
    (32, "Is Smoke Emanating"): "isSmokeEmitting",
}

BITFIELD_DOCSTRINGS = {
    31: """Entity Appearance layout for land platforms [UID 31].

Single-bit properties are bool; True means the enumerated value 1
(e.g. ``paintScheme=True`` is camouflage [UID 378], ``state=True``
is deactivated [UID 386]).""",
    32: "Entity Appearance layout for air platforms [UID 32].",
    450: """Entity Capabilities layout for land platforms [UID 450].

Bits 4–5 are reserved and not exposed; they round-trip untouched.""",
    451: "Entity Capabilities layout for air platforms [UID 451].",
    190: """SISO-REF-010 [UID 190] Minefield State-Appearance Bit Map — §7.9.2
Minefield State PDU, 16-bit field.

Bits 4–12 and 14–15 are reserved; they survive round-trips
untouched.""",
    68: """SISO-REF-010 [UID 68] Stop/Freeze-Frozen Behavior — §7.5.5 Stop/
Freeze PDU, 8-bit field.

Bits 3–7 are reserved; they survive round-trips untouched.""",
    313: """SISO-REF-010 [UID 313] DE Fire Flags — §7.3.4 Directed Energy Fire
PDU, 16-bit Boolean field.

Bits 2–15 are reserved; they survive round-trips untouched.""",
}

BITFIELD_MODULE_DOCSTRINGS = {
    "appearance": """Entity Appearance (IEEE 1278.1-2012 §6.2.26) and Entity Capabilities
(§6.2.27) bitfield views.

Layouts transcribed from SISO-REF-010 v37 bitfield tables: Land Platform
Appearance [UID 31], Air Platform Appearance [UID 32], Land Platform
Capabilities [UID 450], Air Platform Capabilities [UID 451]. One view
class per entity kind/domain layout, all over the same uint32 wire field.

# generator: layouts and bit positions are mechanical output of the
# SISO-REF-010 bitfield tables; the row-name to camelCase property
# sanitization ("Spot/Search Light #1 On" -> spotSearchLight1On) needs a
# name-mapping table in the generator.""",
    "minefield": "Minefield-family bitfield view classes (see package docstring).",
    "simulation_management": "Simulation-management bitfield view classes (see package docstring).",
    "warfare": "Warfare-family bitfield view classes (see package docstring).",
}


# -- beyond-mechanical members ----------------------------------------------


class MemberSource:
    """Verbatim member source injected into an emitted class body."""

    def __init__(self, source: str, needs_logger: bool = False):
        self.source = source
        self.needs_logger = needs_logger


CLASS_MEMBERS = {
    "EntityMarking": MemberSource(
        needs_logger=True,
        source='''@property
def string(self) -> str:
    """The marking text, NUL-trimmed."""
    return self.characters.split(b"\\x00", 1)[0].decode("latin-1")

# generator: truncation warning is beyond mechanical generation
# (ruled 2026-10-14: silent truncation would eat bugs; silence via
# log level or stderr redirect)
@string.setter
def string(self, value: str) -> None:
    data = value.encode("latin-1")
    if len(data) > 11:
        _logger.warning(
            "EntityMarking string %r truncated to 11 bytes", value)
    self.characters = data[:11].ljust(11, b"\\x00")''',
    ),
}
