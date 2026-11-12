"""Rasterize P179 suppression effects onto the fire model grid."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from rasterio.features import rasterize
from rasterio.transform import from_origin
from shapely.geometry import LineString, Polygon, mapping

from .models import EffectEvent


@dataclass(frozen=True)
class RasterEffects:
    """Boolean effect layers aligned to the fire model grid."""

    line: np.ndarray
    water: np.ndarray
    foam: np.ndarray
    retardant: np.ndarray

    @property
    def containment(self) -> np.ndarray:
        """Cells removed from the burnable mask for the static P179.1 proof."""
        return self.line


def rasterize_effects(
    events: list[EffectEvent],
    *,
    xll: float,
    yll: float,
    nrows: int,
    ncols: int,
    cell_size_m: float,
) -> RasterEffects:
    """Rasterize line and drop footprints in projected grid coordinates.

    The fire grid uses north-up rows, so the raster transform is anchored at the
    northern edge of the lower-left origin.
    """
    transform = from_origin(xll, yll + nrows * cell_size_m, cell_size_m, cell_size_m)
    shape = (nrows, ncols)
    line = np.zeros(shape, dtype=bool)
    water = np.zeros(shape, dtype=bool)
    foam = np.zeros(shape, dtype=bool)
    retardant = np.zeros(shape, dtype=bool)
    for event in events:
        if event.kind == "line":
            geometry = LineString(event.geometry).buffer(max(0.5, event.width_m / 2.0))
            target = line
        elif event.kind == "water":
            geometry = Polygon(event.geometry)
            target = water
        elif event.kind == "foam":
            geometry = Polygon(event.geometry)
            target = foam
        elif event.kind == "retardant":
            geometry = Polygon(event.geometry)
            target = retardant
        else:
            continue
        mask = rasterize(
            [(mapping(geometry), 1)],
            out_shape=shape,
            transform=transform,
            fill=0,
            dtype="uint8",
            all_touched=True,
        ).astype(bool)
        target |= mask
    return RasterEffects(line=line, water=water, foam=foam, retardant=retardant)
