"""DataInputStream/DataOutputStream: scalar round-trips and layouts.

The alias method families (read_int8/write_int8, ...) and the *_utf pair
had no direct tests — only whatever specific record parsers happened to
call. This pins every reader/writer pair byte-for-byte.
"""

from __future__ import annotations

import io

import pytest

from opendis.stream import DataInputStream, DataOutputStream

SCALARS = [
    ("boolean", True),
    ("boolean", False),
    ("byte", -128),
    ("byte", 127),
    ("unsigned_byte", 0),
    ("unsigned_byte", 255),
    ("char", "A"),
    ("char", "ÿ"),
    ("double", -1234.56789012345),
    ("double", 0.0),
    ("float", 0.5),
    ("float", -1024.25),
    ("short", -32768),
    ("short", 32767),
    ("unsigned_short", 0),
    ("unsigned_short", 65535),
    ("int", -(2**31)),
    ("int", 2**31 - 1),
    ("unsigned_int", 0),
    ("unsigned_int", 2**32 - 1),
    ("long", -(2**63)),
    ("long", 2**63 - 1),
]

# alias name -> canonical name (aliases must behave identically)
ALIASES = {
    "float32": "float",
    "float64": "double",
    "int8": "byte",
    "int16": "short",
    "int32": "int",
    "int64": "long",
    "uint8": "unsigned_byte",
    "uint16": "unsigned_short",
    "uint32": "unsigned_int",
}


def _round_trip(method: str, value) -> object:
    buf = io.BytesIO()
    getattr(DataOutputStream(buf), f"write_{method}")(value)
    buf.seek(0)
    return getattr(DataInputStream(buf), f"read_{method}")()


@pytest.mark.parametrize("method,value", SCALARS)
def test_scalar_round_trip(method: str, value) -> None:
    assert _round_trip(method, value) == value


@pytest.mark.parametrize("alias,canonical", sorted(ALIASES.items()))
def test_alias_methods_match_canonical(alias: str, canonical: str) -> None:
    values = [v for m, v in SCALARS if m == canonical]
    assert values, f"no scalar samples for {canonical}"
    for value in values:
        assert _round_trip(alias, value) == value


def test_utf_round_trip_with_length_prefix() -> None:
    payload = b"DIS-7 capture text"
    buf = io.BytesIO()
    out = DataOutputStream(buf)
    out.write_utf(payload)
    encoded = buf.getvalue()
    # 2-byte big-endian length prefix, then the bytes verbatim
    assert encoded[:2] == len(payload).to_bytes(2, "big")
    assert encoded[2:] == payload
    buf.seek(0)
    assert DataInputStream(buf).read_utf() == payload


def test_write_bytes_is_verbatim() -> None:
    buf = io.BytesIO()
    DataOutputStream(buf).write_bytes(b"\x00\xff\x10")
    assert buf.getvalue() == b"\x00\xff\x10"


def test_big_endian_layouts() -> None:
    layout = [
        ("unsigned_short", 0x0102, b"\x01\x02"),
        ("unsigned_int", 0x01020304, b"\x01\x02\x03\x04"),
        ("long", 0x0102030405060708, b"\x01\x02\x03\x04\x05\x06\x07\x08"),
        ("boolean", True, b"\x01"),
        ("char", "A", b"\x00\x41"),
    ]
    for method, value, expected in layout:
        buf = io.BytesIO()
        getattr(DataOutputStream(buf), f"write_{method}")(value)
        assert buf.getvalue() == expected, method


def test_sequential_reads_preserve_order() -> None:
    buf = io.BytesIO()
    out = DataOutputStream(buf)
    out.write_unsigned_byte(7)
    out.write_unsigned_short(0x1234)
    out.write_double(1.5)
    out.write_utf(b"tail")
    buf.seek(0)
    reader = DataInputStream(buf)
    assert reader.read_unsigned_byte() == 7
    assert reader.read_unsigned_short() == 0x1234
    assert reader.read_double() == 1.5
    assert reader.read_utf() == b"tail"
