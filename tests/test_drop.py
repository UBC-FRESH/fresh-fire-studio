from __future__ import annotations

import math

import pytest

from suppression.drop import (
    DropContour,
    DropPattern,
    cl415_c2_full_effectiveness,
    cl415_c2_full_pattern,
    ellipse_geometry,
    is_breached,
)


def test_ellipse_geometry_is_closed_and_sized() -> None:
    points = ellipse_geometry((0.0, 0.0), 100.0, 40.0, segments=32)
    assert len(points) == 33
    assert points[0] == points[-1]
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    assert max(xs) == pytest.approx(50.0)
    assert min(xs) == pytest.approx(-50.0)
    assert max(ys) == pytest.approx(20.0)
    assert min(ys) == pytest.approx(-20.0)


def test_contour_area_and_stacking() -> None:
    contour = DropContour(0.75, 70.0, 30.0, uniform_fraction=0.33)
    assert contour.area_m2 == pytest.approx(math.pi / 4 * 70 * 30)
    assert contour.area_ha == pytest.approx(0.1649, abs=0.0001)
    assert contour.drops_to_uniform == 4


def test_effective_contour_is_smallest_sufficient_depth() -> None:
    pattern = DropPattern(
        "CL-415",
        "C-2",
        "full",
        (
            DropContour(0.25, 130, 50),
            DropContour(0.5, 90, 40),
            DropContour(1.5, 30, 20),
        ),
    )
    assert pattern.effective_contour(0.1).depth_mm == 0.25
    assert pattern.effective_contour(0.5).depth_mm == 0.5
    assert pattern.effective_contour(0.75).depth_mm == 1.5
    assert pattern.effective_contour(2.0) is None


def test_pattern_ordering_is_validated() -> None:
    with pytest.raises(ValueError, match="ordered"):
        DropPattern(
            "CL-415",
            "C-2",
            "full",
            (DropContour(0.5, 90, 40), DropContour(0.25, 130, 50)),
        )


def test_effect_events_keep_depth_layers() -> None:
    pattern = DropPattern(
        "CL-415",
        "C-2",
        "full",
        (DropContour(0.25, 130, 50), DropContour(1.5, 30, 20)),
    )
    events = pattern.to_effect_events(
        (100.0, 200.0),
        start_min=10,
        end_min=20,
        effect_duration_min=8,
    )
    assert len(events) == 2
    assert [event.coverage_l_m2 for event in events] == [0.25, 1.5]
    assert all(event.kind == "water" for event in events)
    assert all(event.start_min == 10 and event.end_min == 20 for event in events)
    assert all(len(event.geometry) > 12 for event in events)


def test_breach_uses_half_drop_width() -> None:
    assert not is_breached(flame_length_m=14, flame_front_depth_m=14, drop_width_m=30)
    assert is_breached(flame_length_m=16, flame_front_depth_m=10, drop_width_m=30)
    assert is_breached(flame_length_m=10, flame_front_depth_m=16, drop_width_m=30)


@pytest.mark.parametrize(
    ("intensity", "depth", "length", "width", "drops"),
    [
        (10, 0.25, 130, 50, 1),
        (900, 0.5, 90, 40, 1),
        (1_300, 0.75, 70, 30, 2),
    ],
)
def test_cl415_c2_full_catalog(
    intensity: float, depth: float, length: float, width: float, drops: int
) -> None:
    row = cl415_c2_full_effectiveness(intensity)
    assert row.required_depth_mm == depth
    assert row.effective_length_m == length
    assert row.effective_width_m == width
    assert row.drops_to_hold_100m == drops
    assert not row.breached
    pattern = cl415_c2_full_pattern(intensity)
    assert pattern.deepest.depth_mm == depth


def test_cl415_breaches_above_1300() -> None:
    row = cl415_c2_full_effectiveness(3_200)
    assert row.breached
    assert row.effective_length_m is None
    assert row.effective_area_ha is None
