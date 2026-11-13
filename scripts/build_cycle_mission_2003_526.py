#!/usr/bin/env python3
"""Build the schematic cycle mission from the active 600-minute front."""

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
    parser.add_argument("--drop-time-min", type=float, default=600.0)
    parser.add_argument("--aircraft", type=int, default=3)
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "suppression/scenarios/2003-526-cycle-mission.json",
    )
    parser.add_argument(
        "--page-out",
        type=Path,
        default=ROOT / "portal/static/suppression-mission.json",
    )
    args = parser.parse_args()

    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(args.ws4_root))

    from ws4.fire.comparison import observed_mask, run_observed_case
    from ws4.fire.observed import load_cfsds_reanalysis_case

    from suppression.cycle import CyclePerformance, build_cycle, cycle_summary
    from suppression.water_balance import water_balance
    from suppression.models import Scenario
    from suppression.perimeter import cells_to_centers, front_target_cells

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
    front = front_target_cells(burned, burnable)
    # Take the eastern head targets; this is the active side of the 2003_526 front.
    front = tuple(sorted(front, key=lambda cell: cell[1], reverse=True)[:21])
    centers = cells_to_centers(
        front,
        xll=fire.grid.xll,
        yll=fire.grid.yll,
        nrows=fire.grid.nrows,
        cell_size_m=fire.grid.cell_size_m,
    )
    aircraft_ids = tuple(f"aircraft-{index}" for index in range(1, args.aircraft + 1))
    lake = (489900.0, 5725200.0)
    performance = CyclePerformance()
    sorties = build_cycle(
        targets=centers,
        lake=lake,
        aircraft_ids=aircraft_ids,
        performance=performance,
        start_min=args.drop_time_min,
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
    for index, sortie in enumerate(sorties, start=1):
        drop_phase = sortie.phase("drop")
        task_id = f"cycle-task-{index}"
        drop_id = f"cycle-drop-{index}"
        tasks.append(
            {
                "id": task_id,
                "resource_id": sortie.aircraft_id,
                "kind": "drop",
                "start_min": drop_phase.start_min,
                "end_min": drop_phase.end_min,
                "drop_id": drop_id,
                "target": [[sortie.target[0], sortie.target[1]]],
            }
        )
        drops.append(
            {
                "id": drop_id,
                "task_id": task_id,
                "resource_id": sortie.aircraft_id,
                "suppressant": "water",
                "start_min": drop_phase.start_min,
                "end_min": drop_phase.end_min,
                "center": [sortie.target[0], sortie.target[1]],
                "length_m": 100,
                "width_m": 50,
                "coverage_l_m2": 1.0,
                "effect_duration_min": 60.0,
                "canopy_penetration": 1.0,
            }
        )
    scenario = Scenario(
        scenario_id="2003-526-cycle-mission",
        fire_slug="cfsds-2003-526",
        label="Schematic lake-to-fire cycle mission",
        timeline_end_min=22200,
        bases=[{"id": "lake-base", "x": lake[0], "y": lake[1], "kind": "helicopter"}],
        water_sources=[{"id": "lake", "x": lake[0], "y": lake[1], "capacity_l": 1000000}],
        resources=resources,
        tasks=tasks,
        drops=drops,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(scenario.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")
    summary = cycle_summary(sorties)
    summary_path = args.out.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    page = json.loads(args.page_out.read_text(encoding="utf-8"))
    page["sorties"] = [sortie.to_dict() for sortie in sorties]
    page["fire_line"] = [[center[0], center[1]] for center in centers]
    page["lake"] = {"x": lake[0], "y": lake[1], "radius_m": 220.0, "label": "Schematic lake"}
    page["aircraft"] = [
        {"id": aircraft_id, "label": f"CL-415 {index}", "color": color}
        for index, (aircraft_id, color) in enumerate(
            zip(aircraft_ids, ("#ffb347", "#7ce0c6", "#70b7ff")), start=1
        )
    ]
    page["performance"] = {
        "cruise_kmh": performance.cruise_kmh,
        "drop_kmh": performance.drop_kmh,
        "climb_m_min": performance.climb_min,
        "scoop_min": performance.scoop_min,
        "climb_min": performance.climb_min,
        "descent_min": performance.descent_min,
        "drop_min": performance.drop_min,
        "turn_min": performance.turn_min,
    }
    page["timeline"] = {
        "start": args.drop_time_min - 10.0,
        "end": round(max(sortie.end_min for sortie in sorties) + 4.0, 1),
        "drop_time": args.drop_time_min,
    }
    target_line_m = sum(
        float(np.hypot(centers[index + 1][0] - centers[index][0], centers[index + 1][1] - centers[index][1]))
        for index in range(len(centers) - 1)
    )
    balance = water_balance(
        line_length_m=target_line_m,
        drop_length_m=100.0,
        drop_width_m=50.0,
        drop_count=len(sorties),
        delivered_l=summary["total_water_l"],
        required_depth_mm=0.75,
        tank_l=performance.tank_l,
    )
    page["logistics"] = {
        **summary,
        "target_line_m": target_line_m,
        "water_balance": balance.to_dict(),
    }
    page["note"] = "Schematic lake-to-fire flight cycles: scoop, climb, cruise, descend, drop, turn, return. Three aircraft; geometry and times are illustrative, not a dispatch record."
    page["title"] = "2003_526 · schematic aerial suppression cycle"
    args.page_out.write_text(json.dumps(page, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
