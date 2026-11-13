"""Deterministic drop-mission construction.

This is a planning helper, not an optimizer. It distributes targets across a
fixed number of aircraft and schedules drops at the profile cycle time.
"""

from __future__ import annotations

from dataclasses import dataclass

from .aircraft import AircraftProfile, drop_intervals


@dataclass(frozen=True)
class MissionDrop:
    """One scheduled drop in a mission."""

    resource_id: str
    center: tuple[float, float]
    pass_index: int
    start_min: float
    end_min: float

    def to_dict(self) -> dict[str, object]:
        return {
            "resource_id": self.resource_id,
            "center": [self.center[0], self.center[1]],
            "pass_index": self.pass_index,
            "start_min": self.start_min,
            "end_min": self.end_min,
        }


def build_perimeter_mission(
    centers: tuple[tuple[float, float], ...],
    *,
    profile: AircraftProfile,
    start_min: float,
    distance_km: float,
    aircraft_count: int,
    passes: int = 1,
    drop_minutes: float = 1.0,
) -> tuple[MissionDrop, ...]:
    """Distribute perimeter targets across aircraft and repeat for passes."""
    if not centers:
        raise ValueError("centers must not be empty")
    if aircraft_count < 1:
        raise ValueError("aircraft_count must be at least 1")
    if passes < 1:
        raise ValueError("passes must be at least 1")
    if start_min < 0.0:
        raise ValueError("start_min must be non-negative")
    assignments: list[list[tuple[float, float]]] = [[] for _ in range(aircraft_count)]
    for index, center in enumerate(centers):
        assignments[index % aircraft_count].append(center)
    result: list[MissionDrop] = []
    for aircraft_index, targets in enumerate(assignments, start=1):
        if not targets:
            continue
        intervals = drop_intervals(
            profile,
            start_min=start_min,
            distance_km=distance_km,
            count=len(targets) * passes,
            drop_minutes=drop_minutes,
        )
        cursor = 0
        for pass_index in range(1, passes + 1):
            for center in targets:
                start, end = intervals[cursor]
                cursor += 1
                result.append(
                    MissionDrop(
                        resource_id=f"aircraft-{aircraft_index}",
                        center=center,
                        pass_index=pass_index,
                        start_min=start,
                        end_min=end,
                    )
                )
    return tuple(sorted(result, key=lambda item: (item.start_min, item.resource_id)))


__all__ = ["MissionDrop", "build_perimeter_mission"]
