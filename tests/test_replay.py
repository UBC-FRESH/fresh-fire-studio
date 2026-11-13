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
    assert "methods-panel" in page
    assert "Wheatley 2024" in page
    assert (ROOT / "portal/static/p179-case-study.pdf").exists()
    assert len(data["sorties"]) == 21
    assert len(data["aircraft"]) == 3
    assert all(sortie["phases"] for sortie in data["sorties"])
    assert {"scoop", "climb", "cruise_out", "drop", "turn", "cruise_back"} <= {
        phase["kind"] for sortie in data["sorties"] for phase in sortie["phases"]
    }
    assert data["lake"]["radius_m"] > 0
    assert len(data["fire_line"]) == 21
    assert data["logistics"]["sorties"] == 21
    assert data["logistics"]["total_water_l"] == 126000.0
    assert data["logistics"]["litres_per_hour"] > 100000
    assert data["logistics"]["water_balance"]["line_mean_depth_mm"] < 0.75
    assert data["logistics"]["water_balance"]["additional_sorties"] > 0
    assert data["delivery_sweep"]["two_pass_three_aircraft"]["deficit_l"] == 0.0
    assert data["delivery_sweep"]["two_pass_three_aircraft"]["native_area_ha"] == 5325.0
    for name in ("2003-526-native-cycle-3pass", "2003-526-native-cycle-4pass", "2003-526-native-cycle-lead60"):
        assert (ROOT / "suppression/proofs" / f"{name}.json").exists()
    assert (ROOT / "suppression/proofs/2003-526-fine-grid-2pass.json").exists()
    assert (ROOT / "suppression/proofs/2003-526-fine-grid-2pass-25m.json").exists()
    assert (ROOT / "suppression/proofs/2003-526-native-cycle-adaptive.json").exists()
    assert (ROOT / "suppression/proofs/2003-526-native-cycle-continuous.json").exists()
    assert data["results"]["realistic"]["area_ha"] == 5325.0
    assert data["results"]["realistic"]["containment_probability"] == 0.0
    assert data["results"]["control"]["area_ha"] == 3574.7
    assert data["results"]["control"]["ros_correlation"] < -0.5
    assert len(data["model_extent"]) == 19
    assert (ROOT / "portal/static/suppression-evidence-ensemble.json").exists()
    assert (ROOT / "portal/static/suppression-evidence-control.json").exists()
    assert len(data["observed_extent"]) == 3
    assert data["observed_ha"] == 520.0
