"""Diagnose whether wet cells coincide with the fire arrival time."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .wet import WetSchedule


@dataclass(frozen=True)
class WetInteraction:
    wet_cells: int
    wet_at_arrival: int
    burned_before_wet: int
    burned_after_wet: int
    unburned: int
    no_wet_window: int

    def to_dict(self) -> dict[str, int]:
        return {
            "wet_cells": self.wet_cells,
            "wet_at_arrival": self.wet_at_arrival,
            "burned_before_wet": self.burned_before_wet,
            "burned_after_wet": self.burned_after_wet,
            "unburned": self.unburned,
            "no_wet_window": self.no_wet_window,
        }


def analyze_wet_interaction(
    wet: WetSchedule,
    ignition_time_min: np.ndarray,
) -> WetInteraction:
    """Compare cell wetness with the free-burn arrival time."""
    ignition = np.asarray(ignition_time_min, dtype=float)
    if ignition.ndim != 2:
        raise ValueError("ignition_time_min must be two-dimensional")
    rows, cols = ignition.shape
    wet_cells = wet_at_arrival = before = after = unburned = no_window = 0
    for row in range(rows):
        for col in range(cols):
            drops = [
                drop
                for drop in wet.drops
                if drop.fraction[row, col] > 0.0
            ]
            if not drops:
                continue
            wet_cells += 1
            first = min(drop.start_min for drop in drops)
            last = max(drop.end_min + drop.duration_min for drop in drops)
            arrival = float(ignition[row, col])
            if not np.isfinite(arrival):
                unburned += 1
            elif arrival < first:
                before += 1
            elif arrival > last:
                after += 1
            elif wet.is_suppressed(row, col, arrival):
                wet_at_arrival += 1
            else:
                no_window += 1
    return WetInteraction(
        wet_cells=wet_cells,
        wet_at_arrival=wet_at_arrival,
        burned_before_wet=before,
        burned_after_wet=after,
        unburned=unburned,
        no_wet_window=no_window,
    )


__all__ = ["WetInteraction", "analyze_wet_interaction"]
