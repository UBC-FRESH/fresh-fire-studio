"""Sub-cell rasterization and aggregation for drop patterns.

The 100 m fire grid is too coarse to represent a 90 x 40 m drop. This module
keeps a finer depth raster, then aggregates mean depth, maximum depth and
coverage fraction back to fire cells.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from shapely.geometry import Point, Polygon

from .drop import DropPattern


@dataclass(frozen=True)
class SubcellRaster:
    """A depth raster on a regular sub-cell grid."""

    xll: float
    yll: float
    cell_size_m: float
    depth_mm: np.ndarray

    def __post_init__(self) -> None:
        if self.cell_size_m <= 0.0:
            raise ValueError("cell_size_m must be positive")
        array = np.asarray(self.depth_mm, dtype=float)
        if array.ndim != 2:
            raise ValueError("depth_mm must be two-dimensional")
        if bool((array < 0.0).any()):
            raise ValueError("depth_mm must be non-negative")
        object.__setattr__(self, "depth_mm", array)

    @property
    def nrows(self) -> int:
        return int(self.depth_mm.shape[0])

    @property
    def ncols(self) -> int:
        return int(self.depth_mm.shape[1])

    @property
    def area_ha(self) -> float:
        return float((self.depth_mm > 0.0).sum()) * self.cell_size_m**2 / 10_000.0

    def _sub_window(self, fire_xll: float, fire_yll: float, fire_nrows: int, row: int, col: int, fire_cell_m: float):
        ratio = fire_cell_m / self.cell_size_m
        if not math.isclose(ratio, round(ratio), rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError("fire cell size must be an integer multiple of the sub-cell size")
        step = int(round(ratio))
        x0 = fire_xll + col * fire_cell_m
        y0 = fire_yll + (fire_nrows - 1 - row) * fire_cell_m
        sub_col = int(round((x0 - self.xll) / self.cell_size_m))
        sub_row = int(round((self.yll + self.nrows * self.cell_size_m - (y0 + fire_cell_m)) / self.cell_size_m))
        return sub_row, sub_row + step, sub_col, sub_col + step

    def aggregate_mean(
        self,
        *,
        fire_xll: float,
        fire_yll: float,
        fire_nrows: int,
        fire_ncols: int,
        fire_cell_m: float,
    ) -> np.ndarray:
        """Mean sub-cell depth over each fire cell."""
        result = np.zeros((fire_nrows, fire_ncols), dtype=float)
        for row in range(fire_nrows):
            for col in range(fire_ncols):
                r0, r1, c0, c1 = self._sub_window(
                    fire_xll, fire_yll, fire_nrows, row, col, fire_cell_m
                )
                block = np.zeros((r1 - r0, c1 - c0), dtype=float)
                rr0, rr1 = max(0, r0), min(self.nrows, r1)
                cc0, cc1 = max(0, c0), min(self.ncols, c1)
                if rr0 < rr1 and cc0 < cc1:
                    block[rr0 - r0 : rr1 - r0, cc0 - c0 : cc1 - c0] = self.depth_mm[rr0:rr1, cc0:cc1]
                result[row, col] = float(block.mean())
        return result

    def aggregate_max(
        self,
        *,
        fire_xll: float,
        fire_yll: float,
        fire_nrows: int,
        fire_ncols: int,
        fire_cell_m: float,
    ) -> np.ndarray:
        """Maximum sub-cell depth in each fire cell."""
        result = np.zeros((fire_nrows, fire_ncols), dtype=float)
        for row in range(fire_nrows):
            for col in range(fire_ncols):
                r0, r1, c0, c1 = self._sub_window(
                    fire_xll, fire_yll, fire_nrows, row, col, fire_cell_m
                )
                rr0, rr1 = max(0, r0), min(self.nrows, r1)
                cc0, cc1 = max(0, c0), min(self.ncols, c1)
                if rr0 < rr1 and cc0 < cc1:
                    result[row, col] = float(self.depth_mm[rr0:rr1, cc0:cc1].max())
        return result

    def aggregate_coverage(
        self,
        *,
        fire_xll: float,
        fire_yll: float,
        fire_nrows: int,
        fire_ncols: int,
        fire_cell_m: float,
    ) -> np.ndarray:
        """Fraction of each fire cell covered by any positive-depth sub-cell."""
        result = np.zeros((fire_nrows, fire_ncols), dtype=float)
        for row in range(fire_nrows):
            for col in range(fire_ncols):
                r0, r1, c0, c1 = self._sub_window(
                    fire_xll, fire_yll, fire_nrows, row, col, fire_cell_m
                )
                rr0, rr1 = max(0, r0), min(self.nrows, r1)
                cc0, cc1 = max(0, c0), min(self.ncols, c1)
                if rr0 < rr1 and cc0 < cc1:
                    step = int(round(fire_cell_m / self.cell_size_m))
                    result[row, col] = float(
                        (self.depth_mm[rr0:rr1, cc0:cc1] > 0.0).sum() / (step * step)
                    )
        return result


def rasterize_pattern(
    pattern: DropPattern,
    center: tuple[float, float],
    *,
    cell_size_m: float = 10.0,
    rotation_deg: float = 0.0,
    padding_cells: int = 1,
) -> SubcellRaster:
    """Rasterize nested drop contours on a fine grid."""
    if cell_size_m <= 0.0:
        raise ValueError("cell_size_m must be positive")
    if padding_cells < 0:
        raise ValueError("padding_cells must be non-negative")
    polygons = [
        (contour.depth_mm, Polygon(contour.geometry(center, rotation_deg=rotation_deg)))
        for contour in pattern.contours
    ]
    min_x = min(polygon.bounds[0] for _, polygon in polygons)
    min_y = min(polygon.bounds[1] for _, polygon in polygons)
    max_x = max(polygon.bounds[2] for _, polygon in polygons)
    max_y = max(polygon.bounds[3] for _, polygon in polygons)
    xll = math.floor(min_x / cell_size_m) * cell_size_m - padding_cells * cell_size_m
    yll = math.floor(min_y / cell_size_m) * cell_size_m - padding_cells * cell_size_m
    ncols = math.ceil((max_x - xll) / cell_size_m) + padding_cells
    nrows = math.ceil((max_y - yll) / cell_size_m) + padding_cells
    depth = np.zeros((nrows, ncols), dtype=float)
    for row in range(nrows):
        y = yll + (nrows - 1 - row + 0.5) * cell_size_m
        for col in range(ncols):
            x = xll + (col + 0.5) * cell_size_m
            point = Point(x, y)
            value = 0.0
            for contour_depth, polygon in polygons:
                if contour_depth > value and polygon.covers(point):
                    value = contour_depth
            depth[row, col] = value
    return SubcellRaster(xll=xll, yll=yll, cell_size_m=cell_size_m, depth_mm=depth)


__all__ = ["SubcellRaster", "rasterize_pattern"]
