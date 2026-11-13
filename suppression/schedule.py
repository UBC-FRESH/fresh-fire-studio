"""Schedule sorties so drops bracket target arrival times."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .cycle import CyclePerformance, Sortie, build_sortie


@dataclass(frozen=True)
class TimedTarget:
    x: float
    y: float
    arrival_min: float


@dataclass(frozen=True)
class ScheduledSortie:
    sortie: Sortie
    target: TimedTarget
    desired_drop_min: float
    actual_drop_min: float
    late_min: float

    def to_dict(self) -> dict[str, object]:
        return {
            **self.sortie.to_dict(),
            "target_arrival_min": round(self.target.arrival_min, 3),
            "desired_drop_min": round(self.desired_drop_min, 3),
            "actual_drop_min": round(self.actual_drop_min, 3),
            "late_min": round(self.late_min, 3),
        }


def _travel_minutes(lake: tuple[float, float], target: tuple[float, float], performance: CyclePerformance) -> float:
    distance = math.hypot(target[0] - lake[0], target[1] - lake[1])
    return distance / (performance.cruise_kmh * 1000.0 / 60.0)


def schedule_stacked_targets(
    targets: list[TimedTarget] | tuple[TimedTarget, ...],
    *,
    lake: tuple[float, float],
    aircraft_ids: tuple[str, ...] | list[str],
    performance: CyclePerformance,
    hold_min: float = 60.0,
    stack: int = 2,
    pre_arrival_min: float | None = None,
    start_min: float = 0.0,
) -> tuple[ScheduledSortie, ...]:
    """Schedule overlapping drops from several aircraft on each target."""
    if stack < 1:
        raise ValueError("stack must be at least 1")
    if stack > len(aircraft_ids):
        raise ValueError("stack cannot exceed the number of aircraft")
    ready = {aircraft_id: start_min for aircraft_id in aircraft_ids}
    scheduled: list[ScheduledSortie] = []
    for target in sorted(targets, key=lambda item: (item.arrival_min, item.y, item.x)):
        desired = target.arrival_min - (hold_min / 2.0 if pre_arrival_min is None else pre_arrival_min)
        for _ in range(stack):
            best = None
            for aircraft_id in aircraft_ids:
                travel = _travel_minutes(lake, (target.x, target.y), performance)
                lead = performance.scoop_min + performance.climb_min + travel + performance.descent_min
                start = max(ready[aircraft_id], desired - lead)
                actual = start + lead
                candidate = (max(0.0, actual - desired), start, aircraft_id, actual)
                if best is None or candidate < best:
                    best = candidate
            _, start, aircraft_id, actual = best
            sortie = build_sortie(
                aircraft_id=aircraft_id,
                lake=lake,
                target=(target.x, target.y),
                start_min=start,
                performance=performance,
            )
            scheduled.append(
                ScheduledSortie(
                    sortie=sortie,
                    target=target,
                    desired_drop_min=desired,
                    actual_drop_min=sortie.phase("drop").start_min,
                    late_min=max(0.0, sortie.phase("drop").start_min - desired),
                )
            )
            ready[aircraft_id] = sortie.end_min
    return tuple(scheduled)


def schedule_arrival_targets(
    targets: list[TimedTarget] | tuple[TimedTarget, ...],
    *,
    lake: tuple[float, float],
    aircraft_ids: tuple[str, ...] | list[str],
    performance: CyclePerformance,
    hold_min: float = 60.0,
    pre_arrival_min: float | None = None,
    start_min: float = 0.0,
) -> tuple[ScheduledSortie, ...]:
    """Schedule each target so the drop sits in the hold window around arrival."""
    if not targets:
        raise ValueError("targets must not be empty")
    if not aircraft_ids:
        raise ValueError("aircraft_ids must not be empty")
    if hold_min <= 0.0:
        raise ValueError("hold_min must be positive")
    ready = {aircraft_id: start_min for aircraft_id in aircraft_ids}
    scheduled: list[ScheduledSortie] = []
    for target in sorted(targets, key=lambda item: (item.arrival_min, item.y, item.x)):
        desired = target.arrival_min - hold_min / 2.0
        best = None
        for aircraft_id in aircraft_ids:
            travel = _travel_minutes(lake, (target.x, target.y), performance)
            lead = performance.scoop_min + performance.climb_min + travel + performance.descent_min
            start = max(ready[aircraft_id], desired - lead)
            actual = start + lead
            candidate = (max(0.0, actual - desired), start, aircraft_id, actual)
            if best is None or candidate < best:
                best = candidate
        _, start, aircraft_id, actual = best
        sortie = build_sortie(
            aircraft_id=aircraft_id,
            lake=lake,
            target=(target.x, target.y),
            start_min=start,
            performance=performance,
        )
        scheduled.append(
            ScheduledSortie(
                sortie=sortie,
                target=target,
                desired_drop_min=desired,
                actual_drop_min=sortie.phase("drop").start_min,
                late_min=max(0.0, sortie.phase("drop").start_min - desired),
            )
        )
        ready[aircraft_id] = sortie.end_min
    return tuple(scheduled)


__all__ = ["ScheduledSortie", "TimedTarget", "schedule_arrival_targets", "schedule_stacked_targets"]
