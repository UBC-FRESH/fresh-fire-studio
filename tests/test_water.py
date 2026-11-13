from __future__ import annotations

import pytest

from suppression.water import (
    WaterRequirement,
    cooling_depth_mm,
    kcal_s_m_to_kw_m,
    kw_m2_to_kcal_m2_s,
    kw_m_to_kcal_s_m,
    quenching_depth_mm,
    required_depths,
    wetting_depth_mm,
)


@pytest.mark.parametrize(
    ("intensity_kw_m", "fuel_load", "radiant_kw_m2", "ros_m_min", "expected"),
    [
        (418.4, 1.25, 20.92, 1.33, (0.008, 0.28, 0.31)),
        (4184.0, 2.5, 41.84, 6.67, (0.038, 0.56, 0.57)),
        (41840.0, 5.0, 83.68, 33.3, (0.18, 1.13, 1.07)),
    ],
)
def test_van_wagner_table_3(
    intensity_kw_m: float,
    fuel_load: float,
    radiant_kw_m2: float,
    ros_m_min: float,
    expected: tuple[float, float, float],
) -> None:
    result = required_depths(intensity_kw_m, fuel_load, radiant_kw_m2, ros_m_min)
    assert result.quench_mm == pytest.approx(expected[0], abs=0.006)
    assert result.cool_mm == pytest.approx(expected[1], abs=0.006)
    assert result.wet_mm == pytest.approx(expected[2], abs=0.006)


def test_depth_scales_less_than_intensity() -> None:
    low = quenching_depth_mm(1_000.0)
    high = quenching_depth_mm(10_000.0)
    assert high / low == pytest.approx(10.0 ** (2.0 / 3.0), rel=1e-6)


def test_cooling_depth_depends_on_fuel_load() -> None:
    assert cooling_depth_mm(2.0) == pytest.approx(2.0 * cooling_depth_mm(1.0))


def test_wetting_uses_rate_and_radiant_intensity() -> None:
    base = wetting_depth_mm(4_184.0, 41.84, 6.67)
    faster = wetting_depth_mm(4_184.0, 41.84, 13.34)
    brighter = wetting_depth_mm(4_184.0, 83.68, 6.67)
    assert faster == pytest.approx(base / 2.0)
    assert brighter == pytest.approx(base * 2.0)


def test_application_efficiency_scales_required_depth() -> None:
    perfect = required_depths(4_184.0, 2.5, 41.84, 6.67)
    half = required_depths(
        4_184.0,
        2.5,
        41.84,
        6.67,
        application_efficiency=0.5,
    )
    assert isinstance(perfect, WaterRequirement)
    assert half.quench_mm == pytest.approx(perfect.quench_mm * 2.0)
    assert half.cool_mm == pytest.approx(perfect.cool_mm * 2.0)
    assert half.wet_mm == pytest.approx(perfect.wet_mm * 2.0)
    assert half.burning_mm == pytest.approx(perfect.burning_mm * 2.0)
    assert half.wetting_l_m2 == half.wet_mm


def test_unit_conversions_round_trip() -> None:
    assert kcal_s_m_to_kw_m(kw_m_to_kcal_s_m(4_184.0)) == pytest.approx(4_184.0)
    assert kw_m2_to_kcal_m2_s(41.84) == pytest.approx(10.0)


@pytest.mark.parametrize("value", [0.0, -1.0])
def test_invalid_positive_inputs(value: float) -> None:
    with pytest.raises(ValueError):
        quenching_depth_mm(value)
    with pytest.raises(ValueError):
        cooling_depth_mm(value)
    with pytest.raises(ValueError):
        wetting_depth_mm(4_184.0, 41.84, value)


def test_invalid_efficiency() -> None:
    with pytest.raises(ValueError):
        required_depths(4_184.0, 2.5, 41.84, 6.67, application_efficiency=0.0)
