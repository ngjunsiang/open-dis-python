"""Load the corrected DIS 7 XML set into a single element tree.

``DIS_7_2012.xml`` is the entry document; the 12 family files arrive via
``xi:include`` and are spliced in place (stdlib ElementTree has no XInclude
processor, and the include graph is flat and single-directory, so a plain
in-place splice is sufficient — anything else fails loudly). ``aliasFor``
classes are recorded and dropped: the alias map feeds the resolver
(descriptive-canonical ruling, 2026-10-14).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

XI_INCLUDE = "{http://www.w3.org/2001/XInclude}include"

TYPE_TAGS = (
    "primitive",
    "primitivelist",
    "objectlist",
    "classRef",
    "sisoenum",
    "sisobitfield",
    "padtoboundary",
)


class SpecError(Exception):
    """The XML says something this generator refuses to guess about."""


def load_spec(xml_dir: str | Path, entry: str = "DIS_7_2012.xml") -> ET.Element:
    """Parse the spec, expanding xi:include references in document order."""
    base = Path(xml_dir)
    root = ET.parse(base / entry).getroot()
    for _ in range(100):  # bounded: flat include graph, fail loud on cycles
        includes = list(root.iter(XI_INCLUDE))
        if not includes:
            break
        for inc in includes:
            href = inc.get("href")
            if href is None:
                raise SpecError(f"xinclude without href in {entry}")
            sub_root = ET.parse(base / href).getroot()
            parent = _find_parent(root, inc)
            idx = list(parent).index(inc)
            parent.remove(inc)
            for offset, child in enumerate(list(sub_root)):
                parent.insert(idx + offset, child)
    else:
        raise SpecError("xi:include expansion did not terminate")
    return root


def _find_parent(root: ET.Element, target: ET.Element) -> ET.Element:
    for el in root.iter():
        if target in list(el):
            return el
    raise SpecError(f"orphan xi:include {target!r}")


def collect_classes(root: ET.Element) -> tuple[dict[str, ET.Element], dict[str, str]]:
    """Return (concrete classes by name, alias name -> canonical name)."""
    classes: dict[str, ET.Element] = {}
    aliases: dict[str, str] = {}
    for el in root.iter("class"):
        name = el.get("name")
        if not name:
            raise SpecError(f"class without a name: {el!r}")
        target = el.get("aliasFor")
        if target:
            aliases[name] = target
        elif name in classes:
            raise SpecError(f"duplicate class declaration: {name}")
        else:
            classes[name] = el
    return classes, aliases
