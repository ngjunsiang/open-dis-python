"""The example pair, tested in process.

The upstream test spawned both example scripts as subprocesses, slept in
a wall-clock loop for three seconds, terminated them, and asserted on
captured stdout. The spirit is kept — an ESPDU must survive the
sender → UDP → receiver trip with its identity and geodetic position
intact — while the letter (subprocess orchestration, the hardcoded port,
sleeps, os.chdir, stdout scraping) is dropped: the examples expose
importable single-shot units, and this test drives a real loopback UDP
socket on an ephemeral port with a hard recv timeout.
"""

import socket

import pytest

from examples.dis_receiver import describe_datagram
from examples.dis_sender import build_espdu, serialize
from opendis.RangeCoordinates import GPS, deg2rad, rad2deg
from opendis.record.factory import createPdu


@pytest.fixture()
def loopback():
    """One UDP socket talking to itself on an ephemeral port."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.settimeout(5.0)
        yield sock


def test_example_pair_round_trip(loopback):
    pdu = build_espdu()
    wire = serialize(pdu)

    loopback.sendto(wire, loopback.getsockname())
    received, _ = loopback.recvfrom(4096)

    assert received == wire  # byte-exact through the UDP hop

    parsed = createPdu(received)
    assert type(parsed).__name__ == "EntityStatePdu"
    assert parsed.header.pduType == 1  # Entity State [UID 4]
    assert parsed.entityID.simulationAddress.site == 17
    assert parsed.entityID.simulationAddress.application == 23
    assert parsed.entityID.entityNumber == 42
    assert parsed.marking.string == "Igor3d"
    assert parsed.to_bytes() == wire


def test_example_receiver_geodetic_decode(loopback):
    """The receiver side of the demo: the Monterey position survives the
    ECEF round trip the way describe_datagram renders it."""
    pdu = build_espdu()
    loopback.sendto(serialize(pdu), loopback.getsockname())
    received, _ = loopback.recvfrom(4096)

    report = describe_datagram(received)
    assert "Received EntityStatePdu" in report
    assert "Id        : 42" in report

    parsed = createPdu(received)
    body = GPS().ecef2llarpy(
        parsed.entityLocation.x,
        parsed.entityLocation.y,
        parsed.entityLocation.z,
        parsed.entityOrientation.psi,
        parsed.entityOrientation.theta,
        parsed.entityOrientation.phi,
    )
    assert rad2deg(body[0]) == pytest.approx(36.6, abs=1e-4)  # latitude
    assert rad2deg(body[1]) == pytest.approx(-121.9, abs=1e-4)  # longitude
    assert body[2] == pytest.approx(1.0, abs=0.5)  # altitude, meters


def test_example_receiver_reports_unknown_types(loopback):
    """A non-ESPDU datagram still parses and gets the one-line summary."""
    from opendis.record.warfare import FirePdu

    wire = FirePdu().to_bytes()
    loopback.sendto(wire, loopback.getsockname())
    received, _ = loopback.recvfrom(4096)

    assert received == wire
    assert "Received FirePdu, 96 bytes" in describe_datagram(received)
