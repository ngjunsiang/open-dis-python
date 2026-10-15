"""Targeted SISO-REF-010 loader (bitfield layouts + enum table names).

The mirror XML (never hand-edited; git-bound tag per the spec-repo
rulings) is the single source for bit layouts: bitfieldrow bit_position
is 0-based (verified against the exemplar layouts) and `length` is
absent on single-bit rows. Enum table names feed the generated
`[UID N] Name` property docstrings.
"""

from __future__ import annotations

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


def load_ref010(path: str | Path) -> tuple[dict[int, BitfieldTable], dict[int, str]]:
    """Return ({uid: BitfieldTable}, {enum uid: enum table name}).

    Namespace-agnostic: the mirror's root carries the SISO default
    namespace, so tags are matched by local name.
    """
    root = ET.parse(path).getroot()
    bitfields: dict[int, BitfieldTable] = {}
    enum_names: dict[int, str] = {}
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
            enum_names[int(el.get("uid"))] = el.get("name")
    return bitfields, enum_names
