"""Geodetic conversion properties (GPS class).

Round-trip identities and structural invariants only — no reference
coordinates from external sources. Note the unit contract discovered
while writing these: ``llarpy2ecef`` consumes radians (its inverse
``ecef2llarpy`` returns radians), while ``lla2ecef``/``ecef2lla``
take/return degrees.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

import opendis.RangeCoordinates as rc
from opendis.RangeCoordinates import GPS

gps = GPS()

# (lat deg, lon deg, alt m) spread over hemispheres and longitudes
LLA_SAMPLES = [
    (0.0, 0.0, 0.0),
    (35.6762, 139.6503, 40.0),
    (-33.8688, 151.2093, 58.0),
    (-77.8419, 166.6863, 10.0),
    (80.1234, -45.6, 1000.0),
    (0.5, -179.75, 25.0),
]


@pytest.mark.parametrize("lat,lon,alt", LLA_SAMPLES)
def test_lla_ecef_round_trip(lat: float, lon: float, alt: float) -> None:
    ecef = gps.lla2ecef((lat, lon, alt))
    back = gps.ecef2lla(ecef)
    assert np.allclose(back, (lat, lon, alt), atol=1e-6)


@pytest.mark.parametrize("lat,lon,alt", LLA_SAMPLES)
def test_ecef_z_sign_matches_hemisphere(lat: float, lon: float, alt: float) -> None:
    """Northern latitudes must produce positive ECEF Z (axis convention)."""
    x, y, z = gps.lla2ecef((lat, lon, alt))
    assert np.sign(z) == np.sign(lat) if lat != 0 else True


@pytest.mark.parametrize(
    "lat,lon,alt,roll,pitch,yaw",
    [(35.0, 139.0, 100.0, 0.1, -0.2, 0.3), (-10.0, -75.0, 0.0, 0.0, 0.0, 0.0)],
)
def test_llarpy_ecef_position_round_trip(lat, lon, alt, roll, pitch, yaw) -> None:
    """llarpy2ecef takes radians; position must survive the inverse."""
    vec = gps.llarpy2ecef(math.radians(lat), math.radians(lon), alt, roll, pitch, yaw)
    assert len(vec) == 6
    back = gps.ecef2llarpy(vec[0], vec[1], vec[2], 0.0, 0.0, 0.0)
    # the llarpy path carries ~1e-5 m altitude round-off at some sites
    assert np.allclose(back[:3], (math.radians(lat), math.radians(lon), alt), atol=1e-3)


@pytest.mark.parametrize("lat,lon", [(s[0], s[1]) for s in LLA_SAMPLES])
def test_ecefvec2nedvec_rotation_is_orthonormal(lat: float, lon: float) -> None:
    rot = gps.ecefvec2nedvec(lat, lon)
    assert np.allclose(rot @ rot.T, np.eye(3), atol=1e-9)
    assert np.isclose(np.linalg.det(rot), 1.0)


def test_ned_ecef_round_trip() -> None:
    origin = (35.0, 139.0, 0.0)
    ned = np.array([100.0, -50.0, 20.0])
    ecef = gps.ned2ecef(ned, origin)
    back = gps.ecef2ned(ecef, origin)
    assert np.allclose(back, ned, atol=1e-6)


def test_lla2utm_zone_and_ranges() -> None:
    for lat, lon, _alt in LLA_SAMPLES:
        utm, info = gps.lla2utm((lat, lon, 0.0))
        easting, northing = utm[0], utm[1]
        assert np.isfinite(easting) and np.isfinite(northing)
        assert 100_000 < easting < 1_000_000
        # southern sites report negative northing (raw TM y, no false
        # northing); magnitude stays below the 10,000,000 m grid maximum
        assert -10_000_000 < northing < 10_000_000
        if lat != 0:
            assert np.sign(northing) == np.sign(lat)
        # info[0] packs "<zone><band>", e.g. "54S"; zone follows the
        # documented 6-degree band formula
        zone = int("".join(c for c in info[0] if c.isdigit()))
        assert 1 <= zone <= 60
        assert zone == int((lon + 180) // 6) + 1


def test_utm_letter_designator_bands() -> None:
    assert gps.utmLetterDesignator(-80) == "C"  # southernmost band
    assert gps.utmLetterDesignator(0) == "N"  # equator starts band N
    assert gps.utmLetterDesignator(45) == "T"
    letters = {gps.utmLetterDesignator(lat) for lat in range(-80, 84, 8)}
    assert "I" not in letters and "O" not in letters  # reserved letters skipped


def test_rotate_3x3_zero_angle_is_identity() -> None:
    rot = gps.rotate_3x3(0.0, np.array([0.0, 0.0, 1.0]))
    assert np.allclose(rot, np.eye(3))


def test_deg_rad_conversions() -> None:
    assert math.isclose(rc.deg2rad(180.0), math.pi)
    assert math.isclose(rc.rad2deg(math.pi / 2), 90.0)
