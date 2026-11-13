"""Breach classification for the P184 line-forensics diagnostic."""

from __future__ import annotations

import math


def classify_breach(
    *,
    burnable: bool,
    first_wet_min: float,
    last_wet_min: float,
    free_arrival_min: float,
    ignition_min: float,
    suppressed_at_ignition: bool,
) -> str:
    """Classify one barrier cell in the coupled suppression run."""
    if not burnable:
        return "nonburnable"
    if not math.isfinite(ignition_min):
        return "held"
    if suppressed_at_ignition:
        return "burned_while_wet"
    if math.isfinite(first_wet_min) and ignition_min < first_wet_min:
        return "pre_wet"
    if math.isfinite(last_wet_min) and ignition_min > last_wet_min:
        return "post_expiry"
    if not math.isfinite(first_wet_min):
        return "never_wet"
    if math.isfinite(free_arrival_min) and ignition_min < free_arrival_min:
        return "before_free_arrival"
    return "other"


__all__ = ["classify_breach"]
