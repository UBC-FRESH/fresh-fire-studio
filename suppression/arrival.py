"""Helpers for selecting drop targets from the active fire front."""

from __future__ import annotations

import numpy as np

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


__all__ = ["targets_at_time"]
