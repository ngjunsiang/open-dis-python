"""Behavioral parity verification generated bitfield views vs the exemplar.

Run from the repo root with the project venv:
    .venv/bin/python generator/verification/parity_bitfields.py

Asserts, per view class: identical _WIDTH and _FIELDS layout (names,
shifts, widths, uids — the core parity claim), identical get/set
behavior under seeded random bit patterns, unknown-bit preservation,
type-sensitive __eq__, and constructor masking.
"""

from __future__ import annotations

import importlib.util
import random
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import opendis.bitfields as ref_pkg  # noqa: E402
from generator import overrides  # noqa: E402


def regenerate() -> None:
    rc = subprocess.call(
        [
            sys.executable,
            "-m",
            "generator",
            "--xml-dir",
            str(REPO / "submodules" / "open-dis-spec-xml" / "xml"),
            "--ref010",
            str(REPO / "submodules" / "siso-ref-010-xml" / "SISO-REF-010.xml"),
            "--out",
            str(REPO / "generated"),
        ]
    )
    assert rc == 0, "generator run failed"


def load_generated(module_key: str):
    path = REPO / "generated" / "bitfields" / f"{module_key}.py"
    spec = importlib.util.spec_from_file_location(f"gen_bf_{module_key}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    regenerate()
    ref_views = {
        name: getattr(ref_pkg, name)
        for name in ref_pkg.__all__
        if name != "BitfieldView"
    }

    failures: list[str] = []
    checked = 0

    for module_key, uids in overrides.BITFIELD_VIEWS.items():
        gen_mod = load_generated(module_key)
        for gen_name in getattr(gen_mod, "__all__", []):
            ref_cls = ref_views.get(gen_name)
            if ref_cls is None:
                failures.append(
                    f"{module_key}: generated class "
                    f"{gen_name!r} absent from exemplar"
                )
                continue
            checked += 1
            failures += _check_pair(getattr(gen_mod, gen_name), ref_cls, gen_name)

    # uid coverage: every curated uid produced a class the exemplar knows
    emitted = set()
    for module_key in overrides.BITFIELD_VIEWS:
        emitted.update(load_generated(module_key).__all__)
    for name in ref_views:
        if name not in emitted:
            failures.append(f"exemplar view {name!r} not generated")

    if failures:
        print("PARITY VERIFICATION FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(
        f"parity verification PASSED: {checked} view classes, layout-identical "
        "_FIELDS + seeded bit-pattern get/set + policy checks"
    )
    return 0


def _check_pair(gen_cls, ref_cls, name: str) -> list[str]:
    failures = []
    if gen_cls._WIDTH != ref_cls._WIDTH:
        failures.append(f"{name}: _WIDTH {gen_cls._WIDTH} != {ref_cls._WIDTH}")
        return failures
    gen_fields = list(gen_cls._FIELDS)
    ref_fields = list(ref_cls._FIELDS)
    if gen_fields != ref_fields:
        gen_map = {f[0]: f for f in gen_fields}
        ref_map = {f[0]: f for f in ref_fields}
        for fname in sorted(set(gen_map) | set(ref_map)):
            g, r = gen_map.get(fname), ref_map.get(fname)
            if g != r:
                failures.append(f"{name}.{fname}: generated {g} != exemplar {r}")
        return failures

    rng = random.Random(hash(name) & 0xFFFF)
    for trial in range(4):
        base = rng.randrange(1 << ref_cls._WIDTH)
        g, r = gen_cls(base), ref_cls(base)
        if int(g) != int(r):
            failures.append(f"{name}: init value diverged")
        for prop, _shift, width, _uid in ref_fields:
            value = (
                bool(rng.getrandbits(1)) if width == 1 else rng.randrange(1 << width)
            )
            setattr(g, prop, value)
            setattr(r, prop, value)
            if getattr(g, prop) != getattr(r, prop) or int(g) != int(r):
                failures.append(f"{name}.{prop}: get/set diverged " f"(trial {trial})")
        # unknown/reserved bits survive property writes identically
        if int(g) != int(r):
            failures.append(f"{name}: reserved-bit preservation diverged")

    if gen_cls(5) == ref_cls(5):
        failures.append(f"{name}: __eq__ not type-sensitive across modules")
    if gen_cls(5) != gen_cls(5) or not gen_cls(5).__eq__(gen_cls(5)):
        failures.append(f"{name}: __eq__ broken within class")
    over = gen_cls((1 << ref_cls._WIDTH) + 7)
    if int(over) != 7:
        failures.append(f"{name}: constructor did not mask to width")
    return failures


if __name__ == "__main__":
    sys.exit(main())
