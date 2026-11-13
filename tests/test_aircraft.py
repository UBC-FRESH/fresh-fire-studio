from __future__ import annotations

import pytest

from suppression.aircraft import CL415, drop_intervals, line_centers


def test_cl415_table_values() -> None:
    assert CL415.drops_per_hour_at(9.0) == 12.0
    assert CL415.litres_per_hour_at(9.0) == 60_000.0
    assert CL415.cycle_minutes_at(9.0) == 5.0
    assert CL415.effective_litres_per_drop_at(9.0) == 5_000.0


def test_cl415_interpolates_between_table_rows() -> None:
    assert CL415.drops_per_hour_at(1.0) == pytest.approx(19.0)
    assert CL415.litres_per_hour_at(1.0) == pytest.approx(92_500.0)
    assert CL415.drops_per_hour_at(100.0) == 6.0


def test_drop_intervals_use_cycle_time() -> None:
    intervals = drop_intervals(CL415, start_min=600, distance_km=9, count=3)
    assert intervals == ((600, 601), (605, 606), (610, 611))


def test_line_centers_include_endpoints() -> None:
    assert line_centers((0, 0), (100, 0), 3) == ((0, 0), (50.0, 0.0), (100.0, 0.0))
    assert line_centers((0, 0), (100, 0), 1) == ((0, 0),)


def test_repeated_drop_line_artifact() -> None:
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    payload = json.loads(
        (root / "suppression/proofs/2003-526-native-drop-line.json").read_text()
    )
    assert len(payload["wet_schedule"]["drops"]) == 21
    assert payload["wet_schedule"]["drops"][0]["covered_cells"] == 2
    assert payload["native"]["area_sim_ha"] == payload["free_burn"]["area_sim_ha"]


def test_invalid_inputs() -> None:
    with pytest.raises(ValueError):
        drop_intervals(CL415, start_min=0, distance_km=-1, count=3)
    with pytest.raises(ValueError):
        drop_intervals(CL415, start_min=0, distance_km=9, count=0)
    with pytest.raises(ValueError):
        line_centers((0, 0), (1, 1), 0)
