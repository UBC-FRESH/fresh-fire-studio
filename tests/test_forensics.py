from __future__ import annotations

import json
from pathlib import Path

from suppression.forensics import classify_breach

ROOT = Path(__file__).resolve().parents[1]


def test_classify_breach_distinguishes_hold_pre_wet_and_post_expiry() -> None:
    common = {
        "burnable": True,
        "first_wet_min": 100.0,
        "last_wet_min": 160.0,
        "free_arrival_min": 150.0,
        "suppressed_at_ignition": False,
    }
    assert classify_breach(**common, ignition_min=float("inf")) == "held"
    assert classify_breach(**common, ignition_min=90.0) == "pre_wet"
    assert classify_breach(**common, ignition_min=170.0) == "post_expiry"
    assert (
        classify_breach(
            **{**common, "suppressed_at_ignition": True},
            ignition_min=155.0,
        )
        == "burned_while_wet"
    )
    assert (
        classify_breach(
            **{key: value for key, value in common.items() if key != "burnable"},
            burnable=False,
            ignition_min=140.0,
        )
        == "nonburnable"
    )


def test_breach_artifact_shows_post_expiry_breaches() -> None:
    payload = json.loads(
        (
            ROOT / "suppression/proofs/2003-526-line-breach-forensics.json"
        ).read_text(encoding="utf-8")
    )
    summary = payload["summary"]
    assert summary["line_cells"] == 76
    assert summary["burnable_cells"] == 71
    assert summary["breached_cells"] == 71
    assert summary["classes"] == {"post_expiry": 71, "nonburnable": 5}
    assert summary["first_breach"]["class"] == "post_expiry"
