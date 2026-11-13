"""Compare water delivery scenarios against a target-line demand."""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot

from .cycle import CyclePerformance, build_cycle, cycle_summary
from .water_balance import WaterBalance, water_balance


@dataclass(frozen=True)
class DeliveryCase:
    passes: int
    aircraft_count: int
    lake_distance_m: float
    sorties: int
    elapsed_min: float
    mean_cycle_min: float
    litres_per_hour: float
    balance: WaterBalance

    @property
    def delivered_l(self) -> float:
        return self.balance.delivered_l

    @property
    def line_mean_depth_mm(self) -> float:
        return self.balance.line_mean_depth_mm

    @property
    def coverage_fraction(self) -> float:
        return self.balance.coverage_fraction

    @property
    def deficit_l(self) -> float:
        return self.balance.deficit_l

    @property
    def additional_sorties(self) -> int:
        return self.balance.additional_sorties

    def to_dict(self) -> dict[str, object]:
        return {
            "passes": self.passes,
            "aircraft_count": self.aircraft_count,
            "lake_distance_m": round(self.lake_distance_m, 1),
            "sorties": self.sorties,
            "elapsed_min": round(self.elapsed_min, 2),
            "mean_cycle_min": round(self.mean_cycle_min, 3),
            "litres_per_hour": round(self.litres_per_hour, 1),
            **self.balance.to_dict(),
        }


def line_length_m(targets: tuple[tuple[float, float], ...]) -> float:
    return sum(
        hypot(second[0] - first[0], second[1] - first[1])
        for first, second in zip(targets, targets[1:])
    )


def delivery_case(
    *,
    targets: tuple[tuple[float, float], ...],
    lake: tuple[float, float],
    aircraft_count: int,
    passes: int,
    performance: CyclePerformance,
    required_depth_mm: float,
    start_min: float = 600.0,
) -> DeliveryCase:
    if passes < 1:
        raise ValueError("passes must be at least 1")
    if aircraft_count < 1:
        raise ValueError("aircraft_count must be at least 1")
    repeated = tuple(targets) * passes
    aircraft_ids = tuple(f"aircraft-{index}" for index in range(1, aircraft_count + 1))
    sorties = build_cycle(
        targets=repeated,
        lake=lake,
        aircraft_ids=aircraft_ids,
        performance=performance,
        start_min=start_min,
    )
    summary = cycle_summary(sorties)
    mean_lake_distance = sum(hypot(target[0] - lake[0], target[1] - lake[1]) for target in targets) / len(targets)
    balance = water_balance(
        line_length_m=line_length_m(targets),
        drop_length_m=100.0,
        drop_width_m=50.0,
        drop_count=len(sorties),
        delivered_l=summary["total_water_l"],
        required_depth_mm=required_depth_mm,
        tank_l=performance.tank_l,
        unique_targets=len(targets),
    )
    return DeliveryCase(
        passes=passes,
        aircraft_count=aircraft_count,
        lake_distance_m=mean_lake_distance,
        sorties=len(sorties),
        elapsed_min=summary["elapsed_min"],
        mean_cycle_min=summary["mean_cycle_min"],
        litres_per_hour=summary["litres_per_hour"],
        balance=balance,
    )


def delivery_sweep(
    *,
    targets: tuple[tuple[float, float], ...],
    lakes: dict[str, tuple[float, float]],
    aircraft_counts: tuple[int, ...] | list[int],
    passes_values: tuple[int, ...] | list[int],
    performance: CyclePerformance,
    required_depth_mm: float,
) -> dict[str, list[dict[str, object]]]:
    result: dict[str, list[dict[str, object]]] = {}
    for lake_name, lake in lakes.items():
        rows = []
        for passes in passes_values:
            for aircraft_count in aircraft_counts:
                rows.append(
                    delivery_case(
                        targets=targets,
                        lake=lake,
                        aircraft_count=aircraft_count,
                        passes=passes,
                        performance=performance,
                        required_depth_mm=required_depth_mm,
                    ).to_dict()
                )
        result[lake_name] = rows
    return result


__all__ = ["DeliveryCase", "delivery_case", "delivery_sweep", "line_length_m"]
