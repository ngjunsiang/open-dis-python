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

from . import ir

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
        # §7.2.3-§7.2.6 (Phase 5, pduType values per the standard's §5.2.4
        # enumeration: Collision 4, Collision-Elastic 66, ES-Update 67,
        # Attribute 72)
        "CollisionPdu",
        "CollisionElasticPdu",
        "EntityStateUpdatePdu",
        "Attribute",
        "AttributeRecordSet",
        "AttributePdu",
    ],
    "warfare": [
        "WarfareFamilyPdu",
        "FirePdu",
        "DetonationPdu",
        "DirectedEnergyFirePdu",
        "EntityDamageStatusPdu",
        # §6.2.15/.20 Directed Energy records (uid-66 SV records; the
        # deposition record precedes the area aimpoint — the aimpoint's
        # typed list annotations need it defined first)
        "DirectedEnergyDamage",
        "DirectedEnergyTargetEnergyDeposition",
        "DirectedEnergyAreaAimpoint",
        "DirectedEnergyPrecisionAimpoint",
    ],
    "logistics": [
        "LogisticsFamilyPdu",
        "SupplyQuantity",
        "ServiceRequestPdu",
        "ResupplyOfferPdu",
        "ResupplyReceivedPdu",
        "ResupplyCancelPdu",
        "RepairCompletePdu",
        "RepairResponsePdu",
    ],
    "simulation_management": [
        "FixedDatum",
        "VariableDatum",
        "SimulationManagementFamilyPdu",
        "DataPdu",
        "CreateEntityPdu",
        "RemoveEntityPdu",
        "StartResumePdu",
        "StopFreezePdu",
        "AcknowledgePdu",
        "ActionRequestPdu",
        "ActionResponsePdu",
        "DataQueryPdu",
        "SetDataPdu",
        "EventReportPdu",
        "CommentPdu",
    ],
    "minefield": [
        "MinefieldIdentifier",
        "Vector2Float",
        "MineEmplacementTime",
        "MinefieldFamilyPdu",
        "MinefieldStatePdu",
        "MinefieldQueryPdu",
        "MinefieldDataPdu",
        "MinefieldResponseNACKPdu",
    ],
    "radio": [
        # §6.2.8 Antenna Pattern home + §6.2.8.2 Beam record, then the
        # Annex C MP records (C.2/C.3 zero-length markers, Table C.3
        # Basic HAVE QUICK, Table C.7 CCTT SINCGARS) under the §6.2.58
        # home, and the §6.2.95 home + its Table C.4 record — the
        # spec-repo annex-c-mp-ap wave; bases precede their subclasses
        "AntennaPatternRecord",
        "BeamAntennaPattern",
        "ModulationParametersRecord",
        "GenericRadio",
        "SimpleIntercomRadio",
        "BasicHaveQuickMP",
        "CCTTSincgarsMP",
        "VariableTransmitterParametersRecord",
        "HighFidelityHAVEQUICKRadio",
        "ModulationType",
        "RadioCommunicationsFamilyPdu",
        "TransmitterPdu",
        "SignalPdu",
        "ReceiverPdu",
        "IntercomReferenceID",
        "IntercomSignalPdu",
        "IntercomCommunicationsParameters",
        "IntercomControlPdu",
    ],
    "information_operations": [
        "InformationOperationsFamilyPdu",
        "InformationOperationsActionPdu",
        "InformationOperationsReportPdu",
    ],
    "entity_management": [
        "AggregateIdentifier",
        "AggregateType",
        "AggregateMarking",
        "Relationship",
        "NamedLocationIdentification",
        # Table 183's Silent Aggregate System list element (authored in
        # the XML as its own 96-bit record since spec v0.12.3, issue #7;
        # the list previously classRef'd EntityType — 64 bits, wire-wrong)
        "SilentAggregateSystem",
        # §6.2.79 Silent Entity System record — Table 183's Silent Entity
        # System list element (the XML's AggregateStatePdu classRefs
        # EntityType there; upstream XML gap, standard followed)
        "SilentEntitySystem",
        "EntityManagementFamilyPdu",
        "AggregateStatePdu",
        "IsGroupOfPdu",
        "TransferOwnershipPdu",
        "IsPartOfPdu",
    ],
    "synthetic_environment": [
        "ObjectIdentifier",
        "ObjectType",
        "LinearSegmentParameter",
        "EnvironmentRecord",
        "SyntheticEnvironmentFamilyPdu",
        "EnvironmentalProcessPdu",
        # §6.2.40 grid-axis descriptor records (fixed/variable; the shared
        # GridAxisDescriptor base is a Java-side abstraction — abstract
        # marker, resolver drop) + §6.2.41 Grid Data records (the standard
        # defines representation types 0-2 only) + §7.10.3 Gridded Data PDU
        "GridAxisDescriptorFixed",
        "GridAxisDescriptorVariable",
        "GridDataType0",
        "GridDataType1",
        "GridDataType2",
        "GriddedDataPdu",
        "PointObjectStatePdu",
        "LinearObjectStatePdu",
        "ArealObjectStatePdu",
    ],
    "distributed_emissions": [
        "EEFundamentalParameterData",
        "BeamData",
        "BeamStatus",
        "JammingTechnique",
        "TrackJamData",
        "EmitterSystem",
        "EmitterBeam",
        "ElectronicEmitter",
        "DistributedEmissionsRegenerationFamilyPdu",
        "ElectromagneticEmissionPdu",
        "DesignatorPdu",
        "ShaftRPM",
        "APA",
        "AcousticEmitter",
        "UAFundamentalParameter",
        "UABeam",
        "UAEmitter",
        "UnderwaterAcousticPdu",
        # §7.6.5 IFF PDU with its layer records (Phase 5): the Layer 1
        # records, the §6.2.51 Layer Header, the §6.2.43/.44 IFF data
        # records, the Annex-B basic-data records, and the five concrete
        # layer formats — then §7.6.6 SEES
        "SystemIdentifier",
        "FundamentalOperationalData",
        "LayerHeader",
        "IFFFundamentalParameterData",
        "IFFData",
        "Mode5InterrogatorBasicData",
        "Mode5TransponderBasicData",
        "ModeSInterrogatorBasicData",
        "ModeSTransponderBasicData",
        "IFFPduLayer2Data",
        "IFFPduLayer3TransponderFormatData",
        "IFFPduLayer3InterrogatorFormatData",
        "IFFPduLayer4InterrogatorFormatData",
        "IFFPduLayer4TransponderFormatData",
        "IFFPduLayer5Data",
        "IdentificationFriendOrFoePdu",
        "PropulsionSystemData",
        "VectoringNozzleSystem",
        "SupplementalEmissionEntityStatePdu",
    ],
    "live_entity": [
        "LiveSimulationAddress",
        "LiveEntityIdentifier",
        "LiveEntityIdentifierElided",
        "EventIdentifierLiveEntity",
        "EventIdentifierLiveEntityElided",
        "LEMunitionDescriptor",
        "LiveEntityRelativeWorldCoordinates",
        "LiveEntityLinearVelocity",
        "LiveEntityOrientation",
        "LiveEntityOrientation16",
        "LiveEntityPositionError",
        "LiveEntityOrientationError",
        "LEVector3FixedByte",
        "LiveDeadReckoningParameters",
        "LiveEntityRelativeEntityCoordinates",
        "LiveEntityFamilyPdu",
        "TimeSpacePositionInformationPdu",
        "AppearancePdu",
        "ArticulatedPartsPdu",
        "LiveEntityFirePdu",
        "LiveEntityDetonationPdu",
    ],
    "simulation_management_with_reliability": [
        "SimulationManagementWithReliabilityFamilyPdu",
        "RecordSpecificationElement",
        "CreateEntityReliablePdu",
        "RemoveEntityReliablePdu",
        "StartResumeReliablePdu",
        "StopFreezeReliablePdu",
        "AcknowledgeReliablePdu",
        "ActionRequestReliablePdu",
        "ActionResponseReliablePdu",
        "DataQueryReliablePdu",
        "SetDataReliablePdu",
        "DataReliablePdu",
        "EventReportReliablePdu",
        "CommentReliablePdu",
        "RecordReliablePdu",
        "SetRecordReliablePdu",
        "RecordQueryReliablePdu",
    ],
}

# convenience alias (the first milestone emitted only this module)
COMMON_RECORDS = RECORD_MODULES["common"]

FROZEN_RECORDS = {
    "TrackJamData",
    "SystemIdentifier",
    "IFFFundamentalParameterData",
    "LiveSimulationAddress",
    "LiveEntityIdentifier",
    "LiveEntityIdentifierElided",
    "EventIdentifierLiveEntity",
    "EventIdentifierLiveEntityElided",
    "AggregateIdentifier",
    "AggregateType",
    "ObjectIdentifier",
    "ObjectType",
    "IntercomReferenceID",
    "MinefieldIdentifier",
    "SimulationAddress",
    "EntityIdentifier",
    "EventIdentifier",
    "EntityType",
    # promoted seam records are deliberately NOT frozen: they carry
    # wire-pad state (field(init=False)) and the SV protocol is a
    # mutating parse(inputStream, bytelength) — freezing would drop
    # both (resolve fails loud on frozen SV records)
}

# XML class name -> canonical Python class. The XML class is NOT emitted;
# every reference to it rebinds to the canonical class.
RECORD_BINDINGS = {
    "EntityID": "EntityIdentifier",
    "EntityInformationInteractionFamilyPdu": "EntityInformationFamilyPdu",
    # the SM/-R originator/receiver classRef is the same 6-byte wire shape
    # as EntityIdentifier (§6.2.81 vs §6.2.28) — exemplar-consistency ruling
    "SimulationIdentifier": "EntityIdentifier",
    # same 8-byte EntityType shape (§6.2.71 vs §6.2.30); kind defaults
    # come from the XML's symbolic initialValue, not carried as state
    "RadioType": "EntityType",
    # the XML's "not fully defined" §6.2.31 Environment record is the
    # exemplar's opaque EnvironmentRecord
    "Environment": "EnvironmentRecord",
}

# XML class -> plain primitive type. The class is absorbed (its
# Python-side state is the raw integer; view logic is curated per class).
# ChangeOptions is 8 bits (Table B.5; Table 118 totals the System
# Identifier at 48 bits with it) — the pre-Phase-5 uint16 binding was a
# wire bug that made every IFF PDU one byte long (upstream candidate).
PRIMITIVE_BINDINGS = {
    "EntityAppearance": "uint32",
    "ProtocolMode": "uint16",
    "EntityCapabilities": "uint32",
    "ChangeOptions": "uint8",
}

# XML parent classes that are Java-side abstractions, never emitted and
# never Python bases. PARENT_DROPS RETIRED 2026-10-17 (bucket-C item 3,
# spec v0.12.8): the three classes now carry abstract="true" in the XML
# and the resolver infers the drop (abstract + not an emitted class and
# not a kernel base — resolve._is_dropped_parent).

# classRef targets that splice their own fields in place (the ruled
# RadioCommsHeader flattening: the composed PDU header already owns the
# attribute name ``header``).
EXPAND_CLASS_REFS = {
    "RadioCommsHeader",
}

# XML class -> {hidden count -> the list its len() reports} where one
# count drives several lists (MinefieldDataPdu: numberOfMinesInThisPdu
# is the mine count; len(mineLocation) is the canonical reading).
COUNT_FOR_OVERRIDES = {
    "MinefieldDataPdu": {
        "numberOfMinesInThisPdu": "mineLocation",
        "numberOfSensorTypes": "sensorTypes",
    },
}

# XML class -> attribute names removed from the resolved record where a
# curated ruling replaces the XML's shape wholesale (TransmitterPdu: the
# XML's objectlists are wrong — the standard allows one MP and one AP
# record; the counts become curated byte-length properties).
FIELD_DROPS = {
    # EnvironmentRecord (XML class "Environment"): length is derived
    # ((8 + geometry) * 8 bits); the curated property owns it
    "Environment": ["length"],
    # §7.6.2 data lengths count 32-bit words and are always derived
    "ElectronicEmitter": ["systemDataLength"],
    "EmitterBeam": ["beamDataLength"],
    "UABeam": ["beamDataLength"],
    "UAEmitter": ["systemDataLength"],
    # §9.3.2: subprotocolNumber rides the header PDU Status byte; the pad
    # byte is the header's own (composed header — LE PDU adds zero bytes)
    "LiveEntityFamilyPdu": ["subprotocolNumber", "padding"],
    # TransmitterPdu: the parameter-records section (MP/AP optional
    # records + the VTP registry list) resolves natively since spec
    # v0.12.9 — only the three hidden counts stay dropped: their
    # properties are curated CLASS_MEMBERS (the byte-length docstrings
    # are hand-ruled, not the XML comments)
    "TransmitterPdu": [
        "variableTransmitterParameterCount",
        "modulationParameterCount",
        "antennaPatternCount",
    ],
    # SV records: the header fields are the kernel base's contract —
    # recordType is the registry ClassVar, recordLength the derived
    # marshalledSize property (§6.2.83)
    # DirectedEnergy* / HighFidelityHAVEQUICKRadio entries RETIRED
    # 2026-10-17: the §6.2.83 signature inference consumes the header
    # fields mechanically (bucket-C item 4)
    # generic SV-format records: the trailing alignment pad rides the
    # payload contract (recordSpecificFields carries K + pad bytes so a
    # stored recordLength stays the wire truth; Intercom precedent)
    "IFFData": ["padding"],
    "Attribute": ["padding"],
}

# (class, XML field name) -> python field name, where the exemplar ruled a
# better name than the XML carries. Count references follow their fields.
FIELD_RENAMES = {
    ("SimulationManagementFamilyPdu", "originatingID"): "originatingEntityID",
    ("SimulationManagementFamilyPdu", "receivingID"): "receivingEntityID",
    ("VariableDatum", "variableDatumValue"): "variableData",
    ("DataQueryPdu", "fixedDatums"): "fixedDatumIDs",
    ("DataQueryPdu", "variableDatums"): "variableDatumIDs",
    ("DataQueryPdu", "numberOfFixedDatumRecords"): "numberOfFixedDatumIDs",
    ("DataQueryPdu", "numberOfVariableDatumRecords"): "numberOfVariableDatumIDs",
    (
        "SimulationManagementWithReliabilityFamilyPdu",
        "originatingID",
    ): "originatingEntityID",
    (
        "SimulationManagementWithReliabilityFamilyPdu",
        "receivingID",
    ): "receivingEntityID",
    ("DataQueryReliablePdu", "fixedDatumRecords"): "fixedDatumIDs",
    ("DataQueryReliablePdu", "variableDatumRecords"): "variableDatumIDs",
    ("DataQueryReliablePdu", "numberOfFixedDatumRecords"): "numberOfFixedDatumIDs",
    (
        "DataQueryReliablePdu",
        "numberOfVariableDatumRecords",
    ): "numberOfVariableDatumIDs",
    # the six IFF-layer count renames RETIRED 2026-10-17: the
    # spec-corrections wave corrected the count names in the XML
    # (v0.11.0 item 5) — the old-name entries died with it
}

# name -> name across every record (uniform-spelling rulings).
GLOBAL_FIELD_RENAMES = {
    "fixedDatums": "fixedDatumRecords",
    "variableDatums": "variableDatumRecords",
}

# XML class -> extra attributes the XML lacks but the wire demands
# (CommentPdu: the fixed-datum count exists without a list; a malformed
# nonzero count would desynchronize parse — the list keeps such
# datagrams round-tripping byte-exact).
# EXTRA_FIELDS is now EMPTY. The TransmitterPdu extras RETIRED 2026-10-17
# (bucket-C item 1, spec v0.12.9): the XML declares the parameter-records
# section natively — the MP/AP variant groups resolve as optional records
# on their §-home bases (resolve._home_optional_group), the VTP list at
# the §6.2.95 home element.
EXTRA_FIELDS = {}

# (class, XML field) -> (annotation, default, rider|None) for fields whose
# shape is fully curated. The LE/IFF presentIf entries RETIRED 2026-10-17
# (bucket-C item 2): the resolver now evaluates presentIf — scalar/record/
# group fields become ``X | None`` unions (absent = None), record variant
# groups emit first-true-wins unions; lists keep empty-list absence
# (minefield dataFilter precedent). Riders that were SISO data moved to
# FIELD_RIDERS. What remains here is shape curation presentIf cannot
# express.
FIELD_OVERRIDES = {
    # the XML's countFieldName="numberOfGridAxes" on the grid-data list is
    # an upstream bug: Table 192's G = V x product of the per-axis point
    # counts — a derived count with no wire field (curated body owns it)
    ("GriddedDataPdu", "gridDataRecords"): (
        "list[GridDataType0 | GridDataType1 | GridDataType2]",
        "field(default_factory=list)",
        None,
    ),
    # recordLength is caller-settable wire state on the generic SV-format
    # records (6 + K + P, Table 138) — not the derived len() property the
    # XML's hidden="true" would emit (Intercom precedent)
    ("Attribute", "recordLength"): ("uint16", "0", None),
}
# (class, XML field name) -> hand-ruled shape replacing the XML's (the
# Data-Query datum-ID rebinding: §7.5.9 lists carry datum IDs, not
# FixedDatum records — the XML's objectlist classRef is wrong there).
FIELD_SHAPES = {
    # the DataQuery datum-ID rebinding RETIRED 2026-10-17: the
    # spec-corrections wave models the 7.5.9 ID lists natively
    # Record Query-R: flat datum-ID list, not RecordQuerySpecification
    # records (§5.12.4.14; the XML's wrapper layer has no wire bytes)
    ("RecordQueryReliablePdu", "recordIDs"): ir.PrimitiveList(
        element="uint32", count_field="numberOfRecords", element_uid=66
    ),
    # Record-R / Set Record-R recordSets RETIRED 2026-10-17: spec
    # v0.12.5's wrapper-as-element fixes classRef the element as
    # RecordSpecificationElement natively (the wrapper layer the
    # bridge peeled off no longer exists in the XML)
    # Data Query-R: datum-ID lists like the §7.5.9 ruling
    ("DataQueryReliablePdu", "fixedDatumRecords"): ir.PrimitiveList(
        element="uint32", count_field="numberOfFixedDatumRecords", element_uid=66
    ),
    ("DataQueryReliablePdu", "variableDatumRecords"): ir.PrimitiveList(
        element="uint32", count_field="numberOfVariableDatumRecords", element_uid=66
    ),
    # minefield per-mine value lists: plain typed primitives, not records
    ("MinefieldQueryPdu", "sensorTypes"): ir.PrimitiveList(
        element="uint16", count_field="numberOfSensorTypes"
    ),
    ("MinefieldDataPdu", "sensorTypes"): ir.PrimitiveList(
        element="uint16", count_field="numberOfSensorTypes"
    ),
    # vertices: one flat list whose total count is the sum of the
    # per-wire numberOfVertices counts (curated methods own the semantics)
    # recordSpecificField: byte payload sized by the STORED recordLength
    # field (caller-settable wire state, not a derived count)
    ("IntercomCommunicationsParameters", "recordSpecificField"): ir.BytesPayload(
        bit_count_field=None
    ),
    # IsGroupOf: category-dependent descriptions (§7.8.3) held as
    # EntityIdentifier entries — the XML's VariableDatum classRef is
    # un-parseable specing (sample-review ruling)
    ("IsGroupOfPdu", "groupedEntityDescriptions"): ir.ObjectList(
        element="EntityIdentifier", count_field="numberOfGroupedEntities"
    ),
    # TransferOwnership recordSets RETIRED 2026-10-17: the v0.11.0
    # correction wave (10991fe) already flattened the XML to a bare
    # RecordSpecificationElement list — redundant since that repin,
    # missed by both bridge-retirement rounds
    # EnvironmentRecord: opaque geometry (bit-count expression length - 64)
    ("Environment", "geometry"): ir.BytesPayload(bit_count_field=None),
    # TSPI system-specific data: byte-counted payload (§9.4.2)
    ("TimeSpacePositionInformationPdu", "systemSpecificData"): ir.BytesPayload(
        bit_count_field="systemSpecificDataLength", count_is_bits=False
    ),
    ("MinefieldDataPdu", "vertices"): ir.ObjectList(
        element="Vector3Float", count_field="numberOfVertices"
    ),
    # Table 183: the Silent Entity System list carries §6.2.79 Silent
    # Entity System records (96 + 32A bits each), not bare EntityType
    # records — the XML's classRef is an upstream gap; standard followed
    # AggregateState silentEntitySystemList shape RETIRED 2026-10-17:
    # the XML now references SilentEntitySystem natively (v0.11.0 item 3)
    # the five layer 3/4/5 list shapes + the count renames RETIRED
    # 2026-10-17 together: the spec-corrections wave renamed the counts
    # and flattened the lists to §6.2.43 IFF Data records natively (the
    # overrides carried the old count names, so they retired in lockstep)
    # generic SV-format records: the payload is byte-granular wire state
    # sized by the STORED recordLength (K + alignment pad as received;
    # IntercomCommunicationsParameters precedent)
    ("IFFData", "recordSpecificFields"): ir.BytesPayload(bit_count_field=None),
    ("Attribute", "recordSpecificFields"): ir.BytesPayload(bit_count_field=None),
    # axis descriptors dispatch on the trailing axisType byte ([UID 377]);
    # the element annotation narrows to the fixed shape (the curated
    # GriddedDataPdu body stores either subclass)
    ("GriddedDataPdu", "gridAxisDescriptors"): ir.ObjectList(
        element="GridAxisDescriptorFixed", count_field="numberOfGridAxes"
    ),
    # the 24 system-specific bits of the §6.2.44 record are a fixed blob
    # (the XML's primitivelist lacks the fixedlength marker)
    ("IFFFundamentalParameterData", "systemSpecificData"): ir.FixedBytes(length=3),
}

# (class, field) -> force the hidden-count treatment (derived len()
# property, never instance state) where the XML forgot hidden="true"
# (the IFF layer classes' copy-pasted count fields).
# FIELD_HIDDEN RETIRED 2026-10-17: the spec-corrections wave (v0.11.0)
# set hidden="true" on the GridAxis variable-axis point count, and the
# IFF layer counts were renamed in the XML (the old-name entries died).
FIELD_HIDDEN = {}

# (class, field) -> uid-66 registry-decoded list: emitted as plain ``list``
# + parseStandardVariableRecord (Standard Variable records are a tagged
# union the registry owns; the XML's objectlist element types the union).
REGISTRY_LISTS = {
    ("DirectedEnergyFirePdu", "dERecords"),
    ("EntityDamageStatusPdu", "damageDescriptionRecords"),
    ("TransmitterPdu", "variableTransmitterParameters"),
    ("InformationOperationsActionPdu", "ioRecords"),
    ("InformationOperationsReportPdu", "ioRecords"),
}

# XML class -> uid-66 recordType dispatch for the typed Standard Variable
# records. SV_RECORDS RETIRED 2026-10-17 (bucket-C item 4): the resolver
# infers is_sv + the dispatch value from the §6.2.83 signature (recordType
# u32 defaultValue + recordLength u16 hidden/recordOctets); the SV-header
# FIELD_DROPS went with it — the signature consumes the two header fields.
SV_RECORD_TYPE_RIDER = "[UID 66] Variable Record Type"

# XML class -> hand base class for records whose protocol home is a hand
# module (like KERNEL_BASES but without the PDU body-method split).
# Empty since the Annex C promotion: BeamAntennaPattern's parent is now
# XML-declared (AntennaPatternRecord, a generated class below).
RECORD_BASES = {}

# XML abstract record class -> (kernel protocol base, module providing
# it). The §6.2.58/§6.2.8/§6.2.95 homes are generated as fieldless
# classes on the kernel record protocol bases (the annexc.py seam's
# roles, promoted 2026-10-16); concrete records subclass them through
# their XML inheritsFrom.
KERNEL_RECORD_BASES = {
    "ModulationParametersRecord": ("VariableRecord", "opendis.record.base"),
    "AntennaPatternRecord": ("VariableRecord", "opendis.record.base"),
    "VariableTransmitterParametersRecord": (
        "StandardVariableRecord",
        "opendis.record.base",
    ),
}

# (class, field) -> bitfield view attached unconditionally at parse.
# VIEW_ATTACHES RETIRED 2026-10-17 (bucket-C items 5+6): the uid keys it —
# a sisobitfield field whose uid has a generated single-layout view
# attaches it mechanically (resolve stamps Attribute.view from the
# REF-010-derived map); the kind/domain-qualified EntityAppearance /
# EntityCapabilities layouts dispatch on entityType in the emitted parse
# tail (emit). Residual: local-name aliases the mechanical lookup can't
# derive (naming choices, not lookups).
VIEW_LOCAL_ALIASES = {
    313: "DEFireFlagsView",  # DEFireFlags imported under a View alias
}

# class -> replacement leading §citation where the XML comment carries
# stale 1995-edition numbering (upstream campaign candidates; the body
# text stays XML-canonical).
DOCSTRING_CITES = {
    # fully RETIRED 2026-10-17: the spec-corrections wave corrected the
    # family cites in the XML (logistics 7.4.x, radio 7.7.x, minefield
    # 7.9.x, entity management 7.8.x, IFF 7.6.5); the IO pair followed
    # in spec v0.12.1 (issue #8 remainder, 5.13.3/4 -> 7.12.2/3). The
    # mechanism stays for future stale-cite finds.
}

# module key -> verbatim import lines emitted after the docstring
# (stdlib imports the curated members need).
MODULE_IMPORT_LINES = {
    "simulation_management": ["import io"],
}

# (class, method) -> full parameter list for curated methods whose
# signatures carry more than the stream (LEMunitionDescriptor.parse,
# the IFF layers' parseLayer).
METHOD_PARAMS = {
    ("LEMunitionDescriptor", "parse"): [
        "cls",
        "inputStream: DataInputStream",
        "includeWarheadFuse: bool",
        "includeQuantityRate: bool",
    ],
    ("IFFPduLayer2Data", "parseLayer"): [
        "cls",
        "inputStream: DataInputStream",
        "layerNumber: int",
        "layerSpecificInformation: int",
        "length: int",
    ],
    ("IFFPduLayer3TransponderFormatData", "parseLayer"): [
        "cls",
        "inputStream: DataInputStream",
        "layerNumber: int",
        "layerSpecificInformation: int",
        "length: int",
    ],
    ("IFFPduLayer3InterrogatorFormatData", "parseLayer"): [
        "cls",
        "inputStream: DataInputStream",
        "layerNumber: int",
        "layerSpecificInformation: int",
        "length: int",
    ],
    ("IFFPduLayer4InterrogatorFormatData", "parseLayer"): [
        "cls",
        "inputStream: DataInputStream",
        "layerNumber: int",
        "layerSpecificInformation: int",
        "length: int",
    ],
    ("IFFPduLayer4TransponderFormatData", "parseLayer"): [
        "cls",
        "inputStream: DataInputStream",
        "layerNumber: int",
        "layerSpecificInformation: int",
        "length: int",
    ],
    ("IFFPduLayer5Data", "parseLayer"): [
        "cls",
        "inputStream: DataInputStream",
        "layerNumber: int",
        "layerSpecificInformation: int",
        "length: int",
    ],
}

# class -> {method name -> verbatim body} replacing mechanical emission
# (bit-count payloads, packer-computed alignment pads, dispatch tails).
METHOD_BODIES = {
    # Annex C.2/C.3: the zero-length MP markers carry no record-specific
    # fields — nothing on the wire (fieldless classes with curated bodies)
    "GenericRadio": {
        "marshalledSize": "return 0",
        "serialize": "pass",
        "parse": "pass",
    },
    "SimpleIntercomRadio": {
        "marshalledSize": "return 0",
        "serialize": "pass",
        "parse": "pass",
    },
    "IFFData": {
        "marshalledSize": "return 6 + len(self.recordSpecificFields)",
        "serialize": """outputStream.write_uint32(self.recordType)
outputStream.write_uint16(self.recordLength)
outputStream.write_bytes(self.recordSpecificFields)""",
        "parse": """self.recordType = rich_or_int(66, inputStream.read_uint32())
self.recordLength = inputStream.read_uint16()
self.recordSpecificFields = inputStream.read_bytes(self.recordLength - 6)""",
    },
    "Attribute": {
        "marshalledSize": "return 6 + len(self.recordSpecificFields)",
        "serialize": """outputStream.write_uint32(self.recordType)
outputStream.write_uint16(self.recordLength)
outputStream.write_bytes(self.recordSpecificFields)""",
        "parse": """self.recordType = inputStream.read_uint32()
self.recordLength = inputStream.read_uint16()
self.recordSpecificFields = inputStream.read_bytes(self.recordLength - 6)""",
    },
    "IdentificationFriendOrFoePdu": {
        "_marshalledBodySize": """size = (
    self.emittingEntityId.marshalledSize()
    + self.eventID.marshalledSize()
    + self.location.marshalledSize()
    + self.systemID.marshalledSize()
    + 1
    + 1
    + self.fundamentalParameters.marshalledSize()
)
size += sum(layer.marshalledSize() for layer in self._layersInOrder())
return size""",
        "_serializeBody": """self.emittingEntityId.serialize(outputStream)
self.eventID.serialize(outputStream)
self.location.serialize(outputStream)
self.systemID.serialize(outputStream)
outputStream.write_uint8(self.systemDesignator)
outputStream.write_uint8(self.systemSpecificData)
self.fundamentalParameters.serialize(outputStream)
for layer in self._layersInOrder():
    layer.layerHeader.length = layer.marshalledSize()
    layer.serialize(outputStream)""",
        "_parseBody": """self.emittingEntityId = EntityIdentifier.parse(inputStream)
self.eventID = EventIdentifier.parse(inputStream)
self.location.parse(inputStream)
self.systemID = SystemIdentifier.parse(inputStream)
self.systemDesignator = inputStream.read_uint8()
self.systemSpecificData = inputStream.read_uint8()
self.fundamentalParameters.parse(inputStream)
# generator: layers 2-5 presence is FLAG-declared — the Layer 1
# Fundamental Operational Data Information Layers bits, one per layer
# (6.2.39 c, 6.2.45 a/Table 74; declared in the XML since v0.12.0) —
# and each layer self-frames with a Layer Header whose Length includes
# the header (Table 165), so the loop reads while wire length remains.
# Format dispatch: _layerIsInterrogator (System Type [UID 82] plus the
# Combined Interrogator/Transponder Change/Options indicator, Table B.5
# bit 4); parseLayer takes the header fields the dispatch consumed
remaining = self.header._wireLength - 12 - 48
while remaining >= 4:
    layerNumber = inputStream.read_uint8()
    layerSpecificInformation = inputStream.read_uint8()
    length = inputStream.read_uint16()
    if layerNumber == 2:
        self.iFFPduLayer2Data = IFFPduLayer2Data.parseLayer(
            inputStream, layerNumber, layerSpecificInformation, length
        )
    elif layerNumber == 3:
        if self._layerIsInterrogator(3):
            self.iFFPduLayer3Data = IFFPduLayer3InterrogatorFormatData.parseLayer(
                inputStream, layerNumber, layerSpecificInformation, length
            )
        else:
            self.iFFPduLayer3Data = IFFPduLayer3TransponderFormatData.parseLayer(
                inputStream, layerNumber, layerSpecificInformation, length
            )
    elif layerNumber == 4:
        if self._layerIsInterrogator(4):
            self.iFFPduLayer4Data = IFFPduLayer4InterrogatorFormatData.parseLayer(
                inputStream, layerNumber, layerSpecificInformation, length
            )
        else:
            self.iFFPduLayer4Data = IFFPduLayer4TransponderFormatData.parseLayer(
                inputStream, layerNumber, layerSpecificInformation, length
            )
    elif layerNumber == 5:
        self.iFFPduLayer5Data = IFFPduLayer5Data.parseLayer(
            inputStream, layerNumber, layerSpecificInformation, length
        )
    else:
        break  # layers 6-7 are not defined; stop before misparsing
    remaining -= length""",
    },
    "GriddedDataPdu": {
        "_marshalledBodySize": """return (
    6
    + 2
    + 2
    + 2
    + 2
    + 1
    + 1
    + self.environmentType.marshalledSize()
    + self.orientation.marshalledSize()
    + self.sampleTime.marshalledSize()
    + 4
    + 1
    + 1
    + 2
    + sum(axis.marshalledSize() for axis in self.gridAxisDescriptors)
    + sum(record.marshalledSize() for record in self.gridDataRecords)
)""",
        "_serializeBody": """self.environmentalSimulationApplicationID.serialize(outputStream)
outputStream.write_uint16(self.fieldNumber)
outputStream.write_uint16(self.pduNumber)
outputStream.write_uint16(self.pduTotal)
outputStream.write_uint16(self.coordinateSystem)
outputStream.write_uint8(self.numberOfGridAxes)
outputStream.write_uint8(self.constantGrid)
self.environmentType.serialize(outputStream)
self.orientation.serialize(outputStream)
self.sampleTime.serialize(outputStream)
outputStream.write_uint32(self.totalValues)
outputStream.write_uint8(self.vectorDimension)
outputStream.write_uint8(self.padding1)
outputStream.write_uint16(self.padding2)
for axis in self.gridAxisDescriptors:
    axis.serialize(outputStream)
for record in self.gridDataRecords:
    record.serialize(outputStream)""",
        "_parseBody": """self.environmentalSimulationApplicationID = EntityIdentifier.parse(
    inputStream
)
self.fieldNumber = inputStream.read_uint16()
self.pduNumber = inputStream.read_uint16()
self.pduTotal = inputStream.read_uint16()
self.coordinateSystem = rich_or_int(244, inputStream.read_uint16())
numberOfGridAxes = inputStream.read_uint8()
self.constantGrid = rich_or_int(245, inputStream.read_uint8())
self.environmentType = EntityType.parse(inputStream)
self.orientation.parse(inputStream)
self.sampleTime.parse(inputStream)
self.totalValues = inputStream.read_uint32()
self.vectorDimension = inputStream.read_uint8()
self.padding1 = inputStream.read_uint8()
self.padding2 = inputStream.read_uint16()
# generator: axis descriptors dispatch on their trailing axisType byte
# ([UID 377]: 0 = regular/fixed, 1 = irregular/variable) — the XML's
# initialClass hint carries no wire semantics
self.gridAxisDescriptors = []
for _ in range(numberOfGridAxes):
    domainInitialXi = inputStream.read_float64()
    domainFinalXi = inputStream.read_float64()
    domainPointsXi = inputStream.read_uint16()
    interleafFactor = inputStream.read_uint8()
    axisType = inputStream.read_uint8()
    if int(axisType) == 1:
        axis = GridAxisDescriptorVariable(
            domainInitialXi,
            domainFinalXi,
            domainPointsXi,
            interleafFactor,
            axisType,
        )
        numberOfPointsOnXiAxis = inputStream.read_uint16()
        axis.initialIndex = inputStream.read_uint16()
        axis.coordinateScaleXi = inputStream.read_float64()
        axis.coordinateOffsetXi = inputStream.read_float64()
        axis.xiValues = [
            inputStream.read_uint16()
            for _ in range(numberOfPointsOnXiAxis)
        ]
        padding = _padTo64(40 + 2 * len(axis.xiValues))
        if padding:
            inputStream.read_bytes(padding)
    else:
        axis = GridAxisDescriptorFixed(
            domainInitialXi,
            domainFinalXi,
            domainPointsXi,
            interleafFactor,
            axisType,
        )
        axis.numberOfPointsOnXiAxis = inputStream.read_uint16()
        axis.initialIndex = inputStream.read_uint16()
    self.gridAxisDescriptors.append(axis)
# generator: Table 192's G = V x product of the per-axis point counts —
# the record count is derived, not stored (the XML's
# countFieldName="numberOfGridAxes" is an upstream bug)
dataCount = self.vectorDimension
for axis in self.gridAxisDescriptors:
    dataCount *= axis.numberOfPointsOnXiAxis
self.gridDataRecords = []
for _ in range(dataCount):
    sampleType = inputStream.read_uint16()
    dataRepresentation = inputStream.read_uint16()
    # generator: representation types 3-6 have no record format
    # (§6.2.41 defines 0-2 only); stop before misparsing the rest
    if int(dataRepresentation) == 0:
        record = GridDataType0(sampleType, dataRepresentation)
        numberOfBytes = inputStream.read_uint16()
        record.dataValues = [
            inputStream.read_uint8() for _ in range(numberOfBytes)
        ]
        padding = _padTo16(6 + len(record.dataValues))
        if padding:
            inputStream.read_bytes(padding)
    elif int(dataRepresentation) == 1:
        record = GridDataType1(sampleType, dataRepresentation)
        record.fieldScale = inputStream.read_float32()
        record.fieldOffset = inputStream.read_float32()
        numberOfValues = inputStream.read_uint16()
        record.dataValues = [
            inputStream.read_uint16() for _ in range(numberOfValues)
        ]
        padding = _padTo32(10 + 2 * len(record.dataValues))
        if padding:
            inputStream.read_bytes(padding)
    elif int(dataRepresentation) == 2:
        record = GridDataType2(sampleType, dataRepresentation)
        numberOfValues = inputStream.read_uint16()
        record.padding = inputStream.read_uint16()
        record.dataValues = [
            inputStream.read_float32() for _ in range(numberOfValues)
        ]
    else:
        break
    self.gridDataRecords.append(record)""",
    },
    "VariableDatum": {
        "marshalledSize": "return 8 + _paddedDatumSize(len(self.variableData))",
        "serialize": """outputStream.write_uint32(self.variableDatumID)
outputStream.write_uint32(self.variableDatumLength)
outputStream.write_bytes(self.variableData)
padding = _paddedDatumSize(len(self.variableData)) - len(self.variableData)
if padding:
    outputStream.write_bytes(b"\\x00" * padding)""",
        "parse": """self.variableDatumID = rich_or_int(66, inputStream.read_uint32())
variableDatumLength = inputStream.read_uint32()
self.variableData = inputStream.read_bytes(variableDatumLength // 8)
padding = _paddedDatumSize(len(self.variableData)) - len(self.variableData)
if padding:
    inputStream.read_bytes(padding)""",
    },
    "MinefieldDataPdu": {
        "_marshalledBodySize": """n = self.numberOfMinesInThisPdu
s = self.numberOfSensorTypes
consumed = 12 + self._prefixSize()
consumed += _padTo32(consumed)  # padTo32 after sensor types
consumed += 12 * n  # mineLocation
if self.groundPresent:
    consumed += 4 * n
if self._filter(self.WATER):
    consumed += 4 * n
if self._filter(self.SNOW):
    consumed += 4 * n
if self.orientationPresent:
    consumed += 12 * n
if self._filter(self.THERMAL):
    consumed += 4 * n
if self._filter(self.REFLECTANCE):
    consumed += 4 * n
if self._filter(self.EMPLACEMENT):
    consumed += 8 * n
consumed += 2 * n  # mineEntityNumber (unconditional)
if self._filter(self.FUSING):
    consumed += 2 * n
if self._filter(self.SCALAR):
    consumed += n * s
if self._filter(self.PAINT):
    consumed += n
consumed += _padTo32(consumed)  # padTo32_2
if self._filter(self.WIRES):
    consumed += n  # per-mine wire counts
    consumed += _padTo32(consumed)  # padTo32_3
    consumed += len(self.numberOfVertices)  # per-wire vertex counts
    consumed += _padTo32(consumed)  # padTo32_4
    consumed += 12 * self._wireVertexCount()
return consumed - 12""",
        "_serializeBody": """n = self.numberOfMinesInThisPdu
consumed = 12 + self._prefixSize()
self.minefieldID.serialize(outputStream)
self.requestingEntityID.serialize(outputStream)
outputStream.write_uint16(self.minefieldSequenceNumber)
outputStream.write_uint8(self.requestID)
outputStream.write_uint8(self.pduSequenceNumber)
outputStream.write_uint8(self.numberOfPdus)
outputStream.write_uint8(self.numberOfMinesInThisPdu)
outputStream.write_uint8(self.numberOfSensorTypes)
outputStream.write_uint8(self.padding)
outputStream.write_uint32(self.dataFilter)
self.mineType.serialize(outputStream)
for sensorType in self.sensorTypes:
    outputStream.write_uint16(sensorType)

def pad() -> None:
    nonlocal consumed
    padding = _padTo32(consumed)
    if padding:
        outputStream.write_bytes(b"\\x00" * padding)
        consumed += padding

def writeFloats(values: list) -> None:
    nonlocal consumed
    for value in values:
        outputStream.write_float32(value)
    consumed += 4 * len(values)

pad()  # padTo32 after sensor types
for location in self.mineLocation:
    location.serialize(outputStream)
consumed += 12 * n
if self.groundPresent:
    writeFloats(self.groundBurialDepthOffset)
if self._filter(self.WATER):
    writeFloats(self.waterBurialDepthOffset)
if self._filter(self.SNOW):
    writeFloats(self.snowBurialDepthOffset)
if self.orientationPresent:
    for orientation in self.mineOrientation:
        orientation.serialize(outputStream)
    consumed += 12 * n
if self._filter(self.THERMAL):
    writeFloats(self.thermalContrast)
if self._filter(self.REFLECTANCE):
    writeFloats(self.reflectance)
if self._filter(self.EMPLACEMENT):
    for time in self.mineEmplacementTime:
        time.serialize(outputStream)
    consumed += 8 * n
for entityNumber in self.mineEntityNumber:
    outputStream.write_uint16(entityNumber)
consumed += 2 * n
if self._filter(self.FUSING):
    for value in self.fusing:
        outputStream.write_uint16(value)
    consumed += 2 * n
if self._filter(self.SCALAR):
    for value in self.scalarDetectionCoefficient:
        outputStream.write_uint8(value)
    consumed += n * self.numberOfSensorTypes
if self._filter(self.PAINT):
    for value in self.paintScheme:
        outputStream.write_uint8(value)
    consumed += n
pad()  # padTo32_2
if self._filter(self.WIRES):
    for count in self.numberOfTripDetonationWires:
        outputStream.write_uint8(count)
    consumed += n
    pad()  # padTo32_3
    for count in self.numberOfVertices:
        outputStream.write_uint8(count)
    consumed += len(self.numberOfVertices)
    pad()  # padTo32_4
    for vertex in self.vertices:
        vertex.serialize(outputStream)
    consumed += 12 * len(self.vertices)""",
        "_parseBody": """self.minefieldID = MinefieldIdentifier.parse(inputStream)
self.requestingEntityID = EntityIdentifier.parse(inputStream)
self.minefieldSequenceNumber = inputStream.read_uint16()
self.requestID = inputStream.read_uint8()
self.pduSequenceNumber = inputStream.read_uint8()
self.numberOfPdus = inputStream.read_uint8()
numberOfMinesInThisPdu = inputStream.read_uint8()
numberOfSensorTypes = inputStream.read_uint8()
self.padding = inputStream.read_uint8()
self.dataFilter = inputStream.read_uint32()
self.mineType = EntityType.parse(inputStream)
self.sensorTypes = [
    inputStream.read_uint16() for _ in range(numberOfSensorTypes)
]
consumed = 12 + self._prefixSize()

def pad() -> None:
    nonlocal consumed
    padding = _padTo32(consumed)
    if padding:
        inputStream.read_bytes(padding)
        consumed += padding

def readFloats(count: int) -> list:
    nonlocal consumed
    values = [inputStream.read_float32() for _ in range(count)]
    consumed += 4 * count
    return values

pad()  # padTo32 after sensor types
self.mineLocation = []
for _ in range(numberOfMinesInThisPdu):
    location = Vector3Float()
    location.parse(inputStream)
    self.mineLocation.append(location)
consumed += 12 * numberOfMinesInThisPdu
if self.groundPresent:
    self.groundBurialDepthOffset = readFloats(numberOfMinesInThisPdu)
if self._filter(self.WATER):
    self.waterBurialDepthOffset = readFloats(numberOfMinesInThisPdu)
if self._filter(self.SNOW):
    self.snowBurialDepthOffset = readFloats(numberOfMinesInThisPdu)
if self.orientationPresent:
    self.mineOrientation = []
    for _ in range(numberOfMinesInThisPdu):
        orientation = EulerAngles()
        orientation.parse(inputStream)
        self.mineOrientation.append(orientation)
    consumed += 12 * numberOfMinesInThisPdu
if self._filter(self.THERMAL):
    self.thermalContrast = readFloats(numberOfMinesInThisPdu)
if self._filter(self.REFLECTANCE):
    self.reflectance = readFloats(numberOfMinesInThisPdu)
if self._filter(self.EMPLACEMENT):
    self.mineEmplacementTime = [
        MineEmplacementTime.parseFrom(inputStream)
        for _ in range(numberOfMinesInThisPdu)
    ]
    consumed += 8 * numberOfMinesInThisPdu
self.mineEntityNumber = [
    inputStream.read_uint16() for _ in range(numberOfMinesInThisPdu)
]
consumed += 2 * numberOfMinesInThisPdu
if self._filter(self.FUSING):
    self.fusing = [
        inputStream.read_uint16() for _ in range(numberOfMinesInThisPdu)
    ]
    consumed += 2 * numberOfMinesInThisPdu
if self._filter(self.SCALAR):
    count = numberOfMinesInThisPdu * numberOfSensorTypes
    self.scalarDetectionCoefficient = [
        inputStream.read_uint8() for _ in range(count)
    ]
    consumed += count
if self._filter(self.PAINT):
    self.paintScheme = [
        inputStream.read_uint8() for _ in range(numberOfMinesInThisPdu)
    ]
    consumed += numberOfMinesInThisPdu
pad()  # padTo32_2
if self._filter(self.WIRES):
    self.numberOfTripDetonationWires = [
        inputStream.read_uint8() for _ in range(numberOfMinesInThisPdu)
    ]
    consumed += numberOfMinesInThisPdu
    pad()  # padTo32_3
    wireTotal = sum(self.numberOfTripDetonationWires)
    self.numberOfVertices = [inputStream.read_uint8() for _ in range(wireTotal)]
    consumed += wireTotal
    pad()  # padTo32_4
    self.vertices = []
    for _ in range(self._wireVertexCount()):
        vertex = Vector3Float()
        vertex.parse(inputStream)
        self.vertices.append(vertex)""",
    },
    "ElectronicEmitter": {
        "marshalledSize": """return (
    1
    + 1
    + 2
    + self.emitterSystem.marshalledSize()
    + self.location.marshalledSize()
    + sum(beam.marshalledSize() for beam in self.beams)
)""",
        "serialize": """outputStream.write_uint8(self.systemDataLength)
outputStream.write_uint8(self.numberOfBeams)
outputStream.write_uint16(self.padding)
self.emitterSystem.serialize(outputStream)
self.location.serialize(outputStream)
for beam in self.beams:
    beam.serialize(outputStream)""",
        "parse": """inputStream.read_uint8()  # systemDataLength (derived on re-serialize)
numberOfBeams = inputStream.read_uint8()
self.padding = inputStream.read_uint16()
self.emitterSystem = EmitterSystem()
self.emitterSystem.parse(inputStream)
self.location.parse(inputStream)
self.beams = []
for _ in range(numberOfBeams):
    beam = EmitterBeam()
    beam.parse(inputStream)
    self.beams.append(beam)""",
    },
    "EmitterBeam": {
        "marshalledSize": """return (
    1
    + 1
    + 2  # beamDataLength + beamNumber + parameter index
    + self.fundamentalParameterData.marshalledSize()
    + self.beamData.marshalledSize()
    + 1
    + 1
    + 1
    + self.beamStatus.marshalledSize()
    + self.jammingTechnique.marshalledSize()
    + sum(tj.marshalledSize() for tj in self.trackJamData)
)""",
        "serialize": """outputStream.write_uint8(self.beamDataLength)
outputStream.write_uint8(self.beamNumber)
outputStream.write_uint16(self.beamParameterIndex)
self.fundamentalParameterData.serialize(outputStream)
self.beamData.serialize(outputStream)
outputStream.write_uint8(self.beamFunction)
outputStream.write_uint8(self.numberOfTargets)
outputStream.write_uint8(self.highDensityTrackJam)
self.beamStatus.serialize(outputStream)
self.jammingTechnique.serialize(outputStream)
for trackJam in self.trackJamData:
    trackJam.serialize(outputStream)""",
        "parse": """inputStream.read_uint8()  # beamDataLength (derived on re-serialize)
self.beamNumber = inputStream.read_uint8()
self.beamParameterIndex = inputStream.read_uint16()
self.fundamentalParameterData.parse(inputStream)
self.beamData.parse(inputStream)
self.beamFunction = rich_or_int(78, inputStream.read_uint8())
numberOfTargets = inputStream.read_uint8()
self.highDensityTrackJam = rich_or_int(79, inputStream.read_uint8())
self.beamStatus = BeamStatus()
self.beamStatus.parse(inputStream)
self.jammingTechnique = JammingTechnique()
self.jammingTechnique.parse(inputStream)
self.trackJamData = [
    TrackJamData.parse(inputStream) for _ in range(numberOfTargets)
]""",
    },
    "UABeam": {
        "marshalledSize": "return 1 + 1 + 2 + self.fundamentalParameterData.marshalledSize()",
        "serialize": """outputStream.write_uint8(self.beamDataLength)
outputStream.write_uint8(self.beamNumber)
outputStream.write_uint16(self.padding)
self.fundamentalParameterData.serialize(outputStream)""",
        "parse": """inputStream.read_uint8()  # beamDataLength (derived on re-serialize)
self.beamNumber = inputStream.read_uint8()
self.padding = inputStream.read_uint16()
self.fundamentalParameterData.parse(inputStream)""",
    },
    "UAEmitter": {
        "marshalledSize": """return (
    1
    + 1
    + 2
    + self.acousticEmitter.marshalledSize()
    + self.location.marshalledSize()
    + sum(beam.marshalledSize() for beam in self.beams)
)""",
        "serialize": """outputStream.write_uint8(self.systemDataLength)
outputStream.write_uint8(self.numberOfBeams)
outputStream.write_uint16(self.padding)
self.acousticEmitter.serialize(outputStream)
self.location.serialize(outputStream)
for beam in self.beams:
    beam.serialize(outputStream)""",
        "parse": """inputStream.read_uint8()  # systemDataLength (derived on re-serialize)
numberOfBeams = inputStream.read_uint8()
self.padding = inputStream.read_uint16()
self.acousticEmitter = AcousticEmitter()
self.acousticEmitter.parse(inputStream)
self.location.parse(inputStream)
self.beams = []
for _ in range(numberOfBeams):
    beam = UABeam()
    beam.parse(inputStream)
    self.beams.append(beam)""",
    },
    "LEMunitionDescriptor": {
        "marshalledSize": """size = self.munitionType.marshalledSize()
if self.warhead is not None:
    size += 2
if self.fuse is not None:
    size += 2
if self.quantity is not None:
    size += 2
if self.rate is not None:
    size += 2
return size""",
        "serialize": """self.munitionType.serialize(outputStream)
if self.warhead is not None:
    outputStream.write_uint16(self.warhead)
if self.fuse is not None:
    outputStream.write_uint16(self.fuse)
if self.quantity is not None:
    outputStream.write_uint16(self.quantity)
if self.rate is not None:
    outputStream.write_uint16(self.rate)""",
        "parse": """descriptor = cls()
descriptor.munitionType = EntityType.parse(inputStream)
if includeWarheadFuse:
    descriptor.warhead = rich_or_int(60, inputStream.read_uint16())
    descriptor.fuse = rich_or_int(61, inputStream.read_uint16())
if includeQuantityRate:
    descriptor.quantity = inputStream.read_uint16()
    descriptor.rate = inputStream.read_uint16()
return descriptor""",
    },
    "AppearancePdu": {
        "_marshalledBodySize": """size = self.liveEntityId.marshalledSize() + 2
for value in (self.appearanceFlag2, self.forceId):
    if value is not None:
        size += 1
for record in (self.entityType, self.alternateEntityType):
    if record is not None:
        size += record.marshalledSize()
if self.entityMarking is not None:
    size += self.entityMarking.marshalledSize()
for value in (
    self.capabilities,
    self.appearanceVisual,
    self.appearanceIR,
    self.appearanceEM,
    self.appearanceAudio,
):
    if value is not None:
        size += 4
return size""",
        "_serializeBody": """self.liveEntityId.serialize(outputStream)
outputStream.write_uint16(self.appearanceFlag1)
if self.appearanceFlag2 is not None:
    outputStream.write_uint8(self.appearanceFlag2)
if self.forceId is not None:
    outputStream.write_uint8(self.forceId)
if self.entityType is not None:
    self.entityType.serialize(outputStream)
if self.alternateEntityType is not None:
    self.alternateEntityType.serialize(outputStream)
if self.entityMarking is not None:
    self.entityMarking.serialize(outputStream)
if self.capabilities is not None:
    outputStream.write_uint32(self.capabilities)
if self.appearanceVisual is not None:
    outputStream.write_uint32(self.appearanceVisual)
if self.appearanceIR is not None:
    outputStream.write_uint32(self.appearanceIR)
if self.appearanceEM is not None:
    outputStream.write_uint32(self.appearanceEM)
if self.appearanceAudio is not None:
    outputStream.write_uint32(self.appearanceAudio)""",
        "_parseBody": """flag2Available = False
self.liveEntityId = LiveEntityIdentifier.parse(inputStream)
self.appearanceFlag1 = inputStream.read_uint16()
flag1 = self.appearanceFlag1
if flag1 & (1 << 7):
    self.appearanceFlag2 = inputStream.read_uint8()
    flag2Available = True
if flag1 & (1 << 0):
    self.forceId = rich_or_int(6, inputStream.read_uint8())
if flag1 & (1 << 1):
    self.entityType = EntityType.parse(inputStream)
if flag1 & (1 << 2):
    self.alternateEntityType = EntityType.parse(inputStream)
if flag1 & (1 << 3):
    self.entityMarking = EntityMarking()
    self.entityMarking.parse(inputStream)
if flag1 & (1 << 4):
    self.capabilities = inputStream.read_uint32()
if flag1 & (1 << 5):
    self.appearanceVisual = inputStream.read_uint32()
if flag1 & (1 << 6):
    self.appearanceIR = inputStream.read_uint32()
if flag2Available and self.appearanceFlag2 & (1 << 0):
    self.appearanceEM = inputStream.read_uint32()
if flag2Available and self.appearanceFlag2 & (1 << 1):
    self.appearanceAudio = inputStream.read_uint32()""",
    },
    "LiveEntityFirePdu": {
        "_marshalledBodySize": """size = (
    self.firingLiveEntityId.marshalledSize()
    + 1
    + self.eventId.marshalledSize()
    + self.munitionDescriptor.marshalledSize()
    + self.velocity.marshalledSize()
    + 2
)
if self.targetLiveEntityId is not None:
    size += self.targetLiveEntityId.marshalledSize()
if self.munitionLiveEntityId is not None:
    size += self.munitionLiveEntityId.marshalledSize()
if self.location is not None:
    size += self.location.marshalledSize()
return size""",
        "_serializeBody": """self.firingLiveEntityId.serialize(outputStream)
outputStream.write_uint8(self.fireFlag)
if self.targetLiveEntityId is not None:
    self.targetLiveEntityId.serialize(outputStream)
if self.munitionLiveEntityId is not None:
    self.munitionLiveEntityId.serialize(outputStream)
self.eventId.serialize(outputStream)
if self.location is not None:
    self.location.serialize(outputStream)
self.munitionDescriptor.serialize(outputStream)
self.velocity.serialize(outputStream)
outputStream.write_uint16(self.range)""",
        "_parseBody": """self.firingLiveEntityId = LiveEntityIdentifier.parse(inputStream)
fireFlag = inputStream.read_uint8()
self.fireFlag = fireFlag
if fireFlag & (1 << 0):
    self.targetLiveEntityId = LiveEntityIdentifier.parse(inputStream)
if fireFlag & (1 << 2):
    if fireFlag & (1 << 1):
        self.munitionLiveEntityId = LiveEntityIdentifier.parse(inputStream)
    else:
        self.munitionLiveEntityId = LiveEntityIdentifierElided.parse(inputStream)
if fireFlag & (1 << 3):
    self.eventId = EventIdentifierLiveEntity.parse(inputStream)
else:
    self.eventId = EventIdentifierLiveEntityElided.parse(inputStream)
if fireFlag & (1 << 6):
    self.location = LiveEntityRelativeWorldCoordinates()
    self.location.parse(inputStream)
self.munitionDescriptor = LEMunitionDescriptor.parse(
    inputStream,
    includeWarheadFuse=bool(fireFlag & (1 << 4)),
    includeQuantityRate=bool(fireFlag & (1 << 5)),
)
self.velocity.parse(inputStream)
self.range = inputStream.read_uint16()""",
    },
    "LiveEntityDetonationPdu": {
        "_marshalledBodySize": """size = (
    self.firingLiveEntityId.marshalledSize()
    + 1
    + self.velocity.marshalledSize()
    + self.munitionDescriptor.marshalledSize()
    + 1
)
if self.detonationFlag2 is not None:
    size += 1
if self.targetLiveEntityId is not None:
    size += self.targetLiveEntityId.marshalledSize()
if self.munitionLiveEntityId is not None:
    size += self.munitionLiveEntityId.marshalledSize()
if self.eventId is not None:
    size += self.eventId.marshalledSize()
if self.worldLocation is not None:
    size += self.worldLocation.marshalledSize()
if self.munitionOrientation is not None:
    size += self.munitionOrientation.marshalledSize()
if self.entityLocation is not None:
    size += self.entityLocation.marshalledSize()
return size""",
        "_serializeBody": """self.firingLiveEntityId.serialize(outputStream)
outputStream.write_uint8(self.detonationFlag1)
if self.detonationFlag2 is not None:
    outputStream.write_uint8(self.detonationFlag2)
if self.targetLiveEntityId is not None:
    self.targetLiveEntityId.serialize(outputStream)
if self.munitionLiveEntityId is not None:
    self.munitionLiveEntityId.serialize(outputStream)
if self.eventId is not None:
    self.eventId.serialize(outputStream)
if self.worldLocation is not None:
    self.worldLocation.serialize(outputStream)
self.velocity.serialize(outputStream)
if self.munitionOrientation is not None:
    self.munitionOrientation.serialize(outputStream)
self.munitionDescriptor.serialize(outputStream)
if self.entityLocation is not None:
    self.entityLocation.serialize(outputStream)
outputStream.write_uint8(self.detonationResult)""",
        "_parseBody": """self.firingLiveEntityId = LiveEntityIdentifier.parse(inputStream)
detonationFlag1 = inputStream.read_uint8()
self.detonationFlag1 = detonationFlag1
flag2 = detonationFlag1 & (1 << 7)
detonationFlag2 = 0
if flag2:
    detonationFlag2 = inputStream.read_uint8()
    self.detonationFlag2 = detonationFlag2
if detonationFlag1 & (1 << 0):
    self.targetLiveEntityId = LiveEntityIdentifier.parse(inputStream)
if detonationFlag1 & (1 << 2):
    if detonationFlag1 & (1 << 1):
        self.munitionLiveEntityId = LiveEntityIdentifier.parse(inputStream)
    else:
        self.munitionLiveEntityId = LiveEntityIdentifierElided.parse(inputStream)
if flag2 and detonationFlag2 & (1 << 1):
    if detonationFlag1 & (1 << 3):
        self.eventId = EventIdentifierLiveEntity.parse(inputStream)
    else:
        self.eventId = EventIdentifierLiveEntityElided.parse(inputStream)
if not detonationFlag1 & (1 << 6):
    self.worldLocation = LiveEntityRelativeWorldCoordinates()
    self.worldLocation.parse(inputStream)
self.velocity.parse(inputStream)
if flag2 and detonationFlag2 & (1 << 0):
    self.munitionOrientation = LiveEntityOrientation16()
    self.munitionOrientation.parse(inputStream)
self.munitionDescriptor = LEMunitionDescriptor.parse(
    inputStream,
    includeWarheadFuse=bool(detonationFlag1 & (1 << 4)),
    includeQuantityRate=bool(detonationFlag1 & (1 << 5)),
)
if detonationFlag1 & (1 << 6):
    self.entityLocation = LiveEntityRelativeEntityCoordinates()
    self.entityLocation.parse(inputStream)
self.detonationResult = rich_or_int(62, inputStream.read_uint8())""",
    },
    "AggregateStatePdu": {
        "_marshalledBodySize": """idLists = sum(a.marshalledSize() for a in self.aggregateIDList) + sum(
    e.marshalledSize() for e in self.entityIDList
)
size = (
    self._prefixSize()
    + idLists
    + _padTo32(12 + self._prefixSize() + idLists)
    + sum(t.marshalledSize() for t in self.silentAggregateSystemList)
    + sum(t.marshalledSize() for t in self.silentEntitySystemList)
    + 4
    + sum(vd.marshalledSize() for vd in self.variableDatumList)
)
return size""",
        "_serializeBody": """self.aggregateID.serialize(outputStream)
outputStream.write_uint8(self.forceID)
outputStream.write_uint8(self.aggregateState)
self.aggregateType.serialize(outputStream)
outputStream.write_uint32(self.formation)
self.aggregateMarking.serialize(outputStream)
self.dimensions.serialize(outputStream)
self.orientation.serialize(outputStream)
self.centerOfMass.serialize(outputStream)
self.velocity.serialize(outputStream)
outputStream.write_uint16(self.numberOfDisAggregates)
outputStream.write_uint16(self.numberOfDisEntities)
outputStream.write_uint16(self.numberOfSilentAggregateTypes)
outputStream.write_uint16(self.numberOfSilentEntityTypes)
for aggregate in self.aggregateIDList:
    aggregate.serialize(outputStream)
for entity in self.entityIDList:
    entity.serialize(outputStream)
idLists = sum(a.marshalledSize() for a in self.aggregateIDList) + sum(
    e.marshalledSize() for e in self.entityIDList
)
padding = _padTo32(12 + self._prefixSize() + idLists)
if padding:
    outputStream.write_bytes(b"\\x00" * padding)
for aggregateType in self.silentAggregateSystemList:
    aggregateType.serialize(outputStream)
for entityType in self.silentEntitySystemList:
    entityType.serialize(outputStream)
outputStream.write_uint32(self.numberOfVariableDatumRecords)
for datum in self.variableDatumList:
    datum.serialize(outputStream)""",
        "_parseBody": """self.aggregateID = AggregateIdentifier.parse(inputStream)
self.forceID = rich_or_int(6, inputStream.read_uint8())
self.aggregateState = rich_or_int(204, inputStream.read_uint8())
self.aggregateType = AggregateType.parse(inputStream)
self.formation = rich_or_int(205, inputStream.read_uint32())
self.aggregateMarking = AggregateMarking()
self.aggregateMarking.parse(inputStream)
self.dimensions.parse(inputStream)
self.orientation.parse(inputStream)
self.centerOfMass.parse(inputStream)
self.velocity.parse(inputStream)
numberOfDisAggregates = inputStream.read_uint16()
numberOfDisEntities = inputStream.read_uint16()
numberOfSilentAggregateTypes = inputStream.read_uint16()
numberOfSilentEntityTypes = inputStream.read_uint16()
self.aggregateIDList = [
    AggregateIdentifier.parse(inputStream) for _ in range(numberOfDisAggregates)
]
self.entityIDList = [
    EntityIdentifier.parse(inputStream) for _ in range(numberOfDisEntities)
]
idLists = 6 * numberOfDisAggregates + 6 * numberOfDisEntities
padding = _padTo32(12 + self._prefixSize() + idLists)
if padding:
    inputStream.read_bytes(padding)
self.silentAggregateSystemList = [
    SilentAggregateSystem.parseFrom(inputStream)
    for _ in range(numberOfSilentAggregateTypes)
]
self.silentEntitySystemList = [
    SilentEntitySystem.parseFrom(inputStream)
    for _ in range(numberOfSilentEntityTypes)
]
numberOfVariableDatumRecords = inputStream.read_uint32()
self.variableDatumList = [
    VariableDatum.parseFrom(inputStream)
    for _ in range(numberOfVariableDatumRecords)
]""",
    },
    "EnvironmentRecord": {
        "marshalledSize": "return 8 + len(self.geometry) + self._padTo64(len(self.geometry))",
        "serialize": """outputStream.write_uint32(self.environmentType)
outputStream.write_uint16(self.length)
outputStream.write_uint8(self.index)
outputStream.write_uint8(self.padding1)
outputStream.write_bytes(self.geometry)
padding = self._padTo64(len(self.geometry))
if padding:
    outputStream.write_bytes(b"\\x00" * padding)""",
        "parse": """self.environmentType = rich_or_int(250, inputStream.read_uint32())
length = inputStream.read_uint16()  # bits, header included
self.index = inputStream.read_uint8()
self.padding1 = inputStream.read_uint8()
geometryBytes = max(0, length // 8 - 8)
self.geometry = inputStream.read_bytes(geometryBytes)
padding = self._padTo64(geometryBytes)
if padding:
    inputStream.read_bytes(padding)""",
    },
    "IntercomCommunicationsParameters": {
        "marshalledSize": "return 4 + len(self.recordSpecificField)",
        "serialize": """outputStream.write_uint16(self.recordType)
outputStream.write_uint16(self.recordLength)
outputStream.write_bytes(self.recordSpecificField)""",
        "parse": """self.recordType = rich_or_int(185, inputStream.read_uint16())
self.recordLength = inputStream.read_uint16()
self.recordSpecificField = inputStream.read_bytes(self.recordLength)""",
    },
    "TransmitterPdu": {
        "_marshalledBodySize": """size = (
    self.radioReferenceID.marshalledSize()
    + 2
    + self.radioEntityType.marshalledSize()
    + 1
    + 1
    + 2  # variableTransmitterParameterCount
    + self.antennaLocation.marshalledSize()
    + self.relativeAntennaLocation.marshalledSize()
    + 2
    + 2  # antennaPatternType + antennaPatternCount
    + 8
    + 4
    + 4
    + self.modulationType.marshalledSize()
    + 2
    + 2  # cryptoSystem + cryptoKeyId
    + 1
    + 1
    + 2
)  # modulationParameterCount + pads
if self.modulationParameters is not None:
    size += self.modulationParameters.marshalledSize()
if self.antennaPattern is not None:
    size += self.antennaPattern.marshalledSize()
size += sum(vtp.marshalledSize() for vtp in self.variableTransmitterParameters)
return size""",
        "_serializeBody": """self.radioReferenceID.serialize(outputStream)
outputStream.write_uint16(self.radioNumber)
self.radioEntityType.serialize(outputStream)
outputStream.write_uint8(self.transmitState)
outputStream.write_uint8(self.inputSource)
outputStream.write_uint16(self.variableTransmitterParameterCount)
self.antennaLocation.serialize(outputStream)
self.relativeAntennaLocation.serialize(outputStream)
outputStream.write_uint16(self.antennaPatternType)
outputStream.write_uint16(self.antennaPatternCount)
outputStream.write_uint64(self.frequency)
outputStream.write_float32(self.transmitFrequencyBandwidth)
outputStream.write_float32(self.power)
self.modulationType.serialize(outputStream)
outputStream.write_uint16(self.cryptoSystem)
outputStream.write_uint16(self.cryptoKeyId)
outputStream.write_uint8(self.modulationParameterCount)
outputStream.write_uint8(self.padding1)
outputStream.write_uint16(self.padding2)
if self.modulationParameters is not None:
    self.modulationParameters.serialize(outputStream)
if self.antennaPattern is not None:
    self.antennaPattern.serialize(outputStream)
for vtp in self.variableTransmitterParameters:
    vtp.serialize(outputStream)""",
        "_parseBody": """self.radioReferenceID = EntityIdentifier.parse(inputStream)
self.radioNumber = inputStream.read_uint16()
self.radioEntityType = EntityType.parse(inputStream)
self.transmitState = rich_or_int(164, inputStream.read_uint8())
self.inputSource = rich_or_int(165, inputStream.read_uint8())
variableTransmitterParameterCount = inputStream.read_uint16()
self.antennaLocation.parse(inputStream)
self.relativeAntennaLocation.parse(inputStream)
self.antennaPatternType = rich_or_int(167, inputStream.read_uint16())
antennaPatternLength = inputStream.read_uint16()
self.frequency = inputStream.read_uint64()
self.transmitFrequencyBandwidth = inputStream.read_float32()
self.power = inputStream.read_float32()
self.modulationType = ModulationType()
self.modulationType.parse(inputStream)
self.cryptoSystem = rich_or_int(166, inputStream.read_uint16())
self.cryptoKeyId = inputStream.read_uint16()
modulationParametersLength = inputStream.read_uint8()
self.padding1 = inputStream.read_uint8()
self.padding2 = inputStream.read_uint16()

# generator: single-record MP/AP dispatch is beyond mechanical
# generation (record boundaries depend on the radio system and
# antenna pattern type)
if modulationParametersLength > 0:
    radioSystem = int(self.modulationType.radioSystem)
    if radioSystem == 1:  # generic radio or simple intercom
        radio = (
            SimpleIntercomRadio()
            if int(self.modulationType.majorModulation) == 0
            else GenericRadio()
        )
        radio.parse(inputStream)
    elif radioSystem in (2, 3, 4):  # HAVE QUICK I/II/IIA
        radio = BasicHaveQuickMP()
        radio.parse(inputStream)
    elif radioSystem == 6:  # CCTT SINCGARS
        radio = CCTTSincgarsMP()
        radio.parse(inputStream)
    else:
        radio = UnknownRadio()
        radio.parse(inputStream, bytelength=modulationParametersLength)
    self.modulationParameters = radio
else:
    self.modulationParameters = None

if antennaPatternLength > 0:
    if int(self.antennaPatternType) == 1:
        pattern = BeamAntennaPattern()
        pattern.parse(inputStream)
    else:
        pattern = UnknownAntennaPattern()
        pattern.parse(inputStream, bytelength=antennaPatternLength)
    self.antennaPattern = pattern
else:
    self.antennaPattern = None

self.variableTransmitterParameters = [
    parseStandardVariableRecord(inputStream)
    for _ in range(variableTransmitterParameterCount)
]""",
    },
    "RecordSpecificationElement": {
        "marshalledSize": """prefix = 4 + 4 + 4 + 2 + 2
return prefix + len(self.recordValues) + self._padTo64(prefix)""",
        "serialize": """outputStream.write_uint32(self.recordID)
outputStream.write_uint32(self.recordSetSerialNumber)
outputStream.write_uint32(self.padding)
outputStream.write_uint16(self.recordLength)
outputStream.write_uint16(self.recordCount)
outputStream.write_bytes(self.recordValues)
padding = self._padTo64(14 + len(self.recordValues))
if padding:
    outputStream.write_bytes(b"\\x00" * padding)""",
        "parse": """self.recordID = rich_or_int(66, inputStream.read_uint32())
self.recordSetSerialNumber = inputStream.read_uint32()
self.padding = inputStream.read_uint32()
self.recordLength = inputStream.read_uint16()
self.recordCount = inputStream.read_uint16()
valueBytes = self.recordLength * self.recordCount // 8
self.recordValues = inputStream.read_bytes(valueBytes)
padding = self._padTo64(14 + valueBytes)
if padding:
    inputStream.read_bytes(padding)""",
    },
}

# XML base class -> (kernel base to emit, module providing it). Classes
# whose lineage reaches one of these emit PDU body methods.
KERNEL_BASES = {
    "PduBase": ("Pdu", "opendis.record.pdu"),
    # the LE family's base inherits the XML's own "Pdu" (§9.3.2): same
    # kernel boundary — subprotocol+pad ride the header status byte
    "Pdu": ("Pdu", "opendis.record.pdu"),
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

The full entity-information surface: Entity State, Collision,
Collision-Elastic (pduType 66 — the standard's §5.2.4 enumeration;
DIS-6-style type 6 is Resupply Offer), Entity State Update, and
Attribute (§7.2.2-§7.2.6) with the §6.2.10 Attribute record (generic
Standard-Variable format; typed decodes ride the registry separately).
""",
    "warfare": """Warfare family (IEEE 1278.1-2012 §7.3) — target-state PDUs.

Wire ground truth: submodules/open-dis-spec-xml/xml/WarfareFamilyPdus.xml.
Fire, Detonation, Directed Energy Fire, and Entity Damage Status, plus
the §6.2.15/.20 Directed Energy records (damage description, target
energy deposition, aimpoints) — uid-66 Standard Variable records
generated here and decoded via the registry (unknown record types stay
raw bytes); their recordType dispatch values are registry data
(opendis/record/__init__.py), not XML. Named padding fields are
wire-only state (``field(init=False)``).
""",
    "logistics": """Logistics family (IEEE 1278.1-2012 §7.4) — target-state PDUs.

Wire ground truth: submodules/open-dis-spec-xml/xml/LogisticsFamilyPdus.xml.
Service Request, Resupply Offer/Received/Cancel, Repair Complete/Response,
and the §6.2.86 Supply Quantity record.
""",
    "simulation_management": """Simulation Management family (IEEE 1278.1-2012 §7.5) — datum showcase.

Wire ground truth: submodules/open-dis-spec-xml/xml/SimulationManagementFamilyPdus.xml.
DataPdu with FixedDatum records and VariableDatum records whose payloads
are ``bytes`` (never per-byte lists), 64-bit padding computed by the
packer, and a typed uid-66 decoder path through the existing
StandardVariableRecord registry (opendis/record/__init__.py).

Python-side deltas from the XML (sample-review rulings): the base's
originator/receiver fields are EntityIdentifier-shaped
``originatingEntityID``/``receivingEntityID`` (the XML's
SimulationIdentifier classRef is the same 6-byte wire shape, §6.2.81);
Data Query carries datum-ID lists (u32 each, §7.5.9), not FixedDatum
records; datum list field names are fixedDatumRecords/variableDatumRecords
uniformly (the XML mixes fixedDatums/variableDatums spellings).
""",
    "minefield": """Minefield family (IEEE 1278.1-2012 §7.9) — target-state PDUs (QRP mode).

Wire ground truth: submodules/open-dis-spec-xml/xml/MinefieldFamilyPdus.xml.
Minefield State, Query, Data, and Response NACK.
""",
    "radio": """Radio Communications family (IEEE 1278.1-2012 §7.7) — target-state PDUs.

Wire ground truth: submodules/open-dis-spec-xml/xml/RadioCommunicationsFamilyPdus.xml.
Transmitter, Signal, Receiver, and Intercom Signal/Control.

Python-side deltas from the XML (sample-review rulings): the XML's
RadioCommsHeader is flattened onto the PDUs (the composed PDU header
already owns the attribute name ``header``; legacy dis7.py made the same
call); the Transmitter keeps SINGLE Modulation Parameters and Antenna
Pattern records (§7.7.2 s: "zero or one" of each; byte-length counts
per Table 176) with the Annex C MP dispatch (variant group on
``modulationType.radioSystem``) and its VTP list decodes uid-66 records
via the registry. The §6.2.8 Antenna Pattern home and §6.2.8.2 Beam
record (header-less, Table 31), the §6.2.58 home with the Annex C MP
records (Generic Radio / Simple Intercom zero-length markers, Basic
HAVE QUICK Table C.3, CCTT SINCGARS Table C.7), and the §6.2.95 home
with the High-Fidelity HAVE QUICK VTP record (Table C.4, recordType
3000) are generated here since the annex-c-mp-ap spec wave; the unknown
radio/pattern placeholders are curated runtime fallbacks. Signal
and Intercom Signal carry bit-counted byte payloads padded to 32 bits.
""",
    "information_operations": """Information Operations family (IEEE 1278.1-2012 §5.13) — target-state PDUs.

Wire ground truth: submodules/open-dis-spec-xml/xml/InformationOperationsFamilyPdus.xml.
IO Action and IO Report; the IO records (§6.2.48) use the uid-66
Standard Variable record format, so they ride the registry — known
record types decode, unknown ones stay raw bytes byte-exact.
""",
    "entity_management": """Entity Management family (IEEE 1278.1-2012 §7.8) — target-state PDUs.

Wire ground truth: submodules/open-dis-spec-xml/xml/EntityManagementFamilyPdus.xml.
Aggregate State, IsGroupOf, Transfer Ownership, and IsPartOf, plus the
aggregate records (§6.2.5/§6.2.7 Identifier/Type, §6.2.62 Named Location
Identification, §6.2.63 Relationship).

Python-side deltas from the XML (sample-review rulings): AggregateMarking
reuses EntityMarking (same shape and semantics; the XML declares a
separate class); IsGroupOf's Grouped Entity Descriptions are category-
dependent (§7.8.3) and held as EntityIdentifier entries — the XML's
VariableDatum classRef is un-parseable specing; TransferOwnership's
record list is flat (count + record sets), not wrapped in the XML's
RecordSpecification layer; IsPartOf keeps the XML's
``orginatingEntityID`` spelling (name variant, not a wire issue).
""",
    "synthetic_environment": """Synthetic Environment family (IEEE 1278.1-2012 §7.10) — target-state PDUs.

Wire ground truth: submodules/open-dis-spec-xml/xml/SyntheticEnvironmentFamilyPdus.xml.
Environmental Process, Gridded Data, Point/Linear/Areal Object State,
plus the Object Type/Identifier records, Linear Segment Parameter, and
the generic Environment record (opaque geometry, typed decoders
deferred). The Gridded Data PDU (type 42) carries the §6.2.40 grid-axis
descriptors (fixed/variable dispatch) and the §6.2.41 Grid Data records
(representation types 0-2; the XML declares exactly those three).

Python-side deltas from the XML (sample-review rulings): the bitfield-
mapped appearance/modification fields (uids 229, 240, 242, 249) stay raw
integers (the 2026-10-16 viewable-primitive ruling: rich presentation
belongs to the optional plugin layer); the grid-data record count is
derived per Table 192 (the XML's countFieldName is an upstream bug).
""",
    "distributed_emissions": """Distributed Emissions Regeneration family (IEEE 1278.1-2012 §7.6)
— target-state PDUs.

Wire ground truth: submodules/open-dis-spec-xml/xml/DistributedEmissionsFamilyPdus.xml.
Electromagnetic Emission, Designator, Underwater Acoustic, IFF, and SEES
PDUs with their emitter-system / beam record trees. The beam and system
"data length" fields count 32-bit words (§7.6.2) and are always derived
(``marshalledSize() // 4``; zero means the section is "large").

The IFF PDU (type 28) implements the §7.6.5 layer mechanism: Layer 1 is
always present; layers 2-5 are length-driven optionals dispatched by
Layer Header layer number (Table 165), with the Layer 3/4 format picked
by the Layer 1 System Type field. The layer lists hold flat §6.2.43 IFF
Data records (the XML's IFFDataSpecification wrapper adds a count the
layer already carries). SystemIdentifier's Change/Options is 8 bits
(Table B.5, Table 118 total 48 bits — the XML's 16-bit binding made
every IFF PDU one byte long; upstream candidate).
""",
    "live_entity": """Live Entity family (IEEE 1278.1-2012 §9) — target-state PDUs.

Wire ground truth: submodules/open-dis-spec-xml/xml/LiveEntityFamilyPdus.xml.
The LE information family (TSPI, Appearance, Articulated Parts, Fire,
Detonation) over the §9.3.2 header whose PDU Status byte carries the
subprotocol number [UID 417], plus the 4-byte live identifier taxonomy
(§6.2.53/§6.2.54) and the fixed-binary state-vector records.

The conditional PDUs are the conditional-attribute vocabulary's
reference implementation: presentIf gates and when= elided/full
variants are hand-curated (METHOD_BODIES); the TSPIFlag-conditional
state-vector fields are not modeled in the XML and serialize
unconditionally (mechanical XML fidelity).
""",
    "simulation_management_with_reliability": """Simulation Management with Reliability family (IEEE 1278.1-2012
§5.12.4) — target-state PDUs.

Wire ground truth: submodules/open-dis-spec-xml/xml/SimulationManagementWithReliabilityFamilyPdus.xml.
Each PDU pairs a §5.6 twin with a reliability-service level. Per the
aliasFor ruling the descriptive name is canonical and the abbreviation
is a plain module-level alias (e.g. ``CreateEntityRPdu =
CreateEntityReliablePdu``).

Bitfield maps [UID 192]/[UID 202] ride as raw integers inside the per-mine
lists; [UID 190] gets a view on the single appearance field. Minefield Data
exercises the conditional-attribute vocabulary (presentIf on dataFilter
bits, §6.2.16 Table 38) in FIELD-major order per Table 189 — each per-mine
list is a contiguous run; the whole-datagram 32-bit alignment pads
(Table 188/190 P terms) are packer-computed.
""",
    "simulation_management_with_reliability": """Simulation Management with Reliability family (IEEE 1278.1-2012
§5.12.4) — target-state PDUs.

Wire ground truth: submodules/open-dis-spec-xml/xml/SimulationManagementWithReliabilityFamilyPdus.xml.
Each PDU pairs a §5.6 twin with a reliability-service level. Per the
aliasFor ruling the descriptive name is canonical and the abbreviation
is a plain module-level alias (e.g. ``CreateEntityRPdu =
CreateEntityReliablePdu``).

Python-side deltas from the XML (sample-review rulings): originator/
receiver keep the exemplar's EntityIdentifier shape/names (same 6-byte
wire field, §6.2.81); Record Query-R carries a flat datum-ID list and
Record-R/Set Record-R carry flat record-set lists — the XML wraps each
in an extra RecordQuerySpecification/RecordSpecification layer the
standard's §5.12.4.14–16 tables do not have.
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
    "CollisionPdu": "Collision PDU",
    "CollisionElasticPdu": "Collision-Elastic PDU",
    "EntityStateUpdatePdu": "Entity State Update PDU",
    "AttributePdu": "Attribute PDU",
    "Attribute": "Attribute record",
    "AttributeRecordSet": "Attribute Record Set",
    "WarfareFamilyPdu": "Warfare family PDU",
    "FirePdu": "Fire PDU",
    "DetonationPdu": "Detonation PDU",
    "DirectedEnergyFirePdu": "Directed Energy Fire PDU",
    "EntityDamageStatusPdu": "Entity Damage Status PDU",
    "DirectedEnergyDamage": "Directed Energy Damage Description record",
    "DirectedEnergyTargetEnergyDeposition": "DE Target Energy Deposition record",
    "DirectedEnergyAreaAimpoint": "DE Area Aimpoint record",
    "DirectedEnergyPrecisionAimpoint": "DE Precision Aimpoint record",
    "BeamAntennaPattern": "Beam Antenna Pattern record",
    # the §6.2.58/§6.2.8/§6.2.95 record-type homes (Annex C promotion)
    "AntennaPatternRecord": "Antenna Pattern record",
    "ModulationParametersRecord": "Modulation Parameters record",
    "VariableTransmitterParametersRecord": ("Variable Transmitter Parameters record"),
    "LogisticsFamilyPdu": "Logistics family PDU",
    "SupplyQuantity": "Supply Quantity record",
    "ServiceRequestPdu": "Service Request PDU",
    "ResupplyOfferPdu": "Resupply Offer PDU",
    "ResupplyReceivedPdu": "Resupply Received PDU",
    "ResupplyCancelPdu": "Resupply Cancel PDU",
    "RepairCompletePdu": "Repair Complete PDU",
    "RepairResponsePdu": "Repair Response PDU",
    "FixedDatum": "Fixed Datum record",
    "VariableDatum": "Variable Datum record",
    "SimulationManagementFamilyPdu": "Simulation Management family PDU",
    "SimulationManagementWithReliabilityFamilyPdu": (
        "Simulation Management with Reliability family PDU"
    ),
    "RecordSpecificationElement": "Record Set element of a Record Specification",
    "DataPdu": "Data PDU",
    "CreateEntityPdu": "Create Entity PDU",
    "RemoveEntityPdu": "Remove Entity PDU",
    "StartResumePdu": "Start/Resume PDU",
    "StopFreezePdu": "Stop/Freeze PDU",
    "AcknowledgePdu": "Acknowledge PDU",
    "ActionRequestPdu": "Action Request PDU",
    "ActionResponsePdu": "Action Response PDU",
    "DataQueryPdu": "Data Query PDU",
    "SetDataPdu": "Set Data PDU",
    "EventReportPdu": "Event Report PDU",
    "ModulationType": "Modulation Type record",
    "RadioCommunicationsFamilyPdu": "Radio Communications family PDU",
    "TransmitterPdu": "Transmitter PDU",
    "SignalPdu": "Signal PDU",
    "ReceiverPdu": "Receiver PDU",
    "IntercomReferenceID": "Intercom Reference Identifier record",
    "IntercomSignalPdu": "Intercom Signal PDU",
    "IntercomCommunicationsParameters": "Intercom Communications Parameter record",
    "IntercomControlPdu": "Intercom Control PDU",
    "InformationOperationsFamilyPdu": "Information Operations family PDU",
    "InformationOperationsActionPdu": "IO Action PDU",
    "InformationOperationsReportPdu": "IO Report PDU",
    "AggregateIdentifier": "Aggregate Identifier record",
    "AggregateType": "Aggregate Type record",
    "AggregateMarking": "Aggregate Marking record",
    "Relationship": "Relationship record",
    "NamedLocationIdentification": "Named Location Identification record",
    "EntityManagementFamilyPdu": "Entity Management family PDU",
    "AggregateStatePdu": "Aggregate State PDU",
    "IsGroupOfPdu": "IsGroupOf PDU",
    "TransferOwnershipPdu": "Transfer Ownership PDU",
    "IsPartOfPdu": "IsPartOf PDU",
    "ObjectIdentifier": "Object Identifier record",
    "ObjectType": "Object Type record",
    "LinearSegmentParameter": "Linear Segment Parameter record",
    "EnvironmentRecord": "Environment record",
    "SyntheticEnvironmentFamilyPdu": "Synthetic Environment family PDU",
    "EnvironmentalProcessPdu": "Environmental Process PDU",
    "PointObjectStatePdu": "Point Object State PDU",
    "LinearObjectStatePdu": "Linear Object State PDU",
    "ArealObjectStatePdu": "Areal Object State PDU",
    "EEFundamentalParameterData": "EE Fundamental Parameter Data record",
    "BeamData": "Beam Data record",
    "BeamStatus": "Beam Status record",
    "JammingTechnique": "Jamming Technique record",
    "TrackJamData": "Track/Jam Data record",
    "EmitterSystem": "Emitter System record",
    "EmitterBeam": "Emitter Beam record",
    "ElectronicEmitter": "Electronic Emitter record",
    "DistributedEmissionsRegenerationFamilyPdu": (
        "Distributed Emissions Regeneration family PDU"
    ),
    "ElectromagneticEmissionPdu": "Electromagnetic Emission PDU",
    "DesignatorPdu": "Designator PDU",
    "ShaftRPM": "Shaft RPM record",
    "APA": "APA record",
    "AcousticEmitter": "Acoustic Emitter System record",
    "UAFundamentalParameter": "UA Fundamental Parameter Data record",
    "UABeam": "UA Beam record",
    "UAEmitter": "UA Emitter System record",
    "UnderwaterAcousticPdu": "Underwater Acoustic PDU",
    "SystemIdentifier": "System Identifier record",
    "FundamentalOperationalData": "Fundamental Operational Data record",
    "LayerHeader": "Layer Header record",
    "IFFFundamentalParameterData": "IFF Fundamental Parameter Data record",
    "IFFData": "IFF Data record",
    "Mode5InterrogatorBasicData": "Mode 5 Interrogator Basic Data record",
    "Mode5TransponderBasicData": "Mode 5 Transponder Basic Data record",
    "ModeSInterrogatorBasicData": "Mode S Interrogator Basic Data record",
    "ModeSTransponderBasicData": "Mode S Transponder Basic Data record",
    "IFFPduLayer2Data": "IFF PDU Layer 2 Emissions Data",
    "IFFPduLayer3TransponderFormatData": "IFF PDU Layer 3 Mode 5 Transponder Format",
    "IFFPduLayer3InterrogatorFormatData": "IFF PDU Layer 3 Mode 5 Interrogator Format",
    "IFFPduLayer4InterrogatorFormatData": "IFF PDU Layer 4 Mode S Interrogator Format",
    "IFFPduLayer4TransponderFormatData": "IFF PDU Layer 4 Mode S Transponder Format",
    "IFFPduLayer5Data": "IFF PDU Layer 5 Data Communications",
    "IdentificationFriendOrFoePdu": "Identification Friend or Foe (IFF) PDU",
    "PropulsionSystemData": "Propulsion System Data record",
    "VectoringNozzleSystem": "Vectoring Nozzle System Data record",
    "SupplementalEmissionEntityStatePdu": "Supplemental Emission/Entity State (SEES) PDU",
    "SilentEntitySystem": "Silent Entity System record",
    "GridDataType0": "Grid Data record (representation type 0)",
    "GridDataType1": "Grid Data record (representation type 1)",
    "GridDataType2": "Grid Data record (representation type 2)",
    "GriddedDataPdu": "Gridded Data PDU",
    "LiveSimulationAddress": "Live Simulation Address record",
    "LiveEntityIdentifier": "Live Entity Identifier record",
    "LiveEntityIdentifierElided": "Elided Live Entity Identifier record",
    "EventIdentifierLiveEntity": "Live Event Identifier record",
    "EventIdentifierLiveEntityElided": "Elided Live Event Identifier record",
    "LEMunitionDescriptor": "LE Munition Descriptor record",
    "LiveEntityRelativeWorldCoordinates": "LE Relative World Coordinates record",
    "LiveEntityLinearVelocity": "LE Linear Velocity record",
    "LiveEntityOrientation": "LE Orientation record",
    "LiveEntityOrientation16": "LE Orientation (16-bit) record",
    "LiveEntityPositionError": "LE Position Error record",
    "LiveEntityOrientationError": "LE Orientation Error record",
    "LEVector3FixedByte": "Fixed-Byte Vector record",
    "LiveDeadReckoningParameters": "LE Dead Reckoning Parameters record",
    "LiveEntityRelativeEntityCoordinates": "LE Relative Entity Coordinates record",
    "LiveEntityFamilyPdu": "Live Entity family PDU",
    "TimeSpacePositionInformationPdu": "Time Space Position Information PDU",
    "AppearancePdu": "Appearance PDU",
    "ArticulatedPartsPdu": "Articulated Parts PDU",
    "LiveEntityFirePdu": "LE Fire PDU",
    "LiveEntityDetonationPdu": "LE Detonation PDU",
    "MinefieldIdentifier": "Minefield Identifier record",
    "Vector2Float": "Two-Dimensional Vector record",
    "MineEmplacementTime": "Mine Emplacement Time record",
    "MinefieldFamilyPdu": "Minefield family PDU",
    "MinefieldStatePdu": "Minefield State PDU",
    "MinefieldQueryPdu": "Minefield Query PDU",
    "MinefieldDataPdu": "Minefield Data PDU",
    "MinefieldResponseNACKPdu": "Minefield Response NACK PDU",
    "CommentPdu": "Comment PDU",
    "CreateEntityReliablePdu": "Create Entity-R PDU",
    "RemoveEntityReliablePdu": "Remove Entity-R PDU",
    "StartResumeReliablePdu": "Start/Resume-R PDU",
    "StopFreezeReliablePdu": "Stop/Freeze-R PDU",
    "AcknowledgeReliablePdu": "Acknowledge-R PDU",
    "ActionRequestReliablePdu": "Action Request-R PDU",
    "ActionResponseReliablePdu": "Action Response-R PDU",
    "DataQueryReliablePdu": "Data Query-R PDU",
    "SetDataReliablePdu": "Set Data-R PDU",
    "DataReliablePdu": "Data-R PDU",
    "EventReportReliablePdu": "Event Report-R PDU",
    "CommentReliablePdu": "Comment-R PDU",
    "RecordReliablePdu": "Record-R PDU",
    "SetRecordReliablePdu": "Set Record-R PDU",
    "RecordQueryReliablePdu": "Record Query-R PDU",
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
    "DirectedEnergyDamage": """Uid-66 Standard Variable record (§6.2.20.1): the class writes its own
recordType/recordLength header and the registry decodes the wire by
``recordType`` — the 4500 dispatch value is registry data (Table 44's
format, not the XML).""",
    "HighFidelityHAVEQUICKRadio": """Uid-66 Standard Variable record (Annex C.4.2.3): the class writes its own
recordType/recordLength header and the registry decodes the wire by
``recordType`` — the 3000 dispatch value is registry data (Table C.4's
format, not the XML; REF-010 uid 66 names the type "High Fidelity HAVE
QUICK/SATURN Radio"). The Basic HAVE QUICK MP record rides the
Transmitter's modulationParameters slot alongside this record.""",
    "DirectedEnergyAreaAimpoint": """Uid-66 Standard Variable record decoded via the registry (dispatch
value 4001). The lists carry non-self-identifying records (§6.2.20.2):
Beam Antenna Pattern records (320 bits each, §6.2.8.2) and DE Target
Energy Deposition records (96 bits each, §6.2.20.4). The trailing pad
is packer-computed to the 64-bit boundary §6.2.83 requires.""",
    "DirectedEnergyPrecisionAimpoint": """Uid-66 Standard Variable record decoded via the registry (dispatch
value 4000, Table 46's format).""",
    "EntityInformationFamilyPdu": """Thin family marker — per-class identity lives in the ``pduType``/``protocolFamily`` ClassVars; family metadata for middleware lives in ``PDU_FAMILIES`` (opendis.record.factory).""",
    "EntityStatePdu": """``entityAppearance`` and ``capabilities`` hold the raw uint32 on the wire; after parsing a known entity kind they hold the matching bitfield view (``int(view)`` is the raw value, so round-trips are byte-exact and unknown bits survive).""",
    "CollisionElasticPdu": """pduType 66 per the standard's §5.2.4 enumeration and Table 136 — the DIS-6-style type 6 legacy code used is Resupply Offer in the 2012 numbering. The elastic-collision response protocol (§5.3.4): a receiving entity that detects the collision answers with its own Collision-Elastic PDU.""",
    "EntityStateUpdatePdu": """The PDU carries no entityType, so the appearance uint32 cannot be resolved to a bitfield view locally — the receiving application resolves it from its cached entity type for the entity (XML comment).""",
    "Attribute": """Generic §6.2.10 Standard-Variable-format record: ``recordSpecificFields`` carries the K data octets plus the trailing 64-bit alignment pad exactly as received, and ``recordLength`` (= 6 + K + P, Table 138) stays caller-settable wire state — same contract as IntercomCommunicationsParameters. Typed per-record decodes ride the registry separately.""",
    "IFFData": """Generic §6.2.43 Standard-Variable-format record: ``recordSpecificFields`` carries the K data octets plus the trailing 32-bit alignment pad (Table 169) exactly as received, and ``recordLength`` (= 6 + K + P) stays caller-settable wire state. Typed decodes of the B.2.1.1 record types ride the registry separately.""",
    "IdentificationFriendOrFoePdu": """Layer 1 is always present; layers 2-5 are optional, presence declared by the Layer 1 Fundamental Operational Data Information Layers bits (§6.2.39 c, §6.2.45 a/Table 74 — bit N = Layer N; in the spec XML since v0.12.0) and each self-framed by a Layer Header whose Length includes the header (Table 165) — parse reads while wire length remains. Layers 3 and 4 each have interrogator and transponder formats, picked by the Layer 1 System Type [UID 82] plus the Combined Interrogator/Transponder Change/Options indicator (Table B.5 bit 4, B.5.13/.14).""",
    "SupplementalEmissionEntityStatePdu": """Signature representation indexes are handles into the receiving application's signature tables, not physical values (§5.7.7).""",
    "GriddedDataPdu": """The grid-data record count is derived: G = vectorDimension x the product of the per-axis point counts (Table 192) — the XML's countFieldName="numberOfGridAxes" on the list is an upstream bug. Axis descriptors dispatch on their trailing axisType byte ([UID 377]); grid data records on dataRepresentation ([UID 247], formats 0-2 per §6.2.41).""",
    "SilentEntitySystem": """One Silent Entity System record stands for a number of same-typed silent entities; the appearance-record list carries one raw uint32 appearance per entity (§6.2.79, Table 183).""",
    "WarfareFamilyPdu": """Thin family marker — per-class identity lives in the ``pduType``/``protocolFamily`` ClassVars; family metadata for middleware lives in ``PDU_FAMILIES`` (opendis.record.factory).""",
    "DirectedEnergyFirePdu": """``flags`` holds the raw uint16 until parsed, then the [UID 313] view. The DE records are uid-66 Standard Variable records decoded via the registry; unknown record types stay raw bytes. Field names are XML-verbatim, including the ``commulativeShotTime`` spelling.""",
    "EntityDamageStatusPdu": """The damage-description list carries uid-66 Standard Variable records (§6.2.17 Damage Description family) decoded via the registry; unknown record types stay raw bytes.""",
    "LogisticsFamilyPdu": """Thin family marker — per-class identity lives in the ``pduType``/``protocolFamily`` ClassVars; family metadata for middleware lives in ``PDU_FAMILIES`` (opendis.record.factory).""",
    "SimulationManagementFamilyPdu": """Not a thin marker: carries the §6.2.82 Simulation Management PDU header fields (originating and receiving entity IDs, EntityIdentifier-shaped per the sample-review ruling).""",
    "SimulationManagementWithReliabilityFamilyPdu": """Not a thin marker: the §6.2.82 header fields (EntityIdentifier-shaped per the sample-review ruling) plus the reliability-service conventions of the -R family.""",
    "RecordSpecificationElement": """One element of a §6.2.73 Record Specification: a block of same-typed records. ``recordValues`` is the concatenated block as ``bytes`` (byte granularity — bit lengths not divisible by 8 are unsupported, same ruling as VariableDatum); the set is padded to a 64-bit boundary by the packer.""",
    "VariableDatum": """``variableData`` is the raw payload as ``bytes``; ``variableDatumLength`` (in bits) is derived at serialize time and the 64-bit padding is computed by the packer — neither is user-settable state.

# generator: payload carries the complete serialized record when the
# datum ID is a uid-66 record type, so a known record re-serializes
# standalone and an unknown one stays raw bytes (forward compat).""",
    "CommentPdu": """The fixed datum count is not used by this PDU (shall be zero); the list is kept so malformed-but-parseable datagrams still round-trip byte-exact.""",
    "MinefieldDataPdu": """Per-mine data in FIELD-major order (Table 189): each conditional per-mine list is one contiguous run, present when its dataFilter bit (§6.2.16 Table 38) is set. ``mineEntityNumber`` is unconditional; scalar detection is N×S (mines × sensor types); the trip-wire section is mine-major for its count lists with all vertices pooled at the end (§5.10.4.5).

# generator: presentIf-driven section presence — the conditional
# vocabulary's reference implementation; absent sections are simply
# not serialized (empty lists), and marshalledSize consults the
# filter bits.""",
    "InformationOperationsFamilyPdu": """Not a thin marker: carries the originating simulation ID (EntityIdentifier-shaped; §5.13).""",
    "EnvironmentRecord": """The geometry stays opaque — typed per-record decoders ride the registry later (§6.2.31, DIS PCR 240).""",
    "BeamStatus": """One byte: the [UID 318] beam state in bit 0, seven reserved bits (kept so odd wire bytes round-trip byte-exact).""",
    "EEFundamentalParameterData": """Continuous wave emissions are represented by 0.0 in both pulse repetition frequency and pulse width.""",
    "ElectronicEmitter": """Per-emitter-system data section of the EE PDU (§7.6.2). ``systemDataLength`` counts 32-bit words and is derived.""",
    "EmitterBeam": """Emitter beam data section of the EE PDU (§7.6.2). ``beamDataLength`` counts 32-bit words of the whole beam record (including the length field) and is derived; zero means the beam is "large" (§7.6.2).""",
    "UABeam": """``beamDataLength`` counts 32-bit words and is derived.""",
    "UAEmitter": """``systemDataLength`` counts 32-bit words and is derived.""",
    "APA": """14-bit additional passive activity parameter index (plus 2 status bits) and a value, both held raw.""",
    "LiveEntityIdentifier": """The 4-byte live shape of the ruled identifier taxonomy (§6.2.53).""",
    "EventIdentifierLiveEntity": """The 4-byte live event shape (§9.4.5) of the ruled event-identifier taxonomy.""",
    "LEMunitionDescriptor": """Warhead/fuse ride the owning PDU's flag bit 4, quantity/rate bit 5 (None = absent on the wire); ``parse`` takes the inclusion flags (cross-scope presentIf, §6.2.19.2).""",
    "TimeSpacePositionInformationPdu": """The standard's TSPIFlag-conditional fields are not modeled in the XML; this implementation serializes every state-vector field unconditionally (mechanical XML fidelity).""",
    "CommentReliablePdu": """The fixed datum count is not used by this PDU (shall be zero); the list is kept so malformed-but-parseable datagrams still round-trip byte-exact.""",
    "BeamAntennaPattern": """Non-self-identifying (§6.2.8): Antenna Pattern records carry no
record header of their own — the Transmitter PDU's
``antennaPatternType`` field types the record and its byte-length
count bounds it on the wire (Table 31: 320 bits total).""",
}

# Full-text replacements where a ruling makes the docstring deliberately
# non-XML. The Vector3Double docstring IS the WorldCoordinates alias
# ruling (its prose documents the alias emitted below the class).
DOCSTRING_OVERRIDES = {
    "DirectedEnergyAreaAimpoint": """§6.2.20.2 DE Area Aimpoint record

The DE Area Aimpoint record shall be used to communicate targeting
information when the target of the directed energy weapon is an area.
The area may or may not be associated with one or more target entities.

# generator: the XML comment carries the Precision Aimpoint title
# ("DE Precision Aimpoint Record. Section 6.2.20.2") — an upstream
# copy-paste bug; this body is the standard's §6.2.20.2 opening prose
# (XML-comment-enrichment candidate).""",
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

    def __init__(
        self, source: str, needs_logger: bool = False, after_methods: bool = False
    ):
        self.source = source
        self.needs_logger = needs_logger
        self.after_methods = after_methods


# -- class-level constants -------------------------------------------------
#
# (name, expression, comment-or-None). PDU identity constants carry their
# [UID] comments; the numeric values are SISO registry data absent from
# the spec XML (the XML initialValues are symbolic — DisPduType.ENTITY_STATE).

# Residual identity/constant ClassVars the XML cannot declare: the §6.1.8
# Table 25 symbolic constants (symbolic_names). The pduType/protocolFamily
# entries RETIRED 2026-10-17 (bucket-C item 7): the XML's initialValue +
# class id drive them mechanically (resolve). The uid-66 recordType
# dispatch entries RETIRED the same day (item 4): the §6.2.83 signature's
# defaultValue owns them; rider = SV_RECORD_TYPE_RIDER.
CLASS_VARS = {
    "SimulationAddress": [
        ("ALL_SITES", "sym.ALL_SITES", None),
        ("ALL_APPLICATIONS", "sym.ALL_APPLIC", None),
    ],
    "EntityIdentifier": [
        ("ALL_ENTITIES", "sym.ALL_ENTITIES", None),
    ],
}

# canonical family class -> protocolFamily rider. The [UID 5] row labels
# are SISO data (REF-010 uid 5); the slash/space spellings are not
# derivable from the XML's symbolic names, so the labels stay curated.
PROTOCOL_FAMILY_RIDERS = {
    "EntityInformationFamilyPdu": "[UID 5] Entity Information/Interaction",
    "WarfareFamilyPdu": "[UID 5] Warfare",
    "LogisticsFamilyPdu": "[UID 5] Logistics",
    "RadioCommunicationsFamilyPdu": "[UID 5] Radio Communications",
    "SimulationManagementFamilyPdu": "[UID 5] Simulation Management",
    "DistributedEmissionsRegenerationFamilyPdu": (
        "[UID 5] Distributed Emissions Regeneration"
    ),
    "EntityManagementFamilyPdu": "[UID 5] Entity Management",
    "MinefieldFamilyPdu": "[UID 5] Minefield",
    "SyntheticEnvironmentFamilyPdu": "[UID 5] Synthetic Environment",
    "SimulationManagementWithReliabilityFamilyPdu": (
        "[UID 5] Simulation Management with Reliability"
    ),
    "LiveEntityFamilyPdu": "[UID 5] Live Entity",
    "InformationOperationsFamilyPdu": "[UID 5] Information Operations",
}

# -- curated field furniture ----------------------------------------------

# (class, field) -> trailing rider where the mechanical [UID n] misses the
# exemplar text (primitive-bound classes carry no uid for the rider).
FIELD_RIDERS = {
    ("EntityStatePdu", "entityAppearance"): "[UID 31-43] or a bitfield view",
    ("EntityStatePdu", "capabilities"): "[UID 55] or a bitfield view",
    ("AppearancePdu", "capabilities"): "[UID 55] bitmap",
    ("AppearancePdu", "appearanceVisual"): "[UID 31-43]",
    ("SystemIdentifier", "changeOptions"): (
        "8-bit Change/Options (Table B.5); Table 118 totals the record at "
        "48 bits — the §6.2.87 prose cites the 16-bit-looking §6.2.13 shape"
    ),
    ("MinefieldStatePdu", "protocolMode"): "2-bit protocol mode + 14 reserved bits",
    ("MinefieldDataPdu", "fusing"): "[UID 192]",
    ("MinefieldDataPdu", "paintScheme"): "[UID 202]",
    ("ModulationType", "detail"): "[UID 156-162]",
    ("EnvironmentalProcessPdu", "environmentStatus"): "[UID 249] bitmap",
    ("DesignatorPdu", "designatorPower"): "watts",
    ("DesignatorPdu", "designatorWavelength"): "microns",
    ("EEFundamentalParameterData", "frequency"): "Hz",
    ("EEFundamentalParameterData", "frequencyRange"): "Hz",
    ("EEFundamentalParameterData", "effectiveRadiatedPower"): "dBm",
    ("EEFundamentalParameterData", "pulseRepetitionFrequency"): "Hz",
    ("EEFundamentalParameterData", "pulseWidth"): "seconds",
}

# (class, field) -> annotation name where the semantic alias reads better
# than the canonical class (the alias is a module-level name in its home).
FIELD_ANNOTATIONS = {
    ("EntityStatePdu", "entityLocation"): "WorldCoordinates",
    ("FirePdu", "locationInWorldCoordinates"): "WorldCoordinates",
    ("DetonationPdu", "locationInWorldCoordinates"): "WorldCoordinates",
    ("TransmitterPdu", "antennaLocation"): "WorldCoordinates",
}

# Verbatim source appended at the end of _parseBody.
# PARSE_TAILS RETIRED 2026-10-17 (bucket-C item 6): the EntityAppearance
# kind-dispatch derives from REF-010 — table names matched against the
# uid-7/uid-8 row labels (ref010._context_split) drive the module dicts
# and the parse tail (emit._context_dicts_block / _context_tail).

# (after-class, source) blocks injected between emitted classes.
MODULE_SOURCES = {
    # the entity_information context-view dicts entry RETIRED 2026-10-17
    # (bucket-C item 6): the EntityAppearance/EntityCapabilities dispatch
    # derives from REF-010 labels and emits ahead of its first consumer
    # (emit._context_dicts_block); its bitfield imports derive with it
    "entity_management": [
        (
            "EntityManagementFamilyPdu",
            """def _padTo32(byteCount: int) -> int:
    \"\"\"Pad bytes needed to bring the PDU to a 32-bit boundary.\"\"\"
    return (4 - byteCount % 4) % 4""",
        )
    ],
    "simulation_management": [
        (
            "FixedDatum",
            """def _paddedDatumSize(byteCount: int) -> int:
    \"\"\"Datum fields are padded at the end to a multiple of 64 bits.\"\"\"
    remainder = byteCount % 8
    if remainder:
        byteCount += 8 - remainder
    return byteCount""",
        )
    ],
    "radio": [
        (
            "AntennaPatternRecord",
            """# generator: curated runtime placeholder — reserved/unknown antenna
# pattern types carry their bytes raw (§6.2.8 non-self-identifying
# records; not an XML type, so generation adds nothing)


class UnknownAntennaPattern(AntennaPatternRecord):
    \"\"\"Placeholder for unknown or unimplemented antenna pattern types.\"\""

    def __init__(self, data: bytes = b""):
        self.data = data

    def marshalledSize(self) -> int:
        return len(self.data)

    def serialize(self, outputStream: DataOutputStream) -> None:
        super().serialize(outputStream)
        outputStream.write_bytes(self.data)

    def parse(
        self,  # pyright: ignore[reportIncompatibleMethodOverride]
        inputStream: DataInputStream,
        bytelength: int,
    ) -> None:
        # Validate bytelength argument by calling base method
        super().parse(inputStream, bytelength)
        # Antenna Pattern records are non-self-identifying (§6.2.8) — no
        # record header precedes the pattern data (Table 31: the whole
        # 320-bit Beam record is pattern fields), so the full record
        # length is payload. The old ``bytelength - 6`` assumed a
        # 6-byte type/length header that does not exist.
        self.data = inputStream.read_bytes(bytelength)""",
        ),
        (
            "ModulationParametersRecord",
            """# generator: curated runtime placeholder — radio systems without an
# in-standard MP record (SINCGARS 5 and EPLRS 7 define none, Annex
# C.5/C.7; JTIDS/MIDS 8 records live in SISO-STD-002, C.8.2.3) keep
# their bytes raw; not an XML type, so generation adds nothing


class UnknownRadio(ModulationParametersRecord):
    \"\"\"Placeholder for unknown or unimplemented radio types.\"\""

    def __init__(self, data: bytes = b""):
        self.data = data

    def marshalledSize(self) -> int:
        return len(self.data)

    def serialize(self, outputStream: DataOutputStream) -> None:
        super().serialize(outputStream)
        outputStream.write_bytes(self.data)

    def parse(
        self, inputStream: DataInputStream, bytelength: int | None = None
    ) -> None:
        # Validate bytelength argument by calling base method
        super().parse(inputStream, bytelength)
        assert isinstance(bytelength, int)
        self.data = inputStream.read_bytes(bytelength)""",
        ),
    ],
}

# module key -> extra imports the curated blocks above need (the usage
# scan cannot see inside verbatim source strings).
MODULE_SOURCE_IMPORTS = {
    "warfare": {
        "opendis.record.base": [
            "StandardVariableRecord",
        ],
    },
    "simulation_management": {
        "opendis.record.base": [
            "StandardVariableRecord",
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
    # -R family: the XML's aliasFor abbreviation classes (descriptive
    # name canonical, abbreviation aliased — 2026-10-14 ruling)
    "CreateEntityReliablePdu": """# generator: aliasFor elements — one class plus a name assignment;
# descriptive name canonical, abbreviation aliased
CreateEntityRPdu = CreateEntityReliablePdu""",
    "RemoveEntityReliablePdu": "RemoveEntityRPdu = RemoveEntityReliablePdu",
    "StartResumeReliablePdu": "StartResumeRPdu = StartResumeReliablePdu",
    "StopFreezeReliablePdu": "StopFreezeRPdu = StopFreezeReliablePdu",
    "AcknowledgeReliablePdu": "AcknowledgeRPdu = AcknowledgeReliablePdu",
    "ActionRequestReliablePdu": "ActionRequestRPdu = ActionRequestReliablePdu",
    "ActionResponseReliablePdu": "ActionResponseRPdu = ActionResponseReliablePdu",
    "DataQueryReliablePdu": "DataQueryRPdu = DataQueryReliablePdu",
    "SetDataReliablePdu": "SetDataRPdu = SetDataReliablePdu",
    "DataReliablePdu": "DataRPdu = DataReliablePdu",
    "EventReportReliablePdu": "EventReportRPdu = EventReportReliablePdu",
    "CommentReliablePdu": "CommentRPdu = CommentReliablePdu",
    "RecordReliablePdu": "RecordRPdu = RecordReliablePdu",
    "SetRecordReliablePdu": "SetRecordRPdu = SetRecordReliablePdu",
    "RecordQueryReliablePdu": "RecordQueryRPdu = RecordQueryReliablePdu",
    "TimeSpacePositionInformationPdu": "TSPIPdu = TimeSpacePositionInformationPdu",
    "LiveEntityFirePdu": "LEFirePdu = LiveEntityFirePdu",
    "LiveEntityDetonationPdu": "LEDetonationPdu = LiveEntityDetonationPdu",
    # IFF / SEES abbreviation aliases (aliasFor ruling; first alias in the
    # module carries the ruling comment)
    "IdentificationFriendOrFoePdu": """# generator: aliasFor elements — one class plus a name assignment;
# descriptive name canonical, abbreviation aliased
IFFPdu = IdentificationFriendOrFoePdu""",
    "SupplementalEmissionEntityStatePdu": "SEESPdu = SupplementalEmissionEntityStatePdu",
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

# family module -> REF-010 bitfield uids, in definition order. The
# appearance module carries the FULL Entity Appearance / Entity
# Capabilities surface (Phase 5 survey item): all 13 kind/domain
# appearance variants [UID 31-43] and the six capability tables with
# REF-010 layouts [UID 450-455].
BITFIELD_VIEWS = {
    "appearance": [
        31,
        32,
        33,
        34,
        35,
        36,
        37,
        38,
        39,
        40,
        41,
        42,
        43,
        450,
        451,
        452,
        453,
        454,
        455,
    ],
    "minefield": [190],
    "simulation_management": [68],
    "warfare": [313],
}

# View class names where PascalCase(table name) misses the exemplar
BITFIELD_CLASS_NAMES = {
    190: "MinefieldStateAppearance",  # "Minefield State-Appearance Bit Map"
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

Layouts transcribed from SISO-REF-010 v37 bitfield tables: all 13
appearance variants [UID 31-43] — one per entity kind, and per domain
for platforms — plus the six capability tables with REF-010 layouts
[UID 450-455]. One view class per entity kind/domain layout, all over
the same uint32 wire field. Kinds without a capability table
(life forms, environmental, cultural, supply, radio, expendable,
sensor/emitter) keep the raw integer.

# generator: layouts, bit positions and property names are mechanical
# output consumed from the pinned siso-ref-010-python package (which
# derives them from the SISO-REF-010 XML); nothing here renames rows.""",
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
    "VariableDatum": MemberSource(
        after_methods=True,
        source='''@property
def decodedRecord(self) -> StandardVariableRecord | None:
    """The typed record for this datum, via the StandardVariableRecord
    registry keyed on uid 66 — or None when the record type (or a
    decoder for it) is unknown, leaving the raw bytes authoritative.

    # generator: typed uid-66 decoder wiring; unknown record types
    # degrade to raw bytes rather than raising.
    """
    from opendis.record import (
        getStandardVariableClass,
        isKnownStandardVariableRecord,
    )

    recordType = int(self.variableDatumID)
    if not isKnownStandardVariableRecord(recordType):
        return None
    try:
        stream = DataInputStream(io.BytesIO(self.variableData))
        headerType = stream.read_uint32()
        if headerType != recordType:
            return None
        bytelength = stream.read_uint16()
        record = getStandardVariableClass(recordType)()
        record.parse(stream, bytelength)
        return record
    except Exception:
        # Payload did not parse as this record type; the raw bytes
        # remain the truth (tolerance rule).
        return None''',
    ),
    "MinefieldDataPdu": MemberSource(
        source="""# dataFilter bit numbers (§6.2.16 Table 38)
GROUND: ClassVar[int] = 0
WATER: ClassVar[int] = 1
SNOW: ClassVar[int] = 2
ORIENTATION: ClassVar[int] = 3
THERMAL: ClassVar[int] = 4
REFLECTANCE: ClassVar[int] = 5
EMPLACEMENT: ClassVar[int] = 6
WIRES: ClassVar[int] = 7
FUSING: ClassVar[int] = 8
SCALAR: ClassVar[int] = 9
PAINT: ClassVar[int] = 10

def _filter(self, bit: int) -> bool:
    return bool((int(self.dataFilter) >> bit) & 1)

@property
def groundPresent(self) -> bool:
    return (
        self._filter(self.GROUND)
        or self._filter(self.WATER)
        or self._filter(self.SNOW)
    )

@property
def orientationPresent(self) -> bool:
    return (
        self._filter(self.GROUND)
        or self._filter(self.WATER)
        or self._filter(self.SNOW)
        or self._filter(self.ORIENTATION)
    )

def _prefixSize(self) -> int:
    return (
        self.minefieldID.marshalledSize()
        + self.requestingEntityID.marshalledSize()
        + 2
        + 1
        + 1
        + 1
        + 1
        + 1
        + 1  # counts + padding
        + 4
        + self.mineType.marshalledSize()
        + 2 * len(self.sensorTypes)
    )

def _wireVertexCount(self) -> int:
    return sum(self.numberOfVertices)""",
    ),
    "AggregateMarking": MemberSource(
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
    if len(data) > 31:
        _logger.warning(
            "AggregateMarking string %r truncated to 31 bytes", value)
    self.characters = data[:31].ljust(31, b"\\x00")''',
    ),
    "ElectronicEmitter": MemberSource(
        after_methods=True,
        source='''@property
def systemDataLength(self) -> uint8:
    """System data length in 32-bit words — derived."""
    return self.marshalledSize() // 4''',
    ),
    "EmitterBeam": MemberSource(
        after_methods=True,
        source='''@property
def beamDataLength(self) -> uint8:
    """Beam data length in 32-bit words — derived."""
    return self.marshalledSize() // 4''',
    ),
    "UABeam": MemberSource(
        after_methods=True,
        source='''@property
def beamDataLength(self) -> uint8:
    """Beam data length in 32-bit words — derived."""
    return self.marshalledSize() // 4''',
    ),
    "UAEmitter": MemberSource(
        after_methods=True,
        source='''@property
def systemDataLength(self) -> uint8:
    """System data length in 32-bit words — derived."""
    return self.marshalledSize() // 4''',
    ),
    "LiveEntityFamilyPdu": MemberSource(
        source='''@property
def subprotocolNumber(self) -> uint8:
    """Subprotocol used to decode the PDU (§13 of EBV) — rides the
    header's PDU Status byte."""
    return self.header.pduStatus

@subprotocolNumber.setter
def subprotocolNumber(self, value: uint8) -> None:
    self.header.pduStatus = value''',
    ),
    "AggregateStatePdu": MemberSource(
        source="""def _prefixSize(self) -> int:
    return (
        self.aggregateID.marshalledSize()
        + 1
        + 1
        + self.aggregateType.marshalledSize()
        + 4
        + self.aggregateMarking.marshalledSize()
        + self.dimensions.marshalledSize()
        + self.orientation.marshalledSize()
        + self.centerOfMass.marshalledSize()
        + self.velocity.marshalledSize()
        + 2
        + 2
        + 2
        + 2
    )""",
    ),
    "EnvironmentRecord": MemberSource(
        after_methods=True,
        source='''@staticmethod
def _padTo64(byteCount: int) -> int:
    return (8 - byteCount % 8) % 8

@property
def length(self) -> uint16:
    """Record length IN BITS — derived from the geometry bytes."""
    return (8 + len(self.geometry)) * 8''',
    ),
    "TransmitterPdu": MemberSource(
        source='''@property
def modulationParameterCount(self) -> uint8:
    """Length in bytes of the Modulation Parameters record (0 if
    absent)."""
    return (
        self.modulationParameters.marshalledSize()
        if self.modulationParameters is not None
        else 0
    )

@property
def antennaPatternCount(self) -> uint16:
    """Length in bytes of the Antenna Pattern record (0 if absent)."""
    return (
        self.antennaPattern.marshalledSize()
        if self.antennaPattern is not None
        else 0
    )

@property
def variableTransmitterParameterCount(self) -> uint16:
    """How many variable transmitter parameter records follow."""
    return len(self.variableTransmitterParameters)''',
    ),
    "RecordSpecificationElement": MemberSource(
        after_methods=True,
        source="""@staticmethod
def _padTo64(byteCount: int) -> int:
    return (8 - byteCount % 8) % 8""",
    ),
    "IFFPduLayer2Data": MemberSource(
        after_methods=True,
        source="""@classmethod
def parseLayer(
        cls,
        inputStream: DataInputStream,
        layerNumber: int,
        layerSpecificInformation: int,
        length: int,
    ) -> "IFFPduLayer2Data":
        \"\"\"Construct the layer from its payload; the dispatching
        PDU has already read the four Layer Header bytes
        (layerNumber included).\"\"\"
        layer = cls()
        layer.layerHeader = LayerHeader(
            layerNumber, layerSpecificInformation, length
        )
        layer.beamData.parse(inputStream)
        layer.secondaryOpParameter1 = inputStream.read_uint8()
        layer.secondaryOpParameter2 = inputStream.read_uint8()
        numberOfIFFFundamentalParameterDataRecords = inputStream.read_uint16()
        layer.IFFFundamentalParameterDataRecord = [
            IFFFundamentalParameterData.parse(inputStream)
            for _ in range(numberOfIFFFundamentalParameterDataRecords)
        ]
        return layer
""",
    ),
    "IFFPduLayer3TransponderFormatData": MemberSource(
        after_methods=True,
        source="""@classmethod
def parseLayer(
        cls,
        inputStream: DataInputStream,
        layerNumber: int,
        layerSpecificInformation: int,
        length: int,
    ) -> "IFFPduLayer3TransponderFormatData":
        \"\"\"Construct the layer from its payload; the dispatching
        PDU has already read the four Layer Header bytes
        (layerNumber included).\"\"\"
        layer = cls()
        layer.layerHeader = LayerHeader(
            layerNumber, layerSpecificInformation, length
        )
        layer.siteNumber = inputStream.read_uint16()
        layer.applicationNumber = inputStream.read_uint16()
        mode5TransponderBasicData = Mode5TransponderBasicData()
        mode5TransponderBasicData.parse(inputStream)
        layer.mode5TransponderBasicData = mode5TransponderBasicData
        layer.padding = inputStream.read_uint16()
        numberOfIFFDataRecords = inputStream.read_uint16()
        layer.IFFFundamentalParameterDataRecord = [
            IFFData.parseFrom(inputStream) for _ in range(numberOfIFFDataRecords)
        ]
        return layer
""",
    ),
    "IFFPduLayer3InterrogatorFormatData": MemberSource(
        after_methods=True,
        source="""@classmethod
def parseLayer(
        cls,
        inputStream: DataInputStream,
        layerNumber: int,
        layerSpecificInformation: int,
        length: int,
    ) -> "IFFPduLayer3InterrogatorFormatData":
        \"\"\"Construct the layer from its payload; the dispatching
        PDU has already read the four Layer Header bytes
        (layerNumber included).\"\"\"
        layer = cls()
        layer.layerHeader = LayerHeader(
            layerNumber, layerSpecificInformation, length
        )
        layer.siteNumber = inputStream.read_uint16()
        layer.applicationNumber = inputStream.read_uint16()
        mode5InterrogatorBasicData = Mode5InterrogatorBasicData()
        mode5InterrogatorBasicData.parse(inputStream)
        layer.mode5InterrogatorBasicData = mode5InterrogatorBasicData
        layer.padding = inputStream.read_uint16()
        numberOfIFFDataRecords = inputStream.read_uint16()
        layer.IFFFundamentalParameterDataRecord = [
            IFFData.parseFrom(inputStream) for _ in range(numberOfIFFDataRecords)
        ]
        return layer
""",
    ),
    "IFFPduLayer4InterrogatorFormatData": MemberSource(
        after_methods=True,
        source="""@classmethod
def parseLayer(
        cls,
        inputStream: DataInputStream,
        layerNumber: int,
        layerSpecificInformation: int,
        length: int,
    ) -> "IFFPduLayer4InterrogatorFormatData":
        \"\"\"Construct the layer from its payload; the dispatching
        PDU has already read the four Layer Header bytes
        (layerNumber included).\"\"\"
        layer = cls()
        layer.layerHeader = LayerHeader(
            layerNumber, layerSpecificInformation, length
        )
        layer.siteNumber = inputStream.read_uint16()
        layer.applicationNumber = inputStream.read_uint16()
        modeSInterrogatorBasicData = ModeSInterrogatorBasicData()
        modeSInterrogatorBasicData.parse(inputStream)
        layer.modeSInterrogatorBasicData = modeSInterrogatorBasicData
        layer.padding = inputStream.read_uint16()
        numberOfIFFDataRecords = inputStream.read_uint16()
        layer.IFFFundamentalParameterDataRecord = [
            IFFData.parseFrom(inputStream) for _ in range(numberOfIFFDataRecords)
        ]
        return layer
""",
    ),
    "IFFPduLayer4TransponderFormatData": MemberSource(
        after_methods=True,
        source="""@classmethod
def parseLayer(
        cls,
        inputStream: DataInputStream,
        layerNumber: int,
        layerSpecificInformation: int,
        length: int,
    ) -> "IFFPduLayer4TransponderFormatData":
        \"\"\"Construct the layer from its payload; the dispatching
        PDU has already read the four Layer Header bytes
        (layerNumber included).\"\"\"
        layer = cls()
        layer.layerHeader = LayerHeader(
            layerNumber, layerSpecificInformation, length
        )
        layer.siteNumber = inputStream.read_uint16()
        layer.applicationNumber = inputStream.read_uint16()
        modeSTransponderBasicData = ModeSTransponderBasicData()
        modeSTransponderBasicData.parse(inputStream)
        layer.modeSTransponderBasicData = modeSTransponderBasicData
        layer.padding = inputStream.read_uint16()
        numberOfIFFDataRecords = inputStream.read_uint16()
        layer.IFFFundamentalParameterDataRecord = [
            IFFData.parseFrom(inputStream) for _ in range(numberOfIFFDataRecords)
        ]
        return layer
""",
    ),
    "IFFPduLayer5Data": MemberSource(
        after_methods=True,
        source="""@classmethod
def parseLayer(
        cls,
        inputStream: DataInputStream,
        layerNumber: int,
        layerSpecificInformation: int,
        length: int,
    ) -> "IFFPduLayer5Data":
        \"\"\"Construct the layer from its payload; the dispatching
        PDU has already read the four Layer Header bytes
        (layerNumber included).\"\"\"
        layer = cls()
        layer.layerHeader = LayerHeader(
            layerNumber, layerSpecificInformation, length
        )
        layer.siteNumber = inputStream.read_uint16()
        layer.applicationNumber = inputStream.read_uint16()
        layer.padding = inputStream.read_uint16()
        layer.applicableLayers = inputStream.read_uint8()
        layer.dataCategory = rich_or_int(369, inputStream.read_uint8())
        layer.padding2 = inputStream.read_uint16()
        numberOfIFFDataRecords = inputStream.read_uint16()
        layer.IFFFundamentalParameterDataRecord = [
            IFFData.parseFrom(inputStream) for _ in range(numberOfIFFDataRecords)
        ]
        return layer
""",
    ),
    "IdentificationFriendOrFoePdu": MemberSource(
        source="""def _layersInOrder(self) -> list:
    \"\"\"Present layers in numeric wire order (2, 3, 4, 5; one format
    per layer — Table 165 allows no duplicate layer numbers).\"\"\"
    return [
        layer
        for layer in (
            self.iFFPduLayer2Data,
            self.iFFPduLayer3Data,
            self.iFFPduLayer4Data,
            self.iFFPduLayer5Data,
        )
        if layer is not None
    ]

def _layerIsInterrogator(self, layerNumber: int) -> bool:
    \"\"\"Layer 3/4 format dispatch ([UID 82] + the CIT indicator).

    Interrogator sides: Mark XIIA Interrogator (6) and Mode 5
    Interrogator (7, Layer 3) or Mode S Interrogator (8, Layer 4); the
    Combined Interrogator/Transponders (12, 13) read their
    Change/Options Transponder/Interrogator Indicator (Table B.5 bit 4,
    B.5.13/.14) — Interrogator (1) sides with the interrogator format;
    everything else is the transponder format, the true complement
    (Layers 3/4 are Conditionally Required for any capable system type,
    B.5.1.1 b).
    \"\"\"
    systemType = int(self.systemID.systemType)
    if systemType in (6, 7 if layerNumber == 3 else 8):
        return True
    if systemType in (12, 13):
        return bool((int(self.systemID.changeOptions) >> 4) & 1)
    return False""",
    ),
}
