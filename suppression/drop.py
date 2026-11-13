"""Drop-pattern and breach helpers based on McFayden et al. (2023).

The guide describes nested water-depth contours, stacking and a breach test.
This module provides a small, explicit representation for those concepts. It
does not claim to reproduce every airtanker/fuel/canopy chart in GLC-X-35.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from .models import EffectEvent, Point

Aircraft = Literal["CL-415"]
FuelType = Literal["C-2"]
Canopy = Literal["full", "sparse"]


def _valid_length(value: float, name: str) -> float:
    if value <= 0.0:
        raise ValueError(f"{name} must be positive")
    return float(value)


def ellipse_geometry(
    center: Point,
    length_m: float,
    width_m: float,
    *,
    rotation_deg: float = 0.0,
    segments: int = 48,
) -> list[Point]:
    """Return a rotated ellipse as a closed ring of projected points."""
    if segments < 12:
        raise ValueError("segments must be at least 12")
    length = _valid_length(length_m, "length_m")
    width = _valid_length(width_m, "width_m")
    angle = math.radians(rotation_deg)
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    points: list[Point] = []
    for index in range(segments):
        theta = 2.0 * math.pi * index / segments
        x = math.cos(theta) * length / 2.0
        y = math.sin(theta) * width / 2.0
        points.append(
            (
                center[0] + x * cos_a - y * sin_a,
                center[1] + x * sin_a + y * cos_a,
            )
        )
    points.append(points[0])
    return points


@dataclass(frozen=True)
class DropContour:
    """One depth contour inside a drop footprint."""

    depth_mm: float
    length_m: float
    width_m: float
    uniform_fraction: float = 1.0

    def __post_init__(self) -> None:
        _valid_length(self.depth_mm, "depth_mm")
        _valid_length(self.length_m, "length_m")
        _valid_length(self.width_m, "width_m")
        if not 0.0 < self.uniform_fraction <= 1.0:
            raise ValueError("uniform_fraction must be in (0, 1]")

    @property
    def area_m2(self) -> float:
        """Elliptical contour area in square metres."""
        return math.pi / 4.0 * self.length_m * self.width_m

    @property
    def area_ha(self) -> float:
        return self.area_m2 / 10_000.0

    @property
    def drops_to_uniform(self) -> int:
        """Drops needed to fill this contour to a uniform depth."""
        return math.ceil(1.0 / self.uniform_fraction)

    def geometry(self, center: Point, *, rotation_deg: float = 0.0) -> list[Point]:
        return ellipse_geometry(center, self.length_m, self.width_m, rotation_deg=rotation_deg)


@dataclass(frozen=True)
class DropPattern:
    """A nested drop pattern, ordered from shallow to deep contours."""

    aircraft: str
    fuel_type: str
    canopy: str
    contours: tuple[DropContour, ...]

    def __post_init__(self) -> None:
        if not self.contours:
            raise ValueError("a drop pattern needs at least one contour")
        depths = [contour.depth_mm for contour in self.contours]
        if depths != sorted(depths):
            raise ValueError("contours must be ordered from shallow to deep")
        if len(set(depths)) != len(depths):
            raise ValueError("contour depths must be unique")

    @property
    def shallowest(self) -> DropContour:
        return self.contours[0]

    @property
    def deepest(self) -> DropContour:
        return self.contours[-1]

    def effective_contour(self, required_depth_mm: float) -> DropContour | None:
        """Return the smallest contour that meets the required depth."""
        for contour in self.contours:
            if contour.depth_mm >= required_depth_mm:
                return contour
        return None

    def to_effect_events(
        self,
        center: Point,
        *,
        start_min: float,
        end_min: float,
        rotation_deg: float = 0.0,
        strength: float = 1.0,
        suppressant: Literal["water", "foam", "retardant"] = "water",
        effect_duration_min: float = 15.0,
    ) -> list[EffectEvent]:
        """Convert each contour to a time-bounded effect event."""
        return [
            EffectEvent(
                effect_id=f"drop-{self.aircraft}-{contour.depth_mm:g}mm",
                source_id=f"{self.aircraft}-{contour.depth_mm:g}mm",
                kind=suppressant,
                start_min=start_min,
                end_min=end_min,
                geometry=contour.geometry(center, rotation_deg=rotation_deg),
                width_m=0.0,
                coverage_l_m2=contour.depth_mm,
                strength=max(0.0, min(1.0, strength)),
                decay_min=effect_duration_min,
            )
            for contour in self.contours
        ]


def is_breached(
    *,
    flame_length_m: float,
    flame_front_depth_m: float,
    drop_width_m: float,
) -> bool:
    """Apply the McFayden et al. half-drop-width breach test."""
    _valid_length(flame_length_m, "flame_length_m")
    _valid_length(flame_front_depth_m, "flame_front_depth_m")
    _valid_length(drop_width_m, "drop_width_m")
    half_width = drop_width_m / 2.0
    return flame_front_depth_m > half_width or flame_length_m > half_width


def cl415_c2_full_pattern(fireline_intensity_kw_m: float) -> DropPattern:
    """Return a C-2 full-canopy CL-415 pattern at one intensity class.

    The catalogue is intentionally small: it encodes the effective dimensions
    and required depths shown in McFayden et al. (2023), Tables 8-2/8-3.
    """
    if fireline_intensity_kw_m <= 0.0:
        raise ValueError("fireline_intensity_kw_m must be positive")
    if fireline_intensity_kw_m <= 10.0:
        contour = DropContour(depth_mm=0.25, length_m=130.0, width_m=50.0)
    elif fireline_intensity_kw_m <= 900.0:
        contour = DropContour(depth_mm=0.5, length_m=90.0, width_m=40.0)
    elif fireline_intensity_kw_m <= 1_300.0:
        contour = DropContour(depth_mm=0.75, length_m=70.0, width_m=30.0)
    else:
        # The guide marks CL-415 cells above 1,300 kW/m as breached.
        contour = DropContour(depth_mm=1.5, length_m=30.0, width_m=20.0)
    return DropPattern(
        aircraft="CL-415",
        fuel_type="C-2",
        canopy="full",
        contours=(contour,),
    )


@dataclass(frozen=True)
class DropEffectiveness:
    """One row of the guide's operational drop comparison."""

    aircraft: str
    fuel_type: str
    canopy: str
    fireline_intensity_kw_m: float
    required_depth_mm: float
    effective_length_m: float | None
    effective_width_m: float | None
    drops_to_hold_100m: int | None
    breached: bool

    @property
    def effective_area_ha(self) -> float | None:
        if self.effective_length_m is None or self.effective_width_m is None:
            return None
        return math.pi / 4.0 * self.effective_length_m * self.effective_width_m / 10_000.0


def cl415_c2_full_effectiveness(fireline_intensity_kw_m: float) -> DropEffectiveness:
    """Return the CL-415 C-2 full-canopy row for an intensity class."""
    if fireline_intensity_kw_m <= 0.0:
        raise ValueError("fireline_intensity_kw_m must be positive")
    if fireline_intensity_kw_m <= 10.0:
        return DropEffectiveness("CL-415", "C-2", "full", fireline_intensity_kw_m, 0.25, 130, 50, 1, False)
    if fireline_intensity_kw_m <= 900.0:
        return DropEffectiveness("CL-415", "C-2", "full", fireline_intensity_kw_m, 0.5, 90, 40, 1, False)
    if fireline_intensity_kw_m <= 1_300.0:
        return DropEffectiveness("CL-415", "C-2", "full", fireline_intensity_kw_m, 0.75, 70, 30, 2, False)
    if fireline_intensity_kw_m <= 3_200.0:
        return DropEffectiveness("CL-415", "C-2", "full", fireline_intensity_kw_m, 1.5, None, None, None, True)
    return DropEffectiveness("CL-415", "C-2", "full", fireline_intensity_kw_m, 2.5, None, None, None, True)


__all__ = [
    "DropContour",
    "DropEffectiveness",
    "DropPattern",
    "cl415_c2_full_effectiveness",
    "cl415_c2_full_pattern",
    "ellipse_geometry",
    "is_breached",
]
