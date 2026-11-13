from __future__ import annotations

from suppression.aircraft import CL415
from suppression.mission import build_perimeter_mission


def test_mission_distributes_targets_across_aircraft() -> None:
    centers = tuple((float(index), 0.0) for index in range(5))
    mission = build_perimeter_mission(
        centers,
        profile=CL415,
        start_min=600,
        distance_km=9,
        aircraft_count=2,
    )
    assert len(mission) == 5
    assert {item.resource_id for item in mission} == {"aircraft-1", "aircraft-2"}
    assert [item.center for item in mission if item.resource_id == "aircraft-1"] == [
        (0.0, 0.0),
        (2.0, 0.0),
        (4.0, 0.0),
    ]


def test_mission_repeats_passes() -> None:
    centers = ((0.0, 0.0), (100.0, 0.0))
    mission = build_perimeter_mission(
        centers,
        profile=CL415,
        start_min=600,
        distance_km=9,
        aircraft_count=1,
        passes=2,
    )
    assert len(mission) == 4
    assert [item.pass_index for item in mission] == [1, 1, 2, 2]
    assert mission[0].start_min == 600
    assert mission[2].start_min == 610


def test_mission_rejects_empty_or_invalid() -> None:
    import pytest

    with pytest.raises(ValueError):
        build_perimeter_mission((), profile=CL415, start_min=0, distance_km=9, aircraft_count=1)
    with pytest.raises(ValueError):
        build_perimeter_mission(
            ((0.0, 0.0),), profile=CL415, start_min=0, distance_km=9, aircraft_count=0
        )
