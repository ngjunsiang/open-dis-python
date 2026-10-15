"""Resolve the XML element tree into flattened RecordClass IR.

Semantics ported from submodules/open-dis-spec-xml/xml/scripts/validate.py (SizeEval lineage):
inheritance flattens base-first with name deduplication; attributes with
competing type children of one tag become VariantGroups; Python-side
curated bindings (overrides.py) rebind XML names to canonical classes.
"""

from __future__ import annotations

import dataclasses

from . import ir, overrides
from .xmlload import TYPE_TAGS, SpecError, collect_classes


class Resolver:
    def __init__(self, root, overrides_module=overrides):
        self.xml_classes, self.aliases = collect_classes(root)
        self.ov = overrides_module
        # canonical Python name -> XML class element (bindings/aliases may
        # rename classes, e.g. EntityInformationInteractionFamilyPdu ->
        # EntityInformationFamilyPdu). A class whose XML name already IS
        # canonical always wins over rebound names (EntityID must not
        # shadow EntityIdentifier).
        self.by_canonical: dict[str, str] = {}
        for xml_name in self.xml_classes:
            canonical = self.canonical_name(xml_name)
            if canonical == xml_name or canonical not in self.by_canonical:
                self.by_canonical.setdefault(canonical, xml_name)

    def canonical_name(self, xml_name: str) -> str:
        """XML class name -> canonical Python class name (bindings, then
        aliasFor chains)."""
        seen = set()
        name = xml_name
        while name not in seen:
            seen.add(name)
            name = self.ov.RECORD_BINDINGS.get(name, name)
            name = self.aliases.get(name, name)
        return name

    def resolve(self, names: list[str]) -> dict[str, ir.RecordClass]:
        """Resolve the requested classes plus transitive classRef deps."""
        out: dict[str, ir.RecordClass] = {}
        pending = [self.canonical_name(n) for n in names]
        while pending:
            name = pending.pop(0)
            if name in out:
                continue
            rec = self._build(name)
            out[name] = rec
            for attr in rec.attributes:
                target = self._classref_target(attr.shape)
                if target and target not in out:
                    pending.append(target)
            if rec.parent and rec.parent in self.by_canonical and rec.parent not in out:
                pending.append(rec.parent)
        return out

    def _classref_target(self, shape) -> str | None:
        if isinstance(shape, ir.ClassRef):
            return shape.target
        if isinstance(shape, ir.ObjectList):
            return shape.element
        if isinstance(shape, ir.VariantGroup):
            for member in shape.members:
                target = self._classref_target(member)
                if target:
                    return target
        return None

    # -- XML -> IR -------------------------------------------------------

    def _build(self, name: str) -> ir.RecordClass:
        el = self.xml_classes.get(self.by_canonical.get(name, name))
        if el is None:
            raise SpecError(f"unknown class {name!r} (not in spec, not bound)")
        flat = self._flatten(el)
        attributes = [self._attribute(a) for a in flat]
        parent, is_pdu = self._lineage(el)
        attributes = self._validate_counts(name, attributes)
        return ir.RecordClass(
            name=name,
            comment=el.get("comment"),
            attributes=attributes,
            frozen=name in self.ov.FROZEN_RECORDS,
            parent=parent,
            is_pdu=is_pdu,
            xml=el,
        )

    def _lineage(self, el) -> tuple[str | None, bool]:
        """Canonical Python base name + whether the lineage reaches a
        kernel PDU base (the class emits body methods)."""
        parent = el.get("inheritsFrom")
        if parent in (None, "root"):
            return None, False
        canonical = self.canonical_name(parent)
        if canonical in self.ov.KERNEL_BASES:
            base, _module = self.ov.KERNEL_BASES[canonical]
            return base, True
        parent_el = self.xml_classes.get(self.by_canonical.get(canonical, canonical))
        if parent_el is None:
            raise SpecError(f"{el.get('name')!r} inherits unknown class {parent!r}")
        return canonical, self._is_pdu_lineage(parent_el)

    def _is_pdu_lineage(self, el) -> bool:
        cur = el
        while cur is not None:
            parent = cur.get("inheritsFrom")
            if parent in (None, "root"):
                return False
            canonical = self.canonical_name(parent)
            if canonical in self.ov.KERNEL_BASES:
                return True
            cur = self.xml_classes.get(self.by_canonical.get(canonical, canonical))
        return False

    def _validate_counts(
        self, owner: str, attributes: list[ir.Attribute]
    ) -> list[ir.Attribute]:
        """Every hidden attribute must be a primitive count of exactly one
        objectlist; every objectlist count_field must name a hidden
        primitive. Returns attributes with count_for links filled."""
        lists = {
            a.shape.count_field: a.name
            for a in attributes
            if isinstance(a.shape, ir.ObjectList)
        }
        hidden_names = {a.name for a in attributes if a.hidden}
        for attr in attributes:
            shape = attr.shape
            if attr.hidden:
                if not isinstance(shape, ir.Primitive):
                    raise SpecError(
                        f"hidden attribute {attr.name!r} on {owner!r} must be "
                        "a primitive count"
                    )
                if attr.name not in lists:
                    raise SpecError(
                        f"hidden attribute {attr.name!r} on {owner!r} is not "
                        "referenced by any objectlist countFieldName"
                    )
            elif (
                isinstance(shape, ir.ObjectList)
                and shape.count_field not in hidden_names
            ):
                raise SpecError(
                    f"objectlist {attr.name!r} on {owner!r} counts hidden "
                    f"field {shape.count_field!r}, which is not declared hidden"
                )
        return [
            (
                dataclasses.replace(attr, count_for=lists[attr.name])
                if attr.hidden
                else attr
            )
            for attr in attributes
        ]

    def _flatten(self, el):
        """Attributes in declaration order via MRO, base-first, deduped.

        The walk stops at kernel PDU bases: their header fields are the
        hand-maintained ``PduHeader``/``Pdu`` composition (record/pdu.py),
        not generated state.
        """
        chain = []
        cur = el
        while cur is not None:
            chain.append(cur)
            parent = cur.get("inheritsFrom")
            if parent in (None, "root"):
                break
            canonical = self.canonical_name(parent)
            if canonical in self.ov.KERNEL_BASES:
                break
            cur = self.xml_classes.get(self.by_canonical.get(canonical, canonical))
            if cur is None:
                raise SpecError(f"{el.get('name')!r} inherits unknown class {parent!r}")
        seen: set[str] = set()
        flat = []
        for cls in reversed(chain):
            for attr in cls.findall("attribute"):
                if attr.get("name") in seen:
                    continue
                seen.add(attr.get("name"))
                flat.append(attr)
        return flat

    def _attribute(self, attr_el) -> ir.Attribute:
        name = attr_el.get("name")
        kids = [c for c in attr_el if c.tag in TYPE_TAGS]
        by_tag: dict[str, list] = {}
        for kid in kids:
            by_tag.setdefault(kid.tag, []).append(kid)
        shapes = []
        viewable = False
        for tag, group in by_tag.items():
            if len(group) > 1:
                shapes.append(self._variant_group(tag, group, owner=name))
            else:
                kid = group[0]
                if (
                    kid.tag == "classRef"
                    and kid.get("name") in self.ov.PRIMITIVE_BINDINGS
                ):
                    viewable = True  # curated parse may attach a bitfield view
                shapes.append(self._shape(kid))
        if len(shapes) == 1:
            shape = shapes[0]
        elif len(shapes) == 0:
            raise SpecError(f"attribute {name!r} has no type children")
        else:
            raise SpecError(
                f"attribute {name!r} mixes type tags "
                f"{sorted(by_tag)} — not a legal variant group"
            )
        return ir.Attribute(
            name=name,
            comment=attr_el.get("comment"),
            shape=shape,
            present_if=attr_el.get("presentIf"),
            hidden=attr_el.get("hidden") == "true",
            viewable=viewable,
        )

    def _variant_group(self, tag, group, owner: str) -> ir.VariantGroup:
        members = tuple(self._shape(k) for k in group)
        carrying = [m for m in members if getattr(m, "when", None)]
        if not carrying:
            raise SpecError(f"attribute {owner!r} repeats <{tag}> without when= guards")
        defaults = [k for k in group if not k.get("when")]
        if len(defaults) != 1 or group[-1] is not defaults[0]:
            raise SpecError(
                f"attribute {owner!r} variant group must declare exactly "
                "one no-when default, LAST (ruled ordering)"
            )
        return ir.VariantGroup(tag=tag, members=members)

    def _shape(self, kid) -> ir.Shape:
        tag = kid.tag
        if tag == "primitive":
            return ir.Primitive(type=kid.get("type"), default=kid.get("defaultValue"))
        if tag in ("sisoenum", "sisobitfield"):
            uid = kid.get("uid")
            size = kid.get("size")
            if uid is None or size is None:
                raise SpecError(
                    f"<{tag} {kid.get('type')!r}> lacks uid/size — "
                    "the corrected spec must carry both"
                )
            if tag == "sisobitfield":
                return ir.BitfieldRef(uid=int(uid), size=int(size))
            return ir.EnumRef(
                uid=int(uid),
                size=int(size),
                enum_type=kid.get("type"),
                when=kid.get("when"),
                default=kid.get("defaultValue"),
            )
        if tag == "classRef":
            bound = self.ov.PRIMITIVE_BINDINGS.get(kid.get("name"))
            if bound is not None:
                # the XML record class is absorbed as a plain primitive
                # (e.g. EntityAppearance -> raw uint32 state)
                return ir.Primitive(type=bound)
            return ir.ClassRef(
                target=self.canonical_name(kid.get("name")), when=kid.get("when")
            )
        if tag == "objectlist":
            element = kid.find("classRef")
            count_field = kid.get("countFieldName")
            if element is None or not count_field:
                raise SpecError(
                    f"objectlist on {kid.attrib!r} needs one classRef element "
                    "and countFieldName"
                )
            return ir.ObjectList(
                element=self.canonical_name(element.get("name")),
                count_field=count_field,
            )
        if tag == "primitivelist":
            if (
                kid.get("fixedlength") == "true"
                and not kid.get("countFieldName")
                and not kid.get("countExpression")
            ):
                length = int(kid.get("length", "0"))
                if kid.get("length") == "0":
                    raise SpecError(
                        f"unsized primitivelist not supported here: {kid!r}"
                    )
                prim = kid.find("primitive")
                if prim is not None and prim.get("type") == "uint8":
                    return ir.FixedBytes(
                        length=length,
                        could_be_string=kid.get("couldBeString") == "true",
                    )
            return ir.Unsupported(summary=f"primitivelist {kid.attrib!r}")
        if tag == "objectlist":
            return ir.Unsupported(summary=f"objectlist {kid.attrib!r}")
        if tag == "padtoboundary":
            return ir.Unsupported(summary=f"padtoboundary {kid.attrib!r}")
        raise SpecError(f"unhandled type tag {tag!r}")
