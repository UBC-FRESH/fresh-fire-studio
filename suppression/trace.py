"""Per-target drop and wetness traces for diagnosis."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .wet import WetSchedule


@dataclass(frozen=True)
class DropTrace:
    drop_id: str
    start_min: float
    end_min: float
    duration_min: float
    fraction: float
    depth_at_start_mm: float
    depth_at_arrival_mm: float
    depth_at_end_mm: float


@dataclass(frozen=True)
class TargetTrace:
    x: float
    y: float
    row: int
    col: int
    arrival_min: float
    combined_at_arrival_mm: float
    wet_at_arrival: bool
    max_combined_mm: float
    drops: tuple[DropTrace, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "x": round(self.x, 1),
            "y": round(self.y, 1),
            "row": self.row,
            "col": self.col,
            "arrival_min": round(self.arrival_min, 3) if np.isfinite(self.arrival_min) else None,
            "combined_at_arrival_mm": round(self.combined_at_arrival_mm, 4),
            "wet_at_arrival": self.wet_at_arrival,
            "max_combined_mm": round(self.max_combined_mm, 4),
            "drops": [
                {
                    "drop_id": drop.drop_id,
                    "start_min": round(drop.start_min, 3),
                    "end_min": round(drop.end_min, 3),
                    "duration_min": round(drop.duration_min, 3),
                    "fraction": round(drop.fraction, 3),
                    "depth_at_start_mm": round(drop.depth_at_start_mm, 4),
                    "depth_at_arrival_mm": round(drop.depth_at_arrival_mm, 4),
                    "depth_at_end_mm": round(drop.depth_at_end_mm, 4),
                }
                for drop in self.drops
            ],
        }


def trace_targets(
    wet: WetSchedule,
    ignition_time_min: np.ndarray,
    centers: list[tuple[float, float]] | tuple[tuple[float, float], ...],
    *,
    xll: float,
    yll: float,
    nrows: int,
    ncols: int,
    cell_size_m: float,
) -> tuple[TargetTrace, ...]:
    """Summarize each target's drops and combined depth at arrival."""
    ignition = np.asarray(ignition_time_min, dtype=float)
    result: list[TargetTrace] = []
    for x, y in centers:
        col = int((x - xll) // cell_size_m)
        row = nrows - 1 - int((y - yll) // cell_size_m)
        if not (0 <= row < nrows and 0 <= col < ncols):
            continue
        arrival = float(ignition[row, col])
        drops = []
        combined = 0.0
        maximum = 0.0
        for drop in wet.drops:
            fraction = float(drop.fraction[row, col])
            if fraction <= 0.0:
                continue
            at_start = drop.depth_at(row, col, drop.start_min)
            at_arrival = drop.depth_at(row, col, arrival) if np.isfinite(arrival) else 0.0
            at_end = drop.depth_at(row, col, drop.end_min + drop.duration_min)
            combined += at_arrival
            maximum = max(maximum, at_start, at_arrival, at_end)
            drops.append(
                DropTrace(
                    drop_id=drop.drop_id,
                    start_min=drop.start_min,
                    end_min=drop.end_min,
                    duration_min=drop.duration_min,
                    fraction=fraction,
                    depth_at_start_mm=at_start,
                    depth_at_arrival_mm=at_arrival,
                    depth_at_end_mm=at_end,
                )
            )
        result.append(
            TargetTrace(
                x=x,
                y=y,
                row=row,
                col=col,
                arrival_min=arrival,
                combined_at_arrival_mm=combined,
                wet_at_arrival=(np.isfinite(arrival) and combined >= wet.required_depth_mm),
                max_combined_mm=maximum,
                drops=tuple(drops),
            )
        )
    return tuple(result)


__all__ = ["DropTrace", "TargetTrace", "trace_targets"]
