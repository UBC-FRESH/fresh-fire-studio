#!/usr/bin/env python3
"""Build a diagnostic full-perimeter drop scenario from the free-burn front."""

from __future__ import annotations

import argparse
import json
import sys

import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ws4-root", type=Path, required=True)
    parser.add_argument("--drop-time-min", type=float, default=600.0)
    parser.add_argument("--aircraft", type=int, default=5)
    parser.add_argument("--passes", type=int, default=1)
    parser.add_argument("--distance-km", type=float, default=9.0)
    parser.add_argument(
        "--box-margin-m",
        type=float,
        default=None,
        help="use a closed box around the perimeter with this margin",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "suppression/scenarios/2003-526-perimeter-mission.json",
    )
    args = parser.parse_args()

    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(args.ws4_root))

    from ws4.fire.comparison import observed_mask, run_observed_case
    from ws4.fire.observed import load_cfsds_reanalysis_case

    from suppression.aircraft import CL415
    from suppression.mission import build_perimeter_mission
    from suppression.perimeter import (
        cells_to_centers,
        closed_box_centers,
        front_target_cells,
        perimeter_cells,
    )

    fixture = args.ws4_root / "tests/fixtures/fire/cfsds_2003_526"
    fire = load_cfsds_reanalysis_case(fixture)
    metadata = json.loads((fixture / "metadata.json").read_text(encoding="utf-8"))
    free = run_observed_case(
        fire,
        scenario="free-burn",
        ffmc=float(metadata["ffmc"]),
        bui=float(metadata["bui"]),
        duration_min=float(metadata["duration_min"]),
        initial_mask=observed_mask(fire, 0),
        neighbor_radius=2,
    )
    burned = free.growth.ignition_time_min <= args.drop_time_min
    fuel_grid = fire.fbp_fuel_grid()
    burnable = np.array([[value is not None for value in row] for row in fuel_grid], dtype=bool)
    cells = front_target_cells(burned, burnable)
    if args.box_margin_m is not None:
        centers = closed_box_centers(
            perimeter_cells(burned, burnable),
            xll=fire.grid.xll,
            yll=fire.grid.yll,
            nrows=fire.grid.nrows,
            cell_size_m=fire.grid.cell_size_m,
            margin_m=args.box_margin_m,
            spacing_m=fire.grid.cell_size_m,
        )
    else:
        centers = cells_to_centers(
            cells,
            xll=fire.grid.xll,
            yll=fire.grid.yll,
            nrows=fire.grid.nrows,
            cell_size_m=fire.grid.cell_size_m,
        )
    mission = build_perimeter_mission(
        centers,
        profile=CL415,
        start_min=args.drop_time_min,
        distance_km=args.distance_km,
        aircraft_count=args.aircraft,
        passes=args.passes,
    )
    resources = [
        {
            "id": f"aircraft-{index}",
            "label": f"Diagnostic helicopter {index}",
            "kind": "helicopter",
            "home_base_id": "perimeter-base",
            "speed_kmh": 180,
            "capacity_l": 6000,
            "available_start_min": 0,
            "available_end_min": 22200,
        }
        for index in range(1, args.aircraft + 1)
    ]
    tasks = []
    drops = []
    for index, item in enumerate(mission, start=1):
        task_id = f"task-{index}"
        drop_id = f"drop-{index}"
        tasks.append(
            {
                "id": task_id,
                "resource_id": item.resource_id,
                "kind": "drop",
                "start_min": item.start_min,
                "end_min": item.end_min,
                "drop_id": drop_id,
                "target": [[item.center[0], item.center[1]]],
            }
        )
        drops.append(
            {
                "id": drop_id,
                "task_id": task_id,
                "resource_id": item.resource_id,
                "suppressant": "water",
                "start_min": item.start_min,
                "end_min": item.end_min,
                "center": [item.center[0], item.center[1]],
                "length_m": 100,
                "width_m": 50,
                "coverage_l_m2": 1.0,
                "effect_duration_min": 240,
                "canopy_penetration": 1.0,
            }
        )
    scenario = {
        "scenario_id": f"2003-526-perimeter-{args.aircraft}air-{args.passes}pass",
        "fire_slug": "cfsds-2003-526",
        "label": "Diagnostic full-perimeter drop mission",
        "timeline_start_min": 0,
        "timeline_end_min": 22200,
        "metadata": {
            "status": "diagnostic",
            "coordinate_system": "EPSG:26911",
            "note": "Drops placed on the free-burn perimeter at the specified time. Not a real operation.",
        },
        "objective": {"containment_area_ha": 2500, "deadline_min": 1440, "priority": "resource"},
        "bases": [{"id": "perimeter-base", "x": 487700, "y": 5722700, "kind": "ground"}],
        "water_sources": [],
        "resources": resources,
        "tasks": tasks,
        "lines": [],
        "drops": drops,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(scenario, indent=2) + "\n", encoding="utf-8")
    print(f"perimeter cells: {len(cells)}; drops: {len(drops)}; wrote {args.out}")


if __name__ == "__main__":
    main()
