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


def front_target_cells(
    burned: np.ndarray,
    burnable: np.ndarray | None = None,
) -> tuple[tuple[int, int], ...]:
    """Return unburned burnable cells adjacent to the active perimeter."""
    burned = np.asarray(burned, dtype=bool)
    if burnable is None:
        burnable = np.ones_like(burned, dtype=bool)
    else:
        burnable = np.asarray(burnable, dtype=bool)
        if burnable.shape != burned.shape:
            raise ValueError("burnable must have the same shape as burned")
    targets: set[tuple[int, int]] = set()
    rows, cols = burned.shape
    for row, col in perimeter_cells(burned, burnable):
        for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nrow, ncol = row + drow, col + dcol
            if 0 <= nrow < rows and 0 <= ncol < cols and not burned[nrow, ncol] and burnable[nrow, ncol]:
                targets.add((nrow, ncol))
    return tuple(sorted(targets))


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


def closed_box_centers(
    cells: tuple[tuple[int, int], ...],
    *,
    xll: float,
    yll: float,
    nrows: int,
    cell_size_m: float,
    margin_m: float,
    spacing_m: float,
) -> tuple[tuple[float, float], ...]:
    """Return drop centers along a closed rectangle around the perimeter."""
    if not cells:
        return ()
    if margin_m < 0.0 or spacing_m <= 0.0:
        raise ValueError("margin_m must be non-negative and spacing_m positive")
    centers = cells_to_centers(
        cells,
        xll=xll,
        yll=yll,
        nrows=nrows,
        cell_size_m=cell_size_m,
    )
    xs = [point[0] for point in centers]
    ys = [point[1] for point in centers]
    min_x, max_x = min(xs) - margin_m, max(xs) + margin_m
    min_y, max_y = min(ys) - margin_m, max(ys) + margin_m
    points: list[tuple[float, float]] = []
    for start, end in (
        ((min_x, min_y), (max_x, min_y)),
        ((max_x, min_y), (max_x, max_y)),
        ((max_x, max_y), (min_x, max_y)),
        ((min_x, max_y), (min_x, min_y)),
    ):
        length = abs(end[0] - start[0]) + abs(end[1] - start[1])
        count = max(2, int(round(length / spacing_m)) + 1)
        points.extend(
            (
                start[0] + (end[0] - start[0]) * index / (count - 1),
                start[1] + (end[1] - start[1]) * index / (count - 1),
            )
            for index in range(count)
        )
    unique = list(dict.fromkeys(points))
    return tuple(unique + [unique[0]]) if unique else ()


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
    "closed_box_centers",
    "front_target_cells",
    "leading_edge_cells",
    "perimeter_cells",
    "perimeter_mask",
]
