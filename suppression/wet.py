"""Temporary wet-cell schedule derived from P179 drops.

This is a diagnostic threshold model: a cell is treated as non-ignitable while
its decaying water depth remains at or above a required depth. It is not a
validated ROS or fuel-moisture model.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .drop import DropContour, DropPattern, drop_to_pattern
from .effects import coverage_fraction
from .subcell import rasterize_pattern
from .models import EffectEvent, Scenario


@dataclass(frozen=True)
class WetDrop:
    """One drop footprint and its time window."""

    drop_id: str
    fraction: np.ndarray
    depth_mm: float
    start_min: float
    end_min: float
    duration_min: float
    mean_depth_grid_mm: np.ndarray | None = None
    canopy_penetration: float = 1.0

    @property
    def covered_cells(self) -> int:
        return int((self.fraction > 0.0).sum())

    def depth_at(self, row: int, col: int, time_min: float) -> float:
        if time_min < self.start_min or time_min > self.end_min + self.duration_min:
            return 0.0
        if time_min <= self.end_min:
            strength = self.depth_mm
        else:
            strength = self.depth_mm * max(
                0.0,
                1.0 - (time_min - self.end_min) / self.duration_min,
            )
        strength *= self.canopy_penetration
        if self.mean_depth_grid_mm is not None:
            return strength * float(self.mean_depth_grid_mm[row, col])
        return strength * float(self.fraction[row, col])


@dataclass(frozen=True)
class WetSchedule:
    """All drops that can suppress ignition on a grid."""

    required_depth_mm: float
    drops: tuple[WetDrop, ...]

    def wetness_at(self, row: int, col: int, time_min: float) -> float:
        depth = sum(drop.depth_at(row, col, time_min) for drop in self.drops)
        return max(0.0, min(1.0, depth / self.required_depth_mm))

    def ros_factor_at(self, row: int, col: int, time_min: float) -> float:
        """Diagnostic linear ROS factor: 1 dry, 0 at the required depth."""
        return 1.0 - self.wetness_at(row, col, time_min)

    def is_suppressed(self, row: int, col: int, time_min: float) -> bool:
        return self.wetness_at(row, col, time_min) >= 1.0

    def event_times(self) -> tuple[float, ...]:
        times: set[float] = set()
        for drop in self.drops:
            times.add(drop.start_min)
            times.add(drop.end_min)
            times.add(drop.end_min + drop.duration_min)
        return tuple(sorted(times))


def build_wet_schedule(
    scenario: Scenario,
    *,
    required_depth_mm: float,
    xll: float,
    yll: float,
    nrows: int,
    ncols: int,
    cell_size_m: float,
    subcell_cell_size_m: float | None = None,
) -> WetSchedule:
    """Rasterize scenario drops into a temporary wet-cell schedule."""
    if required_depth_mm <= 0.0:
        raise ValueError("required_depth_mm must be positive")
    drops: list[WetDrop] = []
    for drop in scenario.drops:
        if drop.coverage_l_m2 < required_depth_mm:
            continue
        pattern = drop_to_pattern(drop)
        contour = pattern.effective_contour(required_depth_mm)
        if contour is None:
            continue
        event = EffectEvent(
            effect_id=f"drop-{drop.id}",
            source_id=drop.id,
            kind=drop.suppressant.value,
            start_min=drop.start_min,
            end_min=drop.end_min,
            geometry=contour.geometry(drop.center),
            coverage_l_m2=drop.coverage_l_m2,
            decay_min=drop.effect_duration_min,
        )
        fraction = coverage_fraction(
            event.geometry,
            xll=xll,
            yll=yll,
            nrows=nrows,
            ncols=ncols,
            cell_size_m=cell_size_m,
        )
        if not (fraction > 0.0).any():
            continue
        mean_depth = None
        if subcell_cell_size_m is not None:
            raster = rasterize_pattern(
                pattern,
                drop.center,
                cell_size_m=subcell_cell_size_m,
                padding_cells=0,
            )
            mean_depth = raster.aggregate_mean(
                fire_xll=xll,
                fire_yll=yll,
                fire_nrows=nrows,
                fire_ncols=ncols,
                fire_cell_m=cell_size_m,
            )
        drops.append(
            WetDrop(
                drop_id=drop.id,
                fraction=fraction,
                depth_mm=drop.coverage_l_m2,
                start_min=drop.start_min,
                end_min=drop.end_min,
                duration_min=drop.effect_duration_min,
                mean_depth_grid_mm=mean_depth,
                canopy_penetration=drop.canopy_penetration,
            )
        )
    return WetSchedule(required_depth_mm=required_depth_mm, drops=tuple(drops))


__all__ = ["WetDrop", "WetSchedule", "build_wet_schedule"]
