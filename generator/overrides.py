"""Python-side curated tables the generator consumes (fail-loud).

The corrected XML carries wire truth. These tables carry the decisions
that are NOT derivable from it:

* module homes — which classes live in which generated module, in what
  order (design §6 new-homes ruling);
* the frozen-identity set (design §3.3 — frozen is a policy choice about
  how a record is used, not a wire property);
* docstring furniture — the XML comments are the canonical docstring text
  (ruled 2026-10-15 after the upstream cleanup); the curated tables here
  carry only what the XML cannot say: the standard's record headings,
  Python-side design prose, and full-text overrides where a ruling makes
  the docstring deliberately non-XML;
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

# module key -> emitted classes, in definition order. "common" lands at
# record/common.py; family modules at record/<key>/__init__.py.
RECORD_MODULES = {
    "common": [
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
    ],
    "entity_information": [
        "DeadReckoningParameters",
        "VariableParameter",
        "EntityInformationFamilyPdu",
        "EntityStatePdu",
    ],
}

# convenience alias (the first milestone emitted only this module)
COMMON_RECORDS = RECORD_MODULES["common"]

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
    "EntityInformationInteractionFamilyPdu": "EntityInformationFamilyPdu",
}

# XML record class -> plain primitive type. The class is absorbed (its
# Python-side state is the raw integer; view logic is curated per class).
PRIMITIVE_BINDINGS = {
    "EntityAppearance": "uint32",
}

# XML base class -> (kernel base to emit, module providing it). Classes
# whose lineage reaches one of these emit PDU body methods.
KERNEL_BASES = {
    "PduBase": ("Pdu", "opendis.record.pdu"),
}

# -- docstring canon (XML-canonical, .references/decisions.md 2026-10-15) ----
#
# The spec XML's class comments are the canonical docstring text (cleaned
# upstream; the submodule pin is the final word). The emitter §-normalizes
# citations and hoists the record's own citation to the "§N.N <Title>"
# prefix line. These tables carry only what the XML cannot say.

# Module-level docstrings are inherently Python-side prose.
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
    "entity_information": """Entity Information / Interaction family (IEEE 1278.1-2012 §5.3).

Generated from the pinned spec XML (source of truth). The PDU header and
the composed ``Pdu`` base live in opendis.record.pdu; concrete PDUs emit
only their body (``_marshalledBodySize`` / ``_serializeBody`` /
``_parseBody``). Counts are derived ``len()`` properties, never stored;
variable-length lists are replaced wholesale on parse (instance-reuse
corruption, PR #49).
""",
}

# The standard's record headings (the XML comments carry no titles).
DOCSTRING_TITLES = {
    "SimulationAddress": "Simulation Address record",
    "EntityIdentifier": "Entity Identifier record",
    "EventIdentifier": "Event Identifier record",
    "EntityType": "Entity Type record",
    "EulerAngles": "Euler Angles record",
    "Vector3Float": "Vector record",
    "ClockTime": "Clock Time record",
    "MunitionDescriptor": "Munition Descriptor record",
    "EntityMarking": "Entity Marking record",
    "VariableParameter": "Variable Parameter record",
    "EntityInformationFamilyPdu": "Entity Information/Interaction family PDU",
    "EntityStatePdu": "Entity State PDU",
}

# Python-side design prose — repo rulings that exist only here, appended
# after the XML body.
DOCSTRING_ADDENDA = {
    "EntityIdentifier": """This is the standard 6-byte shape of the ruled entity-identifier taxonomy; the 4-byte live form (§6.2.53) belongs to the Live Entity family. Frozen: entity-keyed dicts and Fire → Detonation event correlation must not confuse this with same-shaped identifiers such as EventIdentifier.""",
    "EventIdentifier": """Ruled event-identifier taxonomy: this 6-byte shape, the 4-byte live form (EventIdentifierLiveEntity), a 2-byte flag-conditional elision, and absent-as-None — parse code may construct only these named shapes (see .references/decisions.md).""",
    "EntityType": """The domain field is dual-tabled: its SISO enumeration is [UID 8] for every entity kind except munitions (entity kind 2), which use [UID 14] to describe the target's domain (design §9.4); parse resolves the right table from entityKind, and the raw field stays a plain integer either way.""",
    "ClockTime": """timePastHour is held as its raw 32-bit Timestamp value (§6.2.88) — 64 bits each way, the record is 8 bytes.""",
    "EntityMarking": """The wire state is the raw 11 bytes; ``string`` is a NUL-trimmed view that pads on assignment.

# generator: the str-backed string property (NUL-trimmed, latin-1 to
# stay byte-faithful, truncated to 11 with a logged warning) is
# beyond mechanical generation.""",
    "DeadReckoningParameters": """The 15 ``parameters`` bytes are algorithm-dependent (§E.8) and opaque to the library — bytes, not a per-byte list.""",
    "VariableParameter": """General form (§6.2.94.1). The 15 record-specific bytes stay opaque; typed decoders (articulated parts etc.) ride the StandardVariableRecord registry separately.""",
    "EntityInformationFamilyPdu": """Thin family marker — per-class identity lives in the ``pduType``/``protocolFamily`` ClassVars; family metadata for middleware lives in ``PDU_FAMILIES`` (opendis.record.factory).""",
    "EntityStatePdu": """``entityAppearance`` and ``capabilities`` hold the raw uint32 on the wire; after parsing a known entity kind they hold the matching bitfield view (``int(view)`` is the raw value, so round-trips are byte-exact and unknown bits survive).""",
}

# Full-text replacements where a ruling makes the docstring deliberately
# non-XML. The Vector3Double docstring IS the WorldCoordinates alias
# ruling (its prose documents the alias emitted below the class).
DOCSTRING_OVERRIDES = {
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

# -- beyond-mechanical members ----------------------------------------------


class MemberSource:
    """Verbatim member source injected into an emitted class body."""

    def __init__(self, source: str, needs_logger: bool = False):
        self.source = source
        self.needs_logger = needs_logger


# -- class-level constants -------------------------------------------------
#
# (name, expression, comment-or-None). PDU identity constants carry their
# [UID] comments; the numeric values are SISO registry data absent from
# the spec XML (the XML initialValues are symbolic — DisPduType.ENTITY_STATE).

CLASS_VARS = {
    "SimulationAddress": [
        ("ALL_SITES", "sym.ALL_SITES", None),
        ("ALL_APPLICATIONS", "sym.ALL_APPLIC", None),
    ],
    "EntityIdentifier": [
        ("ALL_ENTITIES", "sym.ALL_ENTITIES", None),
    ],
    "EntityInformationFamilyPdu": [
        ("protocolFamily", "1", "[UID 5] Entity Information/Interaction"),
    ],
    "EntityStatePdu": [
        ("pduType", "1", "[UID 4]"),
    ],
}

# -- curated field furniture ----------------------------------------------

# (class, field) -> trailing rider where the mechanical [UID n] misses the
# exemplar text (primitive-bound classes carry no uid for the rider).
FIELD_RIDERS = {
    ("EntityStatePdu", "entityAppearance"): "[UID 31-43] or a bitfield view",
    ("EntityStatePdu", "capabilities"): "[UID 55] or a bitfield view",
}

# (class, field) -> annotation name where the semantic alias reads better
# than the canonical class (the alias is a module-level name in its home).
FIELD_ANNOTATIONS = {
    ("EntityStatePdu", "entityLocation"): "WorldCoordinates",
}

# -- PDU-body curated seams ------------------------------------------------

# Verbatim source appended at the end of _parseBody (context-dependent
# bitfield view selection is beyond mechanical generation).
PARSE_TAILS = {
    "EntityStatePdu": """key = (int(self.entityType.entityKind), int(self.entityType.domain))
appearanceView = _APPEARANCE_VIEWS.get(key)
if appearanceView is not None:
    self.entityAppearance = appearanceView(self.entityAppearance)
capabilityView = _CAPABILITY_VIEWS.get(key)
if capabilityView is not None:
    self.capabilities = capabilityView(self.capabilities)""",
}

# (after-class, source) blocks injected between emitted classes.
MODULE_SOURCES = {
    "entity_information": [
        (
            "EntityInformationFamilyPdu",
            """# generator: context-dependent bitfield layouts — the EntityAppearance /
# EntityCapabilities tables depend on entity kind (and, for platforms, on
# domain). Parse wraps the raw uint32 into the matching view; unknown
# kinds keep the plain int. The marshaller writes int(field) either way.
_APPEARANCE_VIEWS: dict[tuple[int, int], type] = {
    (1, 1): LandPlatformAppearance,  # platform, land domain [UID 31]
    (1, 2): AirPlatformAppearance,  # platform, air domain [UID 32]
}
_CAPABILITY_VIEWS: dict[tuple[int, int], type] = {
    (1, 1): LandPlatformCapabilities,  # [UID 450]
    (1, 2): AirPlatformCapabilities,  # [UID 451]
}""",
        )
    ],
}

# module key -> extra imports the curated blocks above need (the usage
# scan cannot see inside verbatim source strings).
MODULE_SOURCE_IMPORTS = {
    "entity_information": {
        "opendis.bitfields": [
            "AirPlatformAppearance",
            "AirPlatformCapabilities",
            "LandPlatformAppearance",
            "LandPlatformCapabilities",
        ],
    },
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


# -- beyond-mechanical members (table) ---------------------------------------


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
