"""Time-aware P179 suppression effects.

The P179.0 scenario is a schedule: lines are constructed, held, breached or
abandoned, and drops decay. This module turns that schedule into effect masks
at a requested simulation time. It does not advance fire growth by itself.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .effects import RasterEffects, rasterize_effects
from .models import Drop, EffectEvent, Line, LineState, Scenario, Suppressant


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def line_fraction_at(line: Line, t: float) -> float:
    """Return the fraction of a line that exists at time ``t``.

    Lines under construction grow linearly by length. A held line remains after
    construction. A breached or abandoned line stops providing containment
    once construction ends. A planned line never exists.
    """
    if line.state == LineState.PLANNED:
        return 0.0
    if t < line.constructed_start_min:
        return 0.0
    if line.constructed_end_min <= line.constructed_start_min:
        fraction = 1.0
    else:
        fraction = _clamp(
            (t - line.constructed_start_min)
            / (line.constructed_end_min - line.constructed_start_min)
        )
    if t >= line.constructed_end_min and line.state in {
        LineState.BREACHED,
        LineState.ABANDONED,
    }:
        return 0.0
    return fraction


def partial_line(points: list[tuple[float, float]], fraction: float) -> list[tuple[float, float]]:
    """Return the first ``fraction`` of a polyline by length."""
    if fraction <= 0.0 or len(points) < 2:
        return []
    if fraction >= 1.0:
        return list(points)
    lengths = [
        math.hypot(second[0] - first[0], second[1] - first[1])
        for first, second in zip(points, points[1:])
    ]
    target = sum(lengths) * fraction
    result = [points[0]]
    traveled = 0.0
    for (start, end), length in zip(zip(points, points[1:]), lengths):
        if length <= 0.0:
            continue
        if traveled + length >= target:
            remaining = (target - traveled) / length
            result.append(
                (
                    start[0] + (end[0] - start[0]) * remaining,
                    start[1] + (end[1] - start[1]) * remaining,
                )
            )
            return result
        traveled += length
        result.append(end)
    return result


def line_effect_at(line: Line, t: float) -> EffectEvent | None:
    """Return the active line effect at time ``t``, if any."""
    fraction = line_fraction_at(line, t)
    if fraction <= 0.0:
        return None
    geometry = partial_line(line.points, fraction)
    if len(geometry) < 2:
        return None
    return EffectEvent(
        effect_id=f"line-{line.id}",
        source_id=line.id,
        kind="line",
        start_min=line.constructed_start_min,
        end_min=line.constructed_end_min,
        geometry=geometry,
        width_m=line.width_m,
        fuel_removed=line.fuel_removed,
        moisture=line.moisture,
        strength=1.0,
    )


def drop_strength_at(drop: Drop, t: float) -> float:
    """Return the linear decayed drop strength at time ``t``."""
    if t < drop.start_min or t > drop.end_min + drop.effect_duration_min:
        return 0.0
    if t <= drop.end_min:
        return drop.canopy_penetration
    return drop.canopy_penetration * _clamp(
        1.0 - (t - drop.end_min) / drop.effect_duration_min
    )


def drop_effect_at(drop: Drop, t: float) -> EffectEvent | None:
    """Return the active drop effect at time ``t``, if any."""
    strength = drop_strength_at(drop, t)
    if strength <= 0.0:
        return None
    x, y = drop.center
    half_l, half_w = drop.length_m / 2, drop.width_m / 2
    return EffectEvent(
        effect_id=f"drop-{drop.id}",
        source_id=drop.id,
        kind=drop.suppressant.value,
        start_min=drop.start_min,
        end_min=drop.end_min,
        geometry=[
            (x - half_l, y - half_w),
            (x + half_l, y - half_w),
            (x + half_l, y + half_w),
            (x - half_l, y + half_w),
        ],
        coverage_l_m2=drop.coverage_l_m2,
        strength=strength,
        decay_min=drop.effect_duration_min,
    )


def active_events(scenario: Scenario, t: float) -> list[EffectEvent]:
    """Return all line and drop effects active at time ``t``."""
    events: list[EffectEvent] = []
    for line in scenario.lines:
        event = line_effect_at(line, t)
        if event is not None:
            events.append(event)
    for drop in scenario.drops:
        event = drop_effect_at(drop, t)
        if event is not None:
            events.append(event)
    return events


def effects_at(
    scenario: Scenario,
    t: float,
    *,
    xll: float,
    yll: float,
    nrows: int,
    ncols: int,
    cell_size_m: float,
) -> RasterEffects:
    """Rasterize all active suppression effects at time ``t``."""
    return rasterize_effects(
        active_events(scenario, t),
        xll=xll,
        yll=yll,
        nrows=nrows,
        ncols=ncols,
        cell_size_m=cell_size_m,
    )


def timeline_breaks(scenario: Scenario) -> tuple[float, ...]:
    """Return unique times at which the effect field can change."""
    times = {scenario.timeline_start_min, scenario.timeline_end_min}
    for line in scenario.lines:
        times.add(line.constructed_start_min)
        times.add(line.constructed_end_min)
    for drop in scenario.drops:
        times.add(drop.start_min)
        times.add(drop.end_min)
        times.add(drop.end_min + drop.effect_duration_min)
    return tuple(sorted(t for t in times if scenario.timeline_start_min <= t <= scenario.timeline_end_min))


def line_cells_at(
    scenario: Scenario,
    t: float,
    *,
    xll: float,
    yll: float,
    nrows: int,
    ncols: int,
    cell_size_m: float,
) -> int:
    """Return the number of containment cells at time ``t``."""
    return int(
        effects_at(
            scenario,
            t,
            xll=xll,
            yll=yll,
            nrows=nrows,
            ncols=ncols,
            cell_size_m=cell_size_m,
        ).containment.sum()
    )


__all__ = [
    "active_events",
    "drop_effect_at",
    "drop_strength_at",
    "effects_at",
    "line_cells_at",
    "line_effect_at",
    "line_fraction_at",
    "partial_line",
    "timeline_breaks",
]
