from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_replay_page_and_data_are_consistent() -> None:
    page = (ROOT / "portal/suppression.html").read_text(encoding="utf-8")
    data = json.loads((ROOT / "portal/static/suppression-mission.json").read_text())
    assert "EVIDENCE ENSEMBLE" in page
    assert "mode-control" in page
    assert "assistant-panel" in page
    assert "assistantScript" in page
    assert len(data["drops"]) == 21
    assert data["results"]["realistic"]["area_ha"] == 5325.0
    assert data["results"]["realistic"]["containment_probability"] == 0.0
    assert data["results"]["control"]["area_ha"] == 3574.7
    assert data["results"]["control"]["ros_correlation"] < -0.5
    assert len(data["model_extent"]) == 19
    assert (ROOT / "portal/static/suppression-evidence-ensemble.json").exists()
    assert (ROOT / "portal/static/suppression-evidence-control.json").exists()
    assert len(data["observed_extent"]) == 3
    assert data["observed_ha"] == 520.0
