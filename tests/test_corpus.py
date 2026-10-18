"""Corpus oracle over the upstream golden ``.raw`` captures.

The six datagrams under tests/ are the real-world PDU packets shipped by
upstream open-dis-python (its complete capture set — every ``.raw`` file
in upstream's tree). This puts them into the pytest/CI layer with the
same acceptance the generator-repo corpus harness applies: each capture
decodes via the factory to its concrete type and re-serializes
byte-exact, with a self-consistent wire-length header.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from opendis.record.factory import createPdu
from opendis.stream import DataOutputStream

CAPTURES = sorted((Path(__file__).parent).glob("*.raw"))

EXPECTED_CLASS = {
    "ElectromagneticEmissionPdu-single-system": "ElectromagneticEmissionPdu",
    "EntityStatePdu-26": "EntityStatePdu",
    "SetDataPdu-multi-variable-datums": "SetDataPdu",
    "SetDataPdu-vbs-script-cmd": "SetDataPdu",
    "SignalPdu": "SignalPdu",
    "TransmitterPdu": "TransmitterPdu",
}


def _to_bytes(pdu) -> bytes:
    buf = io.BytesIO()
    pdu.serialize(DataOutputStream(buf))
    return buf.getvalue()


@pytest.mark.parametrize("raw_path", CAPTURES, ids=lambda p: p.name)
def test_capture_decodes_and_round_trips_byte_exact(raw_path: Path) -> None:
    data = raw_path.read_bytes()
    pdu = createPdu(data)
    assert type(pdu).__name__ == EXPECTED_CLASS[raw_path.stem]
    assert int.from_bytes(data[8:10], "big") == len(data)
    assert pdu.marshalledSize() == len(data)
    assert _to_bytes(pdu) == data


@pytest.mark.parametrize("raw_path", CAPTURES, ids=lambda p: p.name)
def test_capture_double_parse_is_stable(raw_path: Path) -> None:
    """Parsing the re-serialized bytes again yields identical bytes."""
    pdu = createPdu(raw_path.read_bytes())
    once = _to_bytes(pdu)
    pdu2 = createPdu(once)
    assert _to_bytes(pdu2) == once
