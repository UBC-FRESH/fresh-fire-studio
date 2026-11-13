#!/usr/bin/env python3
"""Compare native_growth free burn with the benchmark WS4 kernel."""

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
        "--out",
        type=Path,
        default=ROOT / "suppression/proofs/2003-526-native-parity.json",
    )
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(args.ws4_root))

    from ws4.fire.comparison import compare_masks, hourly_weather_steps, observed_mask, run_observed_case
    from ws4.fire.growth import GrowthConfig, SiteGrid, slope_aspect_from_elevation
    from ws4.fire.observed import load_cfsds_reanalysis_case

    from suppression.native_growth import ContainmentSchedule, grow_fire_with_containment

    fixture = args.ws4_root / "tests/fixtures/fire/cfsds_2003_526"
    fire = load_cfsds_reanalysis_case(fixture)
    metadata = json.loads((fixture / "metadata.json").read_text(encoding="utf-8"))
    ffmc = float(metadata["ffmc"])
    bui = float(metadata["bui"])
    duration = float(metadata["duration_min"])
    start_mask = observed_mask(fire, 0)
    observed = observed_mask(fire, -1)
    benchmark = run_observed_case(
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
    native = grow_fire_with_containment(
        grid,
        GrowthConfig(
            ignition_cells=tuple((int(row), int(col)) for row, col in np.argwhere(seed)),
            max_time_min=duration,
            snapshot_interval_min=60.0,
            neighbor_radius=2,
            weather_steps=steps,
        ),
        empty,
    )
    benchmark_mask = np.isfinite(benchmark.growth.ignition_time_min)
    native_mask = np.isfinite(native.ignition_time_min)
    mismatch = benchmark_mask ^ native_mask
    both = benchmark_mask & native_mask
    ignition_delta = np.abs(benchmark.growth.ignition_time_min[both] - native.ignition_time_min[both])
    payload = {
        "case": "2003_526",
        "benchmark_area_ha": benchmark.metrics.area_sim_ha,
        "native_area_ha": float(native_mask.sum() * fire.grid.cell_size_m**2 / 10000.0),
        "benchmark_iou": benchmark.metrics.iou,
        "mismatch_cells": int(mismatch.sum()),
        "both_cells": int(both.sum()),
        "max_abs_arrival_delta_min": float(ignition_delta.max()) if ignition_delta.size else 0.0,
        "mean_abs_arrival_delta_min": float(ignition_delta.mean()) if ignition_delta.size else 0.0,
        "masks_equal": bool(not mismatch.any()),
        "observed": int(observed.sum()),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
