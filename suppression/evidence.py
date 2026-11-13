"""Empirical suppression constants used by the P179 prototype.

Sources:
- Wheatley (2024), Chapter 5: IR-monitored experimental burns.
- McFayden et al. (2023): operational drop holding and intensity limits.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class HoldEvidence:
    """One measured or operational hold-time estimate."""

    label: str
    seconds: float
    source: str
    note: str = ""

    @property
    def minutes(self) -> float:
        return self.seconds / 60.0


# Wheatley 2024, Chapter 5. Mean values; uncertainty is deliberately explicit.
WHEATLEY_ROS_REDUCTION_M_MIN = 0.5
WHEATLEY_ROS_REDUCTION_SD_M_MIN = 0.7
WHEATLEY_INTENSITY_REDUCTION_KW_M = 72.0
WHEATLEY_INTENSITY_REDUCTION_SD_KW_M = 159.0
WHEATLEY_HOLD_SECONDS = 123.0
WHEATLEY_HOLD_SD_SECONDS = 117.0
WHEATLEY_HIGH_WATER_HOLD_SECONDS = 187.0
WHEATLEY_INDIRECT_HIGH_WATER_HOLD_SECONDS = 243.0

# Rainfall-equivalent water applied in the experimental burns, kg/m2 = mm.
WHEATLEY_DIRECT_LOW_DEPTH_MM = 1.4
WHEATLEY_DIRECT_HIGH_DEPTH_MM = 2.3
WHEATLEY_INDIRECT_LOW_DEPTH_MM = 0.7
WHEATLEY_INDIRECT_HIGH_DEPTH_MM = 1.1

# McFayden et al. 2023: effective aerial drops are assumed to hold for at least
# one hour; Wheatley argues the operational intensity limit may be nearer
# 10,000 kW/m than the commonly quoted 4,000 kW/m.
MC_FAYDEN_HOLD_MINUTES = 60.0
MC_FAYDEN_UPPER_INTENSITY_KW_M = 10_000.0

Tactic = Literal["direct", "indirect"]
WaterAmount = Literal["low", "high"]


def hold_time(
    *,
    tactic: Tactic,
    water: WaterAmount,
    source: Literal["wheatley", "mcfayden"] = "wheatley",
) -> HoldEvidence:
    """Return a documented hold-time estimate."""
    if source == "mcfayden":
        return HoldEvidence(
            "effective aerial drop",
            MC_FAYDEN_HOLD_MINUTES * 60.0,
            "McFayden et al. 2023",
            "Assumed operational hold of at least one hour.",
        )
    if tactic == "direct" and water == "low":
        seconds = WHEATLEY_HOLD_SECONDS
        label = "direct low water"
    elif tactic == "direct" and water == "high":
        seconds = WHEATLEY_HIGH_WATER_HOLD_SECONDS
        label = "direct high water"
    elif tactic == "indirect" and water == "low":
        seconds = WHEATLEY_HOLD_SECONDS
        label = "indirect low water"
    else:
        seconds = WHEATLEY_INDIRECT_HIGH_WATER_HOLD_SECONDS
        label = "indirect high water"
    return HoldEvidence(
        label,
        seconds,
        "Wheatley 2024, Chapter 5",
        "IR-monitored experimental burns; mean hold, not a guaranteed duration.",
    )


def suppressed_ros_m_min(
    pre_suppression_ros_m_min: float,
    *,
    reduction_m_min: float = WHEATLEY_ROS_REDUCTION_M_MIN,
) -> float:
    """Apply the observed absolute ROS reduction, floored at zero."""
    if pre_suppression_ros_m_min < 0.0:
        raise ValueError("pre_suppression_ros_m_min must be non-negative")
    if reduction_m_min < 0.0:
        raise ValueError("reduction_m_min must be non-negative")
    return max(0.0, pre_suppression_ros_m_min - reduction_m_min)


__all__ = [
    "HoldEvidence",
    "MC_FAYDEN_HOLD_MINUTES",
    "MC_FAYDEN_UPPER_INTENSITY_KW_M",
    "WHEATLEY_DIRECT_HIGH_DEPTH_MM",
    "WHEATLEY_DIRECT_LOW_DEPTH_MM",
    "WHEATLEY_HIGH_WATER_HOLD_SECONDS",
    "WHEATLEY_HOLD_SECONDS",
    "WHEATLEY_INDIRECT_HIGH_DEPTH_MM",
    "WHEATLEY_INDIRECT_HIGH_WATER_HOLD_SECONDS",
    "WHEATLEY_INDIRECT_LOW_DEPTH_MM",
    "WHEATLEY_INTENSITY_REDUCTION_KW_M",
    "WHEATLEY_ROS_REDUCTION_M_MIN",
    "hold_time",
    "suppressed_ros_m_min",
]
