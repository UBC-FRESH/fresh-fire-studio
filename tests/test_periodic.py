from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from suppression.periodic import PeriodicWetSchedule

ROOT = Path(__file__).resolve().parents[1]


def test_periodic_wetting_hold_and_rewet() -> None:
    mask = np.zeros((3, 3), dtype=bool)
    mask[1, 1] = True
    wet = PeriodicWetSchedule(
        mask=mask,
        depth_mm=1.5,
        required_depth_mm=0.75,
        decay_min=60.0,
        interval_min=30.0,
        start_min=600.0,
        end_min=900.0,
    )
    assert wet.effective_hold_min == 30.0
    assert wet.is_suppressed(1, 1, 600.0)
    assert wet.is_suppressed(1, 1, 620.0)
    assert wet.is_suppressed(1, 1, 630.0)
    assert not wet.is_suppressed(0, 0, 620.0)
    assert wet.depth_at(1, 1, 620.0) == 1.0
    assert wet.depth_at(1, 1, 630.0) == 1.5


def test_rewetting_artifact_shows_interval_threshold_and_fleet_bound() -> None:
    payload = json.loads(
        (ROOT / "suppression/proofs/2003-526-perfect-rewetting.json").read_text(
            encoding="utf-8"
        )
    )
    results = {
        (float(row["interval_min"]), float(row["depth_mm"])): row
        for row in payload["results"]
    }
    reference = payload["reference_depth_mm"]
    assert results[(15.0, reference)]["feasible"] is True
    assert results[(15.0, reference)]["native_area_ha"] == 3504.0
    assert results[(18.0, reference)]["feasible"] is False
    assert results[(30.0, 1.5)]["feasible"] is True
    assert results[(60.0, 3.0)]["feasible"] is False
    assert payload["minimum_feasible"]["aircraft_lower_bound"] == 54
