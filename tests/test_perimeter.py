from __future__ import annotations

import numpy as np

from suppression.perimeter import (
    cells_to_centers,
    front_target_cells,
    leading_edge_cells,
    perimeter_cells,
    perimeter_mask,
)


def test_single_cell_is_perimeter() -> None:
    mask = np.zeros((5, 5), dtype=bool)
    mask[2, 2] = True
    assert perimeter_cells(mask) == ((2, 2),)


def test_internal_cell_is_not_perimeter() -> None:
    mask = np.zeros((5, 5), dtype=bool)
    mask[1:4, 1:4] = True
    perimeter = set(perimeter_cells(mask))
    assert (2, 2) not in perimeter
    assert (1, 1) in perimeter
    assert len(perimeter) == 8


def test_burnable_mask_is_applied() -> None:
    burned = np.ones((3, 3), dtype=bool)
    burnable = np.zeros((3, 3), dtype=bool)
    burnable[1, 1] = True
    assert perimeter_cells(burned, burnable) == ((1, 1),)


def test_leading_edge_east_and_north() -> None:
    mask = np.zeros((5, 5), dtype=bool)
    mask[1:4, 1:4] = True
    east = leading_edge_cells(mask, direction="east", band_m=0, cell_size_m=1)
    north = leading_edge_cells(mask, direction="north", band_m=0, cell_size_m=1)
    assert {cell[1] for cell in east} == {3}
    assert {cell[0] for cell in north} == {1}


def test_front_targets_are_unburned_neighbours() -> None:
    burned = np.zeros((5, 5), dtype=bool)
    burned[2, 2] = True
    assert front_target_cells(burned) == ((1, 2), (2, 1), (2, 3), (3, 2))


def test_cells_to_centers_north_up() -> None:
    centers = cells_to_centers(
        ((0, 0), (1, 2)),
        xll=100.0,
        yll=200.0,
        nrows=3,
        cell_size_m=10.0,
    )
    assert centers == ((105.0, 225.0), (125.0, 215.0))


def test_perimeter_mask_shape_validation() -> None:
    import pytest

    with pytest.raises(ValueError, match="shape"):
        perimeter_mask(np.zeros((2, 2), bool), np.zeros((3, 3), bool))
