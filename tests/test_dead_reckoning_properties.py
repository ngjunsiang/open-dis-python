"""Dead-reckoning math: model-independent invariants.

The eight DRM functions (f/r × p/v × w/b) and the two matrix helpers had
untested bodies. Every assertion here is a property that must hold for
any dead-reckoning model regardless of frame convention: with an
identity orientation, body and world frames coincide, so the linear
update reduces to plain kinematics and orientation changes only via
angular velocity. No scenario data is needed.
"""

from __future__ import annotations

import numpy as np
import pytest

from opendis import DeadReckoning as dr

POSITION = np.array([100.0, -200.0, 300.0])
VELOCITY = np.array([1.0, 2.0, -3.0])
ACCELERATION = np.array([0.5, -0.25, 1.0])
OMEGA = np.array([0.1, -0.2, 0.3])
IDENTITY_ORIENTATION = (0.0, 0.0, 0.0)
DT = 1.5

# (model, takes_acceleration, takes_angular_velocity)
MODELS = [
    (dr.drm_fpw, False, False),
    (dr.drm_fpb, False, False),
    (dr.drm_fvw, True, False),
    (dr.drm_fvb, True, False),
    (dr.drm_rpw, False, True),
    (dr.drm_rpb, False, True),
    (dr.drm_rvw, True, True),
    (dr.drm_rvb, True, True),
]


def _run(model, accel: bool, omega: bool, v, a, w, dt=DT):
    args = [POSITION, v, dt, IDENTITY_ORIENTATION]
    if accel:
        args.insert(2, a)
    if omega:
        args.append(w)
    return model(*args)


@pytest.mark.parametrize(
    "model,accel,omega", MODELS, ids=lambda m: getattr(m, "__name__", m)
)
def test_zero_motion_is_identity(model, accel: bool, omega: bool) -> None:
    new_pos, new_ori = _run(
        model,
        accel,
        omega,
        v=(0.0, 0.0, 0.0),
        a=(0.0, 0.0, 0.0),
        w=(0.0, 0.0, 0.0),
    )
    assert np.allclose(new_pos, POSITION)
    assert np.allclose(new_ori, 0.0)


@pytest.mark.parametrize(
    "model,accel,omega", MODELS, ids=lambda m: getattr(m, "__name__", m)
)
def test_constant_velocity_translation(model, accel: bool, omega: bool) -> None:
    new_pos, new_ori = _run(
        model,
        accel,
        omega,
        v=VELOCITY,
        a=(0.0, 0.0, 0.0),
        w=(0.0, 0.0, 0.0),
    )
    assert np.allclose(new_pos, POSITION + VELOCITY * DT)
    assert np.allclose(new_ori, 0.0)


@pytest.mark.parametrize(
    "model,accel,omega",
    [m for m in MODELS if m[1]],
    ids=lambda m: getattr(m, "__name__", m),
)
def test_acceleration_kinematics(model, accel: bool, omega: bool) -> None:
    new_pos, _ = _run(model, accel, omega, v=VELOCITY, a=ACCELERATION, w=(0, 0, 0))
    expected = POSITION + VELOCITY * DT + 0.5 * ACCELERATION * DT**2
    assert np.allclose(new_pos, expected)


@pytest.mark.parametrize(
    "model,accel,omega",
    [m for m in MODELS if m[2]],
    ids=lambda m: getattr(m, "__name__", m),
)
def test_pure_rotation_keeps_position(model, accel: bool, omega: bool) -> None:
    new_pos, _ = _run(
        model, accel, omega, v=(0.0, 0.0, 0.0), a=(0.0, 0.0, 0.0), w=OMEGA
    )
    assert np.allclose(new_pos, POSITION)


def test_drm_static_returns_inputs_unchanged() -> None:
    pos, ori = dr.drm_static(POSITION, (0.1, 0.2, 0.3))
    assert np.allclose(pos, POSITION)
    assert np.allclose(ori, (0.1, 0.2, 0.3))


def test_rotation_matrix_properties() -> None:
    zero = dr.get_rotation_matrix(0.0, 0.0, 0.0)
    assert np.allclose(zero, np.eye(3))
    for angles in [(0.3, 0.1, 0.2), (-1.0, 0.5, 0.0), (0.0, -0.7, 2.0)]:
        rot = dr.get_rotation_matrix(*angles)
        assert np.allclose(rot @ rot.T, np.eye(3), atol=1e-12)
        assert np.isclose(np.linalg.det(rot), 1.0)


def test_angular_velocity_matrix_is_skew_cross_product() -> None:
    skew = dr.get_angular_velocity_matrix(OMEGA)
    assert np.allclose(skew + skew.T, 0.0)
    for vec in [np.array([1.0, 0.0, 0.0]), np.array([0.3, -2.0, 5.0])]:
        assert np.allclose(skew @ vec, np.cross(OMEGA, vec))
