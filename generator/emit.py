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

# The kernel PduHeader's marshalled size (bytes). Whole-datagram alignment
# pads are computed against header + body (opendis/record/pdu.py).
HEADER_BYTES = 12

# The uid-66 Standard Variable record header (§6.2.83): recordType u32 +
# recordLength u16, written by the generated class itself.
SV_HEADER_BYTES = 6

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


def _count_doc(attr: ir.Attribute) -> str:
    """Count-property docstring: the XML comment's body with trailing
    citations stripped (the §N.N header hoist is a class-docstring rule;
    count properties stand as plain prose)."""
    text = _normalize_cites((attr.comment or "").strip())
    text = re.sub(rf"[,;]?\s*§{_CITE}\.?$", "", text).rstrip()
    if not text:
        return attr.name
    if not text.endswith((".", "!", "?", ":")):
        text += "."
    return "\n".join(textwrap.wrap(text, width=72) or [text])


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
    magic-trailing-comma exploded form black preserves. Entries may
    carry ``orig as alias`` forms verbatim."""
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


def _prim_default(prim_type: str, xml_default: str | None = None) -> str:
    """Field default: the XML primitive's defaultValue when it carries one,
    else the zero of the type. Integer-valued float literals gain ".0" so
    zero-default fields keep the exemplar's ``= 0.0`` style."""
    if xml_default is None:
        return "0.0" if prim_type.startswith("float") else "0"
    if not re.fullmatch(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?", xml_default):
        raise SpecError(
            f"primitive defaultValue {xml_default!r} is not a plain number — "
            "cannot emit it as a field default"
        )
    if prim_type.startswith("float") and not re.search(r"[.eE]", xml_default):
        return xml_default + ".0"
    return xml_default


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


# -- presentIf optionals + record variant groups (bucket-C items 1+2) --------


def _is_record_group(shape) -> bool:
    """A classRef variant group: first-true-wins record selection, the
    union annotation naming every member."""
    return isinstance(shape, ir.VariantGroup) and shape.tag == "classRef"


def _is_optional(attr: ir.Attribute) -> bool:
    """presentIf on a scalar/record/group field makes it ``X | None``
    (absent = None). Lists keep their empty-list absence (minefield
    dataFilter precedent); pads/payloads ignore presentIf."""
    if not attr.present_if:
        return False
    shape = attr.shape
    return isinstance(
        shape, (ir.Primitive, ir.EnumRef, ir.ClassRef, ir.BitfieldRef)
    ) or _is_record_group(shape)


def _guard_dispatch_fields(rec: ir.RecordClass) -> None:
    """Fields whose wire presence/shape dispatches (presentIf optionals,
    record variant groups) parse via curated methods — refuse to emit a
    mechanical body that would silently mis-shape the wire."""
    if rec.name in overrides.METHOD_BODIES:
        return
    offender = next(
        (
            a.name
            for a in rec.attributes
            if _is_optional(a)
            or _is_record_group(a.shape)
            or isinstance(a.shape, ir.OptionalRecord)
        ),
        None,
    )
    if offender is not None:
        raise SpecError(
            f"{rec.name!r}.{offender} dispatches on presentIf/when= — its "
            "wire methods must be curated (METHOD_BODIES)"
        )


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
            for _, expr, _ in list(rec.identity_vars) + overrides.CLASS_VARS.get(
                name, []
            ):
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
            if attr.view:
                # local names ending in ``View`` are aliased imports
                canonical = attr.view[:-4] if attr.view.endswith("View") else attr.view
                self.add_import(
                    "opendis.bitfields",
                    (
                        f"{canonical} as {attr.view}"
                        if canonical != attr.view
                        else attr.view
                    ),
                )
        elif isinstance(shape, ir.ObjectList):
            self.uses_dataclass_field = True
            if (owner, attr.name) in overrides.REGISTRY_LISTS:
                return  # plain list; elements decode via the SV registry
            home = self.module_path(shape.element)
            if home and home != f"opendis.record.{self.module}":
                self.add_import(home, shape.element)
        elif isinstance(shape, ir.PrimitiveList):
            self.uses_dataclass_field = True
            if shape.element_uid is not None:
                self.uses_rich_or_int = True
                self.type_names.add(ir.ENUM_ANN[ir.PRIM_BITS[shape.element]])
            else:
                self.type_names.add(shape.element)
        elif isinstance(shape, ir.CuratedField):
            # curated annotations still need their type imports
            for tok in re.findall(r"\b(enum\d+|u?int\d+|float\d+)\b", shape.annotation):
                self.type_names.add(tok)
        elif isinstance(shape, (ir.BytesPayload, ir.OptionalRecord, ir.PadToBoundary)):
            pass  # payload is bytes; optional records parse curated; pads packer-computed
        elif isinstance(shape, ir.VariantGroup):
            if _is_record_group(shape):
                # union of record members; optional members need no
                # default instance, unconditional unions factory the
                # first member (the no-when/elided shape)
                for member in shape.members:
                    home = self.module_path(member.target)
                    if home and home != f"opendis.record.{self.module}":
                        self.add_import(home, member.target)
                if not _is_optional(attr):
                    self.uses_dataclass_field = True
                return
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
            or (isinstance(a.shape, ir.VariantGroup) and not _is_record_group(a.shape))
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
    records: dict[str, ir.RecordClass],
    order: list[str],
    module: str,
    list_elements: set[str] = frozenset(),
    context_views: dict | None = None,
) -> str:
    info = _ModuleInfo(records, order, module)
    lines: list[str] = []

    # classes whose parse wraps kind-qualified viewable fields, in module
    # order — the first one anchors the module-level dispatch dicts
    context_users: list[tuple[str, str, list[tuple[str, str]]]] = []
    context_suffixes: list[str] = []
    if context_views:
        for name in order:
            bound = _context_bindings(records[name])
            if bound is None:
                continue
            context_users.append((name, *bound))
            for suffix, _field in bound[1]:
                if suffix in context_views and suffix not in context_suffixes:
                    context_suffixes.append(suffix)
        for suffix in context_suffixes:
            for where in ("platform", "kind"):
                for cls, _uid in context_views[suffix][where].values():
                    info.add_import("opendis.bitfields", cls)

    doc = overrides.MODULE_DOCSTRINGS.get(module)
    if doc:
        lines += _doc_block(doc, pad="", close_alone=True)
        lines.append("")

    for extra in overrides.MODULE_IMPORT_LINES.get(module, []):
        lines.append(extra)

    dc_names = ["dataclass"] + (["field"] if info.uses_dataclass_field else [])
    lines.append(f"from dataclasses import {', '.join(dc_names)}")
    if info.needs_logger:
        lines.append("import logging")
    if info.uses_classvar:
        lines.append("from typing import ClassVar")
    lines.append("")

    imports: dict[str, list[str]] = {}
    kernel_exports = {base: mod for base, mod in overrides.KERNEL_BASES.values()}
    # generated record homes parented on kernel protocol bases import them
    # like PDUs import Pdu (§6.2.58/§6.2.8/§6.2.95 of the Annex C wave)
    kernel_exports.update(overrides.KERNEL_RECORD_BASES.values())
    for name in order:
        rec = records[name]
        if rec.parent and rec.parent not in info.own:
            if rec.parent in kernel_exports:
                info.add_import(kernel_exports[rec.parent], rec.parent)
                continue
            home = info.module_path(rec.parent)
            if home:
                info.add_import(home, rec.parent)
            # hand bases (RECORD_BASES targets) ride MODULE_SOURCE_IMPORTS
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
    # curated source blocks may define public classes (the Annex C unknown
    # placeholders) — they export like generated ones
    for _anchor, block in overrides.MODULE_SOURCES.get(module, []):
        for match in re.finditer(
            r"^class ([A-Za-z_][A-Za-z0-9_]*)", block, re.MULTILINE
        ):
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
    # the padding ruling comment rides the first pad field of the module
    pad_owner = next(
        (name for name in order if any(a.pad for a in records[name].attributes)),
        None,
    )
    # trailing whole-datagram alignment pads need the shared helpers, one
    # per boundary the module's trailing pads use (32-bit PDU pads, the
    # 64-bit SV-record alignment of §6.2.83)
    for bits in sorted(
        {
            attrs[-1].shape.length
            for attrs in (records[name].attributes for name in order)
            if attrs and isinstance(attrs[-1].shape, ir.PadToBoundary)
        }
    ):
        octets = bits // 8
        lines.append("")
        lines.append("")
        lines.append(f"def _padTo{bits}(byteCount: int) -> int:")
        lines.append(
            f'    """Pad bytes needed to bring a datagram to a {bits}-bit boundary."""'
        )
        lines.append(f"    return ({octets} - byteCount % {octets}) % {octets}")
    for name in order:
        if context_users and name == context_users[0][0]:
            # dispatch dicts lead the first class whose parse walks them
            lines.append("")
            lines.append("")
            lines += _context_dicts_block(context_views, context_suffixes)
        lines.append("")
        lines.append("")
        _emit_record(
            records[name],
            records,
            lines,
            list_elements,
            name == pad_owner,
            context_bindings=next(
                ((t, b) for n, t, b in context_users if n == name), None
            ),
        )
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


_PAD_RULING = (
    "# Padding ruling: explicit attribute, out of __init__ (zero by default,\n"
    "# holds the wire value after parse so odd pads round-trip byte-exact)."
)


# -- context-dependent bitfield dispatch (bucket-C items 5+6) ---------------
#
# EntityAppearance/EntityCapabilities wire fields are raw uint32 state in
# Python; the REF-010 layouts select per entity kind (per domain for
# platforms), so parse wraps the integer into the matching view class.
# The (kind, domain) -> table mapping derives from REF-010 names matched
# against the uid-7/uid-8 row labels (ref010); this emitter lays out the
# module-level dispatch dicts and the parse tail.

# Verbatim exemplar layout — hand-wrapped for the two known view families
# (the wrap puts the "/" joining the binding names at col 79; anything
# else fails loud rather than re-flowing)
_CONTEXT_COMMENT = (
    "# generator: context-dependent bitfield layouts — the Entity{s1} /\n"
    "# Entity{s2} tables depend on entity kind (and, for platforms, on\n"
    "# domain). Parse wraps the raw uint32 into the matching view; kinds "
    "with\n"
    "# no REF-010 table keep the plain int. The marshaller writes "
    "int(field)\n"
    "# either way."
)


def _context_bindings(rec: ir.RecordClass):
    """(entityType field name, [(layout suffix, field name), ...]) when
    the record holds kind-qualified viewable fields AND an EntityType
    reference to key them on; else None."""
    type_attr = next(
        (
            a
            for a in rec.attributes
            if isinstance(a.shape, ir.ClassRef) and a.shape.target == "EntityType"
        ),
        None,
    )
    if type_attr is None or type_attr.present_if:
        # no key on the wire, or the key itself is flag-optional (the LE
        # Appearance PDU resolves its variants from the receiver's cached
        # entity type — §9.4.3; dispatching on an absent key is unsound)
        return None
    bound = [
        (a.view_binding.removeprefix("Entity"), a.name)
        for a in rec.attributes
        if a.view_binding and a.view_binding.startswith("Entity")
    ]
    if not bound:
        return None
    return type_attr.name, bound


def _context_dict_names(suffix: str) -> tuple[str, str]:
    upper = suffix.upper()
    if upper.endswith("IES"):
        upper = upper[:-3] + "Y"  # CAPABILITIES -> CAPABILITY (exemplar names)
    return f"_{upper}_VIEWS", f"_{upper}_KIND_VIEWS"


def _context_dicts_block(context_views: dict, suffixes: list[str]) -> list[str]:
    """The module-level dispatch dicts (verbatim exemplar layout)."""
    if len(suffixes) != 2:
        raise SpecError(
            f"context dispatch comment assumes two view families, got {suffixes!r}"
        )
    lines = _CONTEXT_COMMENT.format(s1=suffixes[0], s2=suffixes[1]).split("\n")
    for index, suffix in enumerate(suffixes):
        # exemplar comment style: the leading family's rows carry the
        # "platform, <domain> domain" gloss; later families stay bare
        verbose = index == 0
        kind_labels = context_views["kind_labels"]
        domain_labels = context_views["domain_labels"]
        views, kind_views = _context_dict_names(suffix)
        lines.append(f"{views}: dict[tuple[int, int], type] = {{")
        for domain in sorted(context_views[suffix]["platform"]):
            cls, uid = context_views[suffix]["platform"][domain]
            if verbose:
                label = domain_labels[domain].lower()
                comment = f"  # platform, {label} domain [UID {uid}]"
            else:
                comment = f"  # [UID {uid}]"
            lines.append(f"    (1, {domain}): {cls},{comment}")
        lines.append("}")
        lines.append(f"{kind_views}: dict[int, type] = {{")
        for kind in sorted(context_views[suffix]["kind"]):
            cls, uid = context_views[suffix]["kind"][kind]
            lines.append(f"    {kind}: {cls},  # [UID {uid}]")
        lines.append("}")
    return lines


def _context_tail(type_field: str, bound: list[tuple[str, str]]) -> list[str]:
    """Parse-method tail: wrap each bound field into its kind's view."""
    lines = [
        f"key = (int(self.{type_field}.entityKind), int(self.{type_field}.domain))"
    ]
    for suffix, field in bound:
        var = suffix[0].lower() + suffix[1:]
        if var.endswith("ies"):
            var = var[:-3] + "y"
        views, kind_views = _context_dict_names(suffix)
        lines.append(f"{var}View = {views}.get(key) or {kind_views}.get(")
        lines.append(f"    int(self.{type_field}.entityKind)")
        lines.append(")")
        lines.append(f"if {var}View is not None:")
        lines.append(f"    self.{field} = {var}View(self.{field})")
    return lines


def _emit_record(
    rec: ir.RecordClass,
    records: dict[str, ir.RecordClass],
    lines: list[str],
    list_elements: set[str] = frozenset(),
    first_pad: bool = False,
    context_bindings: tuple[str, list[tuple[str, str]]] | None = None,
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
        cite = overrides.DOCSTRING_CITES.get(rec.name)
        comment = rec.comment
        if cite is not None:
            comment = _replace_leading_cite(comment, cite)
        doc = canonical_docstring(
            comment, overrides.DOCSTRING_TITLES.get(rec.name), rec.name
        )
        addendum = overrides.DOCSTRING_ADDENDA.get(rec.name)
        if addendum:
            doc += "\n\n" + _wrap_prose(addendum)
    lines += _doc_block(doc, pad="    ")
    lines.append("")

    # XML-declared identity constants (pduType/protocolFamily/recordType)
    # lead; curated residuals (Table 25 symbols) follow
    class_vars = list(rec.identity_vars) + (overrides.CLASS_VARS.get(rec.name) or [])
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

    super_base = _super_base(rec, records)
    # fields inherited from a generated PDU base come through the class
    # hierarchy (its body methods run via the two-arg super calls)
    inherited = (
        {a.name for a in records[super_base].attributes} if super_base else set()
    )
    wire = [a for a in rec.attributes if a.name not in inherited]

    pads = [a for a in wire if a.pad]
    for attr in wire:
        if attr.hidden or attr.pad or isinstance(attr.shape, ir.PadToBoundary):
            continue  # hidden counts: property below; pads: grouped last;
            # alignment pads: packer-computed, never fields
        lines.append(_field_line(rec.name, attr))
        field_doc = overrides.FIELD_DOCSTRINGS.get((rec.name, attr.name))
        if field_doc:
            lines += _doc_block(field_doc, pad="    ", close_alone=False)

    if pads:
        if first_pad:
            for ln in _PAD_RULING.split("\n"):
                lines.append(f"    {ln}")
        for attr in pads:
            lines.append(_field_line(rec.name, attr))

    for attr in wire:
        if attr.hidden:
            lines.append("")
            lines.append("    @property")
            lines.append(f"    def {attr.name}(self) -> {attr.shape.type}:")
            lines += _doc_block(_count_doc(attr), pad="        ")
            if attr.count_bits:
                lines.append(f"        return len(self.{attr.count_for}) * 8")
            else:
                lines.append(f"        return len(self.{attr.count_for})")

    if not rec.is_pdu:
        _emit_class_vars(class_vars, lines, leading_blank=True)

    member = overrides.CLASS_MEMBERS.get(rec.name)
    if member and not member.after_methods:
        lines.append("")
        lines += [f"    {ln}" if ln.strip() else "" for ln in member.source.split("\n")]

    if not rec.attributes and rec.name not in overrides.METHOD_BODIES:
        # family markers carry no wire body — methods inherit; fieldless
        # records with curated bodies (the zero-length Annex C MP
        # markers) emit them below
        return

    _guard_dispatch_fields(rec)
    body = overrides.METHOD_BODIES.get(rec.name)
    size_name, ser_name, parse_name = (
        ("_marshalledBodySize", "_serializeBody", "_parseBody")
        if rec.is_pdu
        else ("marshalledSize", "serialize", "parse")
    )
    trailing_pad = wire and isinstance(wire[-1].shape, ir.PadToBoundary)
    # the boundary and the header the pad is computed against: PDU pads
    # run over the 12-byte datagram header at a 32-bit boundary; SV
    # records pad over their own 6-byte header to the 64-bit boundary
    # §6.2.83 requires (Table 44's 8P padding octets); plain records pad
    # over the record itself (Grid Data / Grid Axis alignment pads,
    # §6.2.40/.41)
    pad_bits = wire[-1].shape.length if trailing_pad else 32
    pad_fn = f"_padTo{pad_bits}"
    wire_header = SV_HEADER_BYTES if rec.is_sv else (HEADER_BYTES if rec.is_pdu else 0)
    mid_body_pads = [
        a
        for a in (wire[:-1] if trailing_pad else wire)
        if isinstance(a.shape, ir.PadToBoundary)
    ]
    if mid_body_pads and not (body and size_name in body):
        raise SpecError(
            f"{rec.name!r} carries mid-body alignment pads — its wire "
            "methods must be curated (METHOD_BODIES)"
        )
    if body and size_name in body:
        _emit_method(lines, size_name, ["self"], body[size_name])
    elif trailing_pad:
        # trailing alignment pad: size + pad(header + unpadded fields),
        # the pad bytes riding serialize/parse via the unpadded helper
        lines.append("")
        lines.append(f"    def _unpaddedBodySize(self) -> int:")
        for ln in _size_stmts(rec, super_base, wire[:-1]):
            lines.append(ln)
        lines.append("")
        lines.append(f"    def {size_name}(self) -> int:")
        unpadded = "self._unpaddedBodySize()"
        # SV records carry their own 6-byte header in marshalledSize; PDU
        # bodies do not (Pdu.marshalledSize adds the 12-byte header), and
        # plain records are header-less
        prefix = f"{wire_header} + " if rec.is_sv else ""
        pad_base = f"{wire_header} + {unpadded}" if wire_header else unpadded
        lines.append(f"        return {prefix}{unpadded} + " f"{pad_fn}({pad_base})")
    else:
        lines.append("")
        lines.append(f"    def {size_name}(self) -> int:")
        for ln in _size_stmts(rec, super_base, wire, sv_header=rec.is_sv):
            lines.append(ln)
    if body and ser_name in body:
        _emit_method(
            lines, ser_name, ["self", "outputStream: DataOutputStream"], body[ser_name]
        )
    else:
        lines.append("")
        lines.append(
            f"    def {ser_name}(self, outputStream: DataOutputStream) -> None:"
        )
        if rec.is_sv:
            # §6.2.83 SV header: the class writes recordType (the curated
            # registry ClassVar) + recordLength (the derived total length)
            lines.append("        outputStream.write_uint32(self.recordType)")
            lines.append("        outputStream.write_uint16(self.recordLength)")
        elif super_base:
            lines.append(f"        super({rec.name}, self).{ser_name}(outputStream)")
        for attr in wire:
            if isinstance(attr.shape, ir.PadToBoundary):
                continue  # trailing alignment pad: emitted as a block below
            lines += _serialize_line(rec.name, attr)
        if trailing_pad:
            lines.append(
                f"        padding = {pad_fn}({wire_header} + self._unpaddedBodySize())"
            )
            lines.append("        if padding:")
            lines.append('            outputStream.write_bytes(b"\\x00" * padding)')
        lines.append("")
    parse_header = "inputStream: DataInputStream"
    uses_registry = any(
        isinstance(a.shape, ir.ObjectList)
        and (rec.name, a.name) in overrides.REGISTRY_LISTS
        for a in wire
    )
    if body and parse_name in body:
        # curated parse bodies referencing the registry helper get the
        # same function-local import the mechanical path injects (a
        # module-level import would cycle through opendis.record)
        if uses_registry and "parseStandardVariableRecord" in body[parse_name]:
            body = dict(body)
            body[parse_name] = (
                "from opendis.record import parseStandardVariableRecord\n"
                + body[parse_name]
            )
        params = overrides.METHOD_PARAMS.get((rec.name, parse_name))
        if params is not None:
            _emit_method(
                lines,
                parse_name,
                params,
                body[parse_name],
                decorators=["classmethod"] if params and params[0] == "cls" else None,
                ret=f'"{rec.name}"',
            )
        elif rec.frozen:
            _emit_method(
                lines,
                parse_name,
                ["cls", f"inputStream: DataInputStream"],
                body[parse_name],
                decorators=["classmethod"],
                ret=f'"{rec.name}"',
            )
        else:
            _emit_method(lines, parse_name, ["self", parse_header], body[parse_name])
    else:
        if rec.frozen:
            lines.append("    @classmethod")
            lines.append(
                f'    def parse(cls, inputStream: DataInputStream) -> "{rec.name}":'
            )
        else:
            params = "self, inputStream: DataInputStream"
            if rec.is_sv:
                # the wire recordLength rides the signature (§6.2.83);
                # validation lives in the registry helper
                params += ", bytelength: int"
            lines.append(f"    def {parse_name}({params}) -> None:")
        stmts, args = _parse_pieces(rec, super_base, wire, records)
        if uses_registry:
            stmts.insert(
                1 if super_base else 0,
                "        from opendis.record import parseStandardVariableRecord",
            )
            stmts.insert(2 if super_base else 1, "")
        if trailing_pad:
            stmts.append(
                f"        padding = {pad_fn}({wire_header} + self._unpaddedBodySize())"
            )
            stmts.append("        if padding:")
            stmts.append("            inputStream.read_bytes(padding)")
        lines += stmts
        if rec.frozen:
            lines.append(f"        return cls({', '.join(args)})")

    if context_bindings is not None:
        # kind-qualified view wrap (context dispatch): the parse tail
        # walks the module dicts keyed on this record's entityType
        lines.append("")
        for ln in _context_tail(*context_bindings):
            lines.append(f"        {ln}")

    if member and member.after_methods:
        lines.append("")
        lines += [f"    {ln}" if ln.strip() else "" for ln in member.source.split("\n")]

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


def _super_base(rec: ir.RecordClass, records: dict[str, ir.RecordClass]) -> str | None:
    """Parent whose generated body methods this class extends (two-arg
    super, ruled for slots dataclasses)."""
    if not rec.is_pdu or rec.parent is None:
        return None
    parent = records.get(rec.parent)
    if parent is None or not parent.is_pdu or not parent.attributes:
        return None
    return parent.name


def _replace_leading_cite(comment: str | None, cite: str) -> str | None:
    """Swap a stale XML leading citation (1995-edition PDU numbering)
    for the standard's 2012 number; the body text stays XML-canonical."""
    if not comment:
        return comment
    return re.sub(rf"^({_CITE})\.?[ \t]+", f"{cite} ", comment.strip(), count=1)


def _emit_method(
    lines: list[str],
    name: str,
    params: list[str],
    source: str,
    decorators: list[str] | None = None,
    ret: str | None = None,
) -> None:
    sig = f"def {name}({', '.join(params)})"
    if ret:
        sig += f" -> {ret}"
    for dec in decorators or []:
        lines.append(f"    @{dec}")
    lines.append(f"    {sig}:")
    lines += [f"        {ln}" if ln.strip() else "" for ln in source.split("\n")]


def _size_stmts(
    rec: ir.RecordClass,
    super_base: str | None,
    wire: list[ir.Attribute],
    sv_header: bool = False,
) -> list[str]:
    expr = _marshalled_expr(rec, super_base, wire, sv_header=sv_header)
    single = f"        return {expr}"
    if len(single) <= 88:
        return [single]
    # black's style: one term per line inside parentheses
    parts = expr.split(" + ")
    lines = ["        return (", f"            {parts[0]}"]
    for part in parts[1:]:
        lines.append(f"            + {part}")
    lines.append("        )")
    return lines


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
        if _is_optional(attr):
            continue  # optional enums decode via their curated bodies
        if isinstance(attr.shape, ir.EnumRef) and attr.shape.uid is not None:
            entries.append((attr.name, str(attr.shape.uid)))
        elif isinstance(attr.shape, ir.VariantGroup) and not _is_record_group(
            attr.shape
        ):
            _, default = _variant_members(attr.shape, attr.name)
            entries.append((attr.name, _const_name(default.enum_type)))
    return entries


def _field_line(owner: str, attr: ir.Attribute) -> str:
    shape = attr.shape
    if _is_record_group(shape):
        ann = " | ".join(m.target for m in shape.members)
        default = f"field(default_factory={shape.members[0].target})"
    elif isinstance(shape, ir.Primitive):
        if attr.pad:
            ann, default = shape.type, "field(init=False, default=0)"
        else:
            ann, default = shape.type, _prim_default(shape.type, shape.default)
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
        if (owner, attr.name) in overrides.REGISTRY_LISTS:
            ann, default = "list", "field(default_factory=list)"
        else:
            ann, default = f"list[{shape.element}]", "field(default_factory=list)"
    elif isinstance(shape, ir.PrimitiveList):
        if shape.element_uid is not None:
            ann = f"list[{ir.ENUM_ANN[ir.PRIM_BITS[shape.element]]}]"
        else:
            ann = f"list[{shape.element}]"
        default = "field(default_factory=list)"
    elif isinstance(shape, ir.BytesPayload):
        ann, default = "bytes", 'b""'
    elif isinstance(shape, ir.OptionalRecord):
        ann, default = f"{shape.target} | None", "None"
    elif isinstance(shape, ir.CuratedField):
        return f"    {attr.name}: {shape.annotation} = {shape.default}" + (
            f"  # {shape.rider}" if shape.rider else ""
        )
    elif isinstance(shape, ir.VariantGroup):
        _, default_member = _variant_members(shape, attr.name)
        ann, default = ir.ENUM_ANN[default_member.size], "0"
    elif isinstance(shape, ir.PadToBoundary):
        raise SpecError(
            f"alignment pad {attr.name!r} on {owner!r} is packer-computed — "
            "the class needs curated wire methods"
        )
    else:
        raise SpecError(f"unsupported field {attr.name!r}")
    if _is_optional(attr):
        ann += " | None"
        default = "None"
    line = f"    {attr.name}: {ann} = {default}"
    rider = (
        overrides.FIELD_RIDERS.get((owner, attr.name))
        or _view_rider(owner, attr)
        or _uid_rider(attr)
    )
    if rider:
        line += f"  # {rider}"
    return line


def _view_rider(owner: str, attr: ir.Attribute) -> str | None:
    """BitfieldRef rider when a view attaches at parse."""
    shape = attr.shape
    if attr.view is None:
        return None
    if not isinstance(shape, ir.BitfieldRef):
        raise SpecError(f"view attach on non-bitfield field {owner}.{attr.name}")
    if attr.view.endswith("View"):
        return f"[UID {shape.uid}] or the {attr.view[:-4]} view"
    return f"[UID {shape.uid}] or the view"


def _uid_rider(attr: ir.Attribute) -> str | None:
    shape = attr.shape
    if isinstance(shape, ir.EnumRef) and shape.uid is not None:
        return f"[UID {shape.uid}]"
    if isinstance(shape, ir.BitfieldRef):
        return f"[UID {shape.uid}]"
    if isinstance(shape, ir.VariantGroup) and not _is_record_group(shape):
        _, default = _variant_members(shape, attr.name)
        uids = [default.uid] + [
            m.uid for m in shape.members if isinstance(m, ir.EnumRef) and m.when
        ]
        return " / ".join(f"[UID {u}]" for u in uids if u is not None)
    return None


def _marshalled_expr(
    rec: ir.RecordClass,
    super_base: str | None = None,
    wire: list | None = None,
    sv_header: bool = False,
) -> str:
    parts: list[str] = []
    has_ref = False
    if super_base:
        parts.append(f"super({rec.name}, self)._marshalledBodySize()")
        has_ref = True
    elif sv_header:
        # §6.2.83 SV header: recordType u32 + recordLength u16
        parts.append(str(SV_HEADER_BYTES))
    for attr in (wire if wire is not None else rec.attributes):
        shape = attr.shape
        if (
            _is_optional(attr)
            or _is_record_group(shape)
            or isinstance(shape, ir.OptionalRecord)
        ):
            raise SpecError(
                f"{attr.name!r} on {rec.name!r} dispatches on presentIf/when= — "
                "its wire size is curated (METHOD_BODIES)"
            )
        if attr.hidden:
            # wire-only count byte: contributes to size, never to state
            parts.append(str(ir.PRIM_BITS[shape.type] // 8))
        elif isinstance(shape, ir.ClassRef):
            has_ref = True
            parts.append(f"self.{attr.name}.marshalledSize()")
        elif isinstance(shape, (ir.ObjectList, ir.PrimitiveList)):
            has_ref = True
            if isinstance(shape, ir.ObjectList):
                parts.append(f"sum(item.marshalledSize() for item in self.{attr.name})")
            else:
                width = ir.PRIM_BITS[shape.element] // 8
                size_expr = (
                    f"len(self.{attr.name})"
                    if width == 1
                    else f"{width} * len(self.{attr.name})"
                )
                parts.append(size_expr)
        elif isinstance(shape, ir.BytesPayload):
            has_ref = True
            parts.append(f"len(self.{attr.name})")
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
        elif isinstance(shape, ir.PadToBoundary):
            raise SpecError(
                f"alignment pad {attr.name!r} on {rec.name!r}: size is "
                "packer-computed — curated methods required"
            )
    if not has_ref:
        return str(sum(int(p) for p in parts))
    return " + ".join(parts)


def _serialize_line(owner: str, attr: ir.Attribute) -> list[str]:
    shape = attr.shape
    if (
        _is_optional(attr)
        or _is_record_group(shape)
        or isinstance(shape, ir.OptionalRecord)
    ):
        raise SpecError(
            f"{attr.name!r} on {owner!r} dispatches on presentIf/when= — "
            "its serialize is curated (METHOD_BODIES)"
        )
    if isinstance(shape, ir.ClassRef):
        return [f"        self.{attr.name}.serialize(outputStream)"]
    if isinstance(shape, ir.Primitive):
        if attr.viewable:
            # curated parse may attach a bitfield view; int() converts back
            return [f"        outputStream.write_{shape.type}(int(self.{attr.name}))"]
        return [f"        outputStream.write_{shape.type}(self.{attr.name})"]
    if isinstance(shape, ir.BitfieldRef):
        # raw integer on the wire; parsed views convert back via int()
        return [f"        outputStream.write_uint{shape.size}(int(self.{attr.name}))"]
    if isinstance(shape, (ir.ObjectList, ir.PrimitiveList)):
        if isinstance(shape, ir.ObjectList):
            if (owner, attr.name) in overrides.REGISTRY_LISTS:
                return [
                    f"        for item in self.{attr.name}:",
                    f"            item.serialize(outputStream)",
                ]
            return [
                f"        for item in self.{attr.name}:",
                f"            item.serialize(outputStream)",
            ]
        io = shape.element
        if shape.element_uid is not None:
            return [
                f"        for item in self.{attr.name}:",
                f"            outputStream.write_{io}(item)",
            ]
        return [
            f"        for item in self.{attr.name}:",
            f"            outputStream.write_{io}(item)",
        ]
    if isinstance(shape, (ir.EnumRef, ir.VariantGroup)):
        if isinstance(shape, ir.VariantGroup):
            _, default = _variant_members(shape, attr.name)
            size = default.size
        else:
            size = shape.size
        io = ENUM_IO[size]
        return [f"        outputStream.write_{io}(self.{attr.name})"]
    if isinstance(shape, ir.FixedBytes):
        n = shape.length
        return [
            f"        outputStream.write_bytes("
            f'self.{attr.name}[:{n}].ljust({n}, b"\\x00"))'
        ]
    if isinstance(shape, ir.BytesPayload):
        if shape.bit_count_field is None:
            raise SpecError(
                f"bytes payload {attr.name!r} on {owner!r}: serialize is "
                "curated (expression-sized payload)"
            )
        return [f"        outputStream.write_bytes(self.{attr.name})"]
    if isinstance(shape, ir.PadToBoundary):
        raise SpecError(
            f"alignment pad {attr.name!r} on {owner!r}: serialize is "
            "packer-computed — curated methods required"
        )
    raise SpecError(f"cannot serialize field {attr.name!r}")


def _parse_pieces(
    rec: ir.RecordClass,
    super_base: str | None = None,
    wire: list | None = None,
    records: dict[str, ir.RecordClass] | None = None,
) -> tuple[list[str], list[str]]:
    """Returns (statement lines, positional cls() args) — args only for
    frozen records; mutable records use self-assignments instead."""
    stmts: list[str] = []
    args: list[str] = []
    if super_base:
        stmts.append(f"        super({rec.name}, self)._parseBody(inputStream)")
    for attr in (wire if wire is not None else rec.attributes):
        shape = attr.shape
        if (
            _is_optional(attr)
            or _is_record_group(shape)
            or isinstance(shape, ir.OptionalRecord)
        ):
            raise SpecError(
                f"{attr.name!r} on {rec.name!r} dispatches on presentIf/when= — "
                "its parse is curated (METHOD_BODIES)"
            )
        if isinstance(attr.shape, ir.PadToBoundary):
            continue  # trailing alignment pad: parse block handles it
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
            target = records[shape.target] if records is not None else None
            if target is not None and target.frozen:
                expr = f"{shape.target}.parse(inputStream)"
                _emit_value(rec, attr.name, expr, stmts, args)
            elif rec.frozen:
                if target is None:
                    raise SpecError(
                        f"frozen record {rec.name!r} holds hand seam member "
                        f"{attr.name!r} (no constructive parse exists)"
                    )
                # mutable member in a frozen record: construct a fresh
                # instance and repopulate that — the cls() call receives
                # the new object, never a shared default
                stmts.append(f"        {attr.name} = {shape.target}()")
                stmts.append(f"        {attr.name}.parse(inputStream)")
                args.append(attr.name)
            else:
                # mutable member: repopulate the owned default instance
                stmts.append(f"        self.{attr.name}.parse(inputStream)")
        elif isinstance(shape, ir.FixedBytes):
            expr = f"inputStream.read_bytes({shape.length})"
            _emit_value(rec, attr.name, expr, stmts, args)
        elif isinstance(shape, ir.BitfieldRef):
            expr = f"inputStream.read_uint{shape.size}()"
            if attr.view:
                expr = f"{attr.view}({expr})"
            _emit_value(rec, attr.name, expr, stmts, args)
        elif isinstance(shape, ir.ObjectList):
            if (rec.name, attr.name) in overrides.REGISTRY_LISTS:
                # uid-66 Standard Variable records: registry decode; the
                # deferred import leads _parseBody (record/__init__ imports
                # the family modules, so a module-level import would cycle)
                stmts.append(
                    "        # Never append to a pre-existing list (instance-reuse "
                    "corruption,"
                )
                stmts.append("        # PR #49): the list is replaced wholesale.")
                stmts.append(f"        self.{attr.name} = [")
                stmts.append("            parseStandardVariableRecord(inputStream)")
                stmts.append(f"            for _ in range({shape.count_field})")
                stmts.append("        ]")
                continue
            element_target = records.get(shape.element) if records is not None else None
            # frozen elements have no mutating parse: construct per item
            construct = element_target is not None and element_target.frozen
            stmts.extend(
                _list_parse(
                    attr.name,
                    shape.element,
                    shape.count_field,
                    construct=construct,
                )
            )
        elif isinstance(shape, ir.PrimitiveList):
            io = shape.element
            if shape.element_uid is not None:
                expr = f"rich_or_int({shape.element_uid}, inputStream.read_{io}())"
            else:
                expr = f"inputStream.read_{io}()"
            stmts.append(
                "        # Never append to a pre-existing list (instance-reuse "
                "corruption,"
            )
            stmts.append("        # PR #49): the list is replaced wholesale.")
            stmts.append(f"        self.{attr.name} = [")
            stmts.append(f"            {expr}")
            stmts.append(f"            for _ in range({shape.count_field})")
            stmts.append("        ]")
        elif isinstance(shape, ir.BytesPayload):
            if shape.bit_count_field is None:
                raise SpecError(
                    f"bytes payload {attr.name!r} on {rec.name!r}: parse is "
                    "curated (expression-sized payload)"
                )
            divisor = " // 8" if shape.count_is_bits else ""
            expr = f"inputStream.read_bytes({shape.bit_count_field}{divisor})"
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


def _list_parse(
    field: str, element: str, count: str, construct: bool = False
) -> list[str]:
    reader = (
        f"{element}.parse(inputStream)"
        if construct
        else (f"{element}.parseFrom(inputStream)")
    )
    return [
        "        # Never append to a pre-existing list (instance-reuse corruption,",
        "        # PR #49): the list is replaced wholesale.",
        f"        self.{field} = [",
        f"            {reader}",
        f"            for _ in range({count})",
        "        ]",
    ]


def _emit_value(
    rec: ir.RecordClass, name: str, expr: str, stmts: list[str], args: list[str]
) -> None:
    if rec.frozen:
        # every field reads before the cls() call — inline expressions
        # would evaluate at call time, reordering the wire reads
        stmts.append(f"        {name} = {expr}")
        args.append(name)
    else:
        stmts.append(f"        self.{name} = {expr}")
