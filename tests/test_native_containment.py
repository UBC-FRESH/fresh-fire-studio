from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from suppression.models import Scenario
from suppression.native_growth import build_containment_schedule

ROOT = Path(__file__).resolve().parents[1]
GRID = dict(xll=487700.0, yll=5722700.0, nrows=76, ncols=90, cell_size_m=100.0)


def load(name: str) -> Scenario:
    path = ROOT / "suppression" / "scenarios" / f"{name}.json"
    return Scenario.model_validate_json(path.read_text(encoding="utf-8"))


def test_temporal_schedule_has_growing_start_times() -> None:
    schedule = build_containment_schedule(load("2003-526-temporal-proof"), **GRID)
    starts = schedule.start_min[np.isfinite(schedule.start_min)]
    assert len(starts) == 152
    assert starts.min() == 60
    assert starts.max() == 1440
    assert np.all(schedule.end_min[np.isfinite(schedule.end_min)] == 22200)


def test_breach_schedule_ends_at_breach_time() -> None:
    schedule = build_containment_schedule(load("2003-526-breach-proof"), **GRID)
    cells = np.argwhere(np.isfinite(schedule.start_min))
    row, col = cells[0]
    assert schedule.is_contained(int(row), int(col), 7000)
    assert not schedule.is_contained(int(row), int(col), 7200)
    assert np.all(schedule.end_min[np.isfinite(schedule.end_min)] == 7200)


def test_late_schedule_starts_after_growth() -> None:
    schedule = build_containment_schedule(load("2003-526-late-line-proof"), **GRID)
    starts = schedule.start_min[np.isfinite(schedule.start_min)]
    assert len(starts) == 152
    assert starts.min() == 18060
    assert starts.max() == 19440


def test_schedule_is_burnable_after_containment_ends() -> None:
    schedule = build_containment_schedule(load("2003-526-breach-proof"), **GRID)
    row, col = np.argwhere(np.isfinite(schedule.start_min))[0]
    base = np.ones((76, 90), dtype=bool)
    assert not schedule.is_burnable(base, int(row), int(col), 6000)
    assert schedule.is_burnable(base, int(row), int(col), 7200)


def test_native_dispatch_artifact_uses_dispatch_timing() -> None:
    payload = json.loads(
        (ROOT / "suppression/proofs/2003-526-native-dispatch.json").read_text()
    )
    assert payload["method"]["line_timing"] == "dispatch-derived"
    assert payload["dispatch"] is not None
    assert payload["native"]["area_sim_ha"] < payload["free_burn"]["area_sim_ha"]


def test_native_artifacts_record_timing_effect() -> None:
    fast = json.loads((ROOT / "suppression/proofs/2003-526-native-fast.json").read_text())
    slow = json.loads((ROOT / "suppression/proofs/2003-526-native.json").read_text())
    breach = json.loads((ROOT / "suppression/proofs/2003-526-native-breach.json").read_text())
    late = json.loads((ROOT / "suppression/proofs/2003-526-native-late-line.json").read_text())
    assert fast["native"]["area_sim_ha"] == 3113
    assert slow["native"]["area_sim_ha"] == 5183
    assert breach["native"]["area_sim_ha"] == 5325
    assert late["native"]["area_sim_ha"] == 5325
    assert slow["native"]["area_sim_ha"] > fast["native"]["area_sim_ha"]
