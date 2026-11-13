#!/usr/bin/env python3
"""Schedule drops at free-burn arrival time minus half the hold window."""

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
    parser.add_argument("--arrival-time-min", type=float, default=1800.0)
    parser.add_argument("--targets", type=int, default=21)
    parser.add_argument("--aircraft", type=int, default=3)
    parser.add_argument("--hold-min", type=float, default=60.0)
    parser.add_argument("--replicates", type=int, default=1)
    parser.add_argument("--stack", type=int, default=1)
    parser.add_argument("--pre-arrival-min", type=float, default=None)
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "suppression/scenarios/2003-526-arrival-scheduled.json",
    )
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(args.ws4_root))

    from ws4.fire.comparison import observed_mask, run_observed_case
    from ws4.fire.observed import load_cfsds_reanalysis_case

    from suppression.cycle import CyclePerformance
    from suppression.perimeter import cells_to_centers, front_target_cells
    from suppression.schedule import TimedTarget, schedule_arrival_targets, schedule_stacked_targets

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
    ignition = free.growth.ignition_time_min
    target_time = args.arrival_time_min
    burnable = np.array(
        [[value is not None for value in row] for row in fire.fbp_fuel_grid()], dtype=bool
    )
    cells = front_target_cells(ignition <= target_time, burnable)
    cells = tuple(sorted(cells, key=lambda item: (item[1], -item[0]), reverse=True)[: args.targets])
    centers = cells_to_centers(
        cells,
        xll=fire.grid.xll,
        yll=fire.grid.yll,
        nrows=fire.grid.nrows,
        cell_size_m=fire.grid.cell_size_m,
    )
    timed = []
    for cell, center in zip(cells, centers):
        arrival = float(ignition[cell[0], cell[1]])
        if np.isfinite(arrival):
            timed.append(TimedTarget(center[0], center[1], arrival))
    if not timed:
        raise SystemExit("no finite-arrival targets")
    lake = (489900.0, 5725200.0)
    performance = CyclePerformance()
    aircraft_ids = tuple(f"aircraft-{index}" for index in range(1, args.aircraft + 1))
    if args.replicates < 1:
        raise SystemExit("--replicates must be at least 1")
    timed = timed * args.replicates
    if args.stack > 1:
        scheduled = schedule_stacked_targets(
            timed,
            lake=lake,
            aircraft_ids=aircraft_ids,
            performance=performance,
            hold_min=args.hold_min,
            stack=args.stack,
            pre_arrival_min=args.pre_arrival_min,
            start_min=target_time - 120.0,
        )
    else:
        scheduled = schedule_arrival_targets(
            timed,
            lake=lake,
            aircraft_ids=aircraft_ids,
            performance=performance,
            hold_min=args.hold_min,
            pre_arrival_min=args.pre_arrival_min,
            start_min=target_time - 120.0,
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
        tid = f"arrival-task-{index}"
        did = f"arrival-drop-{index}"
        tasks.append(
            {
                "id": tid,
                "resource_id": item.sortie.aircraft_id,
                "kind": "drop",
                "start_min": drop_phase.start_min,
                "end_min": drop_phase.end_min,
                "drop_id": did,
                "target": [[item.target.x, item.target.y]],
            }
        )
        drops.append(
            {
                "id": did,
                "task_id": tid,
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
    from suppression.models import Scenario

    scenario = Scenario(
        scenario_id="2003-526-arrival-scheduled",
        fire_slug="cfsds-2003-526",
        label="Arrival-timed suppression mission",
        timeline_end_min=22200,
        bases=[{"id": "lake-base", "x": lake[0], "y": lake[1], "kind": "helicopter"}],
        water_sources=[{"id": "lake", "x": lake[0], "y": lake[1], "capacity_l": 1000000}],
        resources=resources,
        tasks=tasks,
        drops=drops,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(scenario.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")
    summary_path = args.out.with_suffix(".summary.json")
    summary_path.write_text(
        json.dumps(
            {
                "targets": len(scheduled),
                "aircraft": args.aircraft,
                "hold_min": args.hold_min,
                "mean_late_min": float(np.mean([item.late_min for item in scheduled])),
                "max_late_min": float(np.max([item.late_min for item in scheduled])),
                "sorties": [item.to_dict() for item in scheduled],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"targets {len(scheduled)}; mean late {np.mean([item.late_min for item in scheduled]):.2f} min; wrote {args.out}")


if __name__ == "__main__":
    main()
