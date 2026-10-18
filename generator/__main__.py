"""CLI: generate record + bitfield modules from the corrected XML set.

Usage (repo root, project venv, submodules initialized):
    .venv/bin/python -m generator [--xml-dir ...] [--out generated]

Inputs are the pinned sources of truth (ruled 2026-10-15; REF-010
sourcing re-ruled 2026-10-18): submodules/open-dis-spec-xml/xml is the
canonical final word on DIS 7 wire discrepancies; the pinned
siso-ref-010-python dependency supplies the bitfield layouts, enum
table names and dispatch labels (its wire pin is cross-checked at
load). The black post-pass runs via the invoking interpreter when
available. Output goes to the staging directory only — never into
opendis/ (transition-oracle ruling).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from . import ir, overrides, ref010
from .emit import emit_module
from .emit_bitfields import context_view_layout, direct_view_map, emit_bitfield_module
from .resolve import Resolver
from .xmlload import load_spec

REPO = Path(__file__).resolve().parents[1]
DEFAULT_XML_DIR = REPO / "submodules" / "open-dis-spec-xml" / "xml"


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
        default=str(DEFAULT_XML_DIR),
        help="corrected XML set (default: the pinned spec submodule)",
    )
    ap.add_argument(
        "--out",
        default="generated",
        help="staging output directory (never writes opendis/)",
    )
    args = ap.parse_args(argv)
    out_root = Path(args.out)

    # REF-010 supplies the bitfield views first (bucket-C items 5+6):
    # single-layout tables attach by uid; the kind/domain-qualified
    # EntityAppearance/EntityCapabilities layouts become the context
    # dispatch the entity_information module emits
    tables, enum_names, enum_rows = ref010.load_ref010()
    candidates = {u for uids in overrides.BITFIELD_VIEWS.values() for u in uids}
    context_uids, context_layout = ref010._context_split(tables, enum_rows, candidates)
    view_map = direct_view_map(tables, context_uids)
    context_views = context_view_layout(tables, context_layout, enum_rows)

    root = load_spec(args.xml_dir)
    resolver = Resolver(root, view_map=view_map)
    resolved = {}
    for module_key, order in overrides.RECORD_MODULES.items():
        resolved[module_key] = (order, resolver.resolve(order))
    # list-parse helpers must exist on every record used as a list element
    # in ANY module — the element's home module cannot see the consumers
    all_list_elements = {
        shape.element
        for order, records in resolved.values()
        for name in order
        for attr in records[name].attributes
        if isinstance((shape := attr.shape), ir.ObjectList)
        and (name, attr.name) not in overrides.REGISTRY_LISTS
    }
    for module_key, (order, records) in resolved.items():
        rel = (
            "record/common.py"
            if module_key == "common"
            else f"record/{module_key}/__init__.py"
        )
        src = emit_module(
            records, order, module_key, all_list_elements, context_views=context_views
        )
        path = _write(out_root, rel, src)
        print(
            f"wrote {path} ({len(src.splitlines())} lines, "
            f"{len(records)} resolved records incl. deps)"
        )

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
