#!/usr/bin/env python3
"""Compare free burn and a suppression scenario at fixed times and target cells."""

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
    parser.add_argument(
        "--scenario",
        type=Path,
        default=ROOT / "suppression/scenarios/2003-526-arrival-stacked-ring-200air.json",
    )
    parser.add_argument("--required-depth-mm", type=float, default=0.75)
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "suppression/proofs/2003-526-suppression-metrics.json",
    )
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(args.ws4_root))

    from ws4.fire.comparison import hourly_weather_steps, observed_mask, run_observed_case
    from ws4.fire.growth import GrowthConfig, SiteGrid, slope_aspect_from_elevation
    from ws4.fire.observed import load_cfsds_reanalysis_case

    from suppression.models import Scenario
    from suppression.native_growth import ContainmentSchedule, grow_fire_with_containment
    from suppression.wet import build_wet_schedule

    fixture = args.ws4_root / "tests/fixtures/fire/cfsds_2003_526"
    fire = load_cfsds_reanalysis_case(fixture)
    metadata = json.loads((fixture / "metadata.json").read_text(encoding="utf-8"))
    ffmc = float(metadata["ffmc"])
    bui = float(metadata["bui"])
    duration = float(metadata["duration_min"])
    start_mask = observed_mask(fire, 0)
    free = run_observed_case(
        fire,
        scenario="free-burn",
        ffmc=ffmc,
        bui=bui,
        duration_min=duration,
        initial_mask=start_mask,
        neighbor_radius=2,
    )
    scenario = Scenario.model_validate_json(args.scenario.read_text(encoding="utf-8"))
    rows, cols = fire.grid.nrows, fire.grid.ncols
    fuel_grid = fire.fbp_fuel_grid()
    conifer, dead, closure = fire.fbp_blend_grids()
    slope, aspect = slope_aspect_from_elevation(fire.elevation_m, fire.grid.cell_size_m, nodata=fire.grid.nodata)
    base_burnable = np.array([[value is not None for value in row] for row in fuel_grid], dtype=bool)
    seed = np.asarray(start_mask, dtype=bool) & base_burnable
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
        slope_percent_grid=slope,
        aspect_deg_grid=aspect,
        elevation_m_grid=fire.elevation_m,
        conifer_percent_grid=conifer,
        dead_fir_percent_grid=dead,
        crown_closure_percent_grid=closure,
    )
    empty = ContainmentSchedule(
        start_min=np.full((rows, cols), np.inf),
        end_min=np.full((rows, cols), np.inf),
    )
    config = GrowthConfig(
        ignition_cells=tuple((int(r), int(c)) for r, c in np.argwhere(seed)),
        max_time_min=duration,
        snapshot_interval_min=60.0,
        neighbor_radius=2,
        weather_steps=steps,
    )
    free_growth = grow_fire_with_containment(grid, config, empty)
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
    wet_growth = grow_fire_with_containment(
        grid,
        config,
        empty,
        wet_schedule=wet,
        ros_reduction_m_min=0.5,
    )
    free_times = free.growth.ignition_time_min
    wet_times = wet_growth.ignition_time_min
    free_area = {f"{s.time_min:g}": s.area_ha for s in free_growth.snapshots}
    wet_area = {f"{s.time_min:g}": s.area_ha for s in wet_growth.snapshots}
    targets = []
    seen = set()
    for drop in scenario.drops:
        center = (drop.center[0], drop.center[1])
        if center in seen:
            continue
        seen.add(center)
        col = int((center[0] - fire.grid.xll) // fire.grid.cell_size_m)
        row = rows - 1 - int((center[1] - fire.grid.yll) // fire.grid.cell_size_m)
        if not (0 <= row < rows and 0 <= col < cols):
            continue
        f = float(free_times[row, col])
        w = float(wet_times[row, col])
        targets.append(
            {
                "x": center[0],
                "y": center[1],
                "arrival_free_min": f if np.isfinite(f) else None,
                "arrival_wet_min": w if np.isfinite(w) else None,
                "delay_min": (w - f) if np.isfinite(f) and np.isfinite(w) else None,
                "burned_free": bool(np.isfinite(f)),
                "burned_wet": bool(np.isfinite(w)),
            }
        )
    delays = [t["delay_min"] for t in targets if t["delay_min"] is not None]
    payload = {
        "scenario_id": scenario.scenario_id,
        "required_depth_mm": args.required_depth_mm,
        "free_final_ha": free.metrics.area_sim_ha,
        "wet_final_ha": float(np.isfinite(wet_times).sum() * fire.grid.cell_size_m**2 / 10000.0),
        "areas_by_time": {"free": free_area, "wet": wet_area},
        "targets": targets,
        "summary": {
            "targets": len(targets),
            "targets_burned_free": sum(t["burned_free"] for t in targets),
            "targets_burned_wet": sum(t["burned_wet"] for t in targets),
            "delayed_targets": sum(1 for d in delays if d > 1.0),
            "mean_delay_min": float(np.mean(delays)) if delays else 0.0,
            "max_delay_min": float(np.max(delays)) if delays else 0.0,
            "unchanged_targets": sum(1 for d in delays if abs(d) <= 1.0),
            "never_burned_wet": sum(1 for t in targets if not t["burned_wet"]),
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
