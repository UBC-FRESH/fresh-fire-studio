from __future__ import annotations

import json
from pathlib import Path

from suppression.models import LineState, Scenario
from suppression.temporal import (
    drop_strength_at,
    effects_at,
    line_cells_at,
    line_fraction_at,
    partial_line,
    timeline_breaks,
)

ROOT = Path(__file__).resolve().parents[1]
TEMPORAL = ROOT / "suppression" / "scenarios" / "2003-526-temporal-proof.json"
DEMO = ROOT / "suppression" / "scenarios" / "2003-526-demo.json"
ARTIFACT = ROOT / "suppression" / "proofs" / "2003-526-temporal.json"
GRID = dict(xll=487700.0, yll=5722700.0, nrows=76, ncols=90, cell_size_m=100.0)
DEMO_GRID = dict(xll=0.0, yll=0.0, nrows=20, ncols=20, cell_size_m=100.0)


def load(path: Path) -> Scenario:
    return Scenario.model_validate_json(path.read_text(encoding="utf-8"))


def test_line_fraction_follows_construction_window() -> None:
    line = load(TEMPORAL).lines[0]
    assert line_fraction_at(line, 0) == 0
    assert line_fraction_at(line, 720) == 0.5
    assert line_fraction_at(line, 1440) == 1
    assert line_fraction_at(line, 2000) == 1


def test_breached_and_planned_lines_stop_containing() -> None:
    line = load(TEMPORAL).lines[0]
    breached = line.model_copy(update={"state": LineState.BREACHED})
    planned = line.model_copy(update={"state": LineState.PLANNED})
    assert line_fraction_at(breached, 720) == 0.5
    assert line_fraction_at(breached, 1440) == 0
    assert line_fraction_at(planned, 1440) == 0


def test_partial_line_interpolates_by_length() -> None:
    assert partial_line([(0, 0), (10, 0)], 0) == []
    assert partial_line([(0, 0), (10, 0)], 0.5) == [(0, 0), (5.0, 0.0)]
    assert partial_line([(0, 0), (10, 0)], 1) == [(0, 0), (10, 0)]


def test_drop_strength_decays_linearly_after_the_drop() -> None:
    drop = load(DEMO).drops[0]
    assert drop_strength_at(drop, 120) == drop.canopy_penetration
    assert drop_strength_at(drop, 140) == drop.canopy_penetration
    assert drop_strength_at(drop, 144) == drop.canopy_penetration * 0.5
    assert drop_strength_at(drop, 149) == 0


def test_line_cells_grow_with_construction() -> None:
    scenario = load(TEMPORAL)
    cells = [line_cells_at(scenario, t, **GRID) for t in (0, 720, 1440, 2000)]
    assert cells[0] == 0
    assert 0 < cells[1] < cells[2]
    assert cells[2] == cells[3]


def test_drop_layer_disappears_after_decay() -> None:
    scenario = load(DEMO)
    wet = effects_at(scenario, 130, **DEMO_GRID)
    dry = effects_at(scenario, 149, **DEMO_GRID)
    assert wet.water.any()
    assert not dry.water.any()


def test_timeline_breaks_include_construction_and_decay() -> None:
    breaks = timeline_breaks(load(DEMO))
    assert 0 in breaks
    assert 240 in breaks
    assert 148 in breaks
    assert 1440 in breaks


def test_temporal_artifact_preserves_area_reduction() -> None:
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert payload["temporal"]["area_sim_ha"] < payload["free_burn"]["area_sim_ha"]
    assert payload["line_cells_by_time"]["0.0"] == 0
    assert payload["line_cells_by_time"]["1440.0"] == 152
    assert payload["line_cells_by_time"]["22200.0"] == 152
