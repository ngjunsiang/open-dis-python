"""Behavioral parity verification generated common records vs the exemplar.

Run from the repo root with the project venv:
    .venv/bin/python generator/verification/parity_common.py

Regenerates into generated/ (staging), imports both modules, and asserts
byte-level serialization equality, cross-parse round-trips, size parity,
frozen-ness, parse-style, alias identity, and enum-registry degradation.
Textual identity with the exemplar is NOT claimed — docstring canon and
member ordering ride in overrides.py; this verification pins behavior.
"""

from __future__ import annotations

import dataclasses
import importlib
import io
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import opendis.record.common as ref  # noqa: E402
from opendis.stream import DataInputStream, DataOutputStream  # noqa: E402


def regenerate() -> None:
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
    staging = REPO / "generated" / "record"
    (staging / "__init__.py").touch()
    shutil.copy(
        REPO / "opendis" / "record" / "symbolic_names.py", staging / "symbolic_names.py"
    )


def load_generated():
    sys.path.insert(0, str(REPO / "generated"))
    return importlib.import_module("record.common")


def to_bytes(record) -> bytes:
    buf = io.BytesIO()
    record.serialize(DataOutputStream(buf))
    return buf.getvalue()


def _is_frozen(cls) -> bool:
    return getattr(cls, "__dataclass_params__").frozen


SAMPLES = {
    "SimulationAddress": lambda m: m.SimulationAddress(1, 2),
    "EntityIdentifier": lambda m: m.EntityIdentifier(m.SimulationAddress(1, 2), 3),
    "EventIdentifier": lambda m: m.EventIdentifier(m.SimulationAddress(4, 5), 6),
    "EntityType": lambda m: m.EntityType(1, 2, 3, 4, 5, 6, 7),
    "EulerAngles": lambda m: m.EulerAngles(0.1, 0.2, 0.3),
    "Vector3Float": lambda m: m.Vector3Float(1.0, 2.0, 3.0),
    "Vector3Double": lambda m: m.Vector3Double(1.5, 2.5, 3.5),
    "ClockTime": lambda m: m.ClockTime(3600, 1234),
    "MunitionDescriptor": lambda m: m.MunitionDescriptor(
        m.EntityType(1, 1, 222, 3, 4, 5, 6), 7, 8, 9, 10
    ),
    "EntityMarking": lambda m: m.EntityMarking(1, b"HELLO\x00\x00\x00\x00\x00\x00"),
}


def parse_with(module, name: str, data: bytes):
    cls = getattr(module, name)
    if _is_frozen(cls):
        return cls.parse(DataInputStream(io.BytesIO(data)))
    instance = cls()
    instance.parse(DataInputStream(io.BytesIO(data)))
    return instance


def main() -> int:
    regenerate()
    gen = load_generated()

    failures = []

    for name, make in SAMPLES.items():
        ref_obj = make(ref)
        gen_obj = make(gen)
        ref_bytes = to_bytes(ref_obj)
        gen_bytes = to_bytes(gen_obj)
        if ref_bytes != gen_bytes:
            failures.append(
                f"{name}: serialize mismatch " f"{gen_bytes!r} != {ref_bytes!r}"
            )
            continue
        # cross-parse both directions, then re-serialize
        for src_mod, dst_mod in ((ref, gen), (gen, ref)):
            parsed = parse_with(dst_mod, name, ref_bytes)
            if to_bytes(parsed) != ref_bytes:
                failures.append(
                    f"{name}: {dst_mod.__name__} cross-parse " "round-trip differs"
                )
        if ref_obj.marshalledSize() != gen_obj.marshalledSize():
            failures.append(
                f"{name}: marshalledSize "
                f"{gen_obj.marshalledSize()} != "
                f"{ref_obj.marshalledSize()}"
            )
        if _is_frozen(getattr(ref, name)) != _is_frozen(getattr(gen, name)):
            failures.append(f"{name}: frozen-ness differs")

    # ruled alias
    assert gen.WorldCoordinates is gen.Vector3Double, "alias broken"

    # enum degradation: no registry plugged in -> parse yields plain ints
    et = parse_with(gen, "EntityType", to_bytes(ref.EntityType(2, 5, 830, 1, 0, 0, 0)))
    assert type(et.entityKind) is int and not isinstance(et.entityKind, bool)
    assert type(et.domain) is int
    # munition kind (2) selected the uid-14 table without a registry:
    # still an int, wire value preserved
    assert et.domain == 5

    # marking string property (injected member) works end to end
    marking = gen.EntityMarking(1, b"DIS7\x00\x00\x00\x00\x00\x00\x00")
    assert marking.string == "DIS7"
    marking.string = "TOOLONGNAME-TRUNCATES"
    assert marking.string == "TOOLONGNAME"

    # symbolic ClassVars present
    assert gen.SimulationAddress.ALL_SITES == 0xFFFF
    assert gen.EntityIdentifier.ALL_ENTITIES == 0xFFFF

    if failures:
        print("PARITY VERIFICATION FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(
        f"parity verification PASSED: {len(SAMPLES)} record classes, "
        "byte-exact serialization + cross-parse + sizes + policy checks"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
