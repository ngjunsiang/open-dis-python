"""Resolve the XML element tree into flattened RecordClass IR.

Semantics ported from submodules/open-dis-spec-xml/xml/scripts/validate.py (SizeEval lineage):
inheritance flattens base-first with name deduplication; attributes with
competing type children of one tag become VariantGroups; Python-side
curated bindings (overrides.py) rebind XML names to canonical classes.
"""

from __future__ import annotations

import dataclasses
import re

from . import ir, overrides
from .xmlload import TYPE_TAGS, SpecError, collect_classes


class Resolver:
    def __init__(self, root, overrides_module=overrides, view_map=None):
        self.xml_classes, self.aliases = collect_classes(root)
        self.ov = overrides_module
        # uid -> local view class name for the generated single-layout
        # bitfield tables (bucket-C item 5): a sisobitfield field whose
        # uid has a view attaches it unconditionally at parse. Context
        # tables (EntityAppearance/EntityCapabilities kind layouts) are
        # excluded here — they dispatch on entityType (item 6).
        self.view_map = view_map or {}
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
        # classes emitted into generated modules (module homes are the
        # curated bucket-D decision; every other abstract class is a
        # drop candidate — see _is_dropped_parent)
        self.emitted = {
            self.canonical_name(n)
            for order in self.ov.RECORD_MODULES.values()
            for n in order
        }

    def _is_dropped_parent(self, canonical: str) -> bool:
        """abstract="true" parents that are neither emitted classes nor
        kernel bases are Java-side abstractions (bucket-C item 3, spec
        v0.12.8): never emitted, never a Python base — the subclass
        flattens their fields and stands alone."""
        if (
            canonical in self.ov.KERNEL_BASES
            or canonical in self.ov.KERNEL_RECORD_BASES
            or canonical in self.emitted
        ):
            return False
        el = self.xml_classes.get(self.by_canonical.get(canonical, canonical))
        return el is not None and el.get("abstract") == "true"

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
                # registry-decoded lists are untyped (plain ``list``): the
                # XML's element class is a union member, not a dependency
                if (
                    isinstance(attr.shape, ir.ObjectList)
                    and (name, attr.name) in self.ov.REGISTRY_LISTS
                ):
                    continue
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
        xml_owner = el.get("name")
        flat = self._flatten(el)
        is_sv, sv_dispatch, flat = self._sv_signature(name, flat)
        attributes = [self._attribute(a, declarer) for a, declarer in flat]
        dropped = set(self.ov.FIELD_DROPS.get(xml_owner, []))
        attributes = [a for a in attributes if a.name not in dropped]
        extras = self.ov.EXTRA_FIELDS.get(xml_owner, [])
        # splice positionally: an extra may declare the field it precedes
        # (hidden counts ride their list's wire position, not the tail)
        for extra_name, shape, comment, *rest in extras:
            hidden = rest[0] if rest else False
            before = rest[1] if len(rest) > 1 else None
            attr = ir.Attribute(
                name=extra_name, comment=comment, shape=shape, hidden=hidden
            )
            if before is not None:
                names = [a.name for a in attributes]
                if before in names:
                    attributes.insert(names.index(before), attr)
                    continue
            attributes.append(attr)
        attributes = self._link_counts(name, xml_owner, attributes, extras)
        parent, is_pdu = self._lineage(el)
        # curated parent overrides: SV records resolve onto the kernel
        # StandardVariableRecord base; RECORD_BASES rehomes a record onto
        # a hand protocol class (BeamAntennaPattern -> AntennaPatternRecord)
        if is_sv:
            # an SV record whose XML lineage already provides a generated
            # record base (§6.2.95 home) keeps it — only root-parented SV
            # records rehome onto the kernel base directly
            if parent not in self.ov.KERNEL_RECORD_BASES:
                parent = "StandardVariableRecord"
            if name in self.ov.FROZEN_RECORDS:
                raise SpecError(
                    f"SV record {name!r} must stay mutable: the kernel "
                    "protocol is a mutating parse(inputStream, bytelength) "
                    "and wire pads round-trip through instance state"
                )
        elif xml_owner in self.ov.RECORD_BASES:
            parent = self.ov.RECORD_BASES[xml_owner]
        attributes = self._mark_pads(attributes)
        if name in self.ov.FROZEN_RECORDS and any(a.pad for a in attributes):
            raise SpecError(
                f"frozen record {name!r} carries a named pad: pads are "
                "field(init=False) wire state and cannot cross a frozen "
                "constructor — make the record mutable"
            )
        return ir.RecordClass(
            name=name,
            comment=el.get("comment"),
            attributes=attributes,
            frozen=name in self.ov.FROZEN_RECORDS,
            parent=parent,
            is_pdu=is_pdu,
            is_sv=is_sv,
            identity_vars=self._identity_vars(el, name, sv_dispatch),
            xml=el,
        )

    def _sv_signature(self, name: str, flat):
        """§6.2.83 Standard Variable signature (bucket-C item 4): the
        class's two leading wire fields are recordType u32 carrying a
        FIXED dispatch value (defaultValue) + recordLength u16 (hidden,
        recordOctets role). Typed SV records resolve on the kernel base
        which owns the header; the dispatch value flows from the XML.
        Generic SV-format records (IFFData, Attribute) carry a varying
        recordType with no defaultValue — their headers stay instance
        state and the signature does not fire."""
        if len(flat) < 2:
            return False, None, flat
        (a0, _d0), (a1, _d1) = flat[0], flat[1]
        p0 = a0.find("primitive")
        p1 = a1.find("primitive")
        if a0.get("name") != "recordType" or a1.get("name") != "recordLength":
            return False, None, flat
        if (
            p0 is None
            or p0.get("type") != "uint32"
            or p1 is None
            or p1.get("type") != "uint16"
            or a1.get("hidden") != "true"
            or a1.get("lengthRole") != "recordOctets"
        ):
            return False, None, flat
        value = p0.get("defaultValue")
        if not (value or "").isdigit():
            return False, None, flat  # generic SV record: no fixed dispatch
        return True, value, flat[2:]

    def _identity_vars(
        self, el, name: str, sv_dispatch: str | None = None
    ) -> tuple[tuple[str, str, str | None], ...]:
        """XML-declared identity ClassVars (bucket-C item 7): the class's
        own ``<initialValue name="pduType|protocolFamily">`` says WHICH
        constant the class carries; the numeric value is the class ``id``
        (they agree across the roster; REF-010 owns the symbolic names).
        Riders are SISO data the XML cannot say and stay curated."""
        out: list[tuple[str, str, str | None]] = []
        for iv in el.findall("initialValue"):
            var = iv.get("name")
            if var not in ("pduType", "protocolFamily"):
                continue  # field defaults (e.g. padding) are not identity
            raw = el.get("id")
            if raw is None or not raw.isdigit():
                raise SpecError(
                    f"{name!r} declares {var} ({iv.get('value')!r}) but its "
                    f"class id {raw!r} is not a number"
                )
            if var == "protocolFamily":
                rider = self.ov.PROTOCOL_FAMILY_RIDERS.get(name)
                if rider is None:
                    raise SpecError(
                        f"family {name!r} lacks a curated [UID 5] rider "
                        "(PROTOCOL_FAMILY_RIDERS)"
                    )
            else:
                rider = "[UID 4]"
            out.append((var, raw, rider))
        if len(out) > 1:
            raise SpecError(
                f"{name!r} declares multiple identity constants — "
                "emission order would be ambiguous"
            )
        if sv_dispatch is not None:
            out.append(("recordType", sv_dispatch, self.ov.SV_RECORD_TYPE_RIDER))
        return tuple(out)

    def _link_counts(
        self,
        owner: str,
        xml_owner: str,
        attributes: list[ir.Attribute],
        extras: list | None = None,
    ) -> list[ir.Attribute]:
        """Rename count references with their fields, hide bit-count
        fields of byte payloads, and validate the count contract: every
        hidden attribute is a primitive count of exactly one sized field;
        every sized field counts a hidden primitive. Fills count_for."""
        by_name = {a.name: a for a in attributes}

        def renamed_count(shape):
            field = getattr(shape, "count_field", None) or getattr(
                shape, "bit_count_field", None
            )
            if field is None:
                return shape
            new = self._rename(xml_owner, field)
            if new == field:
                return shape
            if isinstance(shape, ir.BytesPayload):
                return dataclasses.replace(shape, bit_count_field=new)
            return dataclasses.replace(shape, count_field=new)

        attributes = [
            (
                a
                if not isinstance(
                    a.shape, (ir.ObjectList, ir.PrimitiveList, ir.BytesPayload)
                )
                else dataclasses.replace(a, shape=renamed_count(a.shape))
            )
            for a in attributes
        ]
        by_name = {a.name: a for a in attributes}
        # bit-count fields of payloads leave instance state (derived len*8)
        hidden_forced = set()
        for a in attributes:
            if isinstance(a.shape, ir.BytesPayload):
                if a.shape.bit_count_field is None:
                    continue  # expression-sized: curated methods own it
                count = by_name.get(a.shape.bit_count_field)
                if count is None:
                    raise SpecError(
                        f"bytes payload {a.name!r} on {owner!r} names unknown "
                        f"bit-count field {a.shape.bit_count_field!r}"
                    )
                hidden_forced.add(count.name)
        lists: dict[str, str] = {}
        sized: dict[str, ir.Shape] = {}
        for a in attributes:
            shape = a.shape
            if isinstance(shape, ir.ObjectList):
                lists[shape.count_field] = a.name
                sized[a.name] = shape
            elif isinstance(shape, ir.PrimitiveList):
                lists[shape.count_field] = a.name
                sized[a.name] = shape
            elif isinstance(shape, ir.BytesPayload):
                if shape.bit_count_field is not None:
                    lists[shape.bit_count_field] = a.name
                    sized[a.name] = shape
        out = []
        overridden = {
            xml_name for (cls, xml_name) in self.ov.FIELD_SHAPES if cls == xml_owner
        }
        extra_names = {name for name, *_rest in (extras or [])}
        count_override = self.ov.COUNT_FOR_OVERRIDES.get(xml_owner, {})
        for a in attributes:
            shape = a.shape
            if a.name in hidden_forced and not isinstance(shape, ir.Primitive):
                raise SpecError(
                    f"bit-count field {a.name!r} on {owner!r} must be primitive"
                )
            if isinstance(shape, (ir.ObjectList, ir.PrimitiveList, ir.BytesPayload)):
                if isinstance(shape, ir.BytesPayload) and shape.bit_count_field is None:
                    out.append(a)
                    continue
                if a.name in extra_names:
                    out.append(a)  # curated extra: hand-owned count semantics
                    continue
                count_name = (
                    shape.bit_count_field
                    if isinstance(shape, ir.BytesPayload)
                    else shape.count_field
                )
                count = by_name.get(count_name)
                if (
                    (count is None or not count.hidden)
                    and count_name not in overridden
                    and a.name not in overridden
                    # registry lists may carry a curated count property
                    # (Transmitter's VTP list: the FIELD_DROPS'd count's
                    # docstring is hand-ruled) — the registry decode owns
                    # the wire, the contract exemption is deliberate
                    and not (
                        count is None
                        and isinstance(shape, ir.ObjectList)
                        and (owner, a.name) in self.ov.REGISTRY_LISTS
                    )
                ):
                    if count is not None and count.name in hidden_forced:
                        pass  # payload count: hidden below
                    else:
                        raise SpecError(
                            f"sized field {a.name!r} on {owner!r} counts field "
                            f"{count_name!r}, which is not declared hidden"
                        )
            out.append(a)
        # rebuild with hidden/count_for/count_bits filled
        out = []
        for a in attributes:
            if a.name in hidden_forced:
                a = dataclasses.replace(a, hidden=True)
            if a.hidden:
                if not isinstance(a.shape, ir.Primitive):
                    raise SpecError(
                        f"hidden attribute {a.name!r} on {owner!r} must be "
                        "a primitive count"
                    )
                if a.name not in lists:
                    raise SpecError(
                        f"hidden attribute {a.name!r} on {owner!r} is not "
                        "referenced by any sized field"
                    )
                a = dataclasses.replace(
                    a,
                    count_for=count_override.get(a.name, lists[a.name]),
                    count_bits=(
                        isinstance(sized[lists[a.name]], ir.BytesPayload)
                        and getattr(sized[lists[a.name]], "count_is_bits", True)
                    ),
                )
            out.append(a)
        return out

    def _lineage(self, el) -> tuple[str | None, bool]:
        """Canonical Python base name + whether the lineage reaches a
        kernel PDU base (the class emits body methods)."""
        # abstract record bases (§6.2.58/§6.2.8/§6.2.95 homes): generated
        # classes themselves, parented on a kernel protocol base
        if el.get("name") in self.ov.KERNEL_RECORD_BASES:
            base, _module = self.ov.KERNEL_RECORD_BASES[el.get("name")]
            return base, False
        parent = el.get("inheritsFrom")
        if parent in (None, "root"):
            return None, False
        canonical = self.canonical_name(parent)
        if canonical in self.ov.KERNEL_BASES:
            base, _module = self.ov.KERNEL_BASES[canonical]
            return base, True
        if self._is_dropped_parent(canonical):
            # Java-side abstraction (AbstractIFFPduLayerData, GridData…):
            # never emitted, never a Python base — the subclass flattens
            # its fields and stands alone
            return None, False
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
        """Deprecated shim — count linking lives in _link_counts now."""
        raise AssertionError("replaced by _link_counts")

    _PAD_NAME = re.compile(r"^(pad|padding)", re.I)

    def _mark_pads(self, attributes: list[ir.Attribute]) -> list[ir.Attribute]:
        """Named padding primitives (pad, pad1..4, padding1..2, …) are
        wire-only state: emitted as ``field(init=False, default=0)``,
        grouped after the init fields (2026-10-14 ruling)."""

        def is_pad(a: ir.Attribute) -> bool:
            return (
                isinstance(a.shape, ir.Primitive)
                and not a.hidden
                and self._PAD_NAME.match(a.name) is not None
            )

        return [
            dataclasses.replace(a, pad=True) if is_pad(a) else a for a in attributes
        ]

    def _flatten(self, el):
        """Attributes in declaration order via MRO, base-first, deduped.

        The walk stops at kernel PDU bases: their header fields are the
        hand-maintained ``PduHeader``/``Pdu`` composition (record/pdu.py),
        not generated state. ClassRefs to curated expansion targets
        (RadioCommsHeader) splice the target's fields in place — the
        ruled flattening the exemplar applies.
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
        flat: list[tuple[object, str]] = []
        for cls in reversed(chain):
            dropped = set(self.ov.FIELD_DROPS.get(cls.get("name"), []))
            for attr in cls.findall("attribute"):
                if attr.get("name") in seen or attr.get("name") in dropped:
                    continue
                seen.add(attr.get("name"))
                flat.append((attr, cls.get("name")))
        # curated expansions: classRef to a listed class becomes the target's
        # own attributes spliced in place (ruling: RadioCommsHeader flattening)
        expanded: list[tuple[object, str]] = []
        expanding = False
        for attr, declarer in flat:
            refs = attr.findall("classRef")
            if (
                not expanding
                and len(refs) == 1
                and refs[0].get("name") in self.ov.EXPAND_CLASS_REFS
            ):
                target = self.xml_classes.get(refs[0].get("name"))
                if target is None:
                    raise SpecError(
                        f"expansion target {refs[0].get('name')!r} not declared"
                    )
                expanded.extend(self._flatten(target))
                expanding = True  # only the first header ref flattens
                continue
            expanded.append((attr, declarer))
        return expanded

    def _rename(self, owner: str, name: str) -> str:
        return (
            self.ov.FIELD_RENAMES.get((owner, name))
            or self.ov.GLOBAL_FIELD_RENAMES.get(name)
            or name
        )

    def _attribute(self, attr_el, owner: str) -> ir.Attribute:
        name = self._rename(owner, attr_el.get("name"))
        # fully-curated fields replace the XML shape before any group
        # validation (LE flag pairs may carry when= on every member)
        curated = self.ov.FIELD_OVERRIDES.get((owner, attr_el.get("name")))
        if curated is not None:
            annotation, default, rider = curated
            return ir.Attribute(
                name=name,
                comment=attr_el.get("comment"),
                shape=ir.CuratedField(
                    annotation=annotation, default=default, rider=rider
                ),
                present_if=attr_el.get("presentIf"),
            )
        kids = [c for c in attr_el if c.tag in TYPE_TAGS]
        by_tag: dict[str, list] = {}
        for kid in kids:
            by_tag.setdefault(kid.tag, []).append(kid)
        shapes = []
        viewable = False
        view_binding = None
        for tag, group in by_tag.items():
            if len(group) > 1:
                shapes.append(self._variant_group(tag, group, owner=name))
            else:
                kid = group[0]
                if (
                    kid.tag == "classRef"
                    and kid.get("name") in self.ov.PRIMITIVE_BINDINGS
                ):
                    # absorbed primitive: the raw integer may gain a typed
                    # view at parse (uid-keyed direct attach, or the
                    # kind-dispatched context layouts keyed by entityType)
                    viewable = True
                    view_binding = kid.get("name")
                elif (
                    kid.tag == "sisobitfield"
                    and kid.get("type") in self.ov.PRIMITIVE_BINDINGS
                ):
                    # same absorption, XML-spelled as a bitfield typed by
                    # the bound class (EntityCapabilities [UID 55]): no
                    # uid-keyed view exists — the context layout dispatches
                    view_binding = kid.get("type")
                shapes.append(self._shape(kid))
        override = self.ov.FIELD_SHAPES.get((owner, attr_el.get("name")))
        if override is not None:
            if len(shapes) != 1:
                raise SpecError(
                    f"field shape override on non-simple attribute " f"{owner}.{name!r}"
                )
            shape = override
        elif len(shapes) == 1:
            shape = shapes[0]
        elif len(shapes) == 0:
            raise SpecError(f"attribute {name!r} has no type children")
        else:
            raise SpecError(
                f"attribute {name!r} mixes type tags "
                f"{sorted(by_tag)} — not a legal variant group"
            )
        # bucket-C item 1: a record group (or single when-guarded classRef)
        # NOT driven by presentIf is the Transmitter PDU's count-driven
        # parameter-record form when its members share a §-home base —
        # an optional single record on that home (presence rides the
        # hidden byte-length count, selection the first-true-wins terms;
        # the dispatch itself is curated METHOD_BODIES). Exhaustive-when
        # groups without a home (the LE identifier switches) keep the
        # union form.
        if not attr_el.get("presentIf"):
            if (
                isinstance(shape, ir.VariantGroup)
                and shape.tag == "classRef"
                and len(shape.members) > 1
            ):
                shape = self._home_optional_group(shape, name)
            elif isinstance(shape, ir.ClassRef) and shape.when:
                parent = self._xml_parent(shape.target)
                if parent is None or parent not in self.ov.KERNEL_RECORD_BASES:
                    raise SpecError(
                        f"when-guarded classRef {name!r} on {owner!r} selects "
                        f"{shape.target!r} outside a §-home base — unsupported"
                    )
                shape = ir.OptionalRecord(target=parent)
        hidden = (
            attr_el.get("hidden") == "true"
            or (
                owner,
                attr_el.get("name"),
            )
            in self.ov.FIELD_HIDDEN
        )
        count_bits = False
        # a bit-counted payload pulls its length field out of instance state
        if isinstance(shape, ir.BytesPayload):
            hidden = False
            count_bits = True
        view = (
            self.view_map.get(shape.uid)
            if isinstance(shape, ir.BitfieldRef) and not hidden
            else None
        )
        return ir.Attribute(
            name=name,
            comment=attr_el.get("comment"),
            shape=shape,
            present_if=attr_el.get("presentIf"),
            hidden=hidden,
            count_bits=count_bits,
            viewable=viewable,
            view=view,
            view_binding=view_binding,
        )

    def _xml_parent(self, canonical: str) -> str | None:
        """Canonical XML parent (inheritsFrom) of a canonical class, or
        None for root-parented classes."""
        el = self.xml_classes.get(self.by_canonical.get(canonical, canonical))
        if el is None or el.get("inheritsFrom") in (None, "root"):
            return None
        return self.canonical_name(el.get("inheritsFrom"))

    def _home_optional_group(self, group: ir.VariantGroup, owner: str) -> ir.Shape:
        parents = {self._xml_parent(m.target) for m in group.members}
        if len(parents) == 1:
            home = next(iter(parents))
            if home is not None and home in self.ov.KERNEL_RECORD_BASES:
                return ir.OptionalRecord(target=home)
        return group

    def _variant_group(self, tag, group, owner: str) -> ir.VariantGroup:
        members = tuple(self._shape(k) for k in group)
        if tag == "classRef":
            # record variant group (bucket-C items 1+2): first-true-wins
            # over the when= terms. Members may be exhaustive-when (the
            # LE elided/full identifier switches) or carry one trailing
            # no-when default (IFF layer formats); presence itself rides
            # a separate presentIf/count on the attribute
            if not all(isinstance(m, ir.ClassRef) for m in members):
                raise SpecError(f"classRef group on {owner!r} mixes member kinds")
            defaults = [m for m in members if not m.when]
            if len(defaults) > 1 or (defaults and members[-1] is not defaults[0]):
                raise SpecError(
                    f"attribute {owner!r} classRef group may carry at most "
                    "one no-when default, LAST (first-true-wins ordering)"
                )
            return ir.VariantGroup(tag=tag, members=members)
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
            count_field = kid.get("countFieldName") or kid.get("countListFieldName")
            if element is None or not count_field:
                # a list of enum/bitfield values (not records): minefield
                # fusing [UID 192] / paint scheme [UID 202]. NB: is-None
                # checks, not truthiness — childless Elements are falsy
                # (deprecated ElementTree bool), so `find() or find()`
                # silently discarded self-closing enum children.
                val = kid.find("sisoenum")
                if val is None:
                    val = kid.find("sisobitfield")
                if val is not None and count_field:
                    bits = int(val.get("size"))
                    uid = val.get("uid")
                    return ir.PrimitiveList(
                        element=f"uint{bits}",
                        count_field=count_field,
                        element_uid=int(uid) if uid else None,
                    )
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
            if kid.get("bitCountFieldName") or kid.get("bitCountExpression"):
                # byte payload whose wire length counts bits (a named
                # count field, or an expression — curated methods own
                # expression-sized payloads end to end)
                prim = kid.find("primitive")
                if prim is None or prim.get("type") != "uint8":
                    raise SpecError(
                        f"bit-counted primitivelist must be uint8 elements: "
                        f"{kid.attrib!r}"
                    )
                return ir.BytesPayload(bit_count_field=kid.get("bitCountFieldName"))
            count_field = kid.get("countFieldName")
            if count_field:
                prim = kid.find("primitive")
                if prim is None:
                    raise SpecError(
                        f"counted primitivelist without element primitive: "
                        f"{kid.attrib!r}"
                    )
                element = prim.get("type")
                enum = kid.find("sisoenum")
                uid = (
                    int(enum.get("uid"))
                    if enum is not None and enum.get("uid")
                    else None
                )
                return ir.PrimitiveList(
                    element=element,
                    element_uid=uid,
                    count_field=count_field,
                    count_expr=kid.get("countExpression"),
                    count_list=kid.get("countListFieldName"),
                )
            return ir.Unsupported(summary=f"primitivelist {kid.attrib!r}")
        if tag == "padtoboundary":
            length = kid.get("length")
            if length is None:
                raise SpecError(f"padtoboundary without length: {kid.attrib!r}")
            return ir.PadToBoundary(length=int(length))
        raise SpecError(f"unhandled type tag {tag!r}")
