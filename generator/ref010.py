"""Targeted SISO-REF-010 adapter over the siso-ref-010-python package.

The pinned siso-ref-010-python dependency is the single REF-010 input
(ruled 2026-10-18: dis7-ng follows the package, which follows the XML;
the retired hand exemplar's convenience spellings — isSmokeEmitting,
nvgMode-style acronym lowering — no longer override the derived
names). Layouts arrive as derived camelCase property names + bit
structure + verbatim descriptions; enum table names feed the generated
``[UID N] Name`` property docstrings; enum rows ({uid: {value:
label}}) drive the context-bitfield derivation (EntityAppearance/
EntityCapabilities tables are kind/domain-qualified by NAME — "Land
Platform Appearance", "Munition Appearance").

``siso_ref010.wire`` pins the dis7-consumed subset (22 layouts, the
uid-7/8 dispatch enums) under a sha256 digest. ``_check_wire_pin``
reserializes that pin from the adapted data at load time — a lossy
adaptation of the package surface cannot pass silently.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from siso_ref010 import bitfields, registry, wire


@dataclass(frozen=True)
class BitRow:
    name: str  # final property name as derived by the package
    shift: int  # 0-based bit position
    width: int  # bits; 1 when the XML length attribute is absent
    xref_uid: int | None
    description: str  # verbatim from the XML row


@dataclass(frozen=True)
class BitfieldTable:
    uid: int
    name: str
    size: int  # bits
    rows: tuple[BitRow, ...]


# v37 uids live below 1000; by_uid probes return None past the last
# table, so the exact bound only needs to be an upper bound. A future
# REF-010 that outgrows it fails loud in the wire pin / view lookups.
_UID_SPACE = 1000


def load_ref010() -> tuple[
    dict[int, BitfieldTable], dict[int, str], dict[int, dict[int, str]]
]:
    """Return ({uid: BitfieldTable}, {enum uid: table name},
    {enum uid: {value: label}}) adapted from the package registries."""
    tables: dict[int, BitfieldTable] = {}
    enum_names: dict[int, str] = {}
    enum_rows: dict[int, dict[int, str]] = {}
    for uid in range(_UID_SPACE):
        view = bitfields.by_uid(uid)
        if view is None:
            continue
        rows = tuple(
            BitRow(
                name=prop,
                shift=shift,
                width=width,
                xref_uid=xref,
                description=description,
            )
            for prop, shift, width, xref, description in view._FIELDS
        )
        tables[view._siso_uid] = BitfieldTable(
            uid=view._siso_uid, name=view._siso_name, size=view._WIDTH, rows=rows
        )
    for uid in range(_UID_SPACE):
        table = registry.by_uid(uid)
        if table is None:
            continue
        enum_names[table._siso_uid] = table._siso_name
        enum_rows[table._siso_uid] = {int(member): member.description for member in table}
    _check_wire_pin(tables, enum_names, enum_rows)
    return tables, enum_names, enum_rows


# -- wire pin (D16 downstream cross-check) ------------------------------------
#
# siso_ref010.wire serializes the dis7-consumed subset (layouts in uid
# order, rows in bit-position order; dispatch enums in value order)
# under a pinned sha256. Reserializing the same lines from the adapted
# data proves the adaptation above is lossless for identity, bit
# structure, property names and descriptions — anything the emitters
# bake.


def _pin_lines(
    tables: dict[int, BitfieldTable],
    enum_names: dict[int, str],
    enum_rows: dict[int, dict[int, str]],
) -> list[str]:
    lines: list[str] = []
    for uid in wire.DIS7_LAYOUT_UIDS:
        table = tables.get(uid)
        if table is None:
            raise ValueError(f"wire pin lists layout uid {uid} missing from the package")
        lines.append(f"L {uid} {table.size} {table.name!r}")
        for row in sorted(table.rows, key=lambda r: r.shift):
            lines.append(
                f"R {row.shift} {row.width} {row.xref_uid} "
                f"{row.name!r} {row.description!r}"
            )
    for uid in wire.DIS7_ENUM_UIDS:
        if uid not in enum_rows:
            raise ValueError(f"wire pin lists enum uid {uid} missing from the package")
        lines.append(f"E {uid} {enum_names[uid]!r}")
        for value in sorted(enum_rows[uid]):
            lines.append(f"M {value} {enum_rows[uid][value]!r}")
    return lines


def _check_wire_pin(
    tables: dict[int, BitfieldTable],
    enum_names: dict[int, str],
    enum_rows: dict[int, dict[int, str]],
) -> None:
    ours = _pin_lines(tables, enum_names, enum_rows)
    pinned = list(wire.canonical_lines())
    if ours != pinned:
        diffs = [
            f"  adapter: {a!r}\n  pinned: {b!r}"
            for a, b in zip(ours, pinned, strict=False)
            if a != b
        ][:5]
        head = "wire pin mismatch" + (
            f" ({len(ours)} vs {len(pinned)} lines)"
            if len(ours) != len(pinned)
            else ""
        )
        raise ValueError(
            f"{head}: the adapter diverges from siso_ref010.wire — first diffs:\n"
            + "\n".join(diffs)
        )


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
