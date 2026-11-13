from __future__ import annotations

import pytest

from suppression.water_balance import water_balance


def test_line_water_deficit() -> None:
    result = water_balance(
        line_length_m=5300.0,
        drop_length_m=100.0,
        drop_width_m=50.0,
        drop_count=21,
        delivered_l=126000.0,
        required_depth_mm=0.75,
    )
    assert result.target_area_m2 == 265000.0
    assert result.treated_area_m2 == 105000.0
    assert result.line_mean_depth_mm == pytest.approx(0.4755, abs=0.001)
    assert result.treated_mean_depth_mm == pytest.approx(1.2)
    assert result.coverage_fraction == pytest.approx(0.3962, abs=0.001)
    assert result.required_l == pytest.approx(198750.0)
    assert result.deficit_l == pytest.approx(72750.0)
    assert result.additional_sorties == 13


def test_no_deficit_when_delivery_exceeds_demand() -> None:
    result = water_balance(
        line_length_m=1000.0,
        drop_length_m=100.0,
        drop_width_m=50.0,
        drop_count=10,
        delivered_l=100000.0,
        required_depth_mm=0.5,
    )
    assert result.deficit_l == 0.0
    assert result.additional_sorties == 0
