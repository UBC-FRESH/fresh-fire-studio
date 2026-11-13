"""Prototype native time-dependent containment for the WS4 growth kernel.

The WS4 P177 kernel accepts a static burnable mask. This module adapts its
minimum-travel-time loop so that a cell can become contained or un-contained at
a specific simulated time. It is intentionally narrow: no spotting, wind grids
or burning-condition gates yet.
"""

from __future__ import annotations

import bisect
import heapq
import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from .effects import rasterize_effects
from .models import LineState, Scenario
from .temporal import line_effect_at
from .wet import WetSchedule


@dataclass(frozen=True)
class ContainmentSchedule:
    """Earliest containment start and end time for each grid cell."""

    start_min: np.ndarray
    end_min: np.ndarray

    def __post_init__(self) -> None:
        if self.start_min.shape != self.end_min.shape:
            raise ValueError("containment start and end grids must have the same shape")

    @property
    def shape(self) -> tuple[int, int]:
        return self.start_min.shape  # type: ignore[return-value]

    def is_contained(self, row: int, col: int, time_min: float) -> bool:
        return bool(self.start_min[row, col] <= time_min < self.end_min[row, col])

    def is_burnable(self, base_burnable: np.ndarray, row: int, col: int, time_min: float) -> bool:
        return bool(base_burnable[row, col]) and not self.is_contained(row, col, time_min)


def build_containment_schedule(
    scenario: Scenario,
    *,
    xll: float,
    yll: float,
    nrows: int,
    ncols: int,
    cell_size_m: float,
    step_min: float = 60.0,
) -> ContainmentSchedule:
    """Rasterize each line into per-cell containment start/end times.

    Construction is sampled at ``step_min``. A held line remains active to the
    end of the scenario; a breached line ends at ``breached_at_min``; an
    abandoned line ends when construction ends.
    """
    if step_min <= 0:
        raise ValueError("step_min must be positive")
    start = np.full((nrows, ncols), np.inf, dtype=float)
    end = np.full((nrows, ncols), np.inf, dtype=float)
    for line in scenario.lines:
        if line.state == LineState.PLANNED:
            continue
        if line.state == LineState.BREACHED:
            effective_end = (
                line.breached_at_min
                if line.breached_at_min is not None
                else line.constructed_end_min
            )
        elif line.state == LineState.ABANDONED:
            effective_end = line.constructed_end_min
        else:
            effective_end = scenario.timeline_end_min
        full_event = line_effect_at(line, line.constructed_end_min)
        if full_event is None:
            continue
        full = rasterize_effects(
            [full_event],
            xll=xll,
            yll=yll,
            nrows=nrows,
            ncols=ncols,
            cell_size_m=cell_size_m,
        ).line
        if not full.any():
            continue
        end[full] = np.minimum(end[full], effective_end)
        samples = {line.constructed_start_min, line.constructed_end_min}
        sample = line.constructed_start_min
        while sample < line.constructed_end_min:
            samples.add(sample)
            sample += step_min
        for sample in sorted(samples):
            event = line_effect_at(line, sample)
            if event is None:
                continue
            mask = rasterize_effects(
                [event],
                xll=xll,
                yll=yll,
                nrows=nrows,
                ncols=ncols,
                cell_size_m=cell_size_m,
            ).line
            newly = mask & ~np.isfinite(start)
            start[newly] = sample
        # Cells that first appear at the final sample still have a start time.
        start[full & ~np.isfinite(start)] = line.constructed_end_min
    return ContainmentSchedule(start_min=start, end_min=end)


def _line_is_burnable_at(
    schedule: ContainmentSchedule,
    base_burnable: np.ndarray,
    row: int,
    col: int,
    drow: int,
    dcol: int,
    time_min: float,
    wet_schedule: WetSchedule | None = None,
) -> bool:
    steps = max(abs(drow), abs(dcol))
    for step in range(1, steps):
        middle_row = row + round(drow * step / steps)
        middle_col = col + round(dcol * step / steps)
        if not schedule.is_burnable(base_burnable, middle_row, middle_col, time_min):
            return False
        if wet_schedule is not None and wet_schedule.is_suppressed(
            middle_row, middle_col, time_min
        ):
            return False
    return True


def grow_fire_with_containment(
    grid: Any,
    config: Any,
    schedule: ContainmentSchedule,
    wet_schedule: WetSchedule | None = None,
) -> Any:
    """Run a minimum-travel-time growth with a native containment schedule.

    This mirrors the P177 time-dependent loop but consults ``schedule`` at each
    cell expansion. It currently supports the plain FBP path only.
    """
    if config.weather_steps is None:
        raise ValueError("native containment growth requires weather_steps")
    if config.spotting is not None:
        raise NotImplementedError("native containment growth does not support spotting")
    if config.wind_grids is not None:
        raise NotImplementedError("native containment growth does not support wind_grids")
    if config.burning_conditions is not None:
        raise NotImplementedError(
            "native containment growth does not support burning-condition gates"
        )

    from ws4.fire.growth import (
        GrowthConfig,
        GrowthResult,
        GrowthSnapshot,
        _area_and_perimeter,
        _cell_behaviour,
        _dynamic_arrival,
        _local_behaviour,
        _neighbor_offsets,
    )

    if not isinstance(config, GrowthConfig):
        raise TypeError("config must be a ws4 GrowthConfig")
    steps = config.weather_steps
    starts = [step.start_min for step in steps]
    burnable = np.asarray(grid.burnable, dtype=bool)
    if schedule.shape != burnable.shape:
        raise ValueError("containment schedule shape must match the grid")
    summary_head, summary_lb, summary_az, representative = _local_behaviour(
        grid,
        wind_multiplier=config.wind_multiplier,
        head_ros_multiplier=config.head_ros_multiplier,
    )
    active = burnable & (summary_head > 0.0)
    if not bool(active.any()):
        raise ValueError("grid has no burnable fuel cells with a positive rate of spread")
    cache: dict[tuple[int, int, int], tuple[float, float, Any] | None] = {}

    def behaviour(row: int, col: int, index: int) -> tuple[float, float, Any] | None:
        key = (row, col, index)
        if key in cache:
            return cache[key]
        step = steps[index]
        wind_kmh = step.wind_kmh
        wind_direction = step.wind_direction_deg
        patch_active = (
            config.wind_patch_end_min is None or step.start_min < config.wind_patch_end_min
        )
        if patch_active and grid.wind_direction_patch is not None:
            patch = float(grid.wind_direction_patch[row, col])
            if np.isfinite(patch):
                wind_direction = patch
        value = _cell_behaviour(
            grid,
            row,
            col,
            grid.ffmc if step.ffmc is None else step.ffmc,
            grid.bui if step.bui is None else step.bui,
            wind_kmh,
            wind_direction,
            wind_multiplier=config.wind_multiplier,
            head_ros_multiplier=config.head_ros_multiplier,
        )
        cache[key] = value
        return value

    ignition = np.full((grid.rows, grid.cols), np.inf, dtype=float)
    def available(row: int, col: int, time_min: float) -> bool:
        return schedule.is_burnable(burnable, row, col, time_min)

    def wet_ros_factor(row: int, col: int, time_min: float) -> float:
        if wet_schedule is None:
            return 1.0
        return wet_schedule.ros_factor_at(row, col, time_min)

    queue: list[tuple[float, int, int, bool]] = []
    for row, col in config.ignition_cells:
        if not available(row, col, 0.0):
            raise ValueError(f"ignition cell ({row}, {col}) is contained or unburnable at t=0")
        ignition[row, col] = 0.0
        heapq.heappush(queue, (0.0, row, col, False))
    offsets = _neighbor_offsets(config.allow_diagonal, config.neighbor_radius)

    event_values = {
        float(value)
        for value in np.concatenate((schedule.start_min.ravel(), schedule.end_min.ravel()))
        if np.isfinite(value) and 0.0 < value < config.max_time_min
    }
    if wet_schedule is not None:
        event_values.update(
            value for value in wet_schedule.event_times() if 0.0 < value < config.max_time_min
        )
    event_times = sorted(event_values)
    for event_time in event_times:
        heapq.heappush(queue, (event_time, -1, -1, True))

    def push_front(event_time: float) -> None:
        """Re-expand burned boundary cells after a containment change."""
        burned = ignition <= event_time + 1e-12
        for row, col in np.argwhere(burned):
            if not available(int(row), int(col), event_time):
                continue
            reaches_unburned = False
            for drow, dcol in offsets:
                nrow = int(row) + drow
                ncol = int(col) + dcol
                if nrow < 0 or nrow >= grid.rows or ncol < 0 or ncol >= grid.cols:
                    continue
                if (
                    available(nrow, ncol, event_time)
                    and not np.isfinite(ignition[nrow, ncol])
                ):
                    reaches_unburned = True
                    break
            if reaches_unburned:
                heapq.heappush(queue, (event_time, int(row), int(col), True))

    while queue:
        time, row, col, is_source = heapq.heappop(queue)
        if row < 0:
            push_front(time)
            continue
        if time > config.max_time_min:
            break
        if not is_source and time > ignition[row, col] + 1e-12:
            continue
        if not available(row, col, time) or wet_ros_factor(row, col, time) <= 0.0:
            continue
        step_index = max(0, bisect.bisect_right(starts, time) - 1)
        for drow, dcol in offsets:
            nrow = row + drow
            ncol = col + dcol
            if nrow < 0 or nrow >= grid.rows or ncol < 0 or ncol >= grid.cols:
                continue
            if not available(nrow, ncol, time):
                continue
            if not _line_is_burnable_at(
                schedule, burnable, row, col, drow, dcol, time, wet_schedule
            ):
                continue
            distance = grid.cell_size_m * math.hypot(drow, dcol)
            direction = math.degrees(math.atan2(dcol, -drow)) % 360.0
            arrival = _dynamic_arrival(
                behaviour,
                steps,
                starts,
                row,
                col,
                distance,
                direction,
                time,
                step_index,
            )
            factor = wet_ros_factor(nrow, ncol, time)
            if math.isfinite(arrival) and factor > 0.0:
                arrival = time + (arrival - time) / factor
            if (
                math.isfinite(arrival)
                and factor > 0.0
                and arrival <= config.max_time_min
                and arrival < ignition[nrow, ncol] - 1e-12
            ):
                ignition[nrow, ncol] = arrival
                heapq.heappush(queue, (arrival, nrow, ncol, False))

    snapshots: list[Any] = []
    value = 0.0
    while value <= config.max_time_min + 1e-9:
        burned = ignition <= value + 1e-12
        area, perimeter = _area_and_perimeter(burned, grid)
        snapshots.append(
            GrowthSnapshot(
                time_min=value,
                burned_cells=int(burned.sum()),
                area_ha=area,
                perimeter_m=perimeter,
            )
        )
        value += config.snapshot_interval_min
    final = snapshots[-1] if snapshots else GrowthSnapshot(0.0, 0, 0.0, 0.0)
    return GrowthResult(
        grid=grid,
        config=config,
        ignition_time_min=ignition,
        snapshots=tuple(snapshots),
        burned_area_ha=final.area_ha,
        perimeter_m=final.perimeter_m,
        effective_wind=representative,
        head_ros_m_min=float(np.mean(summary_head[active])),
        length_to_breadth=float(np.mean(summary_lb[active])),
        head_ros_grid=summary_head,
        length_to_breadth_grid=summary_lb,
        spread_azimuth_deg_grid=summary_az,
        spot_ignitions=(),
    )


__all__ = [
    "ContainmentSchedule",
    "build_containment_schedule",
    "grow_fire_with_containment",
]
