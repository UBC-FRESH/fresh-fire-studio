"""Phase-based airtanker cycle geometry.

The model is deliberately simple and explicit: scoop, climb, cruise, descend,
drop, turn, climb, return and descend. Each phase carries a start/end time and a
3D start/end position. It is a scheduling/geometry contract, not a flight
simulator.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

PhaseKind = Literal[
    "scoop",
    "climb",
    "cruise_out",
    "descent",
    "drop",
    "turn",
    "climb_back",
    "cruise_back",
    "descent_back",
]


@dataclass(frozen=True)
class FlightPhase:
    kind: PhaseKind
    start_min: float
    end_min: float
    from_xyz: tuple[float, float, float]
    to_xyz: tuple[float, float, float]

    def __post_init__(self) -> None:
        if self.end_min < self.start_min:
            raise ValueError("phase end must be >= start")
        if self.end_min == self.start_min:
            raise ValueError("phase duration must be positive")

    @property
    def duration_min(self) -> float:
        return self.end_min - self.start_min

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "start": round(self.start_min, 3),
            "end": round(self.end_min, 3),
            "from": [round(value, 1) for value in self.from_xyz],
            "to": [round(value, 1) for value in self.to_xyz],
        }


@dataclass(frozen=True)
class CyclePerformance:
    cruise_kmh: float = 180.0
    drop_kmh: float = 130.0
    scoop_min: float = 0.4
    climb_min: float = 0.5
    descent_min: float = 0.3
    drop_min: float = 5.0 / 60.0
    turn_min: float = 0.2
    cruise_alt_m: float = 300.0
    drop_alt_m: float = 80.0
    tank_l: float = 6000.0

    def __post_init__(self) -> None:
        for name in ("cruise_kmh", "drop_kmh", "scoop_min", "climb_min", "descent_min", "drop_min", "turn_min", "tank_l"):
            if getattr(self, name) <= 0.0:
                raise ValueError(f"{name} must be positive")
        if self.cruise_alt_m <= self.drop_alt_m:
            raise ValueError("cruise altitude must be above drop altitude")
        if self.drop_alt_m < 0.0:
            raise ValueError("drop altitude must be non-negative")


@dataclass(frozen=True)
class Sortie:
    aircraft_id: str
    target: tuple[float, float]
    phases: tuple[FlightPhase, ...]
    water_l: float

    @property
    def start_min(self) -> float:
        return self.phases[0].start_min

    @property
    def end_min(self) -> float:
        return self.phases[-1].end_min

    @property
    def cycle_min(self) -> float:
        return self.end_min - self.start_min

    def phase(self, kind: PhaseKind) -> FlightPhase:
        for item in self.phases:
            if item.kind == kind:
                return item
        raise KeyError(kind)

    def validate(self) -> None:
        for previous, current in zip(self.phases, self.phases[1:]):
            if abs(previous.end_min - current.start_min) > 1e-6:
                raise ValueError("phases must be contiguous")

    def to_dict(self) -> dict[str, object]:
        drop = self.phase("drop")
        return {
            "aircraft_id": self.aircraft_id,
            "target": [round(self.target[0], 1), round(self.target[1], 1)],
            "water_l": self.water_l,
            "cycle_min": round(self.cycle_min, 3),
            "drop_start": round(drop.start_min, 3),
            "drop_end": round(drop.end_min, 3),
            "phases": [phase.to_dict() for phase in self.phases],
        }


def _phase(
    kind: PhaseKind,
    start: float,
    duration: float,
    from_xyz: tuple[float, float, float],
    to_xyz: tuple[float, float, float],
) -> FlightPhase:
    return FlightPhase(kind, start, start + duration, from_xyz, to_xyz)


def build_sortie(
    *,
    aircraft_id: str,
    lake: tuple[float, float],
    target: tuple[float, float],
    start_min: float,
    performance: CyclePerformance,
) -> Sortie:
    distance_m = math.hypot(target[0] - lake[0], target[1] - lake[1])
    travel_min = distance_m / (performance.cruise_kmh * 1000.0 / 60.0)
    lake_low = (lake[0], lake[1], 0.0)
    lake_high = (lake[0], lake[1], performance.cruise_alt_m)
    target_high = (target[0], target[1], performance.cruise_alt_m)
    target_low = (target[0], target[1], performance.drop_alt_m)
    drop_start_xy = (target[0] - 50.0, target[1])
    drop_end_xy = (target[0] + 50.0, target[1])
    drop_start = start_min + performance.scoop_min + performance.climb_min + travel_min + performance.descent_min
    phases: list[FlightPhase] = []
    cursor = start_min
    phases.append(_phase("scoop", cursor, performance.scoop_min, lake_low, lake_low)); cursor += performance.scoop_min
    phases.append(_phase("climb", cursor, performance.climb_min, lake_low, lake_high)); cursor += performance.climb_min
    phases.append(_phase("cruise_out", cursor, travel_min, lake_high, target_high)); cursor += travel_min
    phases.append(_phase("descent", cursor, performance.descent_min, target_high, target_low)); cursor += performance.descent_min
    phases.append(_phase("drop", cursor, performance.drop_min, (drop_start_xy[0], drop_start_xy[1], performance.drop_alt_m), (drop_end_xy[0], drop_end_xy[1], performance.drop_alt_m))); cursor += performance.drop_min
    phases.append(_phase("turn", cursor, performance.turn_min, (drop_end_xy[0], drop_end_xy[1], performance.drop_alt_m), (drop_end_xy[0], drop_end_xy[1], performance.drop_alt_m))); cursor += performance.turn_min
    phases.append(_phase("climb_back", cursor, performance.climb_min, (drop_end_xy[0], drop_end_xy[1], performance.drop_alt_m), (drop_end_xy[0], drop_end_xy[1], performance.cruise_alt_m))); cursor += performance.climb_min
    phases.append(_phase("cruise_back", cursor, travel_min, (drop_end_xy[0], drop_end_xy[1], performance.cruise_alt_m), lake_high)); cursor += travel_min
    phases.append(_phase("descent_back", cursor, performance.descent_min, lake_high, lake_low)); cursor += performance.descent_min
    sortie = Sortie(
        aircraft_id=aircraft_id,
        target=(target[0], target[1]),
        phases=tuple(phases),
        water_l=performance.tank_l,
    )
    sortie.validate()
    return sortie


def build_cycle(
    *,
    targets: tuple[tuple[float, float], ...] | list[tuple[float, float]],
    lake: tuple[float, float],
    aircraft_ids: tuple[str, ...] | list[str],
    performance: CyclePerformance,
    start_min: float = 600.0,
) -> tuple[Sortie, ...]:
    if not targets:
        raise ValueError("targets must not be empty")
    if not aircraft_ids:
        raise ValueError("aircraft_ids must not be empty")
    ready = {aircraft_id: start_min for aircraft_id in aircraft_ids}
    sorties: list[Sortie] = []
    for index, target in enumerate(targets):
        aircraft_id = aircraft_ids[index % len(aircraft_ids)]
        sortie = build_sortie(
            aircraft_id=aircraft_id,
            lake=lake,
            target=target,
            start_min=ready[aircraft_id],
            performance=performance,
        )
        sorties.append(sortie)
        ready[aircraft_id] = sortie.end_min
    return tuple(sorted(sorties, key=lambda item: (item.start_min, item.aircraft_id)))


def cycle_summary(sorties: tuple[Sortie, ...]) -> dict[str, object]:
    if not sorties:
        raise ValueError("sorties must not be empty")
    cycles = [sortie.cycle_min for sortie in sorties]
    counts: dict[str, int] = {}
    for sortie in sorties:
        counts[sortie.aircraft_id] = counts.get(sortie.aircraft_id, 0) + 1
    elapsed = max(sortie.end_min for sortie in sorties) - min(sortie.start_min for sortie in sorties)
    total_water = sum(sortie.water_l for sortie in sorties)
    return {
        "sorties": len(sorties),
        "total_water_l": total_water,
        "mean_cycle_min": sum(cycles) / len(cycles),
        "min_cycle_min": min(cycles),
        "max_cycle_min": max(cycles),
        "per_aircraft": counts,
        "elapsed_min": elapsed,
        "litres_per_hour": total_water / elapsed * 60.0 if elapsed > 0 else 0.0,
        "sorties_per_hour": len(sorties) / elapsed * 60.0 if elapsed > 0 else 0.0,
    }


__all__ = [
    "CyclePerformance",
    "FlightPhase",
    "Sortie",
    "build_cycle",
    "build_sortie",
    "cycle_summary",
]
