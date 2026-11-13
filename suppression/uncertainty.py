"""Evidence-bounded parameter sampling for suppression experiments."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .models import Scenario


@dataclass(frozen=True)
class EvidenceRange:
    """A bounded uncertainty range for one model input."""

    name: str
    mean: float
    sd: float
    lower: float
    upper: float
    units: str = ""

    def __post_init__(self) -> None:
        if self.sd < 0.0:
            raise ValueError("sd must be non-negative")
        if self.upper < self.lower:
            raise ValueError("upper must be >= lower")
        if not self.lower <= self.mean <= self.upper:
            raise ValueError("mean must lie within the bounds")

    def sample(self, rng: np.random.Generator) -> float:
        value = rng.normal(self.mean, self.sd) if self.sd > 0.0 else self.mean
        return float(np.clip(value, self.lower, self.upper))


@dataclass(frozen=True)
class EvidenceSample:
    """One sampled suppression-effect parameter set."""

    ros_reduction_m_min: float
    hold_min: float
    water_depth_mm: float
    canopy_penetration: float
    required_depth_mm: float

    def to_dict(self) -> dict[str, float]:
        return {
            "ros_reduction_m_min": self.ros_reduction_m_min,
            "hold_min": self.hold_min,
            "water_depth_mm": self.water_depth_mm,
            "canopy_penetration": self.canopy_penetration,
            "required_depth_mm": self.required_depth_mm,
        }


DEFAULT_RANGES = {
    "ros_reduction_m_min": EvidenceRange(
        "ROS reduction", mean=0.5, sd=0.7, lower=0.0, upper=2.5, units="m/min"
    ),
    "hold_min": EvidenceRange(
        "suppression hold", mean=2.05, sd=1.95, lower=0.25, upper=60.0, units="min"
    ),
    "water_depth_mm": EvidenceRange(
        "water depth", mean=1.8, sd=0.45, lower=0.7, upper=2.5, units="mm"
    ),
    "canopy_penetration": EvidenceRange(
        "canopy penetration", mean=0.75, sd=0.2, lower=0.2, upper=1.0, units="fraction"
    ),
    "required_depth_mm": EvidenceRange(
        "required depth", mean=0.65, sd=0.15, lower=0.25, upper=1.5, units="mm"
    ),
}


def sample_evidence(
    rng: np.random.Generator,
    ranges: dict[str, EvidenceRange] | None = None,
) -> EvidenceSample:
    """Sample one bounded evidence set."""
    selected = ranges or DEFAULT_RANGES
    return EvidenceSample(
        ros_reduction_m_min=selected["ros_reduction_m_min"].sample(rng),
        hold_min=selected["hold_min"].sample(rng),
        water_depth_mm=selected["water_depth_mm"].sample(rng),
        canopy_penetration=selected["canopy_penetration"].sample(rng),
        required_depth_mm=selected["required_depth_mm"].sample(rng),
    )


def apply_sample_to_scenario(scenario: Scenario, sample: EvidenceSample) -> Scenario:
    """Return a scenario with the sample applied to every drop."""
    drops = [
        drop.model_copy(
            update={
                "coverage_l_m2": sample.water_depth_mm,
                "effect_duration_min": sample.hold_min,
                "canopy_penetration": sample.canopy_penetration,
            }
        )
        for drop in scenario.drops
    ]
    return scenario.model_copy(update={"drops": drops})


def summarize_ensemble(
    areas: list[float],
    free_area: float,
    *,
    samples: list[EvidenceSample] | None = None,
) -> dict[str, object]:
    """Summarize final-area outcomes and parameter correlations."""
    array = np.asarray(areas, dtype=float)
    if array.size == 0:
        raise ValueError("at least one area is required")
    payload: dict[str, object] = {
        "n": int(array.size),
        "mean_area_ha": float(array.mean()),
        "median_area_ha": float(np.median(array)),
        "sd_area_ha": float(array.std(ddof=0)),
        "p05_area_ha": float(np.percentile(array, 5)),
        "p95_area_ha": float(np.percentile(array, 95)),
        "free_area_ha": float(free_area),
        "probability_any_reduction": float(np.mean(array < free_area - 1e-9)),
        "probability_area_below_free": float(np.mean(array < free_area - 1e-9)),
    }
    if samples:
        for key in samples[0].to_dict():
            values = np.asarray([getattr(sample, key) for sample in samples], dtype=float)
            if values.std() == 0.0 or array.std() == 0.0:
                payload[f"correlation_{key}"] = 0.0
            else:
                payload[f"correlation_{key}"] = float(np.corrcoef(values, array)[0, 1])
    return payload


__all__ = [
    "DEFAULT_RANGES",
    "EvidenceRange",
    "EvidenceSample",
    "apply_sample_to_scenario",
    "sample_evidence",
    "summarize_ensemble",
]
