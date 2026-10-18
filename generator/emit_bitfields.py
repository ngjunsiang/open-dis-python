"""Bitfield-view emitter: REF-010 bitfield tables -> view classes.

Policies (exemplar-derived, see docs/design/generator-milestones.md):
* single-bit rows -> bool properties (ruled flat rule); every REF-010
  xref stays in the _FIELDS uid column (always-keep ruling 2026-10-15;
  repr ignores the uid for width-1);
* multi-bit rows -> int properties rich-joined via the row's xref uid;
* property names arrive FINAL from the siso-ref-010-python package
  (ruled 2026-10-18: dis7-ng follows the package, which follows the
  XML; the exemplar's convenience renames are retired);
* reserved gaps (bits covered by no row) round-trip untouched and are
  noted in the class docstring.

BitfieldView/base.py and the package __init__ are hand-maintained
runtime kernel (static seams), not generator output.
"""

from __future__ import annotations

import re

from . import overrides
from .ref010 import BitfieldTable
from .xmlload import SpecError


def _tokens(name: str) -> list[str]:
    return [t for t in re.split(r"[^A-Za-z0-9]+", name) if t]


def _pascal(name: str) -> str:
    return "".join(t[:1].upper() + t[1:] for t in _tokens(name))


def _row_uid(row) -> int | None:
    # Always-keep (ruled 2026-10-15): the uid column is a faithful
    # transcription of the REF-010 xrefs; single-bit rows are bool
    # accessors either way, so repr ignores their uid.
    return row.xref_uid


def _exposed_rows(table: BitfieldTable) -> list:
    # Reserved rows are non-accessors (the package derives their
    # property name as "reserved"); their bits fall out of coverage and
    # land in the reserved-note instead.
    return [r for r in table.rows if r.name.strip().lower() != "reserved"]


def _reserved_note(table: BitfieldTable) -> str | None:
    covered: set[int] = set()
    for row in _exposed_rows(table):
        covered.update(range(row.shift, row.shift + row.width))
    missing = [b for b in range(table.size) if b not in covered]
    if not missing:
        return None
    ranges: list[tuple[int, int]] = []
    for bit in missing:
        if ranges and ranges[-1][1] == bit - 1:
            ranges[-1] = (ranges[-1][0], bit)
        else:
            ranges.append((bit, bit))
    parts = [f"Bits {lo}–{hi}" if hi != lo else f"Bit {lo}" for lo, hi in ranges]
    if len(parts) == 1 and "Bit " in parts[0]:
        return f"{parts[0]} is reserved; it survives round-trips untouched."
    return (
        f"{' and '.join(parts)} are reserved; " f"they survive round-trips untouched."
    )


def _fallback_docstring(table: BitfieldTable) -> str:
    text = f"SISO-REF-010 [UID {table.uid}] {table.name} — " f"{table.size}-bit field."
    note = _reserved_note(table)
    if note:
        text += f"\n\n{note}"
    return text


def _view_class_name(table: BitfieldTable) -> str:
    return overrides.BITFIELD_CLASS_NAMES.get(table.uid, _pascal(table.name))


def direct_view_map(
    tables: dict[int, BitfieldTable], context_uids: set[int], ov=overrides
) -> dict[int, str]:
    """uid -> local view name for the generated single-layout tables
    (bucket-C item 5): every generated view that is NOT one of the
    kind/domain-qualified context tables attaches wherever its uid
    appears. Local-name aliases stay curated (naming choices)."""
    out: dict[int, str] = {}
    for uids in ov.BITFIELD_VIEWS.values():
        for uid in uids:
            if uid in context_uids:
                continue
            table = tables.get(uid)
            if table is None:
                raise SpecError(f"view uid {uid} has no REF-010 table")
            out[uid] = ov.VIEW_LOCAL_ALIASES.get(uid, _view_class_name(table))
    return out


def context_view_layout(
    tables: dict[int, BitfieldTable],
    layout: dict,
    enum_rows: dict[int, dict[int, str]],
    kind_uid: int = 7,
    domain_uid: int = 8,
) -> dict:
    """Emit-ready context dispatch data: per suffix, platform/kind rows
    resolved to (view class name, uid), plus the uid-7/8 row labels the
    dict comments quote."""
    out: dict = {
        suffix: {
            where: {
                value: (_view_class_name(tables[uid]), uid)
                for value, uid in rows.items()
            }
            for where, rows in slots.items()
        }
        for suffix, slots in layout.items()
    }
    out["kind_labels"] = enum_rows.get(kind_uid, {})
    out["domain_labels"] = enum_rows.get(domain_uid, {})
    return out


def emit_bitfield_module(
    module_key: str, uids: list[int], tables: dict, enum_names: dict, ov=overrides
) -> str:
    doc = ov.BITFIELD_MODULE_DOCSTRINGS.get(module_key)
    if doc is None:
        raise SpecError(f"no module docstring curated for {module_key!r}")
    if "\n" not in doc:
        lines: list[str] = [f'"""{doc}"""']
    else:
        doc_lines = doc.split("\n")
        lines = [f'"""{doc_lines[0]}'] + doc_lines[1:] + ['"""']
    lines.append("")
    lines.append("from typing import ClassVar")
    lines.append("")
    lines.append("from opendis.bitfields.base import BitfieldView")
    lines.append("")
    names = [_view_class_name(tables[uid]) for uid in uids]
    one_line = "__all__ = [" + ", ".join(f'"{n}"' for n in sorted(names)) + "]"
    if len(one_line) <= 88:
        lines.append(one_line)
    else:
        lines.append("__all__ = [")
        for name in sorted(names):
            lines.append(f'    "{name}",')
        lines.append("]")

    for uid in uids:
        table = tables[uid]
        if table is None:
            raise SpecError(f"uid {uid} not in REF-010")
        lines.append("")
        lines.append("")
        _emit_view(table, enum_names, lines)
    lines.append("")
    return "\n".join(lines)


def _emit_view(table: BitfieldTable, enum_names: dict, lines: list[str]) -> None:
    cls = _view_class_name(table)
    lines.append(f"class {cls}(BitfieldView):")
    doc = overrides.BITFIELD_DOCSTRINGS.get(table.uid) or _fallback_docstring(table)
    doc_lines = doc.split("\n")
    if len(doc_lines) == 1:
        lines.append(f'    """{doc_lines[0]}"""')
    else:
        lines.append(f'    """{doc_lines[0]}')
        lines += [f"    {ln}" if ln.strip() else "" for ln in doc_lines[1:]]
        lines.append('    """')
    lines.append("")
    lines.append(f"    _WIDTH: ClassVar[int] = {table.size}")
    lines.append(
        "    _FIELDS: ClassVar[tuple[tuple[str, int, int, " "int | None], ...]] = ("
    )
    rows = _exposed_rows(table)
    for row in rows:
        lines.append(
            f"        ({row.name!r}, " f"{row.shift}, {row.width}, {_row_uid(row)}),"
        )
    lines.append("    )")
    for row in rows:
        lines.append("")
        lines += _emit_property(table, row, enum_names)


def _emit_property(table: BitfieldTable, row, enum_names: dict) -> list[str]:
    name = row.name
    uid = _row_uid(row)
    out: list[str] = []
    if row.width == 1:
        out.append("    @property")
        out.append(f"    def {name}(self) -> bool:")
        out.append(f"        return self._getBit({row.shift})")
        out.append("")
        out.append(f"    @{name}.setter")
        out.append(f"    def {name}(self, on: bool) -> None:")
        out.append(f"        self._setBit({row.shift}, on)")
        return out
    out.append("    @property")
    out.append(f"    def {name}(self) -> int:")
    if uid is not None:
        enum_name = enum_names.get(uid)
        label = f"[UID {uid}]" + (f" {enum_name}." if enum_name else ".")
        out.append(f'        """{label}"""')
    out.append(
        f"        return self._getBits({row.shift}, {row.width}, "
        f"{uid if uid is not None else 0})"
    )
    out.append("")
    out.append(f"    @{name}.setter")
    out.append(f"    def {name}(self, value: int) -> None:")
    out.append(f"        self._setBits({row.shift}, {row.width}, value)")
    return out
