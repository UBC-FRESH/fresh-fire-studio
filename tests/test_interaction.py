from __future__ import annotations

import numpy as np

from suppression.interaction import analyze_wet_interaction
from suppression.wet import WetDrop, WetSchedule


def test_interaction_counts_arrival_states() -> None:
    fraction = np.zeros((3, 3), dtype=float)
    fraction[0, 0] = 1.0  # arrives after wet
    fraction[0, 1] = 1.0  # arrives during wet
    fraction[0, 2] = 1.0  # arrives before wet
    wet = WetSchedule(
        required_depth_mm=0.5,
        drops=(
            WetDrop(
                drop_id="d",
                fraction=fraction,
                depth_mm=1.0,
                start_min=10.0,
                end_min=20.0,
                duration_min=10.0,
            ),
        ),
    )
    ignition = np.full((3, 3), np.inf)
    ignition[0, 0] = 35.0
    ignition[0, 1] = 15.0
    ignition[0, 2] = 5.0
    result = analyze_wet_interaction(wet, ignition)
    assert result.wet_cells == 3
    assert result.wet_at_arrival == 1
    assert result.burned_after_wet == 1
    assert result.burned_before_wet == 1
    assert result.unburned == 0


def test_interaction_artifacts_exist() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    for name in (
        "2003-526-wet-interaction-continuous.json",
        "2003-526-wet-interaction-lead150.json",
        "2003-526-wet-interaction-arrival-timed.json",
    ):
        assert (root / "suppression/proofs" / name).exists()
