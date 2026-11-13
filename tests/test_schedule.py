from __future__ import annotations

from suppression.cycle import CyclePerformance
from suppression.schedule import TimedTarget, schedule_arrival_targets

LAKE = (489900.0, 5725200.0)


def test_schedule_targets_around_arrival() -> None:
    targets = [
        TimedTarget(491250.0 + 200.0 * index, 5726250.0, 1800.0 + index * 2.0)
        for index in range(6)
    ]
    scheduled = schedule_arrival_targets(
        targets,
        lake=LAKE,
        aircraft_ids=("a1", "a2"),
        performance=CyclePerformance(),
        hold_min=60.0,
        start_min=1600.0,
    )
    assert len(scheduled) == 6
    assert all(item.actual_drop_min >= item.desired_drop_min for item in scheduled)
    assert all(item.sortie.water_l == 6000.0 for item in scheduled)


def test_schedule_rejects_empty() -> None:
    import pytest

    with pytest.raises(ValueError):
        schedule_arrival_targets((), lake=LAKE, aircraft_ids=("a1",), performance=CyclePerformance())
