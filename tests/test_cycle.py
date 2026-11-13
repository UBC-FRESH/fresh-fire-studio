from __future__ import annotations

import pytest

from suppression.cycle import CyclePerformance, build_cycle, build_sortie, cycle_summary

LAKE = (489900.0, 5725200.0)
TARGETS = tuple((491250.0 + 60.0 * i, 5726250.0) for i in range(21))


def test_sortie_phase_order_and_mass() -> None:
    sortie = build_sortie(
        aircraft_id="a1",
        lake=LAKE,
        target=TARGETS[0],
        start_min=600.0,
        performance=CyclePerformance(),
    )
    kinds = [phase.kind for phase in sortie.phases]
    assert kinds == ["scoop", "climb", "cruise_out", "descent", "drop", "turn", "climb_back", "cruise_back", "descent_back"]
    assert sortie.water_l == 6000.0
    assert 2.5 <= sortie.cycle_min <= 5.5
    assert sortie.end_min > sortie.start_min


def test_cycle_distributes_aircraft_and_reuses_them() -> None:
    sorties = build_cycle(
        targets=TARGETS,
        lake=LAKE,
        aircraft_ids=("a1", "a2", "a3"),
        performance=CyclePerformance(),
        start_min=600.0,
    )
    assert len(sorties) == 21
    assert {sortie.aircraft_id for sortie in sorties} == {"a1", "a2", "a3"}
    assert all(sortie.phases[0].kind == "scoop" for sortie in sorties)
    for aircraft_id in ("a1", "a2", "a3"):
        assigned = [sortie for sortie in sorties if sortie.aircraft_id == aircraft_id]
        assert len(assigned) == 7
        for previous, current in zip(assigned, assigned[1:]):
            assert current.start_min >= previous.end_min


def test_summary() -> None:
    sorties = build_cycle(
        targets=TARGETS,
        lake=LAKE,
        aircraft_ids=("a1", "a2", "a3"),
        performance=CyclePerformance(),
    )
    summary = cycle_summary(sorties)
    assert summary["sorties"] == 21
    assert summary["total_water_l"] == 126000.0
    assert summary["per_aircraft"] == {"a1": 7, "a2": 7, "a3": 7}
    assert summary["min_cycle_min"] <= summary["mean_cycle_min"] <= summary["max_cycle_min"]


def test_invalid_inputs() -> None:
    with pytest.raises(ValueError):
        build_cycle(targets=(), lake=LAKE, aircraft_ids=("a1",), performance=CyclePerformance())
    with pytest.raises(ValueError):
        CyclePerformance(cruise_alt_m=0, drop_alt_m=100)
