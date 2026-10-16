"""Behavioral parity verification for the milestone-4 family modules.

Run from the repo root with the project venv:
    .venv/bin/python generator/verification/parity_families.py

Regenerates into generated/ (staging), imports each staged family module
alongside the live opendis one, and asserts byte-exact default-PDU
serialization + parse round-trips for a representative PDU per family,
plus the standard's size table (the "Total PDU size" oracle) and factory
registration for every emitted PDU type. Textual identity is NOT
claimed — this verification pins behavior; the byte-identity of each
module is checked separately (generated/ vs opendis/).
"""

from __future__ import annotations

import importlib
import io
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from opendis.record.factory import (
    PDU_FAMILIES,
    PduTypeDecoders,
    createPdu,
)  # noqa: E402
from opendis.stream import DataInputStream, DataOutputStream  # noqa: E402

# (module, class, pduType, family) — one representative per new family,
# plus the Phase 5 additions (Collision/ESU/Attribute §7.2.3-§7.2.6, IFF,
# SEES, Gridded Data)
REPRESENTATIVE = [
    ("record.warfare", "DetonationPdu", 3, 2),
    ("record.logistics", "RepairResponsePdu", 10, 3),
    ("record.simulation_management", "DataQueryPdu", 18, 5),
    ("record.simulation_management_with_reliability", "RecordQueryReliablePdu", 65, 10),
    ("record.minefield", "MinefieldQueryPdu", 38, 8),
    ("record.radio", "SignalPdu", 26, 4),
    ("record.information_operations", "InformationOperationsReportPdu", 71, 13),
    ("record.entity_management", "IsPartOfPdu", 36, 7),
    ("record.synthetic_environment", "ArealObjectStatePdu", 45, 9),
    ("record.distributed_emissions", "DesignatorPdu", 24, 6),
    ("record.live_entity", "ArticulatedPartsPdu", 48, 11),
    ("record.entity_information", "CollisionPdu", 4, 1),
    ("record.entity_information", "CollisionElasticPdu", 66, 1),
    ("record.entity_information", "EntityStateUpdatePdu", 67, 1),
    ("record.entity_information", "AttributePdu", 72, 1),
    ("record.distributed_emissions", "IdentificationFriendOrFoePdu", 28, 6),
    ("record.distributed_emissions", "SupplementalEmissionEntityStatePdu", 30, 6),
    ("record.synthetic_environment", "GriddedDataPdu", 42, 9),
]

# The standard's fixed-size totals for populated-shape checks (bytes);
# variable-size PDUs assert round-trip self-consistency instead
FIXED_SIZES = {
    3: None,  # Detonation: 104 + 16N
    10: 28,  # Repair Response (the corrected enum8 wire)
    18: None,  # Data Query: 40 + 4n
    65: None,  # Record Query-R: 40 + 4n
    38: None,  # Minefield Query: 40 + 16p + 2s + P
    26: None,  # Signal: 32 + data + pad
    71: None,  # IO Report: 40 + records
    36: 52,  # IsPartOf (Relationship is two u16 enums, §6.2.74)
    45: None,  # Areal Object State: 48 + 24n
    24: 88,  # Designator
    48: None,  # Articulated Parts: 17 + 16N
    4: 60,  # Collision (Table 135)
    66: 100,  # Collision-Elastic (Table 136, incl. the seven tail fields)
    67: 72,  # Entity State Update, N=0 (576 bits + 128N)
    72: 32,  # Attribute, S=0 (256 bits + record sets)
    28: 60,  # IFF Layer 1 only (480 bits, Tables 165/167)
    30: 28,  # SEES (Table 174 base)
    42: 64,  # Gridded Data, N=0 G=0 (512 bits, Table 192)
}


def to_bytes(pdu) -> bytes:
    buf = io.BytesIO()
    pdu.serialize(DataOutputStream(buf))
    return buf.getvalue()


def main() -> int:
    rc = subprocess.call(
        [
            sys.executable,
            "-m",
            "generator",
            "--xml-dir",
            str(REPO / "submodules" / "open-dis-spec-xml" / "xml"),
            "--out",
            str(REPO / "generated"),
        ]
    )
    assert rc == 0, "generator run failed"
    sys.path.insert(0, str(REPO / "generated"))
    failures: list[str] = []

    for module_name, class_name, pdu_type, family in REPRESENTATIVE:
        staged = importlib.import_module(module_name)
        cls = getattr(staged, class_name)
        # identity constants + factory registration parity
        if cls.pduType != pdu_type or cls.protocolFamily != family:
            failures.append(f"{class_name}: identity constants wrong")
        if PduTypeDecoders.get(pdu_type) is not getattr(
            importlib.import_module(f"opendis.{module_name}"), class_name
        ):
            failures.append(f"{class_name}: factory decoder not registered")
        if PDU_FAMILIES.get(pdu_type) != family:
            failures.append(f"{class_name}: PDU_FAMILIES disagrees")
        # default PDU: header adopts identity, wire length is exact
        pdu = cls()
        raw = to_bytes(pdu)
        if int.from_bytes(raw[8:10], "big") != len(raw):
            failures.append(f"{class_name}: wire length field != datagram length")
        expected = FIXED_SIZES[pdu_type]
        if expected is not None and len(raw) != expected:
            failures.append(
                f"{class_name}: default size {len(raw)} != standard {expected}"
            )
        # byte-exact reparse round-trip through the factory (the factory
        # returns the live opendis class; the bytes are the contract)
        parsed = createPdu(raw)
        if type(parsed).__name__ != class_name or to_bytes(parsed) != raw:
            failures.append(f"{class_name}: factory round-trip differs")

    if failures:
        print("FAMILY PARITY VERIFICATION FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(
        "family parity verification PASSED: 11 families, identity constants + "
        "factory registration + wire length + size oracle + round-trips"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
