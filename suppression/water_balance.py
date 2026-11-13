"""Simple water-demand accounting for a drop mission."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class WaterBalance:
    line_length_m: float
    drop_length_m: float
    drop_width_m: float
    drop_count: int
    delivered_l: float
    required_depth_mm: float
    tank_l: float = 6000.0
    unique_targets: int | None = None

    @property
    def target_area_m2(self) -> float:
        return self.line_length_m * self.drop_width_m

    @property
    def treated_area_m2(self) -> float:
        count = self.drop_count if self.unique_targets is None else self.unique_targets
        return count * self.drop_length_m * self.drop_width_m

    @property
    def line_mean_depth_mm(self) -> float:
        """Mean depth if delivered water were spread across the whole strip."""
        return self.delivered_l / self.target_area_m2 if self.target_area_m2 else 0.0

    @property
    def treated_mean_depth_mm(self) -> float:
        return self.delivered_l / self.treated_area_m2 if self.treated_area_m2 else 0.0

    @property
    def coverage_fraction(self) -> float:
        return min(1.0, self.treated_area_m2 / self.target_area_m2) if self.target_area_m2 else 0.0

    @property
    def required_l(self) -> float:
        return self.target_area_m2 * self.required_depth_mm

    @property
    def deficit_l(self) -> float:
        return max(0.0, self.required_l - self.delivered_l)

    @property
    def additional_sorties(self) -> int:
        if self.deficit_l <= 0.0:
            return 0
        return int(math.ceil(self.deficit_l / self.tank_l))

    def to_dict(self) -> dict[str, object]:
        return {
            "line_length_m": round(self.line_length_m, 1),
            "target_area_m2": round(self.target_area_m2, 1),
            "treated_area_m2": round(self.treated_area_m2, 1),
            "drop_count": self.drop_count,
            "unique_targets": self.unique_targets if self.unique_targets is not None else self.drop_count,
            "delivered_l": round(self.delivered_l, 1),
            "required_depth_mm": self.required_depth_mm,
            "line_mean_depth_mm": round(self.line_mean_depth_mm, 3),
            "treated_mean_depth_mm": round(self.treated_mean_depth_mm, 3),
            "coverage_fraction": round(self.coverage_fraction, 3),
            "required_l": round(self.required_l, 1),
            "deficit_l": round(self.deficit_l, 1),
            "additional_sorties": self.additional_sorties,
        }


def water_balance(
    *,
    line_length_m: float,
    drop_length_m: float,
    drop_width_m: float,
    drop_count: int,
    delivered_l: float,
    required_depth_mm: float,
    tank_l: float = 6000.0,
    unique_targets: int | None = None,
) -> WaterBalance:
    for value, name in (
        (line_length_m, "line_length_m"),
        (drop_length_m, "drop_length_m"),
        (drop_width_m, "drop_width_m"),
        (drop_count, "drop_count"),
        (delivered_l, "delivered_l"),
        (required_depth_mm, "required_depth_mm"),
        (tank_l, "tank_l"),
    ):
        if value <= 0:
            raise ValueError(f"{name} must be positive")
    return WaterBalance(
        line_length_m=line_length_m,
        drop_length_m=drop_length_m,
        drop_width_m=drop_width_m,
        drop_count=drop_count,
        delivered_l=delivered_l,
        required_depth_mm=required_depth_mm,
        tank_l=tank_l,
        unique_targets=unique_targets,
    )


__all__ = ["WaterBalance", "water_balance"]
