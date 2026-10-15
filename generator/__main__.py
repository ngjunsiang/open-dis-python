"""CLI: generate record + bitfield modules from the corrected XML set.

Usage (repo root, project venv):
    .venv/bin/python -m generator [--xml-dir xml-fixed]
                                  [--ref010 <SISO-REF-010.xml>]
                                  [--out generated]

The black post-pass runs via the invoking interpreter when available; the
generator itself is stdlib-only by ruling. Output goes to the staging
directory only — never into opendis/ (transition-oracle ruling).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from . import overrides
from .emit import emit_module
from .emit_bitfields import emit_bitfield_module
from .ref010 import load_ref010
from .resolve import Resolver
from .xmlload import load_spec

DEFAULT_REF010 = os.environ.get(
    "REF010_XML",
    str(Path.home() / "ngjunsiang" / "siso-ref-010-xml" / "SISO-REF-010.xml"),
)


def _write(out_root: Path, rel: str, src: str) -> Path:
    path = out_root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(src)
    if subprocess.call([sys.executable, "-m", "black", "-q", str(path)]) != 0:
        print(f"warning: black post-pass failed on {path}", file=sys.stderr)
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="generator")
    ap.add_argument(
        "--xml-dir",
        default="xml-fixed",
        help="corrected XML set (xml-fixed/ or open-dis-spec-xml)",
    )
    ap.add_argument(
        "--ref010", default=DEFAULT_REF010, help="SISO-REF-010.xml (bitfield layouts)"
    )
    ap.add_argument(
        "--out",
        default="generated",
        help="staging output directory (never writes opendis/)",
    )
    args = ap.parse_args(argv)
    out_root = Path(args.out)

    root = load_spec(args.xml_dir)
    resolver = Resolver(root)
    records = resolver.resolve(overrides.COMMON_RECORDS)
    src = emit_module(records, overrides.COMMON_RECORDS, "common")
    path = _write(out_root, "record/common.py", src)
    print(
        f"wrote {path} ({len(src.splitlines())} lines, "
        f"{len(records)} resolved records incl. deps)"
    )

    tables, enum_names = load_ref010(args.ref010)
    for module_key, uids in overrides.BITFIELD_VIEWS.items():
        missing = [u for u in uids if u not in tables]
        if missing:
            raise SystemExit(f"REF-010 missing bitfield uids: {missing}")
        src = emit_bitfield_module(module_key, uids, tables, enum_names)
        path = _write(out_root, f"bitfields/{module_key}.py", src)
        n_classes = len(uids)
        print(f"wrote {path} ({len(src.splitlines())} lines, " f"{n_classes} views)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
