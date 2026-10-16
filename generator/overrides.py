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
        "BeamAntennaPattern",
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
PRIMITIVE_BINDINGS = {
    "EntityAppearance": "uint32",
    "ProtocolMode": "uint16",
    "EntityCapabilities": "uint32",
}

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
    "TransmitterPdu": [
        "variableTransmitterParameterCount",
        "modulationParameterCount",
        "antennaPatternCount",
        "modulationParametersList",
        "antennaPatternList",
    ],
    # SV records: the header fields are the kernel base's contract —
    # recordType is the curated registry ClassVar, recordLength the
    # derived marshalledSize property (§6.2.83)
    "DirectedEnergyDamage": ["recordType", "recordLength"],
    "DirectedEnergyAreaAimpoint": ["recordType", "recordLength"],
    "DirectedEnergyPrecisionAimpoint": ["recordType", "recordLength"],
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
    ("SimulationManagementWithReliabilityFamilyPdu", "originatingID"): "originatingEntityID",
    ("SimulationManagementWithReliabilityFamilyPdu", "receivingID"): "receivingEntityID",
    ("DataQueryReliablePdu", "fixedDatumRecords"): "fixedDatumIDs",
    ("DataQueryReliablePdu", "variableDatumRecords"): "variableDatumIDs",
    ("DataQueryReliablePdu", "numberOfFixedDatumRecords"): "numberOfFixedDatumIDs",
    ("DataQueryReliablePdu", "numberOfVariableDatumRecords"): "numberOfVariableDatumIDs",
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
EXTRA_FIELDS = {
    "TransferOwnershipPdu": [
        (
            "numberOfRecordSets",
            ir.Primitive(type="uint32"),
            "Number of record sets in the transfer",
            True,
            "recordSets",
        )
    ],
    "CommentPdu": [
        (
            "fixedDatumRecords",
            ir.ObjectList(element="FixedDatum", count_field="numberOfFixedDatumRecords"),
            "Fixed datum records (shall be zero on this PDU; kept for "
            "malformed-but-parseable datagrams)",
        )
    ],
    "TransmitterPdu": [
        (
            "modulationParameters",
            ir.OptionalRecord(target="ModulationParametersRecord"),
            "The Modulation Parameters record (single, Annex C; absent as None)",
        ),
        (
            "antennaPattern",
            ir.OptionalRecord(target="AntennaPatternRecord"),
            "The Antenna Pattern record (single, §6.2.8; absent as None)",
        ),
        (
            "variableTransmitterParameters",
            ir.ObjectList(
                element="StandardVariableRecord",
                count_field="variableTransmitterParameterCount",
            ),
            "Variable Transmitter Parameters (uid-66 records, registry decode)",
        ),
    ],
    "CommentReliablePdu": [
        (
            "fixedDatumRecords",
            ir.ObjectList(element="FixedDatum", count_field="numberOfFixedDatumRecords"),
            "Fixed datum records (shall be zero on this PDU; kept for "
            "malformed-but-parseable datagrams)",
        )
    ],
}

# (class, XML field) -> (annotation, default, rider|None) for fields whose
# shape is fully curated — the LE flag-conditional optionals. Owning
# classes carry METHOD_BODIES (presence dispatch is curated).
FIELD_OVERRIDES = {
    # Table 221 carries a 16-bit Appearance Flag-1 (the XML's uint8
    # under-sizes it — upstream candidate; exemplar math is Table-locked)
    ("AppearancePdu", "appearanceFlag1"): ("uint16", "0", None),
    ("AppearancePdu", "appearanceFlag2"): ("uint8 | None", "None", None),
    ("AppearancePdu", "forceId"): ("enum8 | None", "None", "[UID 6]"),
    ("AppearancePdu", "entityType"): ("EntityType | None", "None", None),
    ("AppearancePdu", "alternateEntityType"): ("EntityType | None", "None", None),
    ("AppearancePdu", "entityMarking"): ("EntityMarking | None", "None", None),
    ("AppearancePdu", "capabilities"): ("uint32 | None", "None", "[UID 55] bitmap"),
    ("AppearancePdu", "appearanceVisual"): ("uint32 | None", "None", "[UID 31-43]"),
    ("AppearancePdu", "appearanceIR"): ("uint32 | None", "None", None),
    ("AppearancePdu", "appearanceEM"): ("uint32 | None", "None", None),
    ("AppearancePdu", "appearanceAudio"): ("uint32 | None", "None", None),
    ("LEMunitionDescriptor", "warhead"): ("enum16 | None", "None", "[UID 60]"),
    ("LEMunitionDescriptor", "fuse"): ("enum16 | None", "None", "[UID 61]"),
    ("LEMunitionDescriptor", "quantity"): ("uint16 | None", "None", None),
    ("LEMunitionDescriptor", "rate"): ("uint16 | None", "None", None),
    ("LiveEntityFirePdu", "targetLiveEntityId"): (
        "LiveEntityIdentifier | None", "None", None),
    ("LiveEntityFirePdu", "munitionLiveEntityId"): (
        "LiveEntityIdentifierElided | LiveEntityIdentifier | None", "None", None),
    ("LiveEntityFirePdu", "eventId"): (
        "EventIdentifierLiveEntityElided | EventIdentifierLiveEntity",
        "field(default_factory=EventIdentifierLiveEntityElided)", None),
    ("LiveEntityFirePdu", "location"): (
        "LiveEntityRelativeWorldCoordinates | None", "None", None),
    ("LiveEntityDetonationPdu", "detonationFlag2"): ("uint8 | None", "None", None),
    ("LiveEntityDetonationPdu", "targetLiveEntityId"): (
        "LiveEntityIdentifier | None", "None", None),
    ("LiveEntityDetonationPdu", "munitionLiveEntityId"): (
        "LiveEntityIdentifierElided | LiveEntityIdentifier | None", "None", None),
    ("LiveEntityDetonationPdu", "eventId"): (
        "EventIdentifierLiveEntityElided | EventIdentifierLiveEntity | None",
        "None", None),
    ("LiveEntityDetonationPdu", "worldLocation"): (
        "LiveEntityRelativeWorldCoordinates | None", "None", None),
    ("LiveEntityDetonationPdu", "munitionOrientation"): (
        "LiveEntityOrientation16 | None", "None", None),
    ("LiveEntityDetonationPdu", "entityLocation"): (
        "LiveEntityRelativeEntityCoordinates | None", "None", None),
}
# (class, XML field name) -> hand-ruled shape replacing the XML's (the
# Data-Query datum-ID rebinding: §7.5.9 lists carry datum IDs, not
# FixedDatum records — the XML's objectlist classRef is wrong there).
FIELD_SHAPES = {
    ("DataQueryPdu", "fixedDatums"): ir.PrimitiveList(
        element="uint32", count_field="numberOfFixedDatumRecords", element_uid=66
    ),
    ("DataQueryPdu", "variableDatums"): ir.PrimitiveList(
        element="uint32", count_field="numberOfVariableDatumRecords", element_uid=66
    ),
    # Record Query-R: flat datum-ID list, not RecordQuerySpecification
    # records (§5.12.4.14; the XML's wrapper layer has no wire bytes)
    ("RecordQueryReliablePdu", "recordIDs"): ir.PrimitiveList(
        element="uint32", count_field="numberOfRecords", element_uid=66
    ),
    # Record-R / Set Record-R: flat record-set lists — the XML's
    # RecordSpecification wrapper adds a count the PDU already carries
    ("RecordReliablePdu", "recordSets"): ir.ObjectList(
        element="RecordSpecificationElement", count_field="numberOfRecordSets"
    ),
    ("SetRecordReliablePdu", "recordSets"): ir.ObjectList(
        element="RecordSpecificationElement", count_field="numberOfRecordSets"
    ),
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
    # TransferOwnership: flat record-set list (the XML's RecordSpecification
    # wrapper layer has no wire bytes; count rides the PDU)
    ("TransferOwnershipPdu", "recordSets"): ir.ObjectList(
        element="RecordSpecificationElement", count_field="numberOfRecordSets"
    ),
    # EnvironmentRecord: opaque geometry (bit-count expression length - 64)
    ("Environment", "geometry"): ir.BytesPayload(bit_count_field=None),
    # TSPI system-specific data: byte-counted payload (§9.4.2)
    ("TimeSpacePositionInformationPdu", "systemSpecificData"): ir.BytesPayload(
        bit_count_field="systemSpecificDataLength", count_is_bits=False
    ),
    ("MinefieldDataPdu", "vertices"): ir.ObjectList(
        element="Vector3Float", count_field="numberOfVertices"
    ),
}

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

# XML class -> uid-66 recordType value for the typed Standard Variable
# records generated into the family modules (2026-10-16 seam promotion).
# The XML declares recordType as a bare uint32 — the dispatch values live
# only in the standard's record tables (Table 44: Record Type = 4001) and
# the registry (opendis/record/__init__.py). Classes here resolve frozen
# on the kernel StandardVariableRecord base with an SV-header wire shape
# (recordType u32 + recordLength u16 written by the class, §6.2.83).
SV_RECORDS = {
    "DirectedEnergyDamage": 4500,
    "DirectedEnergyAreaAimpoint": 4001,
    "DirectedEnergyPrecisionAimpoint": 4000,
}

# XML class -> hand base class for records whose protocol home is a hand
# module (like KERNEL_BASES but without the PDU body-method split).
# BeamAntennaPattern subclasses the seam's AntennaPatternRecord
# (radio/annexc.py), keeping one VariableRecord dispatch spine for the
# Transmitter PDU's single antenna-pattern record.
RECORD_BASES = {
    "BeamAntennaPattern": "AntennaPatternRecord",
}

# (class, field) -> bitfield view class name attached unconditionally at
# parse (context-independent layouts only; kind-dependent wraps stay in
# PARSE_TAILS). Names ending in ``View`` import as aliases.
VIEW_ATTACHES = {
    ("DirectedEnergyFirePdu", "flags"): "DEFireFlagsView",
    ("StopFreezePdu", "frozenBehavior"): "StopFreezeFrozenBehavior",
    ("StopFreezeReliablePdu", "frozenBehavior"): "StopFreezeFrozenBehavior",
    ("MinefieldStatePdu", "appearance"): "MinefieldStateAppearance",
}

# class -> replacement leading §citation where the XML comment carries
# stale 1995-edition numbering (upstream campaign candidates; the body
# text stays XML-canonical).
DOCSTRING_CITES = {
    # XML comments still carry 1995-edition PDU numbering; the standard's
    # 2012 numbers rule (upstream campaign candidates, logged in the
    # milestones doc)
    "ServiceRequestPdu": "7.4.2",
    "ResupplyOfferPdu": "7.4.3",
    "ResupplyReceivedPdu": "7.4.4",
    "ResupplyCancelPdu": "7.4.5",
    "RepairCompletePdu": "7.4.6",
    "RepairResponsePdu": "7.4.7",
    "TransmitterPdu": "7.7.2",
    "SignalPdu": "7.7.3",
    "ReceiverPdu": "7.7.4",
    "IntercomSignalPdu": "7.7.6",
    "IntercomControlPdu": "7.7.7",
    "InformationOperationsActionPdu": "5.13.3",
    "InformationOperationsReportPdu": "5.13.4",
    "AggregateStatePdu": "7.8.2",
    "IsGroupOfPdu": "7.8.3",
    "TransferOwnershipPdu": "7.8.4",
    "IsPartOfPdu": "7.8.5",
    "MinefieldStatePdu": "7.9.2",
    "MinefieldQueryPdu": "7.9.3",
    "MinefieldDataPdu": "7.9.4",
    "MinefieldResponseNACKPdu": "7.9.5",
}

# module key -> verbatim import lines emitted after the docstring
# (stdlib imports the curated members need).
MODULE_IMPORT_LINES = {
    "simulation_management": ["import io"],
}

# (class, method) -> full parameter list for curated methods whose
# signatures carry more than the stream (LEMunitionDescriptor.parse).
METHOD_PARAMS = {
    ("LEMunitionDescriptor", "parse"): [
        "cls",
        "inputStream: DataInputStream",
        "includeWarheadFuse: bool",
        "includeQuantityRate: bool",
    ],
}

# class -> {method name -> verbatim body} replacing mechanical emission
# (bit-count payloads, packer-computed alignment pads, dispatch tails).
METHOD_BODIES = {
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
    EntityType.parse(inputStream) for _ in range(numberOfSilentAggregateTypes)
]
self.silentEntitySystemList = [
    EntityType.parse(inputStream) for _ in range(numberOfSilentEntityTypes)
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
Pattern records (the XML's objectlists are wrong there — the standard
allows one of each, §7.7.2/Annex C/§6.2.8) with byte-length counts, and
its VTP list decodes uid-66 records via the registry. The §6.2.8.2 Beam
Antenna Pattern record is generated here (header-less, Table 31 — the
Transmitter's ``antennaPatternType`` field types it); the Annex C
dispatch classes (GenericRadio, HAVE QUICK, SINCGARS, unknown
placeholders) live in the hand seam ``radio/annexc.py``. Signal
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
Environmental Process, Point/Linear/Areal Object State, plus the Object
Type/Identifier records, Linear Segment Parameter, and the generic
Environment record (opaque geometry, typed decoders deferred).

Scope note: GriddedDataPdu (type 42) — grid-axis descriptors × grid
data representation types 0–6 — is NOT implemented in this pass; its
pduType stays unregistered, so datagrams degrade to the lossless
``UnrecognizedPdu`` fallback (see docs/design/sample-review.md).

Python-side deltas from the XML (sample-review rulings): the bitfield-
mapped appearance/modification fields (uids 229, 240, 242, 249) stay raw
integers in this pass (views deferred, PduStatus precedent).
""",
    "distributed_emissions": """Distributed Emissions Regeneration family (IEEE 1278.1-2012 §7.6)
— target-state PDUs.

Wire ground truth: submodules/open-dis-spec-xml/xml/DistributedEmissionsFamilyPdus.xml.
Electromagnetic Emission, Designator, and Underwater Acoustic PDUs with
their emitter-system / beam record trees. The beam and system "data
length" fields count 32-bit words (§7.6.2) and are always derived
(``marshalledSize() // 4``; zero means the section is "large").

Scope note: the IFF PDU (type 28) and SEE PDU (type 30) with their
Annex-B layer structures are NOT implemented in this pass — their
pduTypes stay unregistered, so datagrams degrade to the lossless
``UnrecognizedPdu`` fallback (see docs/design/sample-review.md).
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
    "DirectedEnergyAreaAimpoint": """Uid-66 Standard Variable record decoded via the registry (dispatch
value 4001). The lists carry non-self-identifying records (§6.2.20.2):
Beam Antenna Pattern records (320 bits each, §6.2.8.2) and DE Target
Energy Deposition records (96 bits each, §6.2.20.4). The trailing pad
is packer-computed to the 64-bit boundary §6.2.83 requires.""",
    "DirectedEnergyPrecisionAimpoint": """Uid-66 Standard Variable record decoded via the registry (dispatch
value 4000, Table 46's format).""",
    "EntityInformationFamilyPdu": """Thin family marker — per-class identity lives in the ``pduType``/``protocolFamily`` ClassVars; family metadata for middleware lives in ``PDU_FAMILIES`` (opendis.record.factory).""",
    "EntityStatePdu": """``entityAppearance`` and ``capabilities`` hold the raw uint32 on the wire; after parsing a known entity kind they hold the matching bitfield view (``int(view)`` is the raw value, so round-trips are byte-exact and unknown bits survive).""",
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

    def __init__(self, source: str, needs_logger: bool = False, after_methods: bool = False):
        self.source = source
        self.needs_logger = needs_logger
        self.after_methods = after_methods


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
    "WarfareFamilyPdu": [
        ("protocolFamily", "2", "[UID 5] Warfare"),
    ],
    "FirePdu": [
        ("pduType", "2", "[UID 4]"),
    ],
    "DetonationPdu": [
        ("pduType", "3", "[UID 4]"),
    ],
    "DirectedEnergyFirePdu": [
        ("pduType", "68", "[UID 4]"),
    ],
    "EntityDamageStatusPdu": [
        ("pduType", "69", "[UID 4]"),
    ],
    # uid-66 dispatch values (Table 44/46; the XML's recordType primitives
    # carry no value — registry data, mirrored in record/__init__.py)
    "DirectedEnergyDamage": [
        ("recordType", "4500", "[UID 66] Variable Record Type"),
    ],
    "DirectedEnergyAreaAimpoint": [
        ("recordType", "4001", "[UID 66] Variable Record Type"),
    ],
    "DirectedEnergyPrecisionAimpoint": [
        ("recordType", "4000", "[UID 66] Variable Record Type"),
    ],
    "LogisticsFamilyPdu": [
        ("protocolFamily", "3", "[UID 5] Logistics"),
    ],
    "ServiceRequestPdu": [
        ("pduType", "5", "[UID 4]"),
    ],
    "ResupplyOfferPdu": [
        ("pduType", "6", "[UID 4]"),
    ],
    "ResupplyReceivedPdu": [
        ("pduType", "7", "[UID 4]"),
    ],
    "ResupplyCancelPdu": [
        ("pduType", "8", "[UID 4]"),
    ],
    "RepairCompletePdu": [
        ("pduType", "9", "[UID 4]"),
    ],
    "RepairResponsePdu": [
        ("pduType", "10", "[UID 4]"),
    ],
    "SimulationManagementFamilyPdu": [
        ("protocolFamily", "5", "[UID 5] Simulation Management"),
    ],
    "CreateEntityPdu": [
        ("pduType", "11", "[UID 4]"),
    ],
    "RemoveEntityPdu": [
        ("pduType", "12", "[UID 4]"),
    ],
    "StartResumePdu": [
        ("pduType", "13", "[UID 4]"),
    ],
    "StopFreezePdu": [
        ("pduType", "14", "[UID 4]"),
    ],
    "AcknowledgePdu": [
        ("pduType", "15", "[UID 4]"),
    ],
    "ActionRequestPdu": [
        ("pduType", "16", "[UID 4]"),
    ],
    "ActionResponsePdu": [
        ("pduType", "17", "[UID 4]"),
    ],
    "DataQueryPdu": [
        ("pduType", "18", "[UID 4]"),
    ],
    "SetDataPdu": [
        ("pduType", "19", "[UID 4]"),
    ],
    "DataPdu": [
        ("pduType", "20", "[UID 4]"),
    ],
    "EventReportPdu": [
        ("pduType", "21", "[UID 4]"),
    ],
    "CommentPdu": [
        ("pduType", "22", "[UID 4]"),
    ],
    "CreateEntityReliablePdu": [
        ("pduType", "51", "[UID 4]"),
    ],
    "RemoveEntityReliablePdu": [
        ("pduType", "52", "[UID 4]"),
    ],
    "StartResumeReliablePdu": [
        ("pduType", "53", "[UID 4]"),
    ],
    "StopFreezeReliablePdu": [
        ("pduType", "54", "[UID 4]"),
    ],
    "AcknowledgeReliablePdu": [
        ("pduType", "55", "[UID 4]"),
    ],
    "ActionRequestReliablePdu": [
        ("pduType", "56", "[UID 4]"),
    ],
    "ActionResponseReliablePdu": [
        ("pduType", "57", "[UID 4]"),
    ],
    "DataQueryReliablePdu": [
        ("pduType", "58", "[UID 4]"),
    ],
    "SetDataReliablePdu": [
        ("pduType", "59", "[UID 4]"),
    ],
    "DataReliablePdu": [
        ("pduType", "60", "[UID 4]"),
    ],
    "EventReportReliablePdu": [
        ("pduType", "61", "[UID 4]"),
    ],
    "CommentReliablePdu": [
        ("pduType", "62", "[UID 4]"),
    ],
    "RecordReliablePdu": [
        ("pduType", "63", "[UID 4]"),
    ],
    "SetRecordReliablePdu": [
        ("pduType", "64", "[UID 4]"),
    ],
    "RecordQueryReliablePdu": [
        ("pduType", "65", "[UID 4]"),
    ],
    "SimulationManagementWithReliabilityFamilyPdu": [
        ("protocolFamily", "10", "[UID 5] Simulation Management with Reliability"),
    ],
    "RadioCommunicationsFamilyPdu": [
        ("protocolFamily", "4", "[UID 5] Radio Communications"),
    ],
    "TransmitterPdu": [
        ("pduType", "25", "[UID 4]"),
    ],
    "SignalPdu": [
        ("pduType", "26", "[UID 4]"),
    ],
    "ReceiverPdu": [
        ("pduType", "27", "[UID 4]"),
    ],
    "IntercomSignalPdu": [
        ("pduType", "31", "[UID 4]"),
    ],
    "IntercomControlPdu": [
        ("pduType", "32", "[UID 4]"),
    ],
    "InformationOperationsFamilyPdu": [
        ("protocolFamily", "13", "[UID 5] Information Operations"),
    ],
    "InformationOperationsActionPdu": [
        ("pduType", "70", "[UID 4]"),
    ],
    "InformationOperationsReportPdu": [
        ("pduType", "71", "[UID 4]"),
    ],
    "EntityManagementFamilyPdu": [
        ("protocolFamily", "7", "[UID 5] Entity Management"),
    ],
    "AggregateStatePdu": [
        ("pduType", "33", "[UID 4]"),
    ],
    "IsGroupOfPdu": [
        ("pduType", "34", "[UID 4]"),
    ],
    "TransferOwnershipPdu": [
        ("pduType", "35", "[UID 4]"),
    ],
    "IsPartOfPdu": [
        ("pduType", "36", "[UID 4]"),
    ],
    "SyntheticEnvironmentFamilyPdu": [
        ("protocolFamily", "9", "[UID 5] Synthetic Environment"),
    ],
    "EnvironmentalProcessPdu": [
        ("pduType", "41", "[UID 4]"),
    ],
    "PointObjectStatePdu": [
        ("pduType", "43", "[UID 4]"),
    ],
    "LinearObjectStatePdu": [
        ("pduType", "44", "[UID 4]"),
    ],
    "ArealObjectStatePdu": [
        ("pduType", "45", "[UID 4]"),
    ],
    "DistributedEmissionsRegenerationFamilyPdu": [
        ("protocolFamily", "6", "[UID 5] Distributed Emissions Regeneration"),
    ],
    "ElectromagneticEmissionPdu": [
        ("pduType", "23", "[UID 4]"),
    ],
    "DesignatorPdu": [
        ("pduType", "24", "[UID 4]"),
    ],
    "UnderwaterAcousticPdu": [
        ("pduType", "29", "[UID 4]"),
    ],
    "LiveEntityFamilyPdu": [
        ("protocolFamily", "11", "[UID 5] Live Entity"),
    ],
    "TimeSpacePositionInformationPdu": [
        ("pduType", "46", "[UID 4]"),
    ],
    "AppearancePdu": [
        ("pduType", "47", "[UID 4]"),
    ],
    "ArticulatedPartsPdu": [
        ("pduType", "48", "[UID 4]"),
    ],
    "LiveEntityFirePdu": [
        ("pduType", "49", "[UID 4]"),
    ],
    "LiveEntityDetonationPdu": [
        ("pduType", "50", "[UID 4]"),
    ],
    "MinefieldFamilyPdu": [
        ("protocolFamily", "8", "[UID 5] Minefield"),
    ],
    "MinefieldStatePdu": [
        ("pduType", "37", "[UID 4]"),
    ],
    "MinefieldQueryPdu": [
        ("pduType", "38", "[UID 4]"),
    ],
    "MinefieldDataPdu": [
        ("pduType", "39", "[UID 4]"),
    ],
    "MinefieldResponseNACKPdu": [
        ("pduType", "40", "[UID 4]"),
    ],
}

# -- curated field furniture ----------------------------------------------

# (class, field) -> trailing rider where the mechanical [UID n] misses the
# exemplar text (primitive-bound classes carry no uid for the rider).
FIELD_RIDERS = {
    ("EntityStatePdu", "entityAppearance"): "[UID 31-43] or a bitfield view",
    ("EntityStatePdu", "capabilities"): "[UID 55] or a bitfield view",
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
    "entity_management": [
        (
            "EntityManagementFamilyPdu",
            '''def _padTo32(byteCount: int) -> int:
    \"\"\"Pad bytes needed to bring the PDU to a 32-bit boundary.\"\"\"
    return (4 - byteCount % 4) % 4''',
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
    "radio": {
        "opendis.record.radio.annexc": [
            "AntennaPatternRecord",
            "BasicHaveQuickMP",
            "ModulationParametersRecord",
            "CCTTSincgarsMP",
            "GenericRadio",
            "SimpleIntercomRadio",
            "UnknownAntennaPattern",
            "UnknownRadio",
        ],
    },
    "warfare": {
        "opendis.record.base": [
            "StandardVariableRecord",
        ],
    },
    "live_entity": {
        "opendis.record.common": [
            "EntityMarking",
            "EntityType",
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
        source='''@staticmethod
def _padTo64(byteCount: int) -> int:
    return (8 - byteCount % 8) % 8''',
    ),
}
