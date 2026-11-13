#!/usr/bin/env python3
"""P179.10 diagnostic: 50 m fire grid for a drop line.

The P179 native kernel is grid-agnostic, but the observed fixture is 100 m.
This script upsamples fuel, terrain and observed masks by nearest neighbour,
runs a 50 m free burn and a 50 m wet-line case, and reports the comparison.
It is a resolution experiment, not a calibrated high-resolution reconstruction.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ws4-root", type=Path, required=True)
    parser.add_argument(
        "--scenario",
        type=Path,
        default=ROOT / "suppression/scenarios/2003-526-drop-line-proof.json",
    )
    parser.add_argument("--fine-cell-m", type=float, default=50.0)
    parser.add_argument("--subcell-cell-size-m", type=float, default=10.0)
    parser.add_argument("--required-depth-mm", type=float, default=0.75)
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "suppression/proofs/2003-526-fine-grid.json",
    )
    args = parser.parse_args()
    if args.fine_cell_m <= 0 or 100.0 % args.fine_cell_m != 0:
        raise SystemExit("--fine-cell-m must divide 100 m")

    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(args.ws4_root))

    from ws4.fire.comparison import compare_masks, hourly_weather_steps, observed_mask
    from ws4.fire.growth import GrowthConfig, SiteGrid, slope_aspect_from_elevation
    from ws4.fire.observed import load_cfsds_reanalysis_case

    from suppression.models import Scenario
    from suppression.native_growth import (
        ContainmentSchedule,
        grow_fire_with_containment,
    )
    from suppression.wet import build_wet_schedule

    fixture = args.ws4_root / "tests/fixtures/fire/cfsds_2003_526"
    fire = load_cfsds_reanalysis_case(fixture)
    metadata = json.loads((fixture / "metadata.json").read_text(encoding="utf-8"))
    scenario = Scenario.model_validate_json(args.scenario.read_text(encoding="utf-8"))
    ffmc = float(metadata["ffmc"])
    bui = float(metadata["bui"])
    duration = float(metadata["duration_min"])
    factor = int(round(100.0 / args.fine_cell_m))
    fine_nrows = fire.grid.nrows * factor
    fine_ncols = fire.grid.ncols * factor
    fine_grid = replace(
        fire.grid,
        nrows=fine_nrows,
        ncols=fine_ncols,
        cell_size_m=args.fine_cell_m,
    )

    def upsample(array: np.ndarray) -> np.ndarray:
        return np.repeat(np.repeat(array, factor, axis=0), factor, axis=1)

    fuel_grid = upsample(fire.fbp_fuel_grid())
    conifer, dead, closure = (upsample(array) for array in fire.fbp_blend_grids())
    elevation = upsample(fire.elevation_m)
    slope, aspect = slope_aspect_from_elevation(
        elevation,
        args.fine_cell_m,
        nodata=fire.grid.nodata,
    )
    base_burnable = np.array(
        [[value is not None for value in row] for row in fuel_grid], dtype=bool
    )
    seed = upsample(observed_mask(fire, 0)) & base_burnable
    observed = upsample(observed_mask(fire, -1))
    steps = hourly_weather_steps(fire, ffmc=ffmc, bui=bui)
    empty = ContainmentSchedule(
        start_min=np.full((fine_nrows, fine_ncols), np.inf),
        end_min=np.full((fine_nrows, fine_ncols), np.inf),
    )

    def run(wet):
        grid = SiteGrid(
            fuel_type="C2",
            rows=fine_nrows,
            cols=fine_ncols,
            cell_size_m=args.fine_cell_m,
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
            elevation_m_grid=elevation,
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
        return growth, compare_masks(simulated, observed, fine_grid)

    wet = build_wet_schedule(
        scenario,
        required_depth_mm=args.required_depth_mm,
        xll=fire.grid.xll,
        yll=fire.grid.yll,
        nrows=fine_nrows,
        ncols=fine_ncols,
        cell_size_m=args.fine_cell_m,
        subcell_cell_size_m=args.subcell_cell_size_m,
    )
    free_growth, free_metrics = run(None)
    wet_growth, wet_metrics = run(wet)
    payload = {
        "proof": "P179.10 fine-grid drop line",
        "case_id": metadata["case_id"],
        "scenario_id": scenario.scenario_id,
        "fine_cell_m": args.fine_cell_m,
        "grid": {
            "xll": fire.grid.xll,
            "yll": fire.grid.yll,
            "nrows": fine_nrows,
            "ncols": fine_ncols,
            "cell_size_m": args.fine_cell_m,
        },
        "free_burn": free_metrics.to_dict(),
        "wet_line": wet_metrics.to_dict(),
        "delta": {
            "area_reduction_ha": free_metrics.area_sim_ha - wet_metrics.area_sim_ha,
            "iou_change": wet_metrics.iou - free_metrics.iou,
        },
        "wet_schedule": {
            "required_depth_mm": wet.required_depth_mm,
            "drops": len(wet.drops),
        },
        "limits": [
            "Fine fuel and terrain are nearest-neighbour upsampled from 100 m.",
            "The observed masks are upsampled, not re-digitized at 50 m.",
            "The wet ROS factor is diagnostic.",
            "This is a resolution experiment, not a calibrated reconstruction.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"free: {free_metrics.area_sim_ha:.1f} ha, IoU {free_metrics.iou:.3f}")
    print(f"wet:  {wet_metrics.area_sim_ha:.1f} ha, IoU {wet_metrics.iou:.3f}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
