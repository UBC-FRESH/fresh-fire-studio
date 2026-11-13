from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from suppression.drop import DropContour, DropPattern, drop_to_pattern
from suppression.effects import coverage_fraction
from suppression.models import Scenario
from suppression.wet import build_wet_schedule

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "suppression/scenarios/2003-526-drop-proof.json"
ARTIFACT = ROOT / "suppression/proofs/2003-526-native-drop.json"
SUBCELL_ARTIFACT = ROOT / "suppression/proofs/2003-526-native-drop-line-subcell.json"
GRID = dict(xll=487700.0, yll=5722700.0, nrows=76, ncols=90, cell_size_m=100.0)


def test_coverage_fraction_handles_subcell_drop() -> None:
    geometry = DropContour(1.0, 100.0, 50.0).geometry((492150.0, 5726250.0))
    fraction = coverage_fraction(geometry, **GRID)
    assert fraction.max() > 0.3
    assert fraction.max() < 0.5
    assert int((fraction > 0).sum()) == 1


def test_drop_to_pattern_preserves_depth_and_dimensions() -> None:
    scenario = Scenario.model_validate_json(SCENARIO.read_text(encoding="utf-8"))
    pattern = drop_to_pattern(scenario.drops[0])
    assert pattern.deepest.depth_mm == 1.0
    assert pattern.deepest.length_m == 100.0
    assert pattern.deepest.width_m == 50.0


def test_stacked_drops_cross_threshold_then_decay() -> None:
    scenario = Scenario.model_validate_json(SCENARIO.read_text(encoding="utf-8"))
    wet = build_wet_schedule(
        scenario,
        required_depth_mm=0.75,
        **GRID,
    )
    assert len(wet.drops) == 3
    row = 76 - 1 - int((5726250.0 - 5722700.0) // 100)
    col = int((492150.0 - 487700.0) // 100)
    assert not wet.is_suppressed(row, col, 600)
    assert wet.is_suppressed(row, col, 620)
    assert wet.is_suppressed(row, col, 660)
    assert not wet.is_suppressed(row, col, 900)


def test_subcell_mean_depth_drives_partial_ros_factor() -> None:
    scenario = Scenario.model_validate_json(SCENARIO.read_text(encoding="utf-8"))
    wet = build_wet_schedule(
        scenario,
        required_depth_mm=0.75,
        **GRID,
        subcell_cell_size_m=10,
    )
    row = 76 - 1 - int((5726250.0 - 5722700.0) // 100)
    col = int((492150.0 - 487700.0) // 100)
    depth = wet.drops[0].depth_at(row, col, 620)
    assert 0.3 < depth < 0.5
    assert 0.0 < wet.wetness_at(row, col, 620) < 1.0
    assert 0.0 < wet.ros_factor_at(row, col, 620) < 1.0


def test_wet_artifact_records_coupling_and_resolution_limit() -> None:
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert payload["method"]["drops"].startswith("temporary wet threshold")
    assert payload["wet_schedule"]["required_depth_mm"] == 0.75
    assert len(payload["wet_schedule"]["drops"]) == 3
    assert payload["wet_schedule"]["drops"][0]["covered_cells"] == 1
    assert payload["native"]["area_sim_ha"] == payload["free_burn"]["area_sim_ha"]


def test_subcell_artifact_records_factor_mode() -> None:
    payload = json.loads(SUBCELL_ARTIFACT.read_text())
    assert "sub-cell" in payload["method"]["drops"]
    assert payload["native"]["area_sim_ha"] == payload["free_burn"]["area_sim_ha"]
