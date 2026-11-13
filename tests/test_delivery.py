from __future__ import annotations

from suppression.cycle import CyclePerformance
from suppression.delivery import delivery_case

LAKE = (489900.0, 5725200.0)
TARGETS = tuple((491250.0 + 250.0 * i, 5726250.0) for i in range(21))


def test_two_passes_close_the_nominal_deficit() -> None:
    one = delivery_case(
        targets=TARGETS,
        lake=LAKE,
        aircraft_count=3,
        passes=1,
        performance=CyclePerformance(),
        required_depth_mm=0.75,
    )
    two = delivery_case(
        targets=TARGETS,
        lake=LAKE,
        aircraft_count=3,
        passes=2,
        performance=CyclePerformance(),
        required_depth_mm=0.75,
    )
    assert one.deficit_l > 0
    assert two.deficit_l == 0
    assert two.delivered_l == 2 * one.delivered_l
    assert two.sorties == 2 * one.sorties
    assert two.coverage_fraction == one.coverage_fraction


def test_more_aircraft_reduce_elapsed_time_not_total_water() -> None:
    one = delivery_case(
        targets=TARGETS,
        lake=LAKE,
        aircraft_count=1,
        passes=1,
        performance=CyclePerformance(),
        required_depth_mm=0.75,
    )
    three = delivery_case(
        targets=TARGETS,
        lake=LAKE,
        aircraft_count=3,
        passes=1,
        performance=CyclePerformance(),
        required_depth_mm=0.75,
    )
    assert three.elapsed_min < one.elapsed_min
    assert three.delivered_l == one.delivered_l
