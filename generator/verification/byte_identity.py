"""Byte-identity convergence verification: the exemplar IS the output.

Run from the repo root with the project venv:
    .venv/bin/python generator/verification/byte_identity.py

Regenerates every module from the pinned spec submodules into generated/
(staging) and asserts each staged file is byte-identical to the live
opendis module it ships as — the drift check the family harnesses
deliberately leave out (they pin behavior; this one pins text). Any
hand edit to a generated module, generator-output change, or XML pin
advance shows up here as a named file diff.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
STAGING = REPO / "generated"

MODULES = (
    ["record/common.py"]
    + [
        f"record/{family}/__init__.py"
        for family in (
            "entity_information",
            "warfare",
            "logistics",
            "simulation_management",
            "minefield",
            "radio",
            "information_operations",
            "entity_management",
            "synthetic_environment",
            "distributed_emissions",
            "live_entity",
            "simulation_management_with_reliability",
        )
    ]
    + [
        f"bitfields/{name}.py"
        for name in ("appearance", "minefield", "simulation_management", "warfare")
    ]
)


def main() -> int:
    result = subprocess.run(
        [sys.executable, "-m", "generator", "--out", str(STAGING)],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        print("CONVERGENCE VERIFICATION FAILED: generator run failed")
        return 1

    drifted = []
    for rel in MODULES:
        generated = STAGING / rel
        live = REPO / "opendis" / rel
        if not live.exists():
            drifted.append(f"{rel} (missing from opendis/)")
            continue
        if generated.read_bytes() != live.read_bytes():
            drifted.append(rel)

    if drifted:
        print("CONVERGENCE VERIFICATION FAILED — byte drift in:")
        for rel in drifted:
            print(f"  - {rel}")
        print("regenerate and converge (cp generated/... opendis/...) or")
        print("revert the hand edit; generated output is the canon.")
        return 1
    print(
        f"convergence verification PASSED: {len(MODULES)} modules "
        "(13 record + 4 bitfield) byte-identical to regeneration from "
        "the pinned spec submodules"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
