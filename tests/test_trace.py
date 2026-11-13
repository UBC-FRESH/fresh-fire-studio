from __future__ import annotations

import numpy as np

from suppression.trace import trace_targets
from suppression.wet import WetDrop, WetSchedule


def test_trace_reports_low_depth_and_timing() -> None:
    fraction = np.zeros((3, 3), dtype=float)
    fraction[1, 1] = 1.0
    wet = WetSchedule(
        required_depth_mm=0.75,
        drops=(
            WetDrop("d", fraction, 0.5, 10.0, 20.0, 10.0),
        ),
    )
    ignition = np.full((3, 3), np.inf)
    ignition[1, 1] = 15.0
    trace = trace_targets(
        wet, ignition, [(15.0, 15.0)], xll=0.0, yll=0.0, nrows=3, ncols=3, cell_size_m=10.0
    )[0]
    assert trace.row == 1 and trace.col == 1
    assert trace.combined_at_arrival_mm == 0.5
    assert not trace.wet_at_arrival


def test_trace_artifact_exists() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    assert (root / "suppression/proofs/2003-526-target-wetness-trace-5targets.json").exists()
    assert (root / "suppression/proofs/2003-526-wet-interaction-ring-200air.json").exists()
