"""Static explicit-body emitter (ruled architecture, 2026-10-14).

Consumes resolved RecordClass IR and lays out Python source. Everything
semantic (sizes, uids, variant selection, frozen-ness, curated prose)
was decided upstream; this module only formats text. Output is run
through black afterwards, so spacing here can be conservative.
"""

from __future__ import annotations

import re
import textwrap

from . import ir, overrides
from .xmlload import SpecError

ENUM_IO = {8: "uint8", 16: "uint16", 32: "uint32"}

# types-import ordering: kind group (enum, float, uint, int, ...), then
# width — matches the exemplar's hand order (enum8, enum16, float32,
# float64, uint8, uint16, uint32)
_TYPE_KIND = {"enum": 0, "float": 1, "uint": 2, "int": 3, "struct": 4, "char": 5}


def _type_sort_key(name: str) -> tuple[int, int]:
    for prefix, rank in _TYPE_KIND.items():
        if name.startswith(prefix):
            digits = name[len(prefix) :]
            return (rank, int(digits) if digits.isdigit() else 999)
    return (9, 0)


_TERM_ENUM = re.compile(r"^([A-Za-z_][A-Za-z0-9_.]*)=([A-Za-z0-9_]+)$")
_TERM_BIT = re.compile(r"^([A-Za-z_][A-Za-z0-9_.]*):(\d+)(?:=([01]))?$")


def _const_name(enum_type: str | None) -> str:
    """PlatformDomain -> PLATFORM_DOMAIN_UID (module-level uid constant,
    emitted only for variant-group members)."""
    if not enum_type:
        raise SpecError("variant member without an enum type name")
    words = re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+", enum_type)
    return "_".join(w.upper() for w in words) + "_UID"


def _when_expr(when: str, owner: str) -> str:
    """when= vocabulary term -> Python expression (supports & only)."""
    exprs = []
    for term in (t.strip() for t in when.split("&")):
        m = _TERM_ENUM.match(term)
        if m:
            exprs.append(f"int({m.group(1)}) == {m.group(2)}")
            continue
        m = _TERM_BIT.match(term)
        if m:
            path, bit, val = m.groups()
            masked = f"({path} >> {bit}) & 1"
            exprs.append(f"{masked} == {val}" if val is not None else f"bool({masked})")
            continue
        raise SpecError(f"unsupported when= term {term!r} on {owner!r}")
    return " and ".join(exprs)


def _prim_default(prim_type: str) -> str:
    return "0.0" if prim_type.startswith("float") else "0"


def _variant_members(group: ir.VariantGroup, owner: str):
    """Return (when-carrying members, default member) of an enum group."""
    members = [m for m in group.members if isinstance(m, ir.EnumRef)]
    if len(members) != len(group.members):
        raise SpecError(f"non-enum variant group on {owner!r}")
    when_members = [m for m in members if m.when]
    defaults = [m for m in members if not m.when]
    if len(when_members) != 1 or len(defaults) != 1:
        raise SpecError(
            f"variant group on {owner!r} must have exactly one when= "
            "member plus one default (multi-variant chains: not yet)"
        )
    sizes = {m.size for m in members}
    if len(sizes) != 1:
        raise SpecError(f"variant group on {owner!r} mixes sizes {sizes}")
    return when_members[0], defaults[0]


class _ModuleInfo:
    """Module-level usage scan (imports, constants, logger)."""

    def __init__(self, records: dict[str, ir.RecordClass], order: list[str]):
        self.records = records
        self.order = order
        self.type_names: set[str] = set()
        self.uses_dataclass_field = False
        self.uses_rich_or_int = False
        self.uses_classvar = False
        self.uses_sym = False
        self.needs_logger = False
        self.uid_constants: dict[str, tuple[int, str]] = {}
        for name in order:
            rec = records[name]
            self.needs_logger |= overrides.CLASS_MEMBERS.get(
                name, overrides.MemberSource("", False)
            ).needs_logger
            for var, expr in overrides.CLASS_VARS.get(name, []):
                self.uses_classvar = True
                self.uses_sym |= expr.startswith("sym.")
            for attr in rec.attributes:
                self._scan(attr)

    def _scan(self, attr: ir.Attribute) -> None:
        shape = attr.shape
        if isinstance(shape, ir.Primitive):
            self.type_names.add(shape.type)
        elif isinstance(shape, ir.EnumRef):
            if shape.uid is not None:
                self.uses_rich_or_int = True
                self.uses_classvar = True  # FIELD_ENUM_UID entry
            self.type_names.add(ir.ENUM_ANN[shape.size])
        elif isinstance(shape, ir.ClassRef):
            self.uses_dataclass_field = True
        elif isinstance(shape, ir.FixedBytes):
            pass
        elif isinstance(shape, ir.VariantGroup):
            when_member, default = _variant_members(shape, attr.name)
            for member in (when_member, default):
                self.type_names.add(ir.ENUM_ANN[member.size])
                if member.uid is not None:
                    self.uid_constants[_const_name(member.enum_type)] = (
                        member.uid,
                        member.enum_type,
                    )
            self.uses_rich_or_int = True
            self.uses_classvar = True
        elif isinstance(shape, ir.Unsupported):
            raise SpecError(
                f"unsupported construct on {attr.name!r}: " f"{shape.summary}"
            )

    def uses_enum_uids(self, rec: ir.RecordClass) -> bool:
        return any(
            (isinstance(a.shape, ir.EnumRef) and a.shape.uid is not None)
            or isinstance(a.shape, ir.VariantGroup)
            for a in rec.attributes
        )


def _doc_block(text: str, pad: str, close_alone: bool = True) -> list[str]:
    lines = text.strip("\n").split("\n")
    out = [f'{pad}"""{lines[0]}']
    out += [f"{pad}{ln}" if ln.strip() else "" for ln in lines[1:]]
    if close_alone:
        out.append(f'{pad}"""')
    else:
        out[-1] = f'{out[-1]}"""'
    return out


def _fallback_docstring(rec: ir.RecordClass) -> str:
    if not rec.comment:
        return rec.name
    return "\n".join(
        textwrap.wrap(rec.comment, width=72, initial_indent="", subsequent_indent="")
    )


def emit_module(
    records: dict[str, ir.RecordClass], order: list[str], module: str
) -> str:
    info = _ModuleInfo(records, order)
    lines: list[str] = []

    doc = overrides.MODULE_DOCSTRINGS.get(module)
    if doc:
        lines += _doc_block(doc, pad="", close_alone=True)
        lines.append("")

    dc_names = ["dataclass"] + (["field"] if info.uses_dataclass_field else [])
    lines.append(f"from dataclasses import {', '.join(dc_names)}")
    if info.needs_logger:
        lines.append("import logging")
    if info.uses_classvar:
        lines.append("from typing import ClassVar")
    lines.append("")
    if info.uses_rich_or_int:
        lines.append("from opendis.enum_registry import rich_or_int")
    lines.append("from opendis.stream import DataInputStream, DataOutputStream")
    if info.type_names:
        lines.append("from opendis.types import (")
        for name in sorted(info.type_names, key=_type_sort_key):
            lines.append(f"    {name},")
        lines.append(")")
    if info.uses_sym:
        lines.append("")
        lines.append("from . import symbolic_names as sym")
    if info.needs_logger:
        lines.append("")
        lines.append("_logger = logging.getLogger(__name__)")
    lines.append("")

    exports = list(order)
    for tail in overrides.CLASS_TAILS.values():
        for match in re.finditer(r"^([A-Za-z_][A-Za-z0-9_]*) = ", tail, re.MULTILINE):
            exports.append(match.group(1))
    lines.append("__all__ = [")
    for name in sorted(exports):
        lines.append(f'    "{name}",')
    lines.append("]")

    if info.uid_constants:
        lines.append("")
        for const in sorted(info.uid_constants, key=lambda c: info.uid_constants[c][0]):
            uid, enum_type = info.uid_constants[const]
            label = overrides.VARIANT_UID_COMMENTS.get(uid, enum_type)
            lines.append(f"# [UID {uid}] {label}")
            lines.append(f"{const} = {uid}")

    for name in order:
        lines.append("")
        lines.append("")
        _emit_record(records[name], records, lines)
        tail = overrides.CLASS_TAILS.get(name)
        if tail:
            lines.append("")
            lines.append("")
            lines += tail.split("\n")

    return "\n".join(lines) + "\n"


def _emit_record(
    rec: ir.RecordClass, records: dict[str, ir.RecordClass], lines: list[str]
) -> None:
    if rec.frozen:
        lines.append("@dataclass(frozen=True, slots=True)")
    else:
        lines.append("@dataclass(slots=True)")
    lines.append(f"class {rec.name}:")
    doc = overrides.DOCSTRINGS.get(rec.name) or _fallback_docstring(rec)
    lines += _doc_block(doc, pad="    ")
    lines.append("")

    enum_entries = _field_enum_entries(rec)
    if enum_entries:
        lines.append("    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {")
        for field_name, value in enum_entries:
            lines.append(f'        "{field_name}": {value},')
        lines.append("    }")
        lines.append("")

    for attr in rec.attributes:
        lines.append(_field_line(attr))
        field_doc = overrides.FIELD_DOCSTRINGS.get((rec.name, attr.name))
        if field_doc:
            lines += _doc_block(field_doc, pad="    ", close_alone=False)

    class_vars = overrides.CLASS_VARS.get(rec.name)
    if class_vars:
        lines.append("")
        for var, expr in class_vars:
            lines.append(f"    {var}: ClassVar[int] = {expr}")

    member = overrides.CLASS_MEMBERS.get(rec.name)
    if member:
        lines.append("")
        lines += [f"    {ln}" if ln.strip() else "" for ln in member.source.split("\n")]

    lines.append("")
    lines.append("    def marshalledSize(self) -> int:")
    lines.append(f"        {_marshalled_expr(rec)}")
    lines.append("")
    lines.append("    def serialize(self, outputStream: DataOutputStream) -> None:")
    for attr in rec.attributes:
        lines.append(_serialize_line(attr))
    lines.append("")
    if rec.frozen:
        lines.append("    @classmethod")
        lines.append(
            f'    def parse(cls, inputStream: DataInputStream) -> "{rec.name}":'
        )
    else:
        lines.append("    def parse(self, inputStream: DataInputStream) -> None:")
    stmts, args = _parse_pieces(rec, records)
    lines += stmts
    if rec.frozen:
        lines.append(f"        return cls({', '.join(args)})")


def _field_enum_entries(rec: ir.RecordClass) -> list[tuple[str, str]]:
    entries = []
    for attr in rec.attributes:
        if isinstance(attr.shape, ir.EnumRef) and attr.shape.uid is not None:
            entries.append((attr.name, str(attr.shape.uid)))
        elif isinstance(attr.shape, ir.VariantGroup):
            _, default = _variant_members(attr.shape, attr.name)
            entries.append((attr.name, _const_name(default.enum_type)))
    return entries


def _field_line(attr: ir.Attribute) -> str:
    shape = attr.shape
    if isinstance(shape, ir.Primitive):
        ann, default = shape.type, _prim_default(shape.type)
    elif isinstance(shape, ir.EnumRef):
        ann, default = ir.ENUM_ANN[shape.size], "0"
    elif isinstance(shape, ir.ClassRef):
        ann = shape.target
        default = f"field(default_factory={shape.target})"
    elif isinstance(shape, ir.FixedBytes):
        ann, default = "bytes", f'b"\\x00" * {shape.length}'
    elif isinstance(shape, ir.VariantGroup):
        _, default_member = _variant_members(shape, attr.name)
        ann, default = ir.ENUM_ANN[default_member.size], "0"
    else:
        raise SpecError(f"unsupported field {attr.name!r}")
    line = f"    {attr.name}: {ann} = {default}"
    rider = _uid_rider(attr)
    if rider:
        line += f"  # {rider}"
    return line


def _uid_rider(attr: ir.Attribute) -> str | None:
    shape = attr.shape
    if isinstance(shape, ir.EnumRef) and shape.uid is not None:
        return f"[UID {shape.uid}]"
    if isinstance(shape, ir.VariantGroup):
        _, default = _variant_members(shape, attr.name)
        uids = [default.uid] + [
            m.uid for m in shape.members if isinstance(m, ir.EnumRef) and m.when
        ]
        return " / ".join(f"[UID {u}]" for u in uids if u is not None)
    return None


def _marshalled_expr(rec: ir.RecordClass) -> str:
    parts: list[str] = []
    has_ref = False
    for attr in rec.attributes:
        shape = attr.shape
        if isinstance(shape, ir.ClassRef):
            has_ref = True
            parts.append(f"self.{attr.name}.marshalledSize()")
        elif isinstance(shape, (ir.EnumRef, ir.VariantGroup)):
            size = (
                shape.size
                if isinstance(shape, ir.EnumRef)
                else _variant_members(shape, attr.name)[1].size
            )
            parts.append(str(size // 8))
        elif isinstance(shape, ir.Primitive):
            parts.append(str(ir.PRIM_BITS[shape.type] // 8))
        elif isinstance(shape, ir.FixedBytes):
            parts.append(str(shape.length))
    if not has_ref:
        return f"return {sum(int(p) for p in parts)}"
    return "return " + " + ".join(parts)


def _serialize_line(attr: ir.Attribute) -> str:
    shape = attr.shape
    if isinstance(shape, ir.ClassRef):
        return f"        self.{attr.name}.serialize(outputStream)"
    if isinstance(shape, ir.Primitive):
        return f"        outputStream.write_{shape.type}(self.{attr.name})"
    if isinstance(shape, (ir.EnumRef, ir.VariantGroup)):
        if isinstance(shape, ir.VariantGroup):
            _, default = _variant_members(shape, attr.name)
            size = default.size
        else:
            size = shape.size
        io = ENUM_IO[size]
        return f"        outputStream.write_{io}(self.{attr.name})"
    if isinstance(shape, ir.FixedBytes):
        n = shape.length
        return (
            f"        outputStream.write_bytes("
            f'self.{attr.name}[:{n}].ljust({n}, b"\\x00"))'
        )
    raise SpecError(f"cannot serialize field {attr.name!r}")


def _parse_pieces(
    rec: ir.RecordClass, records: dict[str, ir.RecordClass]
) -> tuple[list[str], list[str]]:
    """Returns (statement lines, positional cls() args) — args only for
    frozen records; mutable records use self-assignments instead."""
    stmts: list[str] = []
    args: list[str] = []
    for attr in rec.attributes:
        shape = attr.shape
        if isinstance(shape, ir.Primitive):
            expr = f"inputStream.read_{shape.type}()"
            _emit_value(rec, attr.name, expr, stmts, args)
        elif isinstance(shape, ir.EnumRef):
            io = ENUM_IO[shape.size]
            expr = f"rich_or_int({shape.uid}, inputStream.read_{io}())"
            _emit_value(rec, attr.name, expr, stmts, args)
        elif isinstance(shape, ir.ClassRef):
            target = records[shape.target]
            if target.frozen:
                expr = f"{shape.target}.parse(inputStream)"
            else:
                expr = f"{shape.target}.parseFrom(inputStream)"
            _emit_value(rec, attr.name, expr, stmts, args)
        elif isinstance(shape, ir.FixedBytes):
            expr = f"inputStream.read_bytes({shape.length})"
            _emit_value(rec, attr.name, expr, stmts, args)
        elif isinstance(shape, ir.VariantGroup):
            when_member, default = _variant_members(shape, attr.name)
            io = ENUM_IO[when_member.size]
            guard = _when_expr(when_member.when, attr.name)
            note = overrides.VARIANT_PARSE_NOTES.get((rec.name, attr.name))
            stmts.append(f"        {attr.name}Raw = inputStream.read_{io}()")
            if note:
                stmts += [f"        {ln}" for ln in note.split("\n")]
            stmts.append(
                f"        {attr.name}Uid = "
                f"{_const_name(when_member.enum_type)} if {guard} "
                f"else {_const_name(default.enum_type)}"
            )
            stmts.append(
                f"        {attr.name} = " f"rich_or_int({attr.name}Uid, {attr.name}Raw)"
            )
            args.append(attr.name)
    return stmts, args


def _emit_value(
    rec: ir.RecordClass, name: str, expr: str, stmts: list[str], args: list[str]
) -> None:
    if rec.frozen:
        if expr.startswith("rich_or_int"):
            stmts.append(f"        {name} = {expr}")
            args.append(name)
        else:
            args.append(expr)
    else:
        stmts.append(f"        self.{name} = {expr}")
