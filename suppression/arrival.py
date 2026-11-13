"""Helpers for selecting drop targets from the active fire front."""

from __future__ import annotations

import numpy as np

from math import hypot

from .perimeter import front_target_cells


def targets_at_time(
    ignition_time_min: np.ndarray,
    burnable: np.ndarray,
    *,
    time_min: float,
    count: int,
    xll: float,
    yll: float,
    nrows: int,
    cell_size_m: float,
) -> tuple[tuple[float, float], ...]:
    """Select up to ``count`` unburned front cells at a simulation time."""
    if count < 1:
        raise ValueError("count must be at least 1")
    burned = np.asarray(ignition_time_min) <= time_min
    cells = front_target_cells(burned, burnable)
    if not cells:
        return ()
    # Prefer eastern/head-facing cells, then north-to-south.
    cells = tuple(sorted(cells, key=lambda item: (item[1], -item[0]), reverse=True))
    selected = cells[:count]
    return tuple(
        (
            xll + (col + 0.5) * cell_size_m,
            yll + (nrows - 1 - row + 0.5) * cell_size_m,
        )
        for row, col in selected
    )


def resample_polyline(
    points: tuple[tuple[float, float], ...] | list[tuple[float, float]],
    *,
    spacing_m: float,
) -> tuple[tuple[float, float], ...]:
    """Resample a polyline at approximately uniform spacing."""
    if spacing_m <= 0.0:
        raise ValueError("spacing_m must be positive")
    if len(points) < 2:
        raise ValueError("at least two points are required")
    lengths = [hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(points, points[1:])]
    total = sum(lengths)
    count = max(2, int(total // spacing_m) + 1)
    result = [tuple(points[0])]
    segment = 0
    segment_start = points[0]
    segment_length = lengths[0]
    traveled = 0.0
    for index in range(1, count - 1):
        target = total * index / (count - 1)
        while segment < len(lengths) - 1 and target > traveled + segment_length:
            traveled += segment_length
            segment += 1
            segment_start = points[segment]
            segment_length = lengths[segment]
        fraction = 0.0 if segment_length == 0 else (target - traveled) / segment_length
        result.append(
            (
                segment_start[0] + (points[segment + 1][0] - segment_start[0]) * fraction,
                segment_start[1] + (points[segment + 1][1] - segment_start[1]) * fraction,
            )
        )
    result.append(tuple(points[-1]))
    return tuple(result)


__all__ = ["resample_polyline", "targets_at_time"]
