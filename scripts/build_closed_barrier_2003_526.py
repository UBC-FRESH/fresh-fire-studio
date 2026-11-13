#!/usr/bin/env python3
"""Build a scheduled full-height wet barrier across a grid column."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ws4-root", type=Path, required=True)
    parser.add_argument("--barrier-x", type=float, default=493600.0)
    parser.add_argument("--aircraft", type=int, default=100)
    parser.add_argument("--stack", type=int, default=3)
    parser.add_argument("--hold-min", type=float, default=60.0)
    parser.add_argument("--pre-arrival-min", type=float, default=2.0)
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "suppression/scenarios/2003-526-closed-barrier.json",
    )
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(args.ws4_root))

    from ws4.fire.comparison import observed_mask, run_observed_case
    from ws4.fire.observed import load_cfsds_reanalysis_case

    from suppression.cycle import CyclePerformance
    from suppression.models import Scenario
    from suppression.schedule import TimedTarget, schedule_stacked_targets

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
    col = int(round((args.barrier_x - fire.grid.xll) / fire.grid.cell_size_m))
    burnable = np.array(
        [[value is not None for value in row] for row in fire.fbp_fuel_grid()], dtype=bool
    )
    targets = []
    for row in range(fire.grid.nrows):
        arrival = float(free.growth.ignition_time_min[row, col])
        if burnable[row, col] and np.isfinite(arrival) and arrival > 0.0:
            targets.append(
                TimedTarget(
                    fire.grid.xll + (col + 0.5) * fire.grid.cell_size_m,
                    fire.grid.yll + (fire.grid.nrows - 1 - row + 0.5) * fire.grid.cell_size_m,
                    arrival,
                )
            )
    if not targets:
        raise SystemExit("no target arrivals on the barrier column")
    lake = (489900.0, 5725200.0)
    performance = CyclePerformance()
    aircraft_ids = tuple(f"aircraft-{index}" for index in range(1, args.aircraft + 1))
    scheduled = schedule_stacked_targets(
        targets,
        lake=lake,
        aircraft_ids=aircraft_ids,
        performance=performance,
        hold_min=args.hold_min,
        stack=args.stack,
        pre_arrival_min=args.pre_arrival_min,
        start_min=0.0,
    )
    resources = [
        {
            "id": aircraft_id,
            "label": f"CL-415 {index}",
            "kind": "helicopter",
            "home_base_id": "lake-base",
            "speed_kmh": performance.cruise_kmh,
            "capacity_l": performance.tank_l,
            "available_start_min": 0,
            "available_end_min": 22200,
        }
        for index, aircraft_id in enumerate(aircraft_ids, start=1)
    ]
    tasks = []
    drops = []
    for index, item in enumerate(scheduled, start=1):
        drop_phase = item.sortie.phase("drop")
        task_id = f"barrier-task-{index}"
        drop_id = f"barrier-drop-{index}"
        tasks.append(
            {
                "id": task_id,
                "resource_id": item.sortie.aircraft_id,
                "kind": "drop",
                "start_min": drop_phase.start_min,
                "end_min": drop_phase.end_min,
                "drop_id": drop_id,
                "target": [[item.target.x, item.target.y]],
            }
        )
        drops.append(
            {
                "id": drop_id,
                "task_id": task_id,
                "resource_id": item.sortie.aircraft_id,
                "suppressant": "water",
                "start_min": drop_phase.start_min,
                "end_min": drop_phase.end_min,
                "center": [item.target.x, item.target.y],
                "length_m": 100,
                "width_m": 50,
                "coverage_l_m2": 1.0,
                "effect_duration_min": args.hold_min,
                "canopy_penetration": 1.0,
            }
        )
    scenario = Scenario(
        scenario_id="2003-526-closed-barrier",
        fire_slug="cfsds-2003-526",
        label="Scheduled closed vertical wet barrier",
        timeline_end_min=22200,
        bases=[{"id": "lake-base", "x": lake[0], "y": lake[1], "kind": "helicopter"}],
        water_sources=[{"id": "lake", "x": lake[0], "y": lake[1], "capacity_l": 1000000}],
        resources=resources,
        tasks=tasks,
        drops=drops,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(scenario.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")
    print(f"targets {len(targets)}, sorties {len(scheduled)}, column {col}, wrote {args.out}")


if __name__ == "__main__":
    main()
