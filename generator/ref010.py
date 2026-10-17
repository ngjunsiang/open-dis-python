"""Targeted SISO-REF-010 loader (bitfield layouts, enum table names, rows).

The mirror XML (never hand-edited; git-bound tag per the spec-repo
rulings) is the single source for bit layouts: bitfieldrow bit_position
is 0-based (verified against the exemplar layouts) and `length` is
absent on single-bit rows. Enum table names feed the generated
`[UID N] Name` property docstrings. Enum rows ({uid: {value: label}})
drive the context-bitfield derivation (EntityAppearance/EntityCapabilities
tables are kind/domain-qualified by NAME — "Land Platform Appearance",
"Munition Appearance"); the mirror carries row labels in the
`description` attribute (its `name` is empty).
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BitRow:
    name: str
    shift: int  # 0-based bit position
    width: int  # bits; 1 when the length attribute is absent
    xref_uid: int | None
    description: str | None


@dataclass(frozen=True)
class BitfieldTable:
    uid: int
    name: str
    size: int  # bits
    rows: tuple[BitRow, ...]


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def load_ref010(
    path: str | Path,
) -> tuple[dict[int, BitfieldTable], dict[int, str], dict[int, dict[int, str]]]:
    """Return ({uid: BitfieldTable}, {enum uid: table name},
    {enum uid: {value: label}}). Namespace-agnostic: the mirror's root
    carries the SISO default namespace, so tags are matched by local
    name."""
    root = ET.parse(path).getroot()
    bitfields: dict[int, BitfieldTable] = {}
    enum_names: dict[int, str] = {}
    enum_rows: dict[int, dict[int, str]] = {}
    for el in root.iter():
        tag = _local(el.tag)
        if tag == "bitfield":
            uid = int(el.get("uid"))
            rows = []
            for child in el:
                if _local(child.tag) != "bitfieldrow":
                    continue
                xref = child.get("xref")
                rows.append(
                    BitRow(
                        name=child.get("name"),
                        shift=int(child.get("bit_position")),
                        width=int(child.get("length", "1")),
                        xref_uid=int(xref) if xref else None,
                        description=(child.get("description") or "").strip() or None,
                    )
                )
            bitfields[uid] = BitfieldTable(
                uid=uid, name=el.get("name"), size=int(el.get("size")), rows=tuple(rows)
            )
        elif tag == "enum":
            uid = int(el.get("uid"))
            enum_names[uid] = el.get("name")
            rows: dict[int, str] = {}
            for child in el:
                if _local(child.tag) != "enumrow":
                    continue
                label = child.get("name") or child.get("description") or ""
                label = label.strip()
                if label:
                    rows[int(child.get("value"))] = label
            enum_rows[uid] = rows
    return bitfields, enum_names, enum_rows


# -- context-bitfield derivation (bucket-C items 5+6) ------------------------
#
# Some REF-010 bitfield tables are applicability-qualified by NAME: the
# EntityAppearance/EntityCapabilities layouts select per entity kind
# (and, for platforms, per domain) — "Land Platform Appearance" [UID 31],
# "Munition Appearance" [UID 36], "Land Platform Capabilities" [UID 450].
# Every other generated table applies wherever its uid appears. Label
# matching normalizes case/punctuation and the one plural wrinkle
# ("Life form" [UID 7 row] vs table "Life Forms Appearance").

_LABEL_TOKENS = re.compile(r"[^a-z0-9]+")


def _label_key(label: str) -> str:
    """Case/punctuation-insensitive label key with the plural tail folded
    ("Life Forms" == "Life form")."""
    key = _LABEL_TOKENS.sub("", label.lower())
    return key[:-1] if key.endswith("s") and not key.endswith("ss") else key


def context_bitfield_uids(
    tables: dict[int, BitfieldTable],
    enum_rows: dict[int, dict[int, str]],
    candidates: set[int],
    kind_uid: int = 7,
    domain_uid: int = 8,
    suffixes: tuple[str, ...] = ("Appearance", "Capabilities"),
) -> set[int]:
    """Uids of the kind/domain-qualified tables — the context-dependent
    layouts that must NOT attach directly to a raw field. Only generated
    view tables (``candidates``) are classified: REF-010 v37 carries
    further Appearance-family tables (Cultural Feature General/Detail)
    the generator does not view."""
    contextual, _ = _context_split(
        tables, enum_rows, candidates, kind_uid, domain_uid, suffixes
    )
    return contextual


def _context_split(
    tables: dict[int, BitfieldTable],
    enum_rows: dict[int, dict[int, str]],
    candidates: set[int],
    kind_uid: int = 7,
    domain_uid: int = 8,
    suffixes: tuple[str, ...] = ("Appearance", "Capabilities"),
) -> tuple[set[int], dict[str, dict[str, dict[int, int]]]]:
    """Return (context uids, {suffix: {"platform": {domain value: uid},
    "kind": {kind value: uid}}}) over the candidate tables. Fail loud on
    ambiguity — a candidate that qualifies twice, or whose qualifier no
    enum row carries, is a labeling change in REF-010 that needs eyes."""
    kind_keys = {
        _label_key(label): value for value, label in enum_rows.get(kind_uid, {}).items()
    }
    domain_keys = {
        _label_key(label): value
        for value, label in enum_rows.get(domain_uid, {}).items()
    }
    context: set[int] = set()
    layout: dict[str, dict[str, dict[int, int]]] = {
        s: {"platform": {}, "kind": {}} for s in suffixes
    }
    for uid in sorted(candidates):
        table = tables.get(uid)
        if table is None:
            raise ValueError(f"candidate view uid {uid} has no REF-010 table")
        for suffix in suffixes:
            tail = f" {suffix}"
            if not table.name.endswith(tail):
                continue
            qualifier = table.name[: -len(tail)]
            slot = None
            if qualifier.endswith(" Platform"):
                domain = _label_key(qualifier[: -len(" Platform")])
                if domain in domain_keys:
                    slot = ("platform", domain_keys[domain])
            else:
                kind = _label_key(qualifier)
                if kind in kind_keys:
                    slot = ("kind", kind_keys[kind])
            if slot is None:
                raise ValueError(
                    f"REF-010 table {table.name!r} [UID {table.uid}] reads as a "
                    f"context layout but its qualifier matches no {kind_uid}/"
                    f"{domain_uid} row — labeling drift needs review"
                )
            where, value = slot
            bucket = layout[suffix][where]
            if value in bucket:
                raise ValueError(
                    f"two {suffix} tables claim {where} value {value}: "
                    f"[UID {bucket[value]}] and [UID {table.uid}]"
                )
            bucket[value] = table.uid
            context.add(table.uid)
    return context, layout
