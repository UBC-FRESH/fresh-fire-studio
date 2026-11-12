from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from suppression.models import Scenario

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "suppression" / "scenarios" / "2003-526-demo.json"


def load() -> dict:
    return json.loads(SCENARIO.read_text(encoding="utf-8"))


def test_example_scenario_validates() -> None:
    scenario = Scenario.model_validate(load())
    assert scenario.scenario_id == "2003-526-suppression-demo"
    assert len(scenario.resources) == 6
    assert len(scenario.tasks) == 8


def test_effect_contract_from_lines_and_drops() -> None:
    scenario = Scenario.model_validate(load())
    events = scenario.effect_events()
    assert len(events) == 5
    assert {event.kind for event in events} == {"line", "water", "retardant"}
    assert all(event.end_min >= event.start_min for event in events)


def test_unknown_resource_is_rejected() -> None:
    payload = load()
    payload["tasks"][0]["resource_id"] = "missing"
    with pytest.raises(ValidationError, match="unknown resource"):
        Scenario.model_validate(payload)


def test_double_booked_resource_is_rejected() -> None:
    payload = load()
    payload["tasks"][0]["start_min"] = 130
    payload["tasks"][0]["end_min"] = 190
    with pytest.raises(ValidationError, match="double-booked"):
        Scenario.model_validate(payload)


def test_drop_capacity_is_enforced() -> None:
    payload = deepcopy(load())
    payload["drops"][2]["coverage_l_m2"] = 20
    with pytest.raises(ValidationError, match="needs"):
        Scenario.model_validate(payload)


def test_line_must_fit_its_task() -> None:
    payload = load()
    payload["lines"][0]["constructed_end_min"] = 300
    with pytest.raises(ValidationError, match="must fall within task"):
        Scenario.model_validate(payload)
