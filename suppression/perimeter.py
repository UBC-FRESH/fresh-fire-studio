"""Small perimeter-query helpers for drop placement.

These helpers identify active perimeter cells and a leading-edge band. They do
not choose a suppression tactic; a mission policy must still decide where to
place drops.
"""

from __future__ import annotations

import numpy as np


def perimeter_mask(
    burned: np.ndarray,
    burnable: np.ndarray | None = None,
) -> np.ndarray:
    """Return burned cells with at least one four-neighbour unburned cell."""
    burned = np.asarray(burned, dtype=bool)
    if burned.ndim != 2:
        raise ValueError("burned must be two-dimensional")
    if burnable is not None:
        burnable = np.asarray(burnable, dtype=bool)
        if burnable.shape != burned.shape:
            raise ValueError("burnable must have the same shape as burned")
        burned = burned & burnable
    padded = np.pad(burned, 1, constant_values=False)
    interior = (
        padded[:-2, 1:-1]
        & padded[2:, 1:-1]
        & padded[1:-1, :-2]
        & padded[1:-1, 2:]
    )
    return burned & ~interior


def perimeter_cells(
    burned: np.ndarray,
    burnable: np.ndarray | None = None,
) -> tuple[tuple[int, int], ...]:
    """Return perimeter cells as ``(row, col)`` pairs."""
    return tuple((int(row), int(col)) for row, col in np.argwhere(perimeter_mask(burned, burnable)))


def leading_edge_cells(
    burned: np.ndarray,
    burnable: np.ndarray | None = None,
    *,
    direction: str = "east",
    band_m: float,
    cell_size_m: float,
) -> tuple[tuple[int, int], ...]:
    """Return perimeter cells in a band at the leading edge.

    ``direction`` is one of ``east``, ``west``, ``north`` or ``south``. North is
    decreasing row index, matching the north-up fire grid.
    """
    if band_m < 0.0:
        raise ValueError("band_m must be non-negative")
    if cell_size_m <= 0.0:
        raise ValueError("cell_size_m must be positive")
    cells = perimeter_cells(burned, burnable)
    if not cells:
        return ()
    rows = np.array([cell[0] for cell in cells])
    cols = np.array([cell[1] for cell in cells])
    if direction == "east":
        threshold = cols.max() - band_m / cell_size_m
        keep = cols >= threshold
    elif direction == "west":
        threshold = cols.min() + band_m / cell_size_m
        keep = cols <= threshold
    elif direction == "north":
        threshold = rows.min() + band_m / cell_size_m
        keep = rows <= threshold
    elif direction == "south":
        threshold = rows.max() - band_m / cell_size_m
        keep = rows >= threshold
    else:
        raise ValueError("direction must be east, west, north or south")
    return tuple(cells[index] for index in np.where(keep)[0])


def cells_to_centers(
    cells: tuple[tuple[int, int], ...],
    *,
    xll: float,
    yll: float,
    nrows: int,
    cell_size_m: float,
) -> tuple[tuple[float, float], ...]:
    """Convert row/col cells to projected cell centers."""
    return tuple(
        (
            xll + (col + 0.5) * cell_size_m,
            yll + (nrows - 1 - row + 0.5) * cell_size_m,
        )
        for row, col in cells
    )


__all__ = [
    "cells_to_centers",
    "leading_edge_cells",
    "perimeter_cells",
    "perimeter_mask",
]
