"""Aircraft delivery-rate helpers from McFayden et al. (2023).

The table is for a CL-415 and uses the guide's blended-speed + cycle-increment
model. Values are interpolated linearly between the tabulated distances.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AircraftProfile:
    """A narrow aircraft delivery profile."""

    name: str
    tank_l: float
    distance_km: tuple[float, ...]
    drops_per_hour: tuple[float, ...]
    litres_per_hour: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.distance_km) != len(self.drops_per_hour):
            raise ValueError("distance and drop-rate tables must have equal length")
        if len(self.distance_km) != len(self.litres_per_hour):
            raise ValueError("distance and volume tables must have equal length")
        if any(value < 0.0 for value in self.distance_km):
            raise ValueError("distance values must be non-negative")
        if any(value <= 0.0 for value in self.drops_per_hour):
            raise ValueError("drops-per-hour values must be positive")
        if any(value < 0.0 for value in self.litres_per_hour):
            raise ValueError("litres-per-hour values must be non-negative")

    def _interpolate(self, values: tuple[float, ...], distance_km: float) -> float:
        if distance_km <= self.distance_km[0]:
            return values[0]
        if distance_km >= self.distance_km[-1]:
            return values[-1]
        for index in range(1, len(self.distance_km)):
            if distance_km <= self.distance_km[index]:
                left = self.distance_km[index - 1]
                right = self.distance_km[index]
                fraction = (distance_km - left) / (right - left)
                return values[index - 1] + fraction * (values[index] - values[index - 1])
        return values[-1]

    def drops_per_hour_at(self, distance_km: float) -> float:
        if distance_km < 0.0:
            raise ValueError("distance_km must be non-negative")
        return self._interpolate(self.drops_per_hour, distance_km)

    def litres_per_hour_at(self, distance_km: float) -> float:
        if distance_km < 0.0:
            raise ValueError("distance_km must be non-negative")
        return self._interpolate(self.litres_per_hour, distance_km)

    def cycle_minutes_at(self, distance_km: float) -> float:
        return 60.0 / self.drops_per_hour_at(distance_km)

    def effective_litres_per_drop_at(self, distance_km: float) -> float:
        return self.litres_per_hour_at(distance_km) / self.drops_per_hour_at(distance_km)


CL415 = AircraftProfile(
    name="CL-415",
    tank_l=6_000.0,
    distance_km=(0.0, 2.0, 4.0, 6.0, 7.0, 9.0, 11.0, 13.0, 15.0, 17.0, 19.0, 28.0, 37.0),
    drops_per_hour=(20.0, 18.0, 16.0, 14.0, 13.0, 12.0, 11.0, 11.0, 10.0, 9.0, 9.0, 7.0, 6.0),
    litres_per_hour=(
        98_000.0,
        87_000.0,
        78_000.0,
        71_000.0,
        65_000.0,
        60_000.0,
        56_000.0,
        52_000.0,
        49_000.0,
        46_000.0,
        43_000.0,
        34_000.0,
        28_000.0,
    ),
)


def drop_intervals(
    profile: AircraftProfile,
    *,
    start_min: float,
    distance_km: float,
    count: int,
    drop_minutes: float = 1.0,
) -> tuple[tuple[float, float], ...]:
    """Return sequential drop windows at the profile cycle time."""
    if start_min < 0.0:
        raise ValueError("start_min must be non-negative")
    if count < 1:
        raise ValueError("count must be at least 1")
    if drop_minutes <= 0.0:
        raise ValueError("drop_minutes must be positive")
    cycle = profile.cycle_minutes_at(distance_km)
    return tuple(
        (start_min + index * cycle, start_min + index * cycle + drop_minutes)
        for index in range(count)
    )


def line_centers(
    start: tuple[float, float],
    end: tuple[float, float],
    count: int,
) -> tuple[tuple[float, float], ...]:
    """Return evenly spaced centers along a straight line."""
    if count < 1:
        raise ValueError("count must be at least 1")
    return tuple(
        (
            start[0] + (end[0] - start[0]) * index / max(1, count - 1),
            start[1] + (end[1] - start[1]) * index / max(1, count - 1),
        )
        for index in range(count)
    )


__all__ = ["AircraftProfile", "CL415", "drop_intervals", "line_centers"]
