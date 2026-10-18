"""Simulation Management with Reliability family: wire discipline.

The family was the largest pytest coverage gap (68%): its fourteen PDUs
are big and the suite only exercised one representative. These tests are
purely mechanical — identity constants, factory registration, wire-length
self-consistency, and byte-exact round-trips for every concrete class
(default and populated shapes), no scenario knowledge required. The XML
exports each class under two names (``*RPdu`` and ``*ReliablePdu`` —
explicit aliasFor elements), so classes are deduped by identity.
"""

from __future__ import annotations

import io

import pytest

import opendis.record.simulation_management as sm
import opendis.record.simulation_management_with_reliability as smr
from opendis.record.factory import PduTypeDecoders, createPdu
from opendis.stream import DataOutputStream

_FAMILY_BASE = "SimulationManagementWithReliabilityFamilyPdu"

# dedupe the aliasFor pairs (e.g. DataQueryRPdu is DataQueryReliablePdu)
CONCRETE: dict[str, type] = {}
for _name in smr.__all__:
    if _name.endswith("Pdu") and _name != _FAMILY_BASE:
        CONCRETE.setdefault(id(getattr(smr, _name)), getattr(smr, _name))
CONCRETE = {cls.__name__: cls for cls in CONCRETE.values()}


def _to_bytes(pdu) -> bytes:
    buf = io.BytesIO()
    pdu.serialize(DataOutputStream(buf))
    return buf.getvalue()


def _round_trip(cls: type, pdu) -> bytes:
    raw = _to_bytes(pdu)
    assert int.from_bytes(raw[8:10], "big") == len(raw)
    assert pdu.marshalledSize() == len(raw)
    assert PduTypeDecoders[cls.pduType] is cls
    parsed = createPdu(raw)
    assert type(parsed) is cls
    assert _to_bytes(parsed) == raw
    return raw


@pytest.mark.parametrize("cls_name", sorted(CONCRETE))
def test_default_pdu_wire_discipline(cls_name: str) -> None:
    cls = CONCRETE[cls_name]
    assert cls.protocolFamily == 10
    assert isinstance(cls.pduType, int) and 0 < cls.pduType < 256
    _round_trip(cls, cls())


def _fixed(i: int) -> sm.FixedDatum:
    return sm.FixedDatum(fixedDatumID=1000 + i, fixedDatumValue=0xDEAD + i)


def _variable(i: int, payload: bytes) -> sm.VariableDatum:
    return sm.VariableDatum(
        variableDatumID=2000 + i,
        variableData=payload,  # non-multiple-of-8 exercises the pad path
    )


@pytest.mark.parametrize(
    "cls_name",
    [
        "ActionRequestReliablePdu",
        "CommentReliablePdu",
        "DataReliablePdu",
        "EventReportReliablePdu",
        "SetDataReliablePdu",
    ],
)
def test_datum_records_round_trip(cls_name: str) -> None:
    cls = CONCRETE[cls_name]
    pdu = cls()
    pdu.fixedDatumRecords = [_fixed(0), _fixed(1)]
    pdu.variableDatumRecords = [
        _variable(0, b"ABCDE"),  # 5 bytes -> pads to 8
        _variable(1, b"0123456789ab"),  # 12 bytes -> pads to 16
    ]
    raw = _round_trip(cls, pdu)
    parsed = createPdu(raw)
    assert [d.fixedDatumID for d in parsed.fixedDatumRecords] == [1000, 1001]
    assert [d.variableDatumID for d in parsed.variableDatumRecords] == [2000, 2001]
    assert parsed.variableDatumRecords[0].variableData == b"ABCDE"
    assert parsed.variableDatumRecords[1].variableData == b"0123456789ab"


@pytest.mark.parametrize("cls_name", ["DataQueryReliablePdu", "RecordQueryReliablePdu"])
def test_id_lists_round_trip(cls_name: str) -> None:
    cls = CONCRETE[cls_name]
    pdu = cls()
    field = "fixedDatumIDs" if hasattr(pdu, "fixedDatumIDs") else "recordIDs"
    setattr(pdu, field, [1, 0xFFFF, 0x12345678, 7])
    if hasattr(pdu, "variableDatumIDs"):
        pdu.variableDatumIDs = [2, 0xABCDEF]
    raw = _round_trip(cls, pdu)
    assert getattr(createPdu(raw), field) == [1, 0xFFFF, 0x12345678, 7]


@pytest.mark.parametrize("cls_name", ["RecordReliablePdu", "SetRecordReliablePdu"])
def test_record_sets_round_trip(cls_name: str) -> None:
    cls = CONCRETE[cls_name]
    # recordLength is bits-per-record; block = recordLength * recordCount / 8 bytes
    aligned = smr.RecordSpecificationElement(
        recordID=3000,
        recordSetSerialNumber=5,
        recordLength=32,
        recordCount=2,
        recordValues=b"\x00\x01\x00\x02\x00\x03\x00\x04",  # 8 bytes, no pad needed
    )
    padded = smr.RecordSpecificationElement(
        recordID=4500,
        recordSetSerialNumber=6,
        recordLength=12,
        recordCount=2,
        recordValues=b"\x0a\x0b\x0c",  # 3 bytes -> pads 5 to the 64-bit boundary
    )
    pdu = cls()
    pdu.recordSets = [aligned, padded]
    raw = _round_trip(cls, pdu)
    assert len(raw) % 8 == 0  # every record-set block stays 64-bit aligned
    parsed = createPdu(raw)
    assert len(parsed.recordSets) == 2
    got_aligned, got_padded = parsed.recordSets
    assert got_aligned.recordID == 3000
    assert got_aligned.recordLength == 32
    assert got_aligned.recordCount == 2
    assert got_aligned.recordValues == b"\x00\x01\x00\x02\x00\x03\x00\x04"
    assert got_padded.recordID == 4500
    assert got_padded.recordValues == b"\x0a\x0b\x0c"
