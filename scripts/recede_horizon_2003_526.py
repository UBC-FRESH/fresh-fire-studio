#!/usr/bin/env python3
"""P179.14 diagnostic receding-horizon drop mission.

At each planning epoch, read the current simulated front, place one
perimeter-target mission, rerun the native growth with all missions, and repeat.
This is a small closed-loop experiment, not an online optimizer.
"""

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
    parser.add_argument("--start-min", type=float, default=600.0)
    parser.add_argument("--interval-min", type=float, default=300.0)
    parser.add_argument("--cycles", type=int, default=4)
    parser.add_argument("--aircraft", type=int, default=5)
    parser.add_argument("--passes", type=int, default=1)
    parser.add_argument("--distance-km", type=float, default=9.0)
    parser.add_argument("--required-depth-mm", type=float, default=0.75)
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "suppression/proofs/2003-526-receding-horizon.json",
    )
    args = parser.parse_args()

    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(args.ws4_root))

    from ws4.fire.comparison import compare_masks, hourly_weather_steps, observed_mask
    from ws4.fire.growth import GrowthConfig, SiteGrid, slope_aspect_from_elevation
    from ws4.fire.observed import load_cfsds_reanalysis_case

    from suppression.aircraft import CL415
    from suppression.mission import build_perimeter_mission
    from suppression.models import Scenario
    from suppression.native_growth import ContainmentSchedule, grow_fire_with_containment
    from suppression.perimeter import cells_to_centers, front_target_cells
    from suppression.wet import build_wet_schedule

    fixture = args.ws4_root / "tests/fixtures/fire/cfsds_2003_526"
    fire = load_cfsds_reanalysis_case(fixture)
    metadata = json.loads((fixture / "metadata.json").read_text(encoding="utf-8"))
    ffmc = float(metadata["ffmc"])
    bui = float(metadata["bui"])
    duration = float(metadata["duration_min"])
    rows, cols = fire.grid.nrows, fire.grid.ncols
    fuel_grid = fire.fbp_fuel_grid()
    conifer, dead, closure = fire.fbp_blend_grids()
    slope, aspect = slope_aspect_from_elevation(
        fire.elevation_m, fire.grid.cell_size_m, nodata=fire.grid.nodata
    )
    base_burnable = np.array(
        [[value is not None for value in row] for row in fuel_grid], dtype=bool
    )
    seed = np.asarray(observed_mask(fire, 0), dtype=bool) & base_burnable
    observed = observed_mask(fire, -1)
    steps = hourly_weather_steps(fire, ffmc=ffmc, bui=bui)
    empty = ContainmentSchedule(
        start_min=np.full((rows, cols), np.inf),
        end_min=np.full((rows, cols), np.inf),
    )

    def run(wet):
        grid = SiteGrid(
            fuel_type="C2",
            rows=rows,
            cols=cols,
            cell_size_m=fire.grid.cell_size_m,
            ffmc=ffmc,
            bui=bui,
            wind_kmh=steps[0].wind_kmh,
            wind_direction_deg=steps[0].wind_direction_deg,
            slope_percent=32.0,
            aspect_deg=180.0,
            burnable=base_burnable,
            fuel_type_grid=fuel_grid,
            slope_percent_grid=slope,
            aspect_deg_grid=aspect,
            elevation_m_grid=fire.elevation_m,
            conifer_percent_grid=conifer,
            dead_fir_percent_grid=dead,
            crown_closure_percent_grid=closure,
        )
        growth = grow_fire_with_containment(
            grid,
            GrowthConfig(
                ignition_cells=tuple(
                    (int(row), int(col)) for row, col in np.argwhere(seed)
                ),
                max_time_min=duration,
                snapshot_interval_min=60.0,
                neighbor_radius=2,
                weather_steps=steps,
            ),
            empty,
            wet_schedule=wet,
        )
        simulated = np.isfinite(growth.ignition_time_min)
        return growth, compare_masks(simulated, observed, fire.grid)

    # Start from a free run; each epoch reads the current front.
    growth, metrics = run(None)
    free_metrics = metrics
    missions: list[dict[str, object]] = []
    tasks: list[dict[str, object]] = []
    drops: list[dict[str, object]] = []
    resources = [
        {
            "id": f"aircraft-{index}",
            "label": f"Receding-horizon aircraft {index}",
            "kind": "helicopter",
            "home_base_id": "rh-base",
            "speed_kmh": 180,
            "capacity_l": 6000,
            "available_start_min": 0,
            "available_end_min": 22200,
        }
        for index in range(1, args.aircraft + 1)
    ]

    for cycle in range(args.cycles):
        epoch = args.start_min + cycle * args.interval_min
        burned = growth.ignition_time_min <= epoch
        targets = front_target_cells(burned, base_burnable)
        if not targets:
            break
        centers = cells_to_centers(
            targets,
            xll=fire.grid.xll,
            yll=fire.grid.yll,
            nrows=rows,
            cell_size_m=fire.grid.cell_size_m,
        )
        mission = build_perimeter_mission(
            centers,
            profile=CL415,
            start_min=epoch,
            distance_km=args.distance_km,
            aircraft_count=args.aircraft,
            passes=args.passes,
        )
        mission_tasks = []
        mission_drops = []
        for index, item in enumerate(mission, start=1):
            task_id = f"cycle-{cycle}-task-{index}"
            drop_id = f"cycle-{cycle}-drop-{index}"
            mission_tasks.append(
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
            mission_drops.append(
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
        tasks.extend(mission_tasks)
        drops.extend(mission_drops)
        missions.append({"epoch_min": epoch, "targets": len(targets), "drops": len(mission)})
        scenario = Scenario(
            scenario_id=f"2003-526-receding-{cycle + 1}",
            fire_slug="cfsds-2003-526",
            timeline_end_min=22200,
            bases=[{"id": "rh-base", "x": 487700, "y": 5722700, "kind": "ground"}],
            resources=resources,
            tasks=tasks,
            drops=drops,
        )
        wet = build_wet_schedule(
            scenario,
            required_depth_mm=args.required_depth_mm,
            xll=fire.grid.xll,
            yll=fire.grid.yll,
            nrows=rows,
            ncols=cols,
            cell_size_m=fire.grid.cell_size_m,
            subcell_cell_size_m=10.0,
        )
        growth, metrics = run(wet)

    payload = {
        "proof": "P179.14 receding-horizon perimeter mission",
        "case_id": metadata["case_id"],
        "start_min": args.start_min,
        "interval_min": args.interval_min,
        "cycles": len(missions),
        "missions": missions,
        "free_burn": free_metrics.to_dict(),
        "receding": metrics.to_dict(),
        "delta": {
            "area_reduction_ha": free_metrics.area_sim_ha - metrics.area_sim_ha,
            "iou_change": metrics.iou - free_metrics.iou,
        },
        "total_drops": len(drops),
        "limits": [
            "The mission is re-planned after each full 300-minute epoch, not continuously.",
            "Aircraft have no refill, turn-around, visibility or competing-fire constraints.",
            "The wet ROS mapping remains diagnostic.",
            "The fire grid is 100 m.",
            "This is a diagnostic closed-loop experiment, not an incident plan.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"free: {free_metrics.area_sim_ha:.1f} ha, IoU {free_metrics.iou:.3f}")
    print(f"receding: {metrics.area_sim_ha:.1f} ha, IoU {metrics.iou:.3f}")
    print(f"missions: {len(missions)}, drops: {len(drops)}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
