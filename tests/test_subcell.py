from __future__ import annotations

import math

import pytest

from suppression.drop import DropContour, DropPattern, cl415_c2_full_pattern
from suppression.subcell import rasterize_pattern


GRID = dict(fire_xll=487700.0, fire_yll=5722700.0, fire_nrows=76, fire_ncols=90, fire_cell_m=100.0)


def test_subcell_raster_preserves_nested_depths() -> None:
    pattern = DropPattern(
        "CL-415",
        "C-2",
        "full",
        (DropContour(0.25, 130, 50), DropContour(0.5, 90, 40)),
    )
    raster = rasterize_pattern(pattern, (492150.0, 5726250.0), cell_size_m=10)
    assert raster.depth_mm.max() == 0.5
    assert raster.depth_mm.min() == 0.0
    assert raster.depth_mm.shape[0] >= 5
    assert raster.depth_mm.shape[1] >= 9


def test_aggregate_mean_and_coverage_are_spatially_local() -> None:
    pattern = cl415_c2_full_pattern(900)
    raster = rasterize_pattern(pattern, (492150.0, 5726250.0), cell_size_m=10)
    mean = raster.aggregate_mean(**GRID)
    coverage = raster.aggregate_coverage(**GRID)
    assert mean.max() > 0.0
    assert mean.max() < 0.5
    assert coverage.max() > 0.0
    assert (coverage > 0).sum() >= 1
    assert mean.sum() > 0.0


def test_aggregate_max_captures_deepest_layer() -> None:
    pattern = cl415_c2_full_pattern(900)
    raster = rasterize_pattern(pattern, (492150.0, 5726250.0), cell_size_m=10)
    maximum = raster.aggregate_max(**GRID)
    assert maximum.max() == pytest.approx(0.5)


def test_fire_cell_must_be_multiple_of_subcell() -> None:
    pattern = cl415_c2_full_pattern(900)
    raster = rasterize_pattern(pattern, (492150.0, 5726250.0), cell_size_m=10)
    with pytest.raises(ValueError, match="integer multiple"):
        raster.aggregate_mean(
            fire_xll=487700.0,
            fire_yll=5722700.0,
            fire_nrows=76,
            fire_ncols=90,
            fire_cell_m=15.0,
        )


def test_ellipse_area_matches_subcell_occupancy() -> None:
    pattern = DropPattern("CL-415", "C-2", "full", (DropContour(1.0, 100.0, 100.0),))
    raster = rasterize_pattern(pattern, (0.0, 0.0), cell_size_m=10, padding_cells=0)
    occupied = (raster.depth_mm > 0).sum()
    expected = math.pi / 4.0 * 100.0 * 100.0 / 100.0
    assert occupied == pytest.approx(expected, rel=0.05)
