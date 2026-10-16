#!python
"""Tests for the DIS 7 target-state exemplar slice (branch dis7-ng).

Covers the acceptance criteria of docs/design/sample-code-kickoff.md:
unknown-pduType capture with byte-exact re-serialization, bitfield
unknown-bit preservation, and Timestamp wrap behavior — plus the design §2
construct categories the slice is meant to demonstrate. The old-vs-new
dis7.py transition-oracle parity tests retired with dis7.py itself
(2026-10-16 replacement review; the .raw corpus + verification harnesses
carry the wire guarantees now).
"""

import io
import struct
import unittest
from enum import IntEnum
from os import path

from opendis.bitfields import (
    AirPlatformAppearance,
    AirPlatformCapabilities,
    DEFireFlags,
    LandPlatformAppearance,
    LandPlatformCapabilities,
    SupplyAppearance,
)
from opendis.enum_registry import (
    register_enum_factory,
    unregister_enum_factory,
)
from opendis.record.base import FrozenRecord, Record, Serializable
from opendis.record.common import (
    EntityIdentifier,
    EntityMarking,
    EntityType,
    EulerAngles,
    EventIdentifier,
    MunitionDescriptor,
    SimulationAddress,
    Vector3Double,
    Vector3Float,
    WorldCoordinates,
)
from opendis.record.entity_management import (
    AggregateIdentifier,
    AggregateStatePdu,
    AggregateType,
    IsGroupOfPdu,
    IsPartOfPdu,
    NamedLocationIdentification,
    Relationship,
    SilentEntitySystem,
    TransferOwnershipPdu,
)
from opendis.record.minefield import (
    MineEmplacementTime,
    MinefieldDataPdu,
    MinefieldIdentifier,
    MinefieldQueryPdu,
    MinefieldResponseNACKPdu,
    MinefieldStatePdu,
    Vector2Float,
)
from opendis.bitfields import MinefieldStateAppearance
from opendis.record.information_operations import (
    InformationOperationsActionPdu,
    InformationOperationsReportPdu,
)
from opendis.record.live_entity import (
    AppearancePdu,
    ArticulatedPartsPdu,
    EventIdentifierLiveEntity,
    EventIdentifierLiveEntityElided,
    LEMunitionDescriptor,
    LiveEntityDetonationPdu,
    LiveEntityFirePdu,
    LiveEntityIdentifier,
    LiveEntityIdentifierElided,
    LiveSimulationAddress,
    TimeSpacePositionInformationPdu,
)
from opendis.record.logistics import (
    RepairCompletePdu,
    RepairResponsePdu,
    ResupplyCancelPdu,
    ResupplyOfferPdu,
    ServiceRequestPdu,
    SupplyQuantity,
)
from opendis.record.distributed_emissions import (
    APA,
    AcousticEmitter,
    BeamStatus,
    DesignatorPdu,
    EEFundamentalParameterData,
    ElectromagneticEmissionPdu,
    ElectronicEmitter,
    EmitterBeam,
    EmitterSystem,
    FundamentalOperationalData,
    IFFData,
    IFFFundamentalParameterData,
    IFFPduLayer2Data,
    IFFPduLayer3InterrogatorFormatData,
    IFFPduLayer3TransponderFormatData,
    IFFPduLayer5Data,
    IdentificationFriendOrFoePdu,
    JammingTechnique,
    LayerHeader,
    PropulsionSystemData,
    ShaftRPM,
    SupplementalEmissionEntityStatePdu,
    SystemIdentifier,
    TrackJamData,
    UABeam,
    UAEmitter,
    UAFundamentalParameter,
    UnderwaterAcousticPdu,
)
from opendis.record.entity_information import (
    Attribute,
    AttributePdu,
    AttributeRecordSet,
    CollisionElasticPdu,
    CollisionPdu,
    DeadReckoningParameters,
    EntityStatePdu,
    EntityStateUpdatePdu,
    VariableParameter,
)
from opendis.record.pdu import Pdu, PduHeader, UnrecognizedPdu
from opendis.record.factory import createPdu, createPduFromFilePath
from opendis.record.radio import (
    IntercomControlPdu,
    IntercomSignalPdu,
    ReceiverPdu,
    SignalPdu,
    TransmitterPdu,
)
from opendis.record.synthetic_environment import (
    ArealObjectStatePdu,
    EnvironmentRecord,
    EnvironmentalProcessPdu,
    GriddedDataPdu,
    GridAxisDescriptorFixed,
    GridAxisDescriptorVariable,
    GridDataType0,
    GridDataType1,
    GridDataType2,
    LinearObjectStatePdu,
    LinearSegmentParameter,
    ObjectIdentifier,
    ObjectType,
    PointObjectStatePdu,
)
from opendis.record.simulation_management_with_reliability import (
    CreateEntityReliablePdu,
    DataReliablePdu,
    RecordQueryReliablePdu,
    RecordReliablePdu,
    RecordSpecificationElement,
    StopFreezeReliablePdu,
)
from opendis.record.simulation_management import (
    AcknowledgePdu,
    ActionRequestPdu,
    ActionResponsePdu,
    CommentPdu,
    CreateEntityPdu,
    DataPdu,
    DataQueryPdu,
    EventReportPdu,
    FixedDatum,
    RemoveEntityPdu,
    SetDataPdu,
    StartResumePdu,
    StopFreezePdu,
    VariableDatum,
)
from opendis.bitfields import StopFreezeFrozenBehavior
from opendis.record.warfare import (
    DetonationPdu,
    DirectedEnergyFirePdu,
    EntityDamageStatusPdu,
    FirePdu,
)
from opendis.stream import DataInputStream, DataOutputStream
from opendis.timestamp import Timestamp

TEST_DIR = path.dirname(path.abspath(__file__))


class TestTimestamp(unittest.TestCase):

    def test_absolute_flag(self):
        self.assertTrue(Timestamp(1).isAbsolute)
        self.assertFalse(Timestamp(0).isAbsolute)
        self.assertTrue(Timestamp(0xFFFFFFFF).isAbsolute)

    def test_seconds_past_hour_bounds(self):
        self.assertEqual(Timestamp(0).secondsPastHour, 0.0)
        self.assertLess(Timestamp(0xFFFFFFFF).secondsPastHour, 3600.0)
        # max time is one unit (~1.676 µs) below the hour
        t = Timestamp(((1 << 31) - 1) << 1 | 1)
        self.assertGreater(t.secondsPastHour, 3600.0 - 1e-5)
        self.assertLess(t.secondsPastHour, 3600.0)

    def test_from_seconds_round_trip(self):
        t = Timestamp.fromSeconds(1234.5)
        self.assertTrue(t.isAbsolute)
        self.assertAlmostEqual(t.secondsPastHour, 1234.5, delta=1e-6)
        self.assertFalse(Timestamp.fromSeconds(10, absolute=False).isAbsolute)

    def test_wrap_across_hour_boundary(self):
        just_before = Timestamp.fromSeconds(3599.0)
        just_after = Timestamp.fromSeconds(0.5)  # next hour
        self.assertAlmostEqual(just_after.deltaSince(just_before), 1.5, delta=1e-4)
        # naive subtraction would give -3598.5
        backwards = just_before.deltaSince(just_after)
        self.assertAlmostEqual(backwards, 3598.5, delta=1e-4)

    def test_now(self):
        t = Timestamp.now()
        self.assertTrue(t.isAbsolute)
        self.assertTrue(0.0 <= t.secondsPastHour < 3600.0)

    def test_frozen_hashable(self):
        t = Timestamp(42)
        with self.assertRaises(Exception):
            t.raw = 43  # type: ignore[misc]
        self.assertEqual(hash(t), hash(Timestamp(42)))


class TestIdentityTypes(unittest.TestCase):

    def test_frozen(self):
        e = EntityIdentifier(SimulationAddress(1, 2), 3)
        with self.assertRaises(Exception):
            e.entityNumber = 9  # type: ignore[misc]
        with self.assertRaises(Exception):
            e.simulationAddress.site = 9  # type: ignore[misc]

    def test_hash_eq_dict_key(self):
        e = EntityIdentifier(SimulationAddress(1, 2), 3)
        table = {e: "tank"}
        self.assertEqual(table[EntityIdentifier(SimulationAddress(1, 2), 3)], "tank")

    def test_same_shaped_types_do_not_collide(self):
        e = EntityIdentifier(SimulationAddress(1, 2), 3)
        ev = EventIdentifier(SimulationAddress(1, 2), 3)
        self.assertNotEqual(e, ev)
        table = {e: "entity"}
        self.assertNotIn(ev, table)

    def test_wire_round_trip(self):
        e = EntityIdentifier(SimulationAddress(0x1234, 0x5678), 0x9ABC)
        buffer = io.BytesIO()
        e.serialize(DataOutputStream(buffer))
        self.assertEqual(buffer.getvalue().hex(), "123456789abc")
        parsed = EntityIdentifier.parse(DataInputStream(io.BytesIO(buffer.getvalue())))
        self.assertEqual(parsed, e)

    def test_sentinels(self):
        self.assertEqual(SimulationAddress.ALL_SITES, 0xFFFF)
        self.assertEqual(SimulationAddress.ALL_APPLICATIONS, 0xFFFF)
        self.assertEqual(EntityIdentifier.ALL_ENTITIES, 0xFFFF)

    def test_world_coordinates_alias(self):
        # ruled 2026-10-14: Vector3Double canonical, WorldCoordinates a
        # plain alias — never a second class
        self.assertIs(WorldCoordinates, Vector3Double)

    def test_protocol_split(self):
        # frozen records parse constructively (classmethod)
        self.assertIsInstance(EntityIdentifier(), FrozenRecord)
        self.assertIsInstance(EntityIdentifier(), Serializable)
        self.assertIsInstance(EventIdentifier(), FrozenRecord)
        self.assertIsInstance(EntityType(), FrozenRecord)
        # mutable records parse in place (instance method)
        self.assertIsInstance(Vector3Double(), Record)
        self.assertIsInstance(Vector3Double(), Serializable)
        # the runtime check cannot distinguish parse styles — both
        # provide a parse attribute; static checkers can and do
        self.assertIsInstance(EntityIdentifier(), Record)


class TestEntityMarkingTruncation(unittest.TestCase):

    def test_truncation_warns(self):
        marking = EntityMarking()
        with self.assertLogs("opendis.record.common", level="WARNING") as log:
            marking.string = "TWELVE-BYTES"  # 12 bytes
        self.assertIn("truncated", log.output[0])
        self.assertEqual(marking.string, "TWELVE-BYTE")
        self.assertEqual(len(marking.characters), 11)

    def test_exact_fit_does_not_warn(self):
        marking = EntityMarking()
        with self.assertNoLogs("opendis.record.common", level="WARNING"):
            marking.string = "ELEVENBYTES"  # exactly 11
        self.assertEqual(marking.string, "ELEVENBYTES")


class TestBitfieldViews(unittest.TestCase):

    def test_single_bit_properties(self):
        v = LandPlatformAppearance()
        self.assertFalse(v.paintScheme)
        v.paintScheme = True
        v.isFlaming = True
        v.occupantsSurrendered = True
        self.assertEqual(int(v), 1 | (1 << 15) | (1 << 30))
        v.isFlaming = False
        self.assertEqual(int(v), 1 | (1 << 30))

    def test_multi_bit_properties(self):
        v = LandPlatformAppearance()
        v.damage = 3  # [UID 379] destroyed
        v.primaryHatch = 4  # [UID 382] open
        v.camouflageType = 2  # [UID 384] forest
        self.assertEqual(v.damage, 3)
        self.assertEqual(v.primaryHatch, 4)
        self.assertEqual(v.camouflageType, 2)
        self.assertEqual(int(v), (3 << 3) | (4 << 9) | (2 << 17))

    def test_all_fields_round_trip(self):
        for view in (
            LandPlatformAppearance,
            AirPlatformAppearance,
            LandPlatformCapabilities,
            AirPlatformCapabilities,
        ):
            v = view(0)
            for name, shift, width, _uid in view._FIELDS:
                sample = (1 << width) - 1 if width > 1 else 1
                setattr(v, name, sample)
                self.assertEqual(getattr(v, name), sample, f"{view.__name__}.{name}")
                setattr(v, name, 0)
                self.assertEqual(int(v), 0)

    def test_unknown_and_reserved_bits_survive(self):
        # bits 4, 8, 11 are unassigned in the land layout; bit 5 of the
        # capabilities layout is reserved
        v = LandPlatformAppearance((1 << 4) | (1 << 8) | (1 << 11))
        v.damage = 2
        v.headLightsOn = True
        self.assertEqual(int(v), (1 << 4) | (1 << 8) | (1 << 11) | (2 << 3) | (1 << 12))
        c = LandPlatformCapabilities(1 << 5)
        c.repair = True
        self.assertEqual(int(c), (1 << 5) | (1 << 3))

    def test_int_interop(self):
        v = AirPlatformAppearance()
        v.damage = 1
        self.assertEqual(v.value, int(v))
        self.assertEqual(int(v) | 0, int(v))

    def test_setter_validation(self):
        v = LandPlatformAppearance()
        with self.assertRaises(ValueError):
            v.damage = 4  # 2-bit field
        with self.assertRaises(ValueError):
            v.damage = -1

    def test_repr_is_readable(self):
        v = LandPlatformAppearance()
        v.damage = 2
        v.isFlaming = True
        text = repr(v)
        self.assertIn("damage=2", text)
        self.assertIn("isFlaming=True", text)

    def test_view_masked_on_construction(self):
        self.assertEqual(int(LandPlatformAppearance(1 << 32)), 0)


class TestEntityStatePdu(unittest.TestCase):

    def test_default_size(self):
        self.assertEqual(EntityStatePdu().marshalledSize(), 144)
        self.assertEqual(EntityStatePdu().length, 144)

    def test_round_trip_with_view(self):
        pdu = EntityStatePdu()
        pdu.entityID = EntityIdentifier(SimulationAddress(42, 4), 26)
        pdu.forceId = 1
        pdu.entityType = EntityType(1, 1, 39, 1, 2, 3, 4)
        pdu.marking.string = "T-72"
        pdu.entityAppearance = LandPlatformAppearance()
        pdu.entityAppearance.damage = 2
        pdu.entityAppearance.isFlaming = True
        pdu.capabilities = LandPlatformCapabilities()
        pdu.capabilities.fuelSupply = True
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, EntityStatePdu)
        self.assertEqual(parsed.entityID, pdu.entityID)
        self.assertEqual(parsed.forceId, 1)
        self.assertEqual(parsed.marking.string, "T-72")
        self.assertIsInstance(parsed.entityAppearance, LandPlatformAppearance)
        self.assertEqual(parsed.entityAppearance.damage, 2)
        self.assertTrue(parsed.entityAppearance.isFlaming)
        self.assertIsInstance(parsed.capabilities, LandPlatformCapabilities)
        self.assertTrue(parsed.capabilities.fuelSupply)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_air_entity_gets_air_view(self):
        pdu = EntityStatePdu()
        pdu.entityType = EntityType(1, 2, 39)  # platform, air
        parsed = createPdu(pdu.to_bytes())
        self.assertIsInstance(parsed.entityAppearance, AirPlatformAppearance)
        self.assertIsInstance(parsed.capabilities, AirPlatformCapabilities)

    def test_unknown_kind_keeps_plain_int(self):
        # Phase 5 view extension: every kind 1-9 has a REF-010 appearance
        # table (kinds 2-9 wrap regardless of domain); the only no-table
        # case is kind 0 (Other)
        pdu = EntityStatePdu()
        pdu.entityType = EntityType(6, 0, 0)  # supply now wraps
        pdu.entityAppearance = 0xDEADBEEF
        parsed = createPdu(pdu.to_bytes())
        self.assertIsInstance(parsed.entityAppearance, SupplyAppearance)
        self.assertEqual(int(parsed.entityAppearance), 0xDEADBEEF)
        self.assertEqual(parsed.to_bytes(), pdu.to_bytes())

        plain = EntityStatePdu()
        plain.entityType = EntityType(0, 0, 0)  # kind 0: no table
        plain.entityAppearance = 0xDEADBEEF
        plain_parsed = createPdu(plain.to_bytes())
        self.assertIs(type(plain_parsed.entityAppearance), int)
        self.assertEqual(plain_parsed.to_bytes(), plain.to_bytes())

    def test_variable_parameters(self):
        pdu = EntityStatePdu()
        pdu.variableParameters.append(VariableParameter(1, bytes(range(15))))
        self.assertEqual(pdu.numberOfVariableParameters, 1)
        self.assertEqual(pdu.marshalledSize(), 160)
        parsed = createPdu(pdu.to_bytes())
        self.assertEqual(parsed.numberOfVariableParameters, 1)
        self.assertEqual(parsed.variableParameters[0].recordType, 1)
        self.assertEqual(
            parsed.variableParameters[0].recordSpecificFields, bytes(range(15))
        )

    def test_parse_does_not_append(self):
        pdu = EntityStatePdu()
        pdu.variableParameters.append(VariableParameter(1))
        raw = pdu.to_bytes()
        first = createPdu(raw)
        second = createPdu(raw)
        self.assertEqual(len(first.variableParameters), 1)
        # re-parsing a *new* instance is the factory path; a reused
        # instance must also replace, not append
        pdu.parse(DataInputStream(io.BytesIO(raw)))
        pdu.parse(DataInputStream(io.BytesIO(raw)))
        self.assertEqual(pdu.numberOfVariableParameters, 1)

    def test_dis6_capture_byte_exact(self):
        with open(path.join(TEST_DIR, "EntityStatePdu-26.raw"), "rb") as f:
            raw = f.read()
        pdu = createPdu(raw)
        self.assertIsInstance(pdu, EntityStatePdu)
        self.assertEqual(pdu.header.protocolVersion, 6)
        self.assertEqual(pdu.entityID.entityNumber, 26)
        self.assertEqual(pdu.forceId, 1)
        self.assertEqual(pdu.marking.string, "26")
        self.assertEqual(pdu.to_bytes(), raw)

    def test_header_delegation(self):
        pdu = EntityStatePdu()
        pdu.exerciseID = 7
        pdu.timestamp = Timestamp(123)
        self.assertEqual(pdu.header.exerciseID, 7)
        self.assertEqual(pdu.timestamp.raw, 123)
        self.assertEqual(pdu.pduType, 1)
        self.assertEqual(pdu.protocolFamily, 1)
        self.assertEqual(pdu.protocolVersion, 7)

    def test_wire_length_evidence(self):
        pdu = EntityStatePdu()
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertEqual(parsed.header._wireLength, 144)


class TestDataPdu(unittest.TestCase):

    def test_round_trip_with_datums(self):
        pdu = DataPdu()
        pdu.requestID = 0xCAFEBABE
        pdu.originatingEntityID = EntityIdentifier(SimulationAddress(1, 1), 2)
        pdu.fixedDatumRecords.append(FixedDatum(10, 20))
        pdu.fixedDatumRecords.append(FixedDatum(11, 21))
        pdu.variableDatumRecords.append(VariableDatum(1, b"allunits"))
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, DataPdu)
        self.assertEqual(parsed.requestID, 0xCAFEBABE)
        self.assertEqual(parsed.numberOfFixedDatumRecords, 2)
        self.assertEqual(parsed.numberOfVariableDatumRecords, 1)
        self.assertEqual(parsed.fixedDatumRecords[1].fixedDatumValue, 21)
        self.assertEqual(parsed.variableDatumRecords[0].variableData, b"allunits")
        self.assertEqual(parsed.variableDatumRecords[0].variableDatumLength, 64)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_datum_padding_to_64_bits(self):
        # 5-byte payload needs 3 pad bytes -> record is 8+8=16 bytes
        pdu = DataPdu()
        pdu.variableDatumRecords.append(VariableDatum(66, b"abcde"))
        self.assertEqual(pdu.variableDatumRecords[0].marshalledSize(), 16)
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertEqual(parsed.variableDatumRecords[0].variableData, b"abcde")
        self.assertEqual(parsed.to_bytes(), raw)
        # 8-byte payload needs no padding -> 8+8=16
        pdu2 = DataPdu()
        pdu2.variableDatumRecords.append(VariableDatum(66, b"12345678"))
        self.assertEqual(pdu2.variableDatumRecords[0].marshalledSize(), 16)

    def test_typed_uid66_decoder(self):
        from opendis.record.warfare import DirectedEnergyDamage

        record = DirectedEnergyDamage()
        record.damageDiameter = 1.5
        buffer = io.BytesIO()
        record.serialize(DataOutputStream(buffer))
        # StandardVariableRecord.serialize writes the record header once
        # (issue #89 fix, PR #90, applied on this branch).
        canonical = buffer.getvalue()
        self.assertEqual(canonical[:4], b"\x00\x00\x11\x94")  # 4500
        self.assertEqual(len(canonical), 40)
        pdu = DataPdu()
        pdu.variableDatumRecords.append(VariableDatum(4500, canonical))
        parsed = createPdu(pdu.to_bytes())
        decoded = parsed.variableDatumRecords[0].decodedRecord
        self.assertIsInstance(decoded, DirectedEnergyDamage)
        self.assertAlmostEqual(decoded.damageDiameter, 1.5, places=6)

    def test_unknown_record_type_stays_raw(self):
        pdu = DataPdu()
        pdu.variableDatumRecords.append(VariableDatum(0xABCDEF, b"\x01\x02"))
        parsed = createPdu(pdu.to_bytes())
        self.assertIsNone(parsed.variableDatumRecords[0].decodedRecord)
        self.assertEqual(parsed.variableDatumRecords[0].variableData, b"\x01\x02")
        self.assertEqual(parsed.to_bytes(), pdu.to_bytes())

    def test_malformed_known_record_degrades_to_bytes(self):
        pdu = DataPdu()
        pdu.variableDatumRecords.append(VariableDatum(4500, b"\xff"))
        parsed = createPdu(pdu.to_bytes())
        self.assertIsNone(parsed.variableDatumRecords[0].decodedRecord)
        self.assertEqual(parsed.variableDatumRecords[0].variableData, b"\xff")

    def test_padding_attribute_out_of_init(self):
        pdu = DataPdu()
        self.assertEqual(pdu.padding1, 0)
        with self.assertRaises(TypeError):
            DataPdu(padding1=1)  # excluded from __init__ per the ruling
        pdu.padding1 = 5
        parsed = createPdu(pdu.to_bytes())
        self.assertEqual(parsed.padding1, 5)

    def test_padding_wire_value_preserved(self):
        pdu = DataPdu()
        pdu.fixedDatumRecords.append(FixedDatum(1, 2))
        raw = bytearray(pdu.to_bytes())
        raw[28:32] = b"\xde\xad\xbe\xef"  # padding1 slot
        parsed = createPdu(bytes(raw))
        self.assertEqual(parsed.padding1, 0xDEADBEEF)
        self.assertEqual(parsed.to_bytes(), bytes(raw))

    def test_header_padding_byte_preserved(self):
        raw = bytearray(EntityStatePdu().to_bytes())
        raw[11] = 0xAB  # header pad byte
        parsed = createPdu(bytes(raw))
        self.assertEqual(parsed.header.padding, 0xAB)
        self.assertEqual(parsed.to_bytes(), bytes(raw))


class TestWarfareFamily(unittest.TestCase):
    """Fire/Detonation/DE-Fire/Entity-Damage-Status in the target-state
    style (submodules/open-dis-spec-xml/xml/WarfareFamilyPdus.xml ground truth)."""

    def test_fire_default_size_768_bits(self):
        self.assertEqual(FirePdu().marshalledSize(), 96)

    def test_fire_round_trip(self):
        pdu = FirePdu()
        pdu.firingEntityID = EntityIdentifier(SimulationAddress(1, 2), 3)
        pdu.targetEntityID = EntityIdentifier(SimulationAddress(4, 5), 6)
        pdu.munitionExpendibleID = EntityIdentifier(SimulationAddress(7, 8), 9)
        pdu.eventID = EventIdentifier(SimulationAddress(1, 2), 77)
        pdu.fireMissionIndex = 0x01020304
        pdu.locationInWorldCoordinates = WorldCoordinates(1.0, 2.0, 3.0)
        pdu.descriptor = MunitionDescriptor(
            EntityType(1, 1, 39, 3, 1), 1000, 2000, 5, 10
        )
        pdu.velocity = Vector3Float(4.0, 5.0, 6.0)
        pdu.range = 1234.5
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, FirePdu)
        self.assertEqual(parsed.eventID.eventNumber, 77)
        self.assertEqual(parsed.descriptor.warhead, 1000)
        self.assertEqual(parsed.descriptor.quantity, 5)
        self.assertAlmostEqual(parsed.range, 1234.5, places=4)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_detonation_default_size_832_bits(self):
        self.assertEqual(DetonationPdu().marshalledSize(), 104)
        pdu = DetonationPdu()
        pdu.variableParameters.append(VariableParameter(1))
        self.assertEqual(pdu.marshalledSize(), 104 + 16)

    def test_detonation_round_trip_with_variable_parameters(self):
        pdu = DetonationPdu()
        pdu.sourceEntityID = EntityIdentifier(SimulationAddress(1, 1), 11)
        pdu.detonationResult = 3
        pdu.variableParameters.append(VariableParameter(1, bytes(range(15))))
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, DetonationPdu)
        self.assertEqual(parsed.numberOfVariableParameters, 1)
        self.assertEqual(
            parsed.variableParameters[0].recordSpecificFields, bytes(range(15))
        )
        self.assertEqual(parsed.to_bytes(), raw)

    def test_de_fire_default_size_and_flags_view(self):
        pdu = DirectedEnergyFirePdu()
        self.assertEqual(pdu.marshalledSize(), 88)
        pdu.flags = DEFireFlags(0)
        pdu.flags.weaponOn = True
        pdu.pulseShape = 2
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertIsInstance(parsed.flags, DEFireFlags)
        self.assertTrue(parsed.flags.weaponOn)
        self.assertFalse(parsed.flags.stateUpdateFlag)
        self.assertEqual(parsed.pulseShape, 2)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_de_fire_sv_record_list_round_trip(self):
        from opendis.record.warfare import DirectedEnergyDamage

        pdu = DirectedEnergyFirePdu()
        record = DirectedEnergyDamage()
        record.damageDiameter = 2.5
        pdu.dERecords.append(record)
        self.assertEqual(pdu.numberOfDERecords, 1)
        self.assertEqual(pdu.marshalledSize(), 88 + 40)
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertIsInstance(parsed.dERecords[0], DirectedEnergyDamage)
        self.assertAlmostEqual(parsed.dERecords[0].damageDiameter, 2.5, places=6)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_area_aimpoint_64_bit_pad_and_round_trip(self):
        # Table 44: 96 fixed bits + 320N + 96M + 8P — the trailing pad
        # rides the SV record to the 64-bit boundary §6.2.83 requires
        # (generated output; the promoted seam class had no pad at all).
        from opendis.record import parseStandardVariableRecord
        from opendis.record.radio import BeamAntennaPattern
        from opendis.record.warfare import (
            DirectedEnergyAreaAimpoint,
            DirectedEnergyTargetEnergyDeposition,
        )

        record = DirectedEnergyAreaAimpoint()
        self.assertEqual(record.marshalledSize(), 16)
        record.beamAntennaParameterList.append(BeamAntennaPattern())
        record.directedEnergyTargetEnergyDepositionRecordList.append(
            DirectedEnergyTargetEnergyDeposition()
        )
        # 6 + 2 + 4 + 40 + 12 = 64 — already 64-bit aligned, no pad
        self.assertEqual(record.marshalledSize(), 64)
        buffer = io.BytesIO()
        record.serialize(DataOutputStream(buffer))
        self.assertEqual(len(buffer.getvalue()), 64)
        decoded = parseStandardVariableRecord(
            DataInputStream(io.BytesIO(buffer.getvalue()))
        )
        self.assertIsInstance(decoded, DirectedEnergyAreaAimpoint)
        self.assertEqual(len(decoded.beamAntennaParameterList), 1)
        self.assertEqual(len(decoded.directedEnergyTargetEnergyDepositionRecordList), 1)
        self.assertEqual(decoded.marshalledSize(), 64)

    def test_entity_damage_status_unknown_sv_stays_raw(self):
        from opendis.record import getStandardVariableClass

        pdu = EntityDamageStatusPdu()
        self.assertEqual(pdu.marshalledSize(), 24)
        # an unregistered uid-66 record type parses as the opaque
        # placeholder and re-serializes byte-exact
        pdu.damageDescriptionRecords.append(
            getStandardVariableClass(0xABCD)(b"\xee" * 10)
        )
        self.assertEqual(pdu.numberOfDamageDescription, 1)
        raw = pdu.to_bytes()
        self.assertEqual(len(raw), 24 + 16)
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, EntityDamageStatusPdu)
        self.assertEqual(parsed.numberOfDamageDescription, 1)
        unknown = parsed.damageDescriptionRecords[0]
        self.assertEqual(int(unknown.recordType), 0xABCD)
        self.assertEqual(unknown.data, b"\xee" * 10)
        self.assertEqual(parsed.to_bytes(), raw)


class TestRadioFamily(unittest.TestCase):
    """Radio Communications family in the target-state style
    (submodules/open-dis-spec-xml/xml/RadioCommunicationsFamilyPdus.xml ground truth).
    """

    def test_transmitter_default_size(self):
        self.assertEqual(TransmitterPdu().marshalledSize(), 104)

    def test_transmitter_round_trip_with_havequick(self):
        from opendis.record.radio.annexc import BasicHaveQuickMP

        pdu = TransmitterPdu()
        pdu.radioReferenceID = EntityIdentifier(SimulationAddress(5, 6), 7)
        pdu.radioNumber = 2
        pdu.transmitState = 2
        pdu.frequency = 0x0000167E_9B840000  # ~300 MHz scaled example
        pdu.modulationType.radioSystem = 2  # HAVE QUICK
        pdu.modulationParameters = BasicHaveQuickMP()
        raw = pdu.to_bytes()
        self.assertEqual(pdu.modulationParameterCount, 16)
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, TransmitterPdu)
        self.assertIsInstance(parsed.modulationParameters, BasicHaveQuickMP)
        self.assertEqual(parsed.radioNumber, 2)
        self.assertEqual(parsed.frequency, pdu.frequency)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_transmitter_antenna_pattern(self):
        from opendis.record.radio import BeamAntennaPattern

        pdu = TransmitterPdu()
        pdu.antennaPatternType = 1
        pdu.antennaPattern = BeamAntennaPattern()
        self.assertEqual(pdu.antennaPatternCount, 40)
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertIsInstance(parsed.antennaPattern, BeamAntennaPattern)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_unknown_antenna_pattern_consumes_full_length(self):
        # §6.2.8: Antenna Pattern records are non-self-identifying — no
        # 6-byte record header precedes the pattern data (Table 31), so
        # the placeholder consumes the full record length. Regression
        # lock: the seam's ``bytelength - 6`` left 6 bytes unparsed and
        # desynchronized the PDU.
        from opendis.record.radio.annexc import UnknownAntennaPattern

        pdu = TransmitterPdu()
        pdu.antennaPatternType = 2
        pdu.antennaPattern = UnknownAntennaPattern(b"\xab" * 24)
        raw = pdu.to_bytes()
        self.assertEqual(pdu.antennaPatternCount, 24)
        parsed = createPdu(raw)
        self.assertIsInstance(parsed.antennaPattern, UnknownAntennaPattern)
        self.assertEqual(parsed.antennaPattern.data, b"\xab" * 24)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_signal_bit_length_and_alignment(self):
        pdu = SignalPdu()
        pdu.radioReferenceID = EntityIdentifier(SimulationAddress(1, 1), 9)
        pdu.encodingScheme = 1
        pdu.sampleRate = 8000
        pdu.samples = 3
        pdu.data = b"\x01\x02\x03"  # 3 bytes -> 24 bits, 1 pad byte to 32-bit
        self.assertEqual(pdu.dataLength, 24)
        self.assertEqual(pdu.marshalledSize() % 4, 0)
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, SignalPdu)
        self.assertEqual(parsed.data, b"\x01\x02\x03")
        self.assertEqual(parsed.dataLength, 24)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_signal_empty_data_no_padding(self):
        pdu = SignalPdu()
        self.assertEqual(pdu.marshalledSize(), 12 + 20)
        parsed = createPdu(pdu.to_bytes())
        self.assertEqual(parsed.data, b"")
        self.assertEqual(parsed.to_bytes(), pdu.to_bytes())

    def test_receiver_size_and_round_trip(self):
        pdu = ReceiverPdu()
        self.assertEqual(pdu.marshalledSize(), 36)
        pdu.receiverState = 1
        pdu.receivedPower = -42.5
        pdu.transmitterEntityId = EntityIdentifier(SimulationAddress(2, 3), 4)
        pdu.transmitterRadioId = 8
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, ReceiverPdu)
        self.assertAlmostEqual(parsed.receivedPower, -42.5, places=4)
        self.assertEqual(parsed.transmitterRadioId, 8)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_intercom_signal_round_trip(self):
        from opendis.record.radio import IntercomReferenceID

        pdu = IntercomSignalPdu()
        pdu.intercomReferenceID = IntercomReferenceID(1, 2, 3)
        pdu.intercomNumber = 4
        pdu.data = b"\xaa\xbb\xcc\xdd\xee\xff"  # 6 bytes -> 2 pad bytes
        self.assertEqual(pdu.dataLength, 48)
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, IntercomSignalPdu)
        self.assertEqual(parsed.intercomReferenceID.referenceNumber, 3)
        self.assertEqual(parsed.data, b"\xaa\xbb\xcc\xdd\xee\xff")
        self.assertEqual(parsed.to_bytes(), raw)

    def test_intercom_control_round_trip(self):
        from opendis.record.radio import IntercomCommunicationsParameters

        pdu = IntercomControlPdu()
        pdu.controlType = 1
        pdu.command = 2
        parameter = IntercomCommunicationsParameters(1, 2, b"\x07\x08")
        pdu.intercomParameters.append(parameter)
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, IntercomControlPdu)
        self.assertEqual(parsed.intercomParametersLength, 1)
        self.assertEqual(parsed.intercomParameters[0].recordSpecificField, b"\x07\x08")
        self.assertEqual(parsed.to_bytes(), raw)


class TestSimulationManagementFamily(unittest.TestCase):
    """Remaining §7.5 PDUs in the target-state style
    (submodules/open-dis-spec-xml/xml/SimulationManagementFamilyPdus.xml ground truth).
    """

    def test_create_remove_sizes(self):
        self.assertEqual(CreateEntityPdu().marshalledSize(), 28)
        self.assertEqual(RemoveEntityPdu().marshalledSize(), 28)

    def test_create_entity_round_trip(self):
        pdu = CreateEntityPdu()
        pdu.originatingEntityID = EntityIdentifier(SimulationAddress(1, 1), 0)
        pdu.receivingEntityID = EntityIdentifier(SimulationAddress(2, 2), 0)
        pdu.requestID = 77
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, CreateEntityPdu)
        self.assertEqual(parsed.requestID, 77)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_start_resume_round_trip(self):
        from opendis.record.common import ClockTime

        pdu = StartResumePdu()
        pdu.realWorldTime = ClockTime(3600, 120)
        pdu.simulationTime = ClockTime(0, 60)
        pdu.requestID = 5
        raw = pdu.to_bytes()
        self.assertEqual(len(raw), 44)
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, StartResumePdu)
        self.assertEqual(parsed.realWorldTime.hour, 3600)
        self.assertEqual(parsed.simulationTime.timePastHour, 60)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_stop_freeze_frozen_behavior_view(self):
        pdu = StopFreezePdu()
        self.assertEqual(pdu.marshalledSize(), 40)
        pdu.reason = 2  # [UID 67] system restart
        behavior = StopFreezeFrozenBehavior()
        behavior.runSimulationClock = True
        behavior.processUpdates = True
        pdu.frozenBehavior = behavior
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, StopFreezePdu)
        self.assertIsInstance(parsed.frozenBehavior, StopFreezeFrozenBehavior)
        self.assertTrue(parsed.frozenBehavior.runSimulationClock)
        self.assertFalse(parsed.frozenBehavior.transmitUpdates)
        self.assertTrue(parsed.frozenBehavior.processUpdates)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_acknowledge_round_trip(self):
        pdu = AcknowledgePdu()
        pdu.acknowledgeFlag = 2  # [UID 69] Stop/Freeze
        pdu.responseFlag = 1  # [UID 70] able to comply
        pdu.requestID = 9
        raw = pdu.to_bytes()
        self.assertEqual(len(raw), 32)
        parsed = createPdu(raw)
        self.assertEqual(parsed.acknowledgeFlag, 2)
        self.assertEqual(parsed.responseFlag, 1)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_action_request_datums(self):
        pdu = ActionRequestPdu()
        pdu.requestID = 3
        pdu.actionID = 2  # [UID 71] start timer
        pdu.fixedDatumRecords.append(FixedDatum(1000, 222))
        pdu.variableDatumRecords.append(VariableDatum(1, b"payload!"))
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, ActionRequestPdu)
        self.assertEqual(parsed.numberOfFixedDatumRecords, 1)
        self.assertEqual(parsed.numberOfVariableDatumRecords, 1)
        self.assertEqual(parsed.fixedDatumRecords[0].fixedDatumValue, 222)
        self.assertEqual(parsed.variableDatumRecords[0].variableData, b"payload!")
        self.assertEqual(parsed.to_bytes(), raw)

    def test_action_response_round_trip(self):
        pdu = ActionResponsePdu()
        pdu.requestID = 4
        pdu.requestStatus = 1
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, ActionResponsePdu)
        self.assertEqual(parsed.requestStatus, 1)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_data_query_carries_datum_ids(self):
        pdu = DataQueryPdu()
        pdu.requestID = 8
        pdu.timeInterval = 10
        pdu.fixedDatumIDs.extend((1000, 1001, 1002))
        pdu.variableDatumIDs.append(2000)
        raw = pdu.to_bytes()
        self.assertEqual(len(raw), 40 + 4 * 4)
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, DataQueryPdu)
        self.assertEqual(parsed.fixedDatumIDs, [1000, 1001, 1002])
        self.assertEqual(parsed.variableDatumIDs, [2000])
        self.assertEqual(parsed.to_bytes(), raw)

    def test_set_data_round_trip(self):
        pdu = SetDataPdu()
        pdu.requestID = 11
        pdu.fixedDatumRecords.append(FixedDatum(10, 20))
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, SetDataPdu)
        self.assertEqual(parsed.fixedDatumRecords[0].fixedDatumID, 10)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_event_report_round_trip(self):
        pdu = EventReportPdu()
        pdu.eventType = 3  # [UID 73]
        pdu.variableDatumRecords.append(VariableDatum(1, b"abcde"))
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, EventReportPdu)
        self.assertEqual(parsed.eventType, 3)
        self.assertEqual(parsed.variableDatumRecords[0].variableData, b"abcde")
        self.assertEqual(parsed.to_bytes(), raw)

    def test_comment_round_trip(self):
        pdu = CommentPdu()
        pdu.variableDatumRecords.append(VariableDatum(1000, b"hello msg"))
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, CommentPdu)
        self.assertEqual(parsed.numberOfFixedDatumRecords, 0)
        self.assertEqual(parsed.numberOfVariableDatumRecords, 1)
        self.assertEqual(parsed.variableDatumRecords[0].variableData, b"hello msg")
        self.assertEqual(parsed.to_bytes(), raw)


class TestSimulationManagementReliableFamily(unittest.TestCase):
    """-R family PDUs (§5.12.4): reliability header + datum/record tails."""

    def test_create_entity_reliable_round_trip(self):
        pdu = CreateEntityReliablePdu()
        pdu.requiredReliabilityService = 2  # [UID 74] acknowledged
        pdu.requestID = 100
        raw = pdu.to_bytes()
        self.assertEqual(len(raw), 32)
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, CreateEntityReliablePdu)
        self.assertEqual(parsed.requiredReliabilityService, 2)
        self.assertEqual(parsed.requestID, 100)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_stop_freeze_reliable_round_trip(self):
        pdu = StopFreezeReliablePdu()
        behavior = StopFreezeFrozenBehavior()
        behavior.transmitUpdates = True
        pdu.frozenBehavior = behavior
        pdu.reason = 4  # [UID 67] emergency stop
        raw = pdu.to_bytes()
        self.assertEqual(len(raw), 40)
        parsed = createPdu(raw)
        self.assertTrue(parsed.frozenBehavior.transmitUpdates)
        self.assertEqual(parsed.reason, 4)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_data_reliable_datums(self):
        pdu = DataReliablePdu()
        pdu.requestID = 7
        pdu.fixedDatumRecords.append(FixedDatum(1, 2))
        raw = pdu.to_bytes()
        self.assertEqual(len(raw), 40 + 8)
        parsed = createPdu(raw)
        self.assertEqual(parsed.fixedDatumRecords[0].fixedDatumValue, 2)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_record_reliable_record_sets(self):
        pdu = RecordReliablePdu()
        pdu.eventType = 1
        recordSet = RecordSpecificationElement(3300, 1, 64, 2, b"\x00" * 16)
        pdu.recordSets.append(recordSet)
        self.assertEqual(recordSet.marshalledSize(), 14 + 16 + 2)  # padTo64
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, RecordReliablePdu)
        self.assertEqual(parsed.numberOfRecordSets, 1)
        self.assertEqual(parsed.recordSets[0].recordID, 3300)
        self.assertEqual(parsed.recordSets[0].recordCount, 2)
        self.assertEqual(parsed.recordSets[0].recordValues, b"\x00" * 16)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_record_query_reliable_ids(self):
        pdu = RecordQueryReliablePdu()
        pdu.requestID = 5
        pdu.eventType = 1
        pdu.time = 60
        pdu.recordIDs.extend((3300, 3301))
        raw = pdu.to_bytes()
        self.assertEqual(len(raw), 40 + 8)
        parsed = createPdu(raw)
        self.assertEqual(parsed.recordIDs, [3300, 3301])
        self.assertEqual(parsed.to_bytes(), raw)

    def test_r_abbreviations_are_aliases(self):
        import opendis.record.simulation_management_with_reliability as smr

        self.assertIs(smr.CreateEntityRPdu, smr.CreateEntityReliablePdu)
        self.assertIs(smr.RecordRPdu, smr.RecordReliablePdu)
        self.assertIs(smr.CommentRPdu, smr.CommentReliablePdu)


class TestLogisticsFamily(unittest.TestCase):
    """Logistics family (§7.4): service/resupply/repair PDUs."""

    def test_service_request_round_trip(self):
        pdu = ServiceRequestPdu()
        pdu.requestingEntityID = EntityIdentifier(SimulationAddress(1, 1), 2)
        pdu.servicingEntityID = EntityIdentifier(SimulationAddress(3, 3), 4)
        pdu.serviceTypeRequested = 1  # [UID 63] resupply
        pdu.supplies.append(SupplyQuantity(EntityType(1, 1, 39, 5), 100.0))
        raw = pdu.to_bytes()
        self.assertEqual(len(raw), 28 + 12)
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, ServiceRequestPdu)
        self.assertEqual(parsed.numberOfSupplyTypes, 1)
        self.assertAlmostEqual(parsed.supplies[0].quantity, 100.0, places=4)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_resupply_offer_received_cancel(self):
        offer = ResupplyOfferPdu()
        offer.supplies.append(SupplyQuantity(EntityType(1, 1, 39, 5), 3.0))
        raw = offer.to_bytes()
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, ResupplyOfferPdu)
        self.assertEqual(parsed.to_bytes(), raw)

        from opendis.record.logistics import ResupplyReceivedPdu

        received = ResupplyReceivedPdu()
        raw = received.to_bytes()
        self.assertEqual(len(raw), 28)
        self.assertIsInstance(createPdu(raw), ResupplyReceivedPdu)

        cancel = ResupplyCancelPdu()
        raw = cancel.to_bytes()
        self.assertEqual(len(raw), 24)
        self.assertIsInstance(createPdu(raw), ResupplyCancelPdu)

    def test_repair_pdus_round_trip(self):
        complete = RepairCompletePdu()
        complete.repair = 1  # [UID 64] scheduled maintenance?
        raw = complete.to_bytes()
        self.assertEqual(len(raw), 28)
        parsed = createPdu(raw)
        self.assertEqual(parsed.repair, 1)
        self.assertEqual(parsed.to_bytes(), raw)

        response = RepairResponsePdu()
        response.repairResult = 2
        # 28 bytes (224 bits) per §7.4.7: repairResult is enum8 [UID 65]
        # (REF-010 + legacy dis7.py corroborate; the hand exemplar's
        # enum16/uid-64 was a transcription bug caught by generation)
        raw = response.to_bytes()
        self.assertEqual(len(raw), 28)
        parsed = createPdu(raw)
        self.assertEqual(parsed.repairResult, 2)
        self.assertEqual(parsed.to_bytes(), raw)


class TestEntityManagementFamily(unittest.TestCase):
    """Entity Management family (§7.8): aggregates, groups, parts."""

    def test_aggregate_state_round_trip(self):
        pdu = AggregateStatePdu()
        pdu.aggregateID = AggregateIdentifier(SimulationAddress(1, 2), 3)
        pdu.forceID = 1
        pdu.aggregateState = 1  # [UID 204] aggregated
        pdu.aggregateType = AggregateType(1, 1, 39, 2)
        pdu.aggregateMarking.string = "1BN"
        pdu.entityIDList.append(EntityIdentifier(SimulationAddress(1, 2), 5))
        silent = SilentEntitySystem(numberOfEntities=3)
        silent.entityType = EntityType(1, 1, 39, 3)
        silent.appearanceRecordList = [7]
        pdu.silentEntitySystemList.append(silent)
        pdu.variableDatumList.append(VariableDatum(1, b"agg data"))
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, AggregateStatePdu)
        self.assertEqual(parsed.aggregateID, pdu.aggregateID)
        self.assertEqual(parsed.numberOfDisEntities, 1)
        self.assertEqual(parsed.numberOfSilentEntityTypes, 1)
        self.assertEqual(parsed.aggregateMarking.string, "1BN")
        self.assertEqual(parsed.variableDatumList[0].variableData, b"agg data")
        self.assertEqual(parsed.to_bytes(), raw)

    def test_aggregate_state_id_list_alignment(self):
        pdu = AggregateStatePdu()
        pdu.aggregateIDList.append(AggregateIdentifier(SimulationAddress(1, 1), 2))
        # base 136 (aggregate marking is §6.2.4's 1+31 = 32 bytes; the
        # hand exemplar wrongly reused the 12-byte EntityMarking) + 6 = 142
        # -> 2 pad bytes to the 32-bit boundary
        self.assertEqual(pdu.marshalledSize(), 136 + 6 + 2)
        self.assertEqual(pdu.marshalledSize() % 4, 0)
        parsed = createPdu(pdu.to_bytes())
        self.assertEqual(parsed.numberOfDisAggregates, 1)
        self.assertEqual(parsed.to_bytes(), pdu.to_bytes())

    def test_is_group_of_round_trip(self):
        pdu = IsGroupOfPdu()
        pdu.groupedEntityCategory = 1  # [UID 213] vehicle
        pdu.latitude = 51.5
        pdu.longitude = -0.12
        pdu.groupedEntityDescriptions.append(
            EntityIdentifier(SimulationAddress(9, 9), 11)
        )
        raw = pdu.to_bytes()
        self.assertEqual(len(raw), 40 + 6)
        parsed = createPdu(raw)
        self.assertEqual(parsed.numberOfGroupedEntities, 1)
        self.assertEqual(parsed.groupedEntityDescriptions[0].entityNumber, 11)
        self.assertAlmostEqual(parsed.latitude, 51.5, places=6)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_transfer_ownership_round_trip(self):
        from opendis.record.simulation_management_with_reliability import (
            RecordSpecificationElement,
        )

        pdu = TransferOwnershipPdu()
        pdu.requestID = 4
        pdu.transferType = 1  # [UID 224] push transfer
        pdu.recordSets.append(RecordSpecificationElement(3300, 0, 32, 1, b"\xab" * 4))
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, TransferOwnershipPdu)
        self.assertEqual(parsed.numberOfRecordSets, 1)
        self.assertEqual(parsed.recordSets[0].recordID, 3300)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_is_part_of_round_trip(self):
        pdu = IsPartOfPdu()
        pdu.relationship = Relationship(1, 1)
        pdu.namedLocationID = NamedLocationIdentification(1, 2)
        pdu.partEntityType = EntityType(1, 1, 39, 4)
        raw = pdu.to_bytes()
        # 52 bytes: Relationship is §6.2.74's two 16-bit enumerations
        # [UID 210/211]; the hand exemplar wrongly carried them as enum8
        self.assertEqual(len(raw), 52)
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, IsPartOfPdu)
        self.assertEqual(parsed.relationship.nature, 1)
        self.assertEqual(parsed.namedLocationID.stationNumber, 2)
        self.assertEqual(parsed.to_bytes(), raw)


class TestEntityInformationSurface(unittest.TestCase):
    """The §7.2.3-§7.2.6 PDUs (Phase 5): Collision, Collision-Elastic,
    Entity State Update, Attribute."""

    def test_collision_round_trip(self):
        pdu = CollisionPdu()
        pdu.issuingEntityID = EntityIdentifier(SimulationAddress(1, 2), 3)
        pdu.collidingEntityID = EntityIdentifier(SimulationAddress(1, 2), 4)
        pdu.collisionType = 1  # [UID 189] inelastic
        raw = pdu.to_bytes()
        # 60 bytes (Table 135): header + two IDs + event + type + pad
        # + velocity + mass + location
        self.assertEqual(len(raw), 60)
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, CollisionPdu)
        self.assertEqual(parsed.collidingEntityID.entityNumber, 4)
        self.assertEqual(parsed.collisionType, 1)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_collision_elastic_round_trip(self):
        pdu = CollisionElasticPdu()
        pdu.issuingEntityID = EntityIdentifier(SimulationAddress(1, 2), 3)
        pdu.collisionEventID = EventIdentifier(SimulationAddress(1, 2), 9)
        pdu.mass = 1200.0
        pdu.collisionIntermediateResultXX = 1.5
        pdu.coefficientOfRestitution = 0.75
        raw = pdu.to_bytes()
        # 100 bytes (800 bits, Table 136): the XML's six tail fields
        # (intermediate results XX-YY, unit surface normal, coefficient
        # of restitution) are declared — pduType 66 per §5.2.4
        self.assertEqual(len(raw), 100)
        self.assertEqual(CollisionElasticPdu.pduType, 66)
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, CollisionElasticPdu)
        self.assertEqual(parsed.collisionEventID.eventNumber, 9)
        self.assertAlmostEqual(parsed.mass, 1200.0, places=5)
        self.assertAlmostEqual(parsed.collisionIntermediateResultXX, 1.5, places=5)
        self.assertAlmostEqual(parsed.coefficientOfRestitution, 0.75, places=5)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_entity_state_update_round_trip(self):
        pdu = EntityStateUpdatePdu()
        pdu.entityID = EntityIdentifier(SimulationAddress(5, 6), 7)
        pdu.entityAppearance = 0x0040C000
        pdu.variableParameters.append(VariableParameter())
        raw = pdu.to_bytes()
        # 576 + 128N bits (Table 137): 72 bytes at N=1
        self.assertEqual(len(raw), 72 + 16)
        self.assertEqual(EntityStateUpdatePdu.pduType, 67)
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, EntityStateUpdatePdu)
        self.assertEqual(parsed.entityID.entityNumber, 7)
        self.assertEqual(parsed.numberOfVariableParameters, 1)
        self.assertEqual(parsed.entityAppearance, 0x0040C000)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_entity_state_update_appearance_stays_raw(self):
        # the ES-Update carries no entityType, so the appearance uint32
        # cannot resolve to a bitfield view locally (the receiver resolves
        # it from its cached entity type) — it must stay a plain int
        pdu = EntityStateUpdatePdu()
        pdu.entityID = EntityIdentifier(SimulationAddress(1, 1), 1)
        pdu.entityAppearance = 0xDEADBEEF
        parsed = createPdu(pdu.to_bytes())
        self.assertIs(type(parsed.entityAppearance), int)

    def test_attribute_pdu_round_trip(self):
        pdu = AttributePdu()
        pdu.attributeRecordPduType = 1
        pdu.masterAttributeRecordType = 4444
        pdu.actionCode = 1
        record = Attribute(
            recordType=4444,
            recordLength=8,
            recordSpecificFields=b"\x01\x02",  # K+P as received
        )
        recordSet = AttributeRecordSet()
        recordSet.entityId = EntityIdentifier(SimulationAddress(2, 3), 4)
        recordSet.attributeRecords = [record]
        pdu.attributeRecordSets = [recordSet]
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, AttributePdu)
        self.assertEqual(AttributePdu.pduType, 72)
        self.assertEqual(parsed.numberAttributeRecordSet, 1)
        got = parsed.attributeRecordSets[0].attributeRecords[0]
        self.assertEqual(got.recordType, 4444)
        self.assertEqual(got.recordSpecificFields, b"\x01\x02")
        self.assertEqual(parsed.to_bytes(), raw)

    def test_attribute_record_64_bit_pad(self):
        # §6.2.10/Table 138: recordLength = 6 + K + P with the record
        # padded to the 64-bit boundary; a K=2 payload carries 2 pad
        # bytes inside recordSpecificFields (recordLength 8)
        record = Attribute(
            recordType=1, recordLength=8, recordSpecificFields=b"\xaa\xbb"
        )
        self.assertEqual(record.marshalledSize(), 8)
        raw = record.to_bytes() if hasattr(record, "to_bytes") else None
        buf = io.BytesIO()
        record.serialize(DataOutputStream(buf))
        wire = buf.getvalue()
        self.assertEqual(len(wire), 8)
        again = Attribute()
        again.parse(DataInputStream(io.BytesIO(wire)))
        self.assertEqual(again.recordSpecificFields, b"\xaa\xbb")
        self.assertEqual(again.recordLength, 8)


class TestIFFPdu(unittest.TestCase):
    """§7.6.5 IFF PDU: the length-driven layer mechanism."""

    @staticmethod
    def _layer1(systemType):
        pdu = IdentificationFriendOrFoePdu()
        pdu.systemID = SystemIdentifier(
            systemType=systemType,
            systemName=1,
            systemMode=1,
            changeOptions=0,
        )
        return pdu

    def test_layer1_only_round_trip(self):
        pdu = self._layer1(1)
        pdu.emittingEntityId = EntityIdentifier(SimulationAddress(1, 2), 3)
        raw = pdu.to_bytes()
        # Layer 1 is 480 bits (Tables 165/167): header + entity + event
        # + antenna location + 48-bit System Identifier + designator +
        # system data + 128-bit Fundamental Operational Data
        self.assertEqual(len(raw), 60)
        self.assertEqual(IdentificationFriendOrFoePdu.pduType, 28)
        self.assertEqual(SystemIdentifier(1, 1, 1, 0).marshalledSize(), 6)
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, IdentificationFriendOrFoePdu)
        self.assertEqual(parsed.emittingEntityId.entityNumber, 3)
        self.assertEqual(parsed.systemID.systemType, 1)
        self.assertIsNone(parsed.iFFPduLayer2Data)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_iff_layers_round_trip(self):
        pdu = self._layer1(7)  # Mode 5 Interrogator -> Layer 3 interrogator
        layer2 = IFFPduLayer2Data()
        layer2.layerHeader = LayerHeader(layerNumber=2)
        layer2.IFFFundamentalParameterDataRecord = [
            IFFFundamentalParameterData() for _ in range(2)
        ]
        pdu.iFFPduLayer2Data = layer2
        layer3 = IFFPduLayer3InterrogatorFormatData()
        layer3.layerHeader = LayerHeader(layerNumber=3)
        layer3.IFFFundamentalParameterDataRecord = [
            IFFData(recordType=1, recordLength=8, recordSpecificFields=b"\x01\x02")
        ]
        pdu.iFFPduLayer3InterrogatorFormatData = layer3
        raw = pdu.to_bytes()
        # layer lengths include their own headers (§6.2.51)
        self.assertEqual(layer2.layerHeader.length, layer2.marshalledSize())
        self.assertEqual(layer3.layerHeader.length, layer3.marshalledSize())
        parsed = createPdu(raw)
        self.assertIsInstance(parsed.iFFPduLayer2Data, IFFPduLayer2Data)
        self.assertIsInstance(
            parsed.iFFPduLayer3InterrogatorFormatData,
            IFFPduLayer3InterrogatorFormatData,
        )
        self.assertIsNone(parsed.iFFPduLayer3TransponderFormatData)
        got = (
            parsed.iFFPduLayer3InterrogatorFormatData.IFFFundamentalParameterDataRecord[
                0
            ]
        )
        self.assertEqual(got.recordSpecificFields, b"\x01\x02")
        self.assertEqual(parsed.to_bytes(), raw)

    def test_iff_layer_format_dispatch(self):
        # the Layer 1 System Type field [UID 82] picks the Layer 3/4
        # format: 10 (Mode 5 Transponder) reads the transponder format
        pdu = self._layer1(10)
        layer3t = IFFPduLayer3TransponderFormatData()
        layer3t.layerHeader = LayerHeader(layerNumber=3)
        pdu.iFFPduLayer3TransponderFormatData = layer3t
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertIsInstance(
            parsed.iFFPduLayer3TransponderFormatData,
            IFFPduLayer3TransponderFormatData,
        )
        self.assertIsNone(parsed.iFFPduLayer3InterrogatorFormatData)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_iff_layer5_round_trip(self):
        pdu = self._layer1(1)
        layer5 = IFFPduLayer5Data()
        layer5.layerHeader = LayerHeader(layerNumber=5)
        layer5.applicableLayers = 0x01
        layer5.IFFFundamentalParameterDataRecord = [
            IFFData(recordType=2, recordLength=6, recordSpecificFields=b"")
        ]
        pdu.iFFPduLayer5Data = layer5
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertIsInstance(parsed.iFFPduLayer5Data, IFFPduLayer5Data)
        self.assertEqual(parsed.iFFPduLayer5Data.applicableLayers, 0x01)
        self.assertEqual(
            len(parsed.iFFPduLayer5Data.IFFFundamentalParameterDataRecord), 1
        )
        self.assertEqual(parsed.to_bytes(), raw)

    def test_iff_alias(self):
        from opendis.record.distributed_emissions import IFFPdu

        self.assertIs(IFFPdu, IdentificationFriendOrFoePdu)


class TestSEESPdu(unittest.TestCase):
    """§7.6.6 Supplemental Emission/Entity State PDU (Phase 5)."""

    def test_sees_round_trip(self):
        pdu = SupplementalEmissionEntityStatePdu()
        pdu.originatingEntityID = EntityIdentifier(SimulationAddress(1, 2), 3)
        pdu.propulsionSystemData = [PropulsionSystemData() for _ in range(2)]
        raw = pdu.to_bytes()
        # Table 174 base 28 bytes + 8 per propulsion record
        self.assertEqual(len(raw), 28 + 16)
        self.assertEqual(SupplementalEmissionEntityStatePdu.pduType, 30)
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, SupplementalEmissionEntityStatePdu)
        self.assertEqual(parsed.numberOfPropulsionSystems, 2)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_sees_alias(self):
        from opendis.record.distributed_emissions import SEESPdu

        self.assertIs(SEESPdu, SupplementalEmissionEntityStatePdu)


class TestGriddedDataPduWire(unittest.TestCase):
    """§7.10.3 Gridded Data PDU: axis/data dispatch and the derived
    grid-data record count (Table 192)."""

    def test_empty_round_trip(self):
        pdu = GriddedDataPdu()
        raw = pdu.to_bytes()
        # 512 bits (Table 192 base): no axes, no data records
        self.assertEqual(len(raw), 64)
        self.assertEqual(GriddedDataPdu.pduType, 42)
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, GriddedDataPdu)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_axis_dispatch_and_derived_count(self):
        pdu = GriddedDataPdu()
        pdu.vectorDimension = 2
        fixed = GridAxisDescriptorFixed()
        fixed.numberOfPointsOnXiAxis = 4
        variable = GridAxisDescriptorVariable()
        variable.axisType = 1  # [UID 377] irregular axis
        variable.xiValues = [1, 2, 3]
        pdu.gridAxisDescriptors = [fixed, variable]
        records = []
        for i in range(2 * 4 * 3):  # G = V x prod(Ni) = 24
            record = GridDataType0(sampleType=1, dataRepresentation=0)
            record.dataValues = [i % 256, (i + 1) % 256]
            records.append(record)
        pdu.gridDataRecords = records
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertEqual(len(parsed.gridAxisDescriptors), 2)
        self.assertIsInstance(parsed.gridAxisDescriptors[1], GridAxisDescriptorVariable)
        self.assertEqual(parsed.gridAxisDescriptors[1].xiValues, [1, 2, 3])
        # the grid-data count is derived (V x prod Ni), not stored — the
        # XML's countFieldName="numberOfGridAxes" is an upstream bug
        self.assertEqual(len(parsed.gridDataRecords), 24)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_grid_data_type_dispatch(self):
        pdu = GriddedDataPdu()
        pdu.vectorDimension = 1
        axis = GridAxisDescriptorFixed()
        axis.numberOfPointsOnXiAxis = 3
        pdu.gridAxisDescriptors = [axis]
        type0 = GridDataType0(sampleType=1, dataRepresentation=0)
        type0.dataValues = [0xAA]  # odd count -> 16-bit pad byte
        type1 = GridDataType1(sampleType=2, dataRepresentation=1)
        type1.fieldScale = 1.5
        type1.dataValues = [10, 20, 30]
        type2 = GridDataType2(sampleType=3, dataRepresentation=2)
        type2.dataValues = [1.5, 2.5, 3.5]
        pdu.gridDataRecords = [type0, type1, type2]
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertEqual(len(parsed.gridDataRecords), 3)
        got0, got1, got2 = parsed.gridDataRecords
        self.assertIsInstance(got0, GridDataType0)
        self.assertIsInstance(got1, GridDataType1)
        self.assertIsInstance(got2, GridDataType2)
        self.assertEqual(list(got0.dataValues), [0xAA])
        self.assertAlmostEqual(got1.fieldScale, 1.5, places=6)
        self.assertEqual(list(got1.dataValues), [10, 20, 30])
        self.assertAlmostEqual(got2.dataValues[2], 3.5, places=6)
        self.assertEqual(parsed.to_bytes(), raw)


class TestSilentEntitySystem(unittest.TestCase):
    """§6.2.79 Silent Entity System record (Table 183's silent entity
    system list element — the exemplar's bare-EntityType list was a wire
    bug corrected in Phase 5)."""

    def test_silent_entity_system_round_trip(self):
        pdu = AggregateStatePdu()
        silent = SilentEntitySystem(numberOfEntities=4)
        silent.entityType = EntityType(1, 1, 39, 3)
        silent.appearanceRecordList = [7, 8]
        pdu.silentEntitySystemList = [silent]
        raw = pdu.to_bytes()
        # 96 + 32A bits per record (Table 183): 12 + 4*2 = 20 bytes
        parsed = createPdu(raw)
        got = parsed.silentEntitySystemList[0]
        self.assertEqual(got.numberOfEntities, 4)
        self.assertEqual(got.entityType, EntityType(1, 1, 39, 3))
        self.assertEqual(got.appearanceRecordList, [7, 8])
        self.assertEqual(parsed.to_bytes(), raw)


class TestDistributedEmissionsFamily(unittest.TestCase):
    """Distributed Emissions family (§7.6): EEE, Designator, UA."""

    def test_eee_round_trip_with_beam_and_trackjam(self):
        pdu = ElectromagneticEmissionPdu()
        pdu.emittingEntityID = EntityIdentifier(SimulationAddress(1, 1), 9)
        pdu.stateUpdateIndicator = 1
        system = ElectronicEmitter()
        system.emitterSystem = EmitterSystem(100, 121, 3)
        beam = EmitterBeam()
        beam.beamNumber = 1
        beam.fundamentalParameterData = EEFundamentalParameterData(
            1e9, 2e6, 55.0, 1000.0, 1e-6
        )
        beam.beamStatus = BeamStatus(1)  # active
        beam.jammingTechnique = JammingTechnique(1, 2, 3, 4)
        beam.trackJamData.append(
            TrackJamData(EntityIdentifier(SimulationAddress(2, 2), 5), 1, 1)
        )
        system.beams.append(beam)
        pdu.systems.append(system)
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, ElectromagneticEmissionPdu)
        self.assertEqual(parsed.numberOfSystems, 1)
        beamOut = parsed.systems[0].beams[0]
        self.assertEqual(beamOut.beamDataLength, 13 + 2)
        self.assertEqual(beamOut.numberOfTargets, 1)
        self.assertAlmostEqual(
            beamOut.fundamentalParameterData.frequency, 1e9, delta=1.0
        )
        self.assertEqual(beamOut.trackJamData[0].entityID.entityNumber, 5)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_designator_round_trip(self):
        pdu = DesignatorPdu()
        pdu.designatingEntityID = EntityIdentifier(SimulationAddress(1, 1), 2)
        pdu.codeName = 1  # [UID 80]
        pdu.designatorCode = 3  # [UID 81]
        pdu.designatorPower = 50.0
        pdu.designatorWavelength = 1.064
        raw = pdu.to_bytes()
        self.assertEqual(len(raw), 88)
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, DesignatorPdu)
        self.assertAlmostEqual(parsed.designatorWavelength, 1.064, places=6)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_underwater_acoustic_round_trip(self):
        pdu = UnderwaterAcousticPdu()
        pdu.propulsionPlantConfiguration = 3
        pdu.shaftRPMs.append(ShaftRPM(100, 120, 5))
        pdu.apaData.append(APA(0x1002, 7))
        emitter = UAEmitter()
        emitter.acousticEmitter = AcousticEmitter(1, 2, 3)
        beam = UABeam()
        beam.fundamentalParameterData = UAFundamentalParameter(4, 5, 0.1, 0.2, 0.3, 0.4)
        emitter.beams.append(beam)
        pdu.emitterSystems.append(emitter)
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, UnderwaterAcousticPdu)
        self.assertEqual(parsed.numberOfShafts, 1)
        self.assertEqual(parsed.numberOfAPAs, 1)
        self.assertEqual(parsed.numberOfUAEmitterSystems, 1)
        self.assertEqual(parsed.emitterSystems[0].beams[0].beamDataLength, 6)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_iff_type_28_registered(self):
        # Phase 5 withdrew the IFF/SEE deferral: type 28 decodes through
        # the layer machinery now (the old UnrecognizedPdu expectation is
        # retired with it)
        header = bytes([7, 1, 28, 6]) + b"\x00\x11\x22\x33" + b"\x00\x3c\x00\x00"
        raw = header + bytes(48)
        pdu = createPdu(raw)
        self.assertIsInstance(pdu, IdentificationFriendOrFoePdu)
        self.assertEqual(pdu.to_bytes(), raw)


class TestMinefieldFamily(unittest.TestCase):
    """Minefield family (§7.9) incl. the dataFilter-conditional
    MinefieldDataPdu (Table 189 field-major order)."""

    def test_minefield_state_round_trip(self):
        pdu = MinefieldStatePdu()
        pdu.minefieldID = MinefieldIdentifier(SimulationAddress(1, 2), 3)
        pdu.forceID = 2
        appearance = MinefieldStateAppearance()
        appearance.activeStatus = True
        pdu.appearance = appearance
        pdu.protocolMode = 1
        pdu.perimeterPoints.append(Vector2Float(10.0, -5.0))
        pdu.mineType.append(EntityType(1, 3, 39, 6))
        raw = pdu.to_bytes()
        self.assertEqual(len(raw), 72 + 8 + 8)
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, MinefieldStatePdu)
        self.assertIsInstance(parsed.appearance, MinefieldStateAppearance)
        self.assertTrue(parsed.appearance.activeStatus)
        self.assertEqual(parsed.numberOfPerimeterPoints, 1)
        self.assertAlmostEqual(parsed.perimeterPoints[0].x, 10.0, places=5)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_minefield_query_round_trip(self):
        pdu = MinefieldQueryPdu()
        pdu.requestID = 7
        pdu.dataFilter = 0x7FF
        pdu.requestedPerimeterPoints.append(Vector2Float(1.0, 2.0))
        pdu.sensorTypes.append(5)
        raw = pdu.to_bytes()
        # 40 base + 8 (point) + 2 (sensor) + 2 pad (Table 188 P term: the
        # datagram is 32-bit aligned; the hand exemplar omitted the pad)
        self.assertEqual(len(raw), 40 + 8 + 2 + 2)
        parsed = createPdu(raw)
        self.assertEqual(parsed.dataFilter, 0x7FF)
        self.assertEqual(parsed.sensorTypes, [5])
        self.assertEqual(parsed.to_bytes(), raw)

    def test_minefield_data_empty_filter(self):
        pdu = MinefieldDataPdu()
        self.assertEqual(pdu.marshalledSize(), 44)
        parsed = createPdu(pdu.to_bytes())
        self.assertIsInstance(parsed, MinefieldDataPdu)
        self.assertEqual(parsed.to_bytes(), pdu.to_bytes())

    def test_minefield_data_full_filter_table_189_parity(self):
        pdu = MinefieldDataPdu()
        pdu.dataFilter = 0x77F  # bits 0-6 + 8-10 (no wires)
        pdu.sensorTypes.append(1)
        pdu.mineLocation.extend(
            (Vector3Float(1.0, 2.0, 3.0), Vector3Float(4.0, 5.0, 6.0))
        )
        pdu.groundBurialDepthOffset.extend((0.1, 0.2))
        pdu.waterBurialDepthOffset.extend((0.3, 0.4))
        pdu.snowBurialDepthOffset.extend((0.5, 0.6))
        pdu.mineOrientation.extend(
            (EulerAngles(0.1, 0.2, 0.3), EulerAngles(0.4, 0.5, 0.6))
        )
        pdu.thermalContrast.extend((0.7, 0.8))
        pdu.reflectance.extend((0.9, 1.0))
        pdu.mineEmplacementTime.extend(
            (MineEmplacementTime(1, 2), MineEmplacementTime(3, 4))
        )
        pdu.mineEntityNumber.extend((101, 102))
        pdu.fusing.extend((0x0101, 0x0202))
        pdu.scalarDetectionCoefficient.extend((9, 8))  # 2 mines x 1 sensor
        pdu.paintScheme.extend((1, 2))
        # Table 189 arithmetic: header+prefix 46 + pad 2 + 24 (locations)
        #   + 8+8+8 + 24 + 8+8 + 16 + 4 + 4 + 2 + 2 = 164
        self.assertEqual(pdu.marshalledSize(), 164)
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, MinefieldDataPdu)
        self.assertEqual(parsed.numberOfMinesInThisPdu, 2)
        self.assertEqual(parsed.mineEntityNumber, [101, 102])
        self.assertEqual(parsed.scalarDetectionCoefficient, [9, 8])
        self.assertAlmostEqual(parsed.groundBurialDepthOffset[1], 0.2, places=6)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_minefield_data_wires_only(self):
        pdu = MinefieldDataPdu()
        pdu.dataFilter = 0x80  # bit 7: trip/detonation wires only
        pdu.mineLocation.extend(
            (Vector3Float(0.0, 0.0, 0.0), Vector3Float(1.0, 1.0, 1.0))
        )
        pdu.mineEntityNumber.extend((7, 8))
        pdu.numberOfTripDetonationWires.extend((1, 2))
        pdu.numberOfVertices.extend((2, 3, 1))
        for i in range(6):
            pdu.vertices.append(Vector3Float(float(i), 1.0, 2.0))
        # 44 + 24 (locations) + 4 (entity numbers) + pad0
        #   + 2 (wire counts) + pad2 + 3 (vertex counts) + pad1 + 72
        self.assertEqual(pdu.marshalledSize(), 152)
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertEqual(parsed.numberOfTripDetonationWires, [1, 2])
        self.assertEqual(parsed.numberOfVertices, [2, 3, 1])
        self.assertEqual(len(parsed.vertices), 6)
        self.assertAlmostEqual(parsed.vertices[5].x, 5.0, places=5)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_minefield_response_nack(self):
        pdu = MinefieldResponseNACKPdu()
        pdu.requestID = 3
        pdu.missingPduSequenceNumbers.extend((1, 2, 3))
        raw = pdu.to_bytes()
        # 26 base + 3 sequence numbers + 3 pad (Table 190 P term; the
        # hand exemplar omitted the whole-datagram alignment pad)
        self.assertEqual(len(raw), 26 + 3 + 3)
        parsed = createPdu(raw)
        self.assertEqual(parsed.numberOfMissingPdus, 3)
        self.assertEqual(parsed.to_bytes(), raw)


class TestSyntheticEnvironmentFamily(unittest.TestCase):
    """Synthetic Environment family (§7.10): objects + env process."""

    def test_point_object_state_round_trip(self):
        pdu = PointObjectStatePdu()
        pdu.objectID = EntityIdentifier(SimulationAddress(1, 1), 2)
        pdu.referencedObjectID = ObjectIdentifier(SimulationAddress(3, 3), 4)
        pdu.updateNumber = 10
        pdu.forceID = 1
        pdu.modifications = 0x3
        pdu.objectType = ObjectType(1, 3, 2, 1)
        pdu.objectLocation = Vector3Double(100.0, 200.0, 300.0)
        raw = pdu.to_bytes()
        # 88 bytes = 12 header + 76 body (the hand exemplar's "91" was an
        # arithmetic slip — the PDU is 32-bit aligned by construction)
        self.assertEqual(len(raw), 88)
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, PointObjectStatePdu)
        self.assertEqual(parsed.objectType, ObjectType(1, 3, 2, 1))
        self.assertEqual(parsed.updateNumber, 10)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_linear_object_state_round_trip(self):
        pdu = LinearObjectStatePdu()
        pdu.objectType = ObjectType(1, 3, 4)
        segment = LinearSegmentParameter()
        segment.segmentNumber = 1
        segment.segmentLength = 55.5
        segment.segmentWidth = 2.0
        pdu.linearSegmentParameters.append(segment)
        raw = pdu.to_bytes()
        # 40-byte base + 64-byte segment: segmentModification is §7.10.5's
        # 8-bit bitmap (the hand exemplar wrongly carried it as uint16)
        self.assertEqual(len(raw), 40 + 64)
        parsed = createPdu(raw)
        self.assertEqual(parsed.numberOfLinearSegments, 1)
        self.assertAlmostEqual(
            parsed.linearSegmentParameters[0].segmentLength, 55.5, places=4
        )
        self.assertEqual(parsed.to_bytes(), raw)

    def test_areal_object_state_round_trip(self):
        pdu = ArealObjectStatePdu()
        pdu.objectType = ObjectType(1, 3, 5)
        pdu.objectLocation.extend(
            (
                Vector3Double(0.0, 0.0, 0.0),
                Vector3Double(1.0, 0.0, 0.0),
                Vector3Double(1.0, 1.0, 0.0),
            )
        )
        raw = pdu.to_bytes()
        # 48-byte base (12 header + 36 body) + 3 x 24-byte locations; the
        # hand-written "49" expectation was an arithmetic slip
        self.assertEqual(len(raw), 48 + 3 * 24)
        parsed = createPdu(raw)
        self.assertEqual(parsed.numberOfPoints, 3)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_environmental_process_round_trip(self):
        pdu = EnvironmentalProcessPdu()
        pdu.modelType = 1  # [UID 248]
        record = EnvironmentRecord(4100, 1, b"\xaa" * 8)  # 16-byte record
        pdu.environmentRecords.append(record)
        self.assertEqual(record.marshalledSize(), 16)
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, EnvironmentalProcessPdu)
        self.assertEqual(parsed.numberOfEnvironmentRecords, 1)
        self.assertEqual(parsed.environmentRecords[0].environmentType, 4100)
        self.assertEqual(parsed.environmentRecords[0].geometry, b"\xaa" * 8)
        self.assertEqual(parsed.to_bytes(), raw)


class TestLiveEntityFamily(unittest.TestCase):
    """Live Entity family (§9): conditional fields, elided identifiers,
    subprotocol-in-status-byte header."""

    def test_subprotocol_rides_pdu_status_byte(self):
        pdu = TimeSpacePositionInformationPdu()
        pdu.subprotocolNumber = 1
        raw = pdu.to_bytes()
        self.assertEqual(raw[10], 1)  # pduStatus byte position
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, TimeSpacePositionInformationPdu)
        self.assertEqual(parsed.subprotocolNumber, 1)

    def test_tspi_round_trip(self):
        pdu = TimeSpacePositionInformationPdu()
        pdu.liveEntityId = LiveEntityIdentifier(LiveSimulationAddress(4, 5), 6)
        pdu.measuredSpeed = 300
        pdu.systemSpecificData = b"\x01\x02"
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertEqual(parsed.liveEntityId.entityNumber, 6)
        self.assertEqual(parsed.measuredSpeed, 300)
        self.assertEqual(parsed.systemSpecificData, b"\x01\x02")
        self.assertEqual(parsed.to_bytes(), raw)

    def test_appearance_conditional_fields(self):
        pdu = AppearancePdu()
        self.assertEqual(pdu.marshalledSize(), 18)
        pdu.appearanceFlag1 = (1 << 7) | (1 << 0) | (1 << 3) | (1 << 5)
        pdu.appearanceFlag2 = 1 << 1  # audio only
        pdu.forceId = 2
        pdu.entityMarking = EntityMarking()
        pdu.entityMarking.string = "LIVE"
        pdu.appearanceVisual = 0x000022B8
        pdu.appearanceAudio = 7
        raw = pdu.to_bytes()
        self.assertEqual(len(raw), 18 + 1 + 1 + 12 + 4 + 4)
        parsed = createPdu(raw)
        self.assertEqual(parsed.forceId, 2)
        self.assertEqual(parsed.entityMarking.string, "LIVE")
        self.assertEqual(parsed.appearanceVisual, 0x000022B8)
        self.assertIsNone(parsed.appearanceEM)
        self.assertEqual(parsed.appearanceAudio, 7)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_articulated_parts_round_trip(self):
        pdu = ArticulatedPartsPdu()
        pdu.variableParameters.append(VariableParameter(1, bytes(15)))
        raw = pdu.to_bytes()
        self.assertEqual(len(raw), 17 + 16)
        parsed = createPdu(raw)
        self.assertEqual(parsed.numberOfParameterRecords, 1)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_le_fire_table_226_parity(self):
        # total bits = 280 + 32F0 + (16F1+16)F2 + 16F3 + 64F6 + 32F4 + 32F5
        for flags in (0, 1, 8, 0b1111, 0b1001111, 0b1111111):
            pdu = LiveEntityFirePdu()
            pdu.fireFlag = flags
            F = [(flags >> i) & 1 for i in range(8)]
            if F[0]:
                pdu.targetLiveEntityId = LiveEntityIdentifier()
            if F[2]:
                pdu.munitionLiveEntityId = (
                    LiveEntityIdentifier() if F[1] else LiveEntityIdentifierElided()
                )
            pdu.eventId = (
                EventIdentifierLiveEntity()
                if F[3]
                else EventIdentifierLiveEntityElided()
            )
            if F[6]:
                from opendis.record.live_entity import (
                    LiveEntityRelativeWorldCoordinates,
                )

                pdu.location = LiveEntityRelativeWorldCoordinates()
            if F[4]:
                pdu.munitionDescriptor.warhead = 1
                pdu.munitionDescriptor.fuse = 2
            if F[5]:
                pdu.munitionDescriptor.quantity = 3
                pdu.munitionDescriptor.rate = 4
            want = (
                280
                + 32 * F[0]
                + (16 * F[1] + 16) * F[2]
                + 16 * F[3]
                + 64 * F[6]
                + 32 * F[4]
                + 32 * F[5]
            )
            self.assertEqual(pdu.marshalledSize() * 8, want, f"fireFlag={flags:08b}")
            parsed = createPdu(pdu.to_bytes())
            self.assertEqual(parsed.to_bytes(), pdu.to_bytes())

    def test_le_fire_identifier_shapes(self):
        pdu = LiveEntityFirePdu()
        # bits 2 (munition present) + 1 (full shape) + 3 (full event)
        pdu.fireFlag = (1 << 2) | (1 << 1) | (1 << 3)
        pdu.munitionLiveEntityId = LiveEntityIdentifier(LiveSimulationAddress(1, 2), 3)
        pdu.eventId = EventIdentifierLiveEntity(1, 2, 42)
        raw = pdu.to_bytes()
        parsed = createPdu(raw)
        self.assertIsInstance(parsed.munitionLiveEntityId, LiveEntityIdentifier)
        self.assertIsInstance(parsed.eventId, EventIdentifierLiveEntity)
        self.assertEqual(parsed.eventId.eventNumber, 42)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_le_detonation_table_229_parity(self):
        # 256 + 8F7 + 32F0 + (16F1+16)F2 + (16F3+16)G1 + 64(1-F6)
        #   + 48G0 + 32F4 + 32F5 + 48F6  (G* = F7 AND G)
        cases = [
            (0, 0),
            (1, 0),
            (0b01000001, 0),
            (0b01001001, 0b10),
            (0b01001111, 0b11),
            (0b11001111, 0b11),
        ]
        from opendis.record.live_entity import (
            LiveEntityOrientation16,
            LiveEntityRelativeEntityCoordinates,
            LiveEntityRelativeWorldCoordinates,
        )

        for f1, f2 in cases:
            pdu = LiveEntityDetonationPdu()
            pdu.detonationFlag1 = f1
            F = [(f1 >> i) & 1 for i in range(8)]
            G = [(f2 >> i) & 1 for i in range(8)]
            if F[7]:
                pdu.detonationFlag2 = f2
            if F[0]:
                pdu.targetLiveEntityId = LiveEntityIdentifier()
            if F[2]:
                pdu.munitionLiveEntityId = (
                    LiveEntityIdentifier() if F[1] else LiveEntityIdentifierElided()
                )
            if F[7] and G[1]:
                pdu.eventId = (
                    EventIdentifierLiveEntity()
                    if F[3]
                    else EventIdentifierLiveEntityElided()
                )
                # F3 selects the shape: elided when 0, full when 1
            if not F[6]:
                pdu.worldLocation = LiveEntityRelativeWorldCoordinates()
            if F[7] and G[0]:
                pdu.munitionOrientation = LiveEntityOrientation16()
            if F[4]:
                pdu.munitionDescriptor.warhead = 1
                pdu.munitionDescriptor.fuse = 2
            if F[5]:
                pdu.munitionDescriptor.quantity = 3
                pdu.munitionDescriptor.rate = 4
            if F[6]:
                pdu.entityLocation = LiveEntityRelativeEntityCoordinates()
            Gs = [g and F[7] for g in G]
            want = (
                256
                + 8 * F[7]
                + 32 * F[0]
                + (16 * F[1] + 16) * F[2]
                + (16 * F[3] + 16) * Gs[1]
                + 64 * (1 - F[6])
                + 48 * Gs[0]
                + 32 * F[4]
                + 32 * F[5]
                + 48 * F[6]
            )
            self.assertEqual(pdu.marshalledSize() * 8, want, f"f1={f1:08b} f2={f2:08b}")
            parsed = createPdu(pdu.to_bytes())
            self.assertEqual(parsed.to_bytes(), pdu.to_bytes())


class TestInformationOperationsFamily(unittest.TestCase):
    """Information Operations family (§5.13): IO Action/Report with
    uid-66 IO records through the SV registry."""

    def test_io_action_round_trip_with_unknown_record(self):
        from opendis.record import getStandardVariableClass

        pdu = InformationOperationsActionPdu()
        pdu.requestID = 9
        pdu.IOWarfareType = 1  # [UID 285] EW
        pdu.IOActionPhase = 1  # [UID 288] start
        pdu.ioRecords.append(getStandardVariableClass(0x7777)(b"\x13" * 10))
        raw = pdu.to_bytes()
        self.assertEqual(len(raw), 56 + 16)
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, InformationOperationsActionPdu)
        self.assertEqual(parsed.numberOfIORecords, 1)
        self.assertEqual(int(parsed.ioRecords[0].recordType), 0x7777)
        self.assertEqual(parsed.ioRecords[0].data, b"\x13" * 10)
        self.assertEqual(parsed.to_bytes(), raw)

    def test_io_report_round_trip(self):
        pdu = InformationOperationsReportPdu()
        pdu.ioReportType = 1  # [UID 289]
        pdu.ioAttackerID = EntityIdentifier(SimulationAddress(1, 1), 2)
        raw = pdu.to_bytes()
        self.assertEqual(len(raw), 40)
        parsed = createPdu(raw)
        self.assertIsInstance(parsed, InformationOperationsReportPdu)
        self.assertEqual(parsed.ioReportType, 1)
        self.assertEqual(parsed.ioAttackerID.entityNumber, 2)
        self.assertEqual(parsed.to_bytes(), raw)


class TestUnrecognizedPdu(unittest.TestCase):

    def test_unknown_pdu_type_captured_byte_exact(self):
        header = (
            bytes([7, 3, 250, 1])  # version, exercise, type, family
            + b"\x11\x22\x33\x44"  # timestamp
            + bytes([0, 0])  # status, padding
            + b"\x00\x14"
        )  # length = 20
        raw = header + b"rest-of-body"
        pdu = createPdu(raw)
        self.assertIsInstance(pdu, UnrecognizedPdu)
        self.assertEqual(pdu.header.pduType, 250)
        self.assertEqual(pdu.header.protocolVersion, 7)
        self.assertEqual(pdu.header.exerciseID, 3)
        self.assertEqual(pdu.header.timestamp.raw, 0x11223344)
        self.assertEqual(pdu.rawPayload, b"rest-of-body")
        self.assertEqual(pdu.to_bytes(), raw)

    def test_truncated_datagram_does_not_raise(self):
        pdu = createPdu(bytes([7, 1, 1]))
        self.assertIsInstance(pdu, UnrecognizedPdu)

    def test_truncated_known_pdu_parses_partially(self):
        raw = EntityStatePdu().to_bytes()[:60]
        pdu = createPdu(raw)
        self.assertIsInstance(pdu, EntityStatePdu)  # partial parse survives

    def test_from_file(self):
        pdu = createPduFromFilePath(path.join(TEST_DIR, "EntityStatePdu-26.raw"))
        self.assertIsInstance(pdu, EntityStatePdu)


class TestEnumRegistry(unittest.TestCase):

    class ForceId(IntEnum):
        FRIENDLY = 1
        HOSTILE = 2

    def tearDown(self):
        unregister_enum_factory()

    def test_degrades_to_int_without_provider(self):
        self.assertIsInstance(createPdu(self._espdu(forceId=1)).forceId, int)

    def test_rich_enum_when_registered(self):
        register_enum_factory(lambda uid: self.ForceId if uid == 6 else None)
        parsed = createPdu(self._espdu(forceId=1))
        self.assertIs(parsed.forceId, self.ForceId.FRIENDLY)
        self.assertEqual(parsed.forceId, 1)

    def test_unknown_value_degrades_to_int(self):
        register_enum_factory(lambda uid: self.ForceId if uid == 6 else None)
        parsed = createPdu(self._espdu(forceId=200))
        self.assertNotIsInstance(parsed.forceId, self.ForceId)
        self.assertEqual(parsed.forceId, 200)

    def test_round_trip_identical_with_and_without_provider(self):
        raw = self._espdu(forceId=2)
        without = createPdu(raw).to_bytes()
        register_enum_factory(lambda uid: self.ForceId if uid == 6 else None)
        with_provider = createPdu(raw).to_bytes()
        self.assertEqual(without, with_provider)
        self.assertEqual(with_provider, raw)

    @staticmethod
    def _espdu(forceId: int) -> bytes:
        pdu = EntityStatePdu()
        pdu.forceId = forceId
        return pdu.to_bytes()


class TestConstructCategories(unittest.TestCase):
    """Design doc §2: the slice demonstrates every XML construct category."""

    def test_sisoenum(self):
        pdu = createPdu(EntityStatePdu(forceId=2).to_bytes())
        self.assertEqual(pdu.forceId, 2)  # [UID 6] via rich_or_int

    def test_classref(self):
        self.assertEqual(EntityStatePdu().entityID.marshalledSize(), 6)

    def test_objectlist(self):
        pdu = DataPdu()
        pdu.fixedDatumRecords.append(FixedDatum())
        self.assertEqual(pdu.numberOfFixedDatumRecords, len(pdu.fixedDatumRecords))

    def test_primitivelist(self):
        datum = VariableDatum(1, b"\x00\xff" * 4)
        self.assertIsInstance(datum.variableData, bytes)

    def test_padtoboundary(self):
        datum = VariableDatum(1, b"abc")  # 3 bytes -> padded to 8
        self.assertEqual(datum.marshalledSize(), 16)

    def test_bitfield(self):
        self.assertIsInstance(LandPlatformAppearance(0), LandPlatformAppearance)

    def test_header(self):
        header = PduHeader.parse(
            DataInputStream(io.BytesIO(EntityStatePdu().to_bytes()[:12]))
        )
        self.assertEqual(header.pduType, 1)
        self.assertEqual(header.marshalledSize(), 12)


if __name__ == "__main__":
    unittest.main()
