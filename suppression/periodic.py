"""Perfect periodic re-wetting schedule for the P185 persistence test.

This is a diagnostic abstraction: one full-cell application is repeated at a
fixed interval. It is not an aircraft schedule and it does not model partial
coverage. Its purpose is to isolate the effect of re-wetting interval and
application depth.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PeriodicWetSchedule:
    """Repeat a full-cell water application at a fixed interval."""

    mask: np.ndarray
    depth_mm: float
    required_depth_mm: float
    decay_min: float
    interval_min: float
    start_min: float = 600.0
    end_min: float = 22200.0

    def __post_init__(self) -> None:
        if self.depth_mm <= 0.0:
            raise ValueError("depth_mm must be positive")
        if self.required_depth_mm <= 0.0:
            raise ValueError("required_depth_mm must be positive")
        if self.decay_min <= 0.0:
            raise ValueError("decay_min must be positive")
        if self.interval_min <= 0.0:
            raise ValueError("interval_min must be positive")
        if self.end_min <= self.start_min:
            raise ValueError("end_min must be after start_min")

    @property
    def effective_hold_min(self) -> float:
        """Time above threshold after one application."""
        if self.depth_mm <= self.required_depth_mm:
            return 0.0
        return self.decay_min * (1.0 - self.required_depth_mm / self.depth_mm)

    def _age_min(self, time_min: float) -> float:
        if time_min < self.start_min:
            return math.inf
        time_min = min(time_min, self.end_min)
        return (time_min - self.start_min) % self.interval_min

    def depth_at(self, row: int, col: int, time_min: float) -> float:
        if not bool(self.mask[row, col]):
            return 0.0
        age = self._age_min(time_min)
        if not math.isfinite(age):
            return 0.0
        return self.depth_mm * max(0.0, 1.0 - age / self.decay_min)

    def wetness_at(self, row: int, col: int, time_min: float) -> float:
        return min(1.0, self.depth_at(row, col, time_min) / self.required_depth_mm)

    def ros_factor_at(self, row: int, col: int, time_min: float) -> float:
        return 1.0 - self.wetness_at(row, col, time_min)

    def is_suppressed(self, row: int, col: int, time_min: float) -> bool:
        return self.wetness_at(row, col, time_min) >= 1.0

    def event_times(self) -> tuple[float, ...]:
        times: set[float] = set()
        value = self.start_min
        while value <= self.end_min + 1e-9:
            times.add(value)
            times.add(value + self.decay_min)
            value += self.interval_min
        return tuple(sorted(times))


__all__ = ["PeriodicWetSchedule"]
