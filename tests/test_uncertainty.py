from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from suppression.models import Scenario
from suppression.uncertainty import (
    DEFAULT_RANGES,
    EvidenceRange,
    apply_sample_to_scenario,
    sample_evidence,
    summarize_ensemble,
)

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "suppression/scenarios/2003-526-drop-line-proof.json"


def test_sampling_is_reproducible_and_bounded() -> None:
    first = [sample_evidence(np.random.default_rng(7)) for _ in range(1)]
    second = [sample_evidence(np.random.default_rng(7)) for _ in range(1)]
    assert first == second
    sample = first[0]
    for name, value in sample.to_dict().items():
        bounds = DEFAULT_RANGES[name]
        assert bounds.lower <= value <= bounds.upper


def test_invalid_range_is_rejected() -> None:
    import pytest

    with pytest.raises(ValueError):
        EvidenceRange("bad", mean=2.0, sd=0.1, lower=0.0, upper=1.0)


def test_scenario_projection_updates_only_drop_fields() -> None:
    scenario = Scenario.model_validate_json(SCENARIO.read_text(encoding="utf-8"))
    sample = sample_evidence(np.random.default_rng(1))
    projected = apply_sample_to_scenario(scenario, sample)
    assert len(projected.drops) == len(scenario.drops)
    assert all(drop.coverage_l_m2 == sample.water_depth_mm for drop in projected.drops)
    assert all(drop.effect_duration_min == sample.hold_min for drop in projected.drops)
    assert all(drop.canopy_penetration == sample.canopy_penetration for drop in projected.drops)
    assert projected.tasks == scenario.tasks


def test_summary_reports_envelope_and_correlations() -> None:
    rng = np.random.default_rng(3)
    samples = [sample_evidence(rng) for _ in range(5)]
    areas = [5000.0, 5100.0, 5200.0, 5300.0, 5400.0]
    summary = summarize_ensemble(areas, 5325.0, samples=samples)
    assert summary["n"] == 5
    assert summary["p05_area_ha"] <= summary["median_area_ha"] <= summary["p95_area_ha"]
    assert summary["probability_any_reduction"] == 0.8
    assert "correlation_ros_reduction_m_min" in summary


def test_ensemble_artifact_if_present() -> None:
    path = ROOT / "suppression/proofs/2003-526-evidence-ensemble.json"
    assert path.exists()
    payload = json.loads(path.read_text())
    assert payload["n"] == 32
    assert len(payload["samples"]) == payload["n"]
    assert payload["summary"]["probability_any_reduction"] == 0.0
    assert payload["summary"]["sd_area_ha"] == 0.0
