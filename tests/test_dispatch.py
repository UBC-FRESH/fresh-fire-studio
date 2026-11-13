from __future__ import annotations

from pathlib import Path

from suppression.dispatch import dispatch_scenario
from suppression.models import (
    Base,
    Line,
    LineState,
    Resource,
    ResourceKind,
    Scenario,
    Task,
    TaskKind,
)

ROOT = Path(__file__).resolve().parents[1]


def make_scenario(*, available_end: float = 600.0, task_end: float = 200.0) -> Scenario:
    return Scenario(
        scenario_id="dispatch-test",
        fire_slug="test-fire",
        timeline_end_min=1440,
        bases=[Base(id="base", x=0, y=0)],
        resources=[
            Resource(
                id="crew",
                kind=ResourceKind.GROUND_CREW,
                home_base_id="base",
                crew_size=4,
                speed_kmh=60,
                line_rate_m_h=600,
                available_start_min=0,
                available_end_min=available_end,
            )
        ],
        tasks=[
            Task(
                id="assess",
                resource_id="crew",
                kind=TaskKind.ASSESS,
                start_min=0,
                end_min=10,
                target=[(0, 0)],
            ),
            Task(
                id="line-task",
                resource_id="crew",
                kind=TaskKind.CONSTRUCT_LINE,
                start_min=10,
                end_min=task_end,
                line_id="line",
                target=[(0, 6000), (0, 6600)],
            ),
        ],
        lines=[
            Line(
                id="line",
                task_id="line-task",
                points=[(0, 6000), (0, 6600)],
                width_m=2,
                constructed_start_min=10,
                constructed_end_min=task_end,
                state=LineState.HELD,
            )
        ],
    )


def test_travel_and_line_service_time() -> None:
    result = dispatch_scenario(make_scenario())
    line = next(item for item in result.assignments if item.task_id == "line-task")
    assert line.travel_min == 6.0
    assert line.actual_start_min == 16.0
    assert line.service_min == 60.0
    assert line.actual_end_min == 76.0
    assert line.line_length_m == 600.0
    assert not line.late


def test_resource_availability_warning() -> None:
    result = dispatch_scenario(make_scenario(available_end=70.0, task_end=60.0))
    assert any("availability" in warning for warning in result.warnings)


def test_utilization_is_recorded() -> None:
    result = dispatch_scenario(make_scenario())
    assert result.utilization["crew"] > 0


def test_demo_scenario_dispatches_all_tasks() -> None:
    scenario = Scenario.model_validate_json(
        (ROOT / "suppression/scenarios/2003-526-demo.json").read_text(encoding="utf-8")
    )
    result = dispatch_scenario(scenario)
    assert len(result.assignments) == len(scenario.tasks)
    assert any(item.line_length_m > 0 for item in result.assignments)
