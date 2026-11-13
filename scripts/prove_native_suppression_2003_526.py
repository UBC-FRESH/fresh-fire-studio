#!/usr/bin/env python3
"""P179.3 diagnostic: native time-dependent containment on 2003_526.

Unlike the P179.2 chunk harness, this keeps one WS4 growth run and checks the
containment schedule at every cell expansion. It is a prototype adapter around
the P177 growth loop, not a validated operational suppression model.
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
    parser.add_argument(
        "--ws4-root",
        type=Path,
        required=True,
        help="checkout containing the ws4 package and 2003_526 fixture",
    )
    parser.add_argument(
        "--scenario",
        type=Path,
        default=ROOT / "suppression/scenarios/2003-526-temporal-proof.json",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "suppression/proofs/2003-526-native.json",
    )
    parser.add_argument("--step-min", type=float, default=60.0)
    parser.add_argument(
        "--dispatch",
        action="store_true",
        help="derive line construction times from the dispatch prototype",
    )
    parser.add_argument(
        "--drops",
        action="store_true",
        help="apply temporary wet cells from the scenario drops",
    )
    parser.add_argument("--required-depth-mm", type=float, default=0.75)
    args = parser.parse_args()

    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(args.ws4_root))

    from ws4.fire.comparison import (
        compare_masks,
        hourly_weather_steps,
        observed_mask,
        run_observed_case,
    )
    from ws4.fire.growth import GrowthConfig, SiteGrid, slope_aspect_from_elevation
    from ws4.fire.observed import load_cfsds_reanalysis_case

    from suppression.dispatch import apply_line_timings, dispatch_scenario
    from suppression.models import Scenario
    from suppression.native_growth import (
        build_containment_schedule,
        grow_fire_with_containment,
    )
    from suppression.wet import build_wet_schedule

    fixture = args.ws4_root / "tests/fixtures/fire/cfsds_2003_526"
    fire = load_cfsds_reanalysis_case(fixture)
    metadata = json.loads((fixture / "metadata.json").read_text(encoding="utf-8"))
    scenario = Scenario.model_validate_json(args.scenario.read_text(encoding="utf-8"))
    dispatch = None
    if args.dispatch:
        dispatch = dispatch_scenario(scenario)
        scenario = apply_line_timings(scenario, dispatch)
    ffmc = float(metadata["ffmc"])
    bui = float(metadata["bui"])
    duration = float(metadata["duration_min"])
    start_mask = observed_mask(fire, 0)
    observed = observed_mask(fire, -1)

    free = run_observed_case(
        fire,
        scenario="free-burn",
        ffmc=ffmc,
        bui=bui,
        duration_min=duration,
        initial_mask=start_mask,
        neighbor_radius=2,
    )

    rows, cols = fire.grid.nrows, fire.grid.ncols
    fuel_grid = fire.fbp_fuel_grid()
    conifer_grid, dead_grid, closure_grid = fire.fbp_blend_grids()
    slope_grid, aspect_grid = slope_aspect_from_elevation(
        fire.elevation_m,
        fire.grid.cell_size_m,
        nodata=fire.grid.nodata,
    )
    base_burnable = np.array(
        [[value is not None for value in row] for row in fuel_grid], dtype=bool
    )
    seed = np.asarray(start_mask, dtype=bool) & base_burnable
    if not seed.any():
        raise SystemExit("first-day observed mask has no burnable cells")

    steps = hourly_weather_steps(fire, ffmc=ffmc, bui=bui)
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
        slope_percent_grid=slope_grid,
        aspect_deg_grid=aspect_grid,
        elevation_m_grid=fire.elevation_m,
        conifer_percent_grid=conifer_grid,
        dead_fir_percent_grid=dead_grid,
        crown_closure_percent_grid=closure_grid,
    )
    schedule = build_containment_schedule(
        scenario,
        xll=fire.grid.xll,
        yll=fire.grid.yll,
        nrows=rows,
        ncols=cols,
        cell_size_m=fire.grid.cell_size_m,
        step_min=args.step_min,
    )
    wet = None
    if args.drops:
        wet = build_wet_schedule(
            scenario,
            required_depth_mm=args.required_depth_mm,
            xll=fire.grid.xll,
            yll=fire.grid.yll,
            nrows=rows,
            ncols=cols,
            cell_size_m=fire.grid.cell_size_m,
        )
    growth = grow_fire_with_containment(
        grid,
        GrowthConfig(
            ignition_cells=tuple(
                (int(row), int(col)) for row, col in np.argwhere(seed)
            ),
            max_time_min=duration,
            snapshot_interval_min=args.step_min,
            neighbor_radius=2,
            weather_steps=steps,
        ),
        schedule,
        wet_schedule=wet,
    )
    simulated = np.isfinite(growth.ignition_time_min)
    metrics = compare_masks(simulated, observed, fire.grid)

    chunked = None
    chunked_path = ROOT / "suppression/proofs/2003-526-temporal.json"
    if scenario.scenario_id == "2003-526-breach-proof":
        chunked_path = ROOT / "suppression/proofs/2003-526-breach.json"
    elif scenario.scenario_id == "2003-526-late-line-proof":
        chunked_path = ROOT / "suppression/proofs/2003-526-late-line.json"
    if chunked_path.exists():
        chunked = json.loads(chunked_path.read_text(encoding="utf-8"))["temporal"]

    payload = {
        "proof": "P179.3 native time-dependent containment",
        "case_id": metadata["case_id"],
        "scenario_id": scenario.scenario_id,
        "method": {
            "sampling_min": args.step_min,
            "kernel": "single WS4 minimum-travel-time run",
            "mask": "cell containment checked at expansion time",
            "drops": (
                f"temporary wet threshold at {args.required_depth_mm:g} mm"
                if wet is not None
                else "not coupled"
            ),
            "line_timing": "dispatch-derived" if dispatch is not None else "scenario",
        },
        "wet_schedule": (
            {
                "required_depth_mm": wet.required_depth_mm,
                "drops": [
                    {
                        "drop_id": drop.drop_id,
                        "depth_mm": drop.depth_mm,
                        "start_min": drop.start_min,
                        "end_min": drop.end_min,
                        "duration_min": drop.duration_min,
                        "covered_cells": drop.covered_cells,
                    }
                    for drop in wet.drops
                ],
            }
            if wet is not None
            else None
        ),
        "dispatch": dispatch.to_dict() if dispatch is not None else None,
        "grid": {
            "crs": fire.grid.crs,
            "xll": fire.grid.xll,
            "yll": fire.grid.yll,
            "ncols": cols,
            "nrows": rows,
            "cell_size_m": fire.grid.cell_size_m,
        },
        "free_burn": free.metrics.to_dict(),
        "native": metrics.to_dict(),
        "native_area_by_time_ha": {
            f"{snapshot.time_min:g}": snapshot.area_ha for snapshot in growth.snapshots
        },
        "chunked": chunked,
        "delta_vs_free": {
            "area_reduction_ha": free.metrics.area_sim_ha - metrics.area_sim_ha,
            "area_reduction_pct": (
                (free.metrics.area_sim_ha - metrics.area_sim_ha)
                / free.metrics.area_sim_ha
                * 100.0
            )
            if free.metrics.area_sim_ha
            else 0.0,
            "iou_change": metrics.iou - free.metrics.iou,
        },
        "delta_vs_chunked": (
            {
                "area_difference_ha": metrics.area_sim_ha - chunked["area_sim_ha"],
                "iou_change": metrics.iou - chunked["iou"],
            }
            if chunked
            else None
        ),
        "limits": [
            "The line is synthetic and construction is sampled every step_min.",
            "Native containment is a prototype adapter around the P177 loop.",
            "No spotting, wind grids or burning-condition gates are supported.",
            "Drop moisture and decay are not coupled to growth.",
            "This is a diagnostic contract proof, not a calibrated suppression result.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"free burn: {free.metrics.area_sim_ha:.1f} ha, IoU {free.metrics.iou:.3f}")
    print(f"native: {metrics.area_sim_ha:.1f} ha, IoU {metrics.iou:.3f}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
