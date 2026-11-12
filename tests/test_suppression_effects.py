from __future__ import annotations

import json
from pathlib import Path

from suppression.effects import rasterize_effects
from suppression.models import EffectEvent

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / "suppression" / "proofs" / "2003-526.json"


def test_line_and_drop_effects_rasterize_to_separate_layers() -> None:
    line = EffectEvent(
        effect_id="line-1",
        source_id="line-1",
        kind="line",
        start_min=0,
        end_min=10,
        geometry=[(5.5, 0), (5.5, 10)],
        width_m=2,
    )
    drop = EffectEvent(
        effect_id="drop-1",
        source_id="drop-1",
        kind="water",
        start_min=0,
        end_min=1,
        geometry=[(1, 1), (3, 1), (3, 3), (1, 3)],
        width_m=0,
        coverage_l_m2=0.5,
    )
    effects = rasterize_effects(
        [line, drop],
        xll=0,
        yll=0,
        nrows=10,
        ncols=10,
        cell_size_m=1,
    )
    assert effects.line.any()
    assert effects.line.any(axis=1).sum() == 10
    assert effects.water.sum() == 4
    assert not effects.foam.any()
    assert not effects.retardant.any()
    assert (effects.containment == effects.line).all()


def test_2003_526_proof_records_a_real_area_reduction() -> None:
    payload = json.loads(PROOF.read_text(encoding="utf-8"))
    assert payload["case_id"] == "2003_526"
    assert payload["effect_layers"]["line_cells"] > 0
    assert payload["delta"]["area_reduction_ha"] > 0
    assert payload["contained"]["area_sim_ha"] < payload["free_burn"]["area_sim_ha"]
    assert payload["contained"]["iou"] > payload["free_burn"]["iou"]
