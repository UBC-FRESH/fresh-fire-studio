from __future__ import annotations

import numpy as np

from suppression.arrival import targets_at_time


def test_targets_are_unburned_front_cells() -> None:
    burnable = np.ones((5, 5), dtype=bool)
    ignition = np.full((5, 5), np.inf)
    ignition[2, 2] = 0.0
    targets = targets_at_time(
        ignition,
        burnable,
        time_min=1.0,
        count=2,
        xll=0.0,
        yll=0.0,
        nrows=5,
        cell_size_m=10.0,
    )
    assert len(targets) == 2
    assert all(0.0 <= x <= 50.0 and 0.0 <= y <= 50.0 for x, y in targets)


def test_no_front_returns_empty() -> None:
    burnable = np.ones((3, 3), dtype=bool)
    ignition = np.full((3, 3), np.inf)
    assert targets_at_time(
        ignition, burnable, time_min=1.0, count=2, xll=0.0, yll=0.0, nrows=3, cell_size_m=10.0
    ) == ()
