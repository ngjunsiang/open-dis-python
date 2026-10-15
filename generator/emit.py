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

# -- XML-canonical docstrings (ruled 2026-10-15, .references/decisions.md) ---

_CITE = r"\d+(?:\.\d+)+"


def _normalize_cites(text: str) -> str:
    """§-normalize the citation forms the XML uses (conservative, targeted)."""
    text = re.sub(rf"Section ({_CITE})", r"§\1", text, flags=re.IGNORECASE)
    text = re.sub(rf"\bSee ({_CITE})\b", r"See §\1", text)
    text = re.sub(rf"\(({_CITE}) item", r"(§\1 item", text)
    return text


def canonical_docstring(comment: str | None, title: str | None, fallback: str) -> str:
    """Build the canonical docstring from an XML class comment.

    The record's own citation (a leading "N.N." header form or a trailing
    standalone cite) hoists to the "§N.N <Title>" prefix line; the rest is
    the body, wrapped at 72. Without a citation the body stands alone
    (curated titles are only shown with one).
    """
    if not comment or not comment.strip():
        return fallback
    text = _normalize_cites(comment.strip())
    cite = None
    body = text
    m = re.match(rf"^(§)?({_CITE})\.?[ \t]+(.*)$", text, re.S)
    if m:
        cite, body = m.group(2), m.group(3).strip()
    else:
        m = re.search(rf"§({_CITE})\.?$", text)
        if m and m.start() > 0:
            cite = m.group(1)
            body = text[: m.start()].rstrip()
    if not body.endswith((".", "!", "?", ":")):
        body += "."
    if cite:
        head = f"§{cite} {title}" if title else f"§{cite}"
        doc = head + "\n\n"
    else:
        doc = ""
    doc += "\n".join(textwrap.wrap(body, width=72) or [body])
    return doc


def _wrap_prose(text: str) -> str:
    """Wrap curated prose at 72 cols; paragraphs made entirely of comment
    lines (``# generator:`` notes) stay verbatim."""
    paras = text.split("\n\n")
    out = []
    for para in paras:
        stripped = [ln for ln in para.split("\n") if ln.strip()]
        if stripped and all(ln.lstrip().startswith("#") for ln in stripped):
            out.append(para)
        else:
            out.append("\n".join(textwrap.wrap(para, width=72)))
    return "\n\n".join(out)


def _import_stmt(module: str, names: list[str]) -> list[str]:
    """One-line import when it fits 88 cols (black-stable), else the
    magic-trailing-comma exploded form black preserves."""
    single = f"from {module} import {', '.join(names)}"
    if len(single) <= 88:
        return [single]
    return [f"from {module} import ("] + [f"    {n}," for n in names] + [")"]


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

    def __init__(
        self,
        records: dict[str, ir.RecordClass],
        order: list[str],
        module: str,
    ):
        self.records = records
        self.order = order
        self.module = module
        self.own = set(order)
        self.cross_imports: dict[str, set[str]] = {}
        for source_mod, names in overrides.MODULE_SOURCE_IMPORTS.get(
            module, {}
        ).items():
            self.cross_imports.setdefault(source_mod, set()).update(names)
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
            for _, expr, _ in overrides.CLASS_VARS.get(name, []):
                self.uses_classvar = True
                self.uses_sym |= expr.startswith("sym.")
            for attr in rec.attributes:
                self._scan(name, attr)

    def module_path(self, class_name: str) -> str | None:
        """Home module path of an emitted class, or None when the name is
        not a generated record (kernel bases are handled separately)."""
        for key, order in overrides.RECORD_MODULES.items():
            if class_name in order:
                return f"opendis.record.{key}"
        return None

    def add_import(self, module: str, name: str) -> None:
        self.cross_imports.setdefault(module, set()).add(name)

    def _scan(self, owner: str, attr: ir.Attribute) -> None:
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
            annotation = overrides.FIELD_ANNOTATIONS.get(
                (owner, attr.name), shape.target
            )
            home = self.module_path(shape.target)
            if home and home != f"opendis.record.{self.module}":
                self.add_import(home, annotation)
        elif isinstance(shape, ir.FixedBytes):
            pass
        elif isinstance(shape, ir.BitfieldRef):
            self.type_names.add(f"uint{shape.size}")
        elif isinstance(shape, ir.ObjectList):
            self.uses_dataclass_field = True
            home = self.module_path(shape.element)
            if home and home != f"opendis.record.{self.module}":
                self.add_import(home, shape.element)
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


def emit_module(
    records: dict[str, ir.RecordClass], order: list[str], module: str
) -> str:
    info = _ModuleInfo(records, order, module)
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

    imports: dict[str, list[str]] = {}
    kernel_exports = {base: mod for base, mod in overrides.KERNEL_BASES.values()}
    for name in order:
        rec = records[name]
        if rec.is_pdu and rec.parent:
            if rec.parent in kernel_exports:
                info.add_import(kernel_exports[rec.parent], rec.parent)
            elif rec.parent not in info.own:
                home = info.module_path(rec.parent)
                if home:
                    info.add_import(home, rec.parent)
    for mod, names in info.cross_imports.items():
        imports[mod] = sorted(names)
    if info.uses_rich_or_int:
        imports.setdefault("opendis.enum_registry", []).append("rich_or_int")
    imports.setdefault("opendis.stream", []).extend(
        ["DataInputStream", "DataOutputStream"]
    )
    if info.type_names:
        imports["opendis.types"] = sorted(info.type_names, key=_type_sort_key)
    for mod in sorted(imports):
        lines += _import_stmt(mod, imports[mod])

    if info.uses_sym:
        lines.append("")
        lines.append("from . import symbolic_names as sym")
    if info.needs_logger:
        lines.append("")
        lines.append("_logger = logging.getLogger(__name__)")
    lines.append("")

    exports = list(order)
    for name in order:
        tail = overrides.CLASS_TAILS.get(name)
        if not tail:
            continue
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

    insertions = dict(overrides.MODULE_SOURCES.get(module, []))
    list_elements = {
        s.element
        for name in order
        for attr in records[name].attributes
        if isinstance((s := attr.shape), ir.ObjectList)
    }
    for name in order:
        lines.append("")
        lines.append("")
        _emit_record(records[name], records, lines, list_elements)
        tail = overrides.CLASS_TAILS.get(name)
        if tail:
            lines.append("")
            lines.append("")
            lines += tail.split("\n")
        block = insertions.get(name)
        if block:
            lines.append("")
            lines.append("")
            lines += block.split("\n")

    return "\n".join(lines) + "\n"


def _emit_record(
    rec: ir.RecordClass,
    records: dict[str, ir.RecordClass],
    lines: list[str],
    list_elements: set[str] = frozenset(),
) -> None:
    if rec.frozen:
        lines.append("@dataclass(frozen=True, slots=True)")
    else:
        lines.append("@dataclass(slots=True)")
    if rec.parent:
        lines.append(f"class {rec.name}({rec.parent}):")
    else:
        lines.append(f"class {rec.name}:")
    doc = overrides.DOCSTRING_OVERRIDES.get(rec.name)
    if doc is None:
        doc = canonical_docstring(
            rec.comment, overrides.DOCSTRING_TITLES.get(rec.name), rec.name
        )
        addendum = overrides.DOCSTRING_ADDENDA.get(rec.name)
        if addendum:
            doc += "\n\n" + _wrap_prose(addendum)
    lines += _doc_block(doc, pad="    ")
    lines.append("")

    class_vars = overrides.CLASS_VARS.get(rec.name)
    if rec.is_pdu and class_vars:
        # PDU identity constants lead the body (pduType/protocolFamily)
        _emit_class_vars(class_vars, lines)
        lines.append("")

    enum_entries = _field_enum_entries(rec)
    if enum_entries:
        lines.append("    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {")
        for field_name, value in enum_entries:
            lines.append(f'        "{field_name}": {value},')
        lines.append("    }")
        lines.append("")

    for attr in rec.attributes:
        if attr.hidden:
            continue  # wire-only count: derived property below, never state
        lines.append(_field_line(rec.name, attr))
        field_doc = overrides.FIELD_DOCSTRINGS.get((rec.name, attr.name))
        if field_doc:
            lines += _doc_block(field_doc, pad="    ", close_alone=False)

    for attr in rec.attributes:
        if attr.hidden:
            lines.append("")
            lines.append("    @property")
            lines.append(f"    def {attr.name}(self) -> {attr.shape.type}:")
            prop_doc = canonical_docstring(attr.comment, None, attr.name)
            lines += _doc_block(prop_doc, pad="        ")
            lines.append(f"        return len(self.{attr.count_for})")

    if not rec.is_pdu:
        _emit_class_vars(class_vars, lines, leading_blank=True)

    member = overrides.CLASS_MEMBERS.get(rec.name)
    if member:
        lines.append("")
        lines += [f"    {ln}" if ln.strip() else "" for ln in member.source.split("\n")]

    if not rec.attributes:
        return  # family markers carry no wire body — methods inherit

    size_name, ser_name, parse_name = (
        ("_marshalledBodySize", "_serializeBody", "_parseBody")
        if rec.is_pdu
        else ("marshalledSize", "serialize", "parse")
    )
    lines.append("")
    lines.append(f"    def {size_name}(self) -> int:")
    lines.append(f"        {_marshalled_expr(rec)}")
    lines.append("")
    lines.append(f"    def {ser_name}(self, outputStream: DataOutputStream) -> None:")
    for attr in rec.attributes:
        lines.append(_serialize_line(attr))
    lines.append("")
    if rec.frozen:
        lines.append("    @classmethod")
        lines.append(
            f'    def parse(cls, inputStream: DataInputStream) -> "{rec.name}":'
        )
    else:
        lines.append(
            f"    def {parse_name}(self, inputStream: DataInputStream) -> None:"
        )
    stmts, args = _parse_pieces(rec, records)
    lines += stmts
    if rec.frozen:
        lines.append(f"        return cls({', '.join(args)})")

    tail = overrides.PARSE_TAILS.get(rec.name)
    if tail:
        lines.append("")
        lines += [f"        {ln}" if ln.strip() else "" for ln in tail.split("\n")]

    if rec.name in list_elements and not rec.frozen:
        # list-parse helper (mechanical; the exemplar families' convention)
        lines.append("")
        lines.append("    @classmethod")
        lines.append(
            f'    def parseFrom(cls, inputStream: DataInputStream) -> "{rec.name}":'
        )
        lines.append(
            '        """Construct a new record from the stream (list-parse helper; the'
        )
        lines.append(
            '        mutating ``parse`` above satisfies the Record protocol)."""'
        )
        lines.append("        item = cls()")
        lines.append("        item.parse(inputStream)")
        lines.append("        return item")


def _emit_class_vars(
    class_vars: list[tuple[str, str, str | None]] | None,
    lines: list[str],
    leading_blank: bool = False,
) -> None:
    if not class_vars:
        return
    if leading_blank:
        lines.append("")
    for var, expr, comment in class_vars:
        line = f"    {var}: ClassVar[int] = {expr}"
        if comment:
            line += f"  # {comment}"
        lines.append(line)


def _field_enum_entries(rec: ir.RecordClass) -> list[tuple[str, str]]:
    entries = []
    for attr in rec.attributes:
        if isinstance(attr.shape, ir.EnumRef) and attr.shape.uid is not None:
            entries.append((attr.name, str(attr.shape.uid)))
        elif isinstance(attr.shape, ir.VariantGroup):
            _, default = _variant_members(attr.shape, attr.name)
            entries.append((attr.name, _const_name(default.enum_type)))
    return entries


def _field_line(owner: str, attr: ir.Attribute) -> str:
    shape = attr.shape
    if isinstance(shape, ir.Primitive):
        ann, default = shape.type, _prim_default(shape.type)
    elif isinstance(shape, ir.EnumRef):
        ann, default = ir.ENUM_ANN[shape.size], "0"
    elif isinstance(shape, ir.ClassRef):
        ann = overrides.FIELD_ANNOTATIONS.get((owner, attr.name), shape.target)
        default = f"field(default_factory={ann})"
    elif isinstance(shape, ir.FixedBytes):
        ann, default = "bytes", f'b"\\x00" * {shape.length}'
    elif isinstance(shape, ir.BitfieldRef):
        ann, default = f"uint{shape.size}", "0"
    elif isinstance(shape, ir.ObjectList):
        ann, default = f"list[{shape.element}]", "field(default_factory=list)"
    elif isinstance(shape, ir.VariantGroup):
        _, default_member = _variant_members(shape, attr.name)
        ann, default = ir.ENUM_ANN[default_member.size], "0"
    else:
        raise SpecError(f"unsupported field {attr.name!r}")
    line = f"    {attr.name}: {ann} = {default}"
    rider = overrides.FIELD_RIDERS.get((owner, attr.name)) or _uid_rider(attr)
    if rider:
        line += f"  # {rider}"
    return line


def _uid_rider(attr: ir.Attribute) -> str | None:
    shape = attr.shape
    if isinstance(shape, ir.EnumRef) and shape.uid is not None:
        return f"[UID {shape.uid}]"
    if isinstance(shape, ir.BitfieldRef):
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
        if attr.hidden:
            # wire-only count byte: contributes to size, never to state
            parts.append(str(ir.PRIM_BITS[shape.type] // 8))
        elif isinstance(shape, ir.ClassRef):
            has_ref = True
            parts.append(f"self.{attr.name}.marshalledSize()")
        elif isinstance(shape, ir.ObjectList):
            has_ref = True
            parts.append(f"sum(item.marshalledSize() for item in self.{attr.name})")
        elif isinstance(shape, (ir.EnumRef, ir.VariantGroup)):
            size = (
                shape.size
                if isinstance(shape, ir.EnumRef)
                else _variant_members(shape, attr.name)[1].size
            )
            parts.append(str(size // 8))
        elif isinstance(shape, ir.Primitive):
            parts.append(str(ir.PRIM_BITS[shape.type] // 8))
        elif isinstance(shape, ir.BitfieldRef):
            parts.append(str(shape.size // 8))
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
        if attr.viewable:
            # curated parse may attach a bitfield view; int() converts back
            return f"        outputStream.write_{shape.type}(int(self.{attr.name}))"
        return f"        outputStream.write_{shape.type}(self.{attr.name})"
    if isinstance(shape, ir.BitfieldRef):
        # raw integer on the wire; parsed views convert back via int()
        return f"        outputStream.write_uint{shape.size}(int(self.{attr.name}))"
    if isinstance(shape, ir.ObjectList):
        return (
            f"        for item in self.{attr.name}:\n"
            f"            item.serialize(outputStream)"
        )
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
            if attr.hidden:
                # wire-only count: a parse local, never instance state
                stmts.append(f"        {attr.name} = {expr}")
            else:
                _emit_value(rec, attr.name, expr, stmts, args)
        elif isinstance(shape, ir.EnumRef):
            io = ENUM_IO[shape.size]
            expr = f"rich_or_int({shape.uid}, inputStream.read_{io}())"
            _emit_value(rec, attr.name, expr, stmts, args)
        elif isinstance(shape, ir.ClassRef):
            target = records[shape.target]
            if target.frozen:
                expr = f"{shape.target}.parse(inputStream)"
                _emit_value(rec, attr.name, expr, stmts, args)
            elif rec.frozen:
                raise SpecError(
                    f"frozen record {rec.name!r} cannot hold mutable "
                    f"member {attr.name!r} (no constructive parse exists)"
                )
            else:
                # mutable member: repopulate the owned default instance
                stmts.append(f"        self.{attr.name}.parse(inputStream)")
        elif isinstance(shape, ir.FixedBytes):
            expr = f"inputStream.read_bytes({shape.length})"
            _emit_value(rec, attr.name, expr, stmts, args)
        elif isinstance(shape, ir.BitfieldRef):
            expr = f"inputStream.read_uint{shape.size}()"
            _emit_value(rec, attr.name, expr, stmts, args)
        elif isinstance(shape, ir.ObjectList):
            stmts.append(
                "        # Never append to a pre-existing list (instance-reuse "
                "corruption,"
            )
            stmts.append("        # PR #49): the list is replaced wholesale.")
            stmts.append(f"        self.{attr.name} = [")
            stmts.append(f"            {shape.element}.parseFrom(inputStream)")
            stmts.append(f"            for _ in range({shape.count_field})")
            stmts.append("        ]")
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
