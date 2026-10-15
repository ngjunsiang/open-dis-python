"""Behavioral parity verification generated entity_information family vs exemplar.

Run from the repo root with the project venv:
    .venv/bin/python generator/verification/parity_entity_information.py

Regenerates into generated/ (staging), imports both modules, and asserts
byte-exact PDU serialization (header + body), cross-parse round-trips,
size parity, the derived-count property, wholesale list replacement on
reparse (PR #49), context-dependent bitfield view wrapping, wire-length
correctness, PDU identity constants, and factory registration parity.
Textual identity is NOT claimed — this verification pins behavior.
"""

from __future__ import annotations

import importlib
import io
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import opendis.record.common as common  # noqa: E402
import opendis.record.entity_information as ref  # noqa: E402
from opendis.stream import DataInputStream, DataOutputStream  # noqa: E402
from opendis.timestamp import Timestamp  # noqa: E402


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
    return importlib.import_module("record.entity_information")


def to_bytes(pdu) -> bytes:
    buf = io.BytesIO()
    pdu.serialize(DataOutputStream(buf))
    return buf.getvalue()


def parse_into(module, data: bytes):
    pdu = module.EntityStatePdu()
    pdu.parse(DataInputStream(io.BytesIO(data)))
    return pdu


def sample(mod):
    """A fully-populated EntityStatePdu: land platform, 2 variable params,
    short (sub-sized) dead-reckoning parameters — the shape that exposed
    the exemplar's unpadded marshalledSize bug."""
    pdu = mod.EntityStatePdu()
    pdu.header.timestamp = Timestamp(0x12345678)
    pdu.entityID = common.EntityIdentifier(common.SimulationAddress(1, 2), 3)
    pdu.forceId = 2
    pdu.entityType = common.EntityType(1, 1, 222, 3, 4, 5, 6)
    pdu.alternativeEntityType = common.EntityType(1, 2, 223, 3, 4, 5, 6)
    pdu.entityLinearVelocity = common.Vector3Float(1.5, -2.5, 3.5)
    pdu.entityLocation = common.Vector3Double(1.0e6, 2.0e6, 3.0e3)
    pdu.entityOrientation = common.EulerAngles(0.1, 0.2, 0.3)
    pdu.entityAppearance = 0xDEADBEEF
    pdu.deadReckoningParameters = mod.DeadReckoningParameters(
        2, b"ABC", common.Vector3Float(0.1, 0.2, 0.3), common.Vector3Float(0, 0, 0)
    )
    pdu.marking = common.EntityMarking(1, b"TEST-ENTITY")
    pdu.capabilities = 0x0F0F0F0F
    pdu.variableParameters = [
        mod.VariableParameter(1, b"X" * 15),
        mod.VariableParameter(2, b"Y" * 15),
    ]
    return pdu


def main() -> int:
    regenerate()
    gen = load_generated()

    failures: list[str] = []

    # byte-exact serialization + cross-parse both directions
    ref_pdu, gen_pdu = sample(ref), sample(gen)
    ref_bytes, gen_bytes = to_bytes(ref_pdu), to_bytes(gen_pdu)
    if ref_bytes != gen_bytes:
        failures.append(
            f"serialize mismatch ({len(gen_bytes)} vs {len(ref_bytes)} bytes)"
        )
    for mod in (gen, ref):
        data = ref_bytes if mod is gen else gen_bytes
        if to_bytes(parse_into(mod, data)) != ref_bytes:
            failures.append(f"{mod.__name__}: cross-parse round-trip differs")

    # size parity, identity constants, and wire evidence
    if ref_pdu.marshalledSize() != gen_pdu.marshalledSize():
        failures.append("marshalledSize differs")
    if (gen_pdu.pduType, gen_pdu.protocolFamily) != (1, 1):
        failures.append("identity ClassVars wrong on generated PDU")
    if gen_pdu.header.pduType != 1:
        failures.append("default header did not adopt the class identity")
    if len(gen_bytes) >= 10:
        wire_length = int.from_bytes(gen_bytes[8:10], "big")
        if wire_length != len(gen_bytes):
            failures.append(
                f"wire length field {wire_length} != actual {len(gen_bytes)}"
            )

    # derived count property + wholesale list replacement (PR #49)
    parsed = parse_into(gen, ref_bytes)
    if parsed.numberOfVariableParameters != 2 or len(parsed.variableParameters) != 2:
        failures.append("derived count property wrong")
    parse_into(gen, ref_bytes + ref_bytes)  # double payload: reparse
    if len(parsed.variableParameters) != 2:
        failures.append("list appended on reparse (PR #49 corruption)")

    # context-dependent bitfield views: land platform wraps, unknown stays int
    from opendis.bitfields import (
        AirPlatformAppearance,
        LandPlatformAppearance,
        LandPlatformCapabilities,
    )

    parsed = parse_into(gen, ref_bytes)
    if not isinstance(parsed.entityAppearance, LandPlatformAppearance):
        failures.append(f"appearance not wrapped: {type(parsed.entityAppearance)}")
    if not isinstance(parsed.capabilities, LandPlatformCapabilities):
        failures.append(f"capabilities not wrapped: {type(parsed.capabilities)}")
    if (
        int(parsed.entityAppearance) != 0xDEADBEEF
        or int(parsed.capabilities) != 0x0F0F0F0F
    ):
        failures.append("view round-trip lost raw bits")

    air = sample(ref)
    air.entityType = common.EntityType(1, 2, 222, 3, 4, 5, 6)
    air_pdu = parse_into(gen, to_bytes(air))
    if not isinstance(air_pdu.entityAppearance, AirPlatformAppearance):
        failures.append("air platform appearance not wrapped")

    unknown = sample(ref)
    unknown.entityType = common.EntityType(2, 5, 830, 1, 0, 0, 0)
    unknown_bytes = to_bytes(unknown)
    unknown_parsed = parse_into(gen, unknown_bytes)
    if type(unknown_parsed.entityAppearance) is not int:
        failures.append("unknown entity kind did not keep plain int")
    if to_bytes(unknown_parsed) != unknown_bytes:
        failures.append("unknown-kind round-trip differs")

    # sub-sized fixed bytes must not shrink the size (unpadded-len bug)
    short = sample(ref)
    short.deadReckoningParameters.parameters = b""
    if short.marshalledSize() != len(to_bytes(short)):
        failures.append("marshalledSize != serialized length for sub-sized parameters")

    # factory registration parity (hand-maintained factory vs generated class)
    from opendis.record.factory import PDU_FAMILIES, PduTypeDecoders, createPdu

    if PduTypeDecoders.get(1) is not ref.EntityStatePdu:
        failures.append("factory pduType 1 not registered to EntityStatePdu")
    if PDU_FAMILIES.get(1) != gen.EntityStatePdu.protocolFamily:
        failures.append("factory family metadata disagrees with generated PDU")
    via_factory = createPdu(gen_bytes)
    if (
        type(via_factory) is not ref.EntityStatePdu
        or to_bytes(via_factory) != gen_bytes
    ):
        failures.append("factory decode of generated bytes failed")

    if failures:
        print("PARITY VERIFICATION FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(
        "parity verification PASSED: EntityStatePdu byte-exact + cross-parse + "
        "derived counts + view wraps + wire length + factory registration"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
