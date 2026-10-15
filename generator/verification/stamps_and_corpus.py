"""Stamp-manifest + corpus-oracle verification (milestone 4).

Run from the repo root with the project venv:
    .venv/bin/python generator/verification/stamps_and_corpus.py

Two acceptance passes:

* Stamp manifest — every ``# generator:`` stamp in the emitted record and
  bitfield modules must appear in ``stamp_manifest.txt`` verbatim, and
  every manifest line must still exist. A new or removed stamp without a
  manifest update fails loud (the 2026-10-14 manual-work ruling).
* Corpus oracle — the golden ``.raw`` captures decode via the factory
  and re-serialize byte-exact; every registered PDU type constructs,
  reports ``marshalledSize() == len(to_bytes())`` (wire-length
  self-consistency), and the standard's fixed total sizes hold.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from opendis.record.factory import PduTypeDecoders, createPdu  # noqa: E402
from opendis.stream import DataInputStream, DataOutputStream  # noqa: E402

MANIFEST = Path(__file__).resolve().parent / "stamp_manifest.txt"

# The standard's fixed total PDU sizes (bytes) for the registered,
# fixed-shape types; variable-size types assert self-consistency only.
STANDARD_FIXED_SIZES = {
    1: 144,  # Entity State (1152 bits)
    2: 96,  # Fire (768 bits)
    5: 28,  # Service Request base
    8: 24,  # Resupply Cancel (192 bits)
    9: 28,  # Repair Complete (224 bits)
    10: 28,  # Repair Response (224 bits; enum8 repairResult, uid 65)
    11: 28,  # Create Entity (224 bits)
    12: 28,  # Remove Entity
    13: 44,  # Start/Resume (352 bits)
    14: 40,  # Stop/Freeze (320 bits)
    15: 32,  # Acknowledge (256 bits)
    24: 88,  # Designator (704 bits)
    27: 36,  # Receiver (288 bits)
    33: None,  # Aggregate State: 136+ base (32-byte aggregate marking)
    36: 52,  # IsPartOf (Relationship: two u16 enums, §6.2.74)
    46: 54,  # TSPI default (§9.4.2 minimal state vector)
    47: 18,  # Appearance base (Table 221: 16-bit flag-1)
    48: 17,  # Articulated Parts base (136 bits)
    51: 32,  # Create Entity-R (256 bits)
    52: 32,  # Remove Entity-R
    53: 48,  # Start/Resume-R (384 bits)
    54: 40,  # Stop/Freeze-R (320 bits)
    55: 32,  # Acknowledge-R (256 bits)
    71: 40,  # IO Report base (320 bits)
}


def to_bytes(pdu) -> bytes:
    buf = io.BytesIO()
    pdu.serialize(DataOutputStream(buf))
    return buf.getvalue()


def check_stamps(failures: list[str]) -> None:
    found: set[str] = set()
    for path in sorted(
        list((REPO / "opendis" / "record").rglob("*.py"))
        + list((REPO / "opendis" / "bitfields").rglob("*.py"))
    ):
        for line in path.read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith("# generator:"):
                found.add(stripped)
    manifest = {
        line.rstrip("\n").strip()
        for line in MANIFEST.read_text().splitlines()
        if line.strip() and not line.startswith("##")
    }
    for missing in sorted(found - manifest):
        failures.append(f"stamp not in manifest: {missing!r}")
    for stale in sorted(manifest - found):
        failures.append(f"manifest entry no longer emitted: {stale!r}")


def check_corpus(failures: list[str]) -> None:
    for raw_path in sorted((REPO / "tests").glob("*.raw")):
        data = raw_path.read_bytes()
        pdu = createPdu(data)
        if to_bytes(pdu) != data:
            failures.append(f"{raw_path.name}: re-serialization differs from capture")
    for pdu_type, decoder in sorted(PduTypeDecoders.items()):
        pdu = decoder()
        raw = to_bytes(pdu)
        if pdu.marshalledSize() != len(raw):
            failures.append(
                f"pduType {pdu_type}: marshalledSize {pdu.marshalledSize()} "
                f"!= serialized {len(raw)}"
            )
        wire_length = int.from_bytes(raw[8:10], "big")
        if wire_length != len(raw):
            failures.append(f"pduType {pdu_type}: wire length {wire_length} != {len(raw)}")
        expected = STANDARD_FIXED_SIZES.get(pdu_type)
        if expected is not None and len(raw) != expected:
            failures.append(
                f"pduType {pdu_type}: default size {len(raw)} != standard {expected}"
            )


def main() -> int:
    failures: list[str] = []
    check_stamps(failures)
    check_corpus(failures)
    if failures:
        print("STAMP/CORPUS VERIFICATION FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(
        "stamp + corpus verification PASSED: manifest in sync; .raw captures "
        "byte-exact; every registered PDU wire-length self-consistent; "
        "fixed-size oracle holds"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
