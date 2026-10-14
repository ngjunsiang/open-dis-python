"""Core-side SISO enum pluggability hook.

Design: docs/design/siso-enums.md §3.1. The core package carries no SISO
enumeration data; when a provider (the generated ``opendis.siso`` module)
is plugged in via :func:`register_enum_factory`, parse sites resolve wire
values to rich ``IntEnum`` members through :func:`rich_or_int`. Because
``IntEnum`` members *are* ``int``, serialization, equality and hashing are
identical in both modes — pluggability reduces to what ``parse()`` returns.
"""

from typing import Callable, Optional

__all__ = [
    "EnumFactory",
    "register_enum_factory",
    "unregister_enum_factory",
    "rich_or_int",
]

EnumFactory = Callable[[int], Optional[type]]
"""uid -> enum type or None"""


_factory: Optional[EnumFactory] = None


def register_enum_factory(factory: EnumFactory) -> None:
    """Plug in a SISO-REF-010 enum provider (keyed by table uid)."""
    global _factory
    _factory = factory


def unregister_enum_factory() -> None:
    """Unplug the provider; parse returns plain ints again (mainly for tests)."""
    global _factory
    _factory = None


def rich_or_int(uid: int, value: int) -> int:
    """Resolve a raw wire value against the registered provider.

    Degrades to plain int when: no provider registered, table unknown,
    or value not present in the table. Parsers must never raise on
    out-of-range enum values.
    """
    if _factory is None:
        return value
    table = _factory(uid)
    if table is None:
        return value
    try:
        return table(value)
    except ValueError:
        return value
