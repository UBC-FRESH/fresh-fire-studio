#!/usr/bin/env python3
"""P179.2 diagnostic: time-aware line construction on the 2003_526 grid.

The P177 kernel has a static containment mask. This harness steps the fire
forward in fixed chunks; at each chunk it applies the P179 line mask that exists
at that time. The entire previously burned area is used as the next chunk's
ignition seed, which preserves the burned perimeter without changing the P177
kernel. The result is an approximation, not a replacement for a native
time-dependent growth kernel.
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
    parser.add_argument("--step-min", type=float, default=60.0)
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "suppression/proofs/2003-526-temporal.json",
    )
    args = parser.parse_args()

    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(args.ws4_root))

    from ws4.fire.comparison import (
        compare_masks,
        hourly_weather_steps,
        observed_mask,
        run_observed_case,
    )
    from ws4.fire.growth import GrowthConfig, SiteGrid, grow_fire, slope_aspect_from_elevation
    from ws4.fire.observed import load_cfsds_reanalysis_case

    from suppression.models import Scenario
    from suppression.temporal import effects_at, line_cells_at

    fixture = args.ws4_root / "tests/fixtures/fire/cfsds_2003_526"
    fire = load_cfsds_reanalysis_case(fixture)
    metadata = json.loads((fixture / "metadata.json").read_text(encoding="utf-8"))
    scenario = Scenario.model_validate_json(args.scenario.read_text(encoding="utf-8"))
    if args.step_min <= 0:
        raise SystemExit("--step-min must be positive")

    ffmc = float(metadata["ffmc"])
    bui = float(metadata["bui"])
    duration = float(metadata["duration_min"])
    start_mask = observed_mask(fire, 0)
    observed = observed_mask(fire, -1)
    steps = hourly_weather_steps(fire, ffmc=ffmc, bui=bui)

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
    burned = np.asarray(start_mask, dtype=bool) & base_burnable

    def weather_for(start: float, end: float):
        selected = [step for step in steps if start <= step.start_min < end]
        if not selected:
            prior = [step for step in steps if step.start_min <= start]
            selected = [prior[-1] if prior else steps[-1]]
        shifted = [replace(step, start_min=max(0.0, step.start_min - start)) for step in selected]
        if shifted[0].start_min != 0.0:
            prior = [step for step in steps if step.start_min <= start]
            source = prior[-1] if prior else steps[-1]
            shifted.insert(0, replace(source, start_min=0.0))
        return tuple(shifted)

    def run_chunk(start: float, end: float) -> np.ndarray:
        chunk_weather = weather_for(start, end)
        line_mask = effects_at(
            scenario,
            start,
            xll=fire.grid.xll,
            yll=fire.grid.yll,
            nrows=rows,
            ncols=cols,
            cell_size_m=fire.grid.cell_size_m,
        ).containment
        burnable = base_burnable & ~line_mask
        seed = burned & burnable
        if not seed.any():
            return burned
        first = chunk_weather[0]
        grid = SiteGrid(
            fuel_type="C2",
            rows=rows,
            cols=cols,
            cell_size_m=fire.grid.cell_size_m,
            ffmc=float(first.ffmc if first.ffmc is not None else ffmc),
            bui=float(first.bui if first.bui is not None else bui),
            wind_kmh=first.wind_kmh,
            wind_direction_deg=first.wind_direction_deg,
            slope_percent=32.0,
            aspect_deg=180.0,
            burnable=burnable,
            fuel_type_grid=fuel_grid,
            slope_percent_grid=slope_grid,
            aspect_deg_grid=aspect_grid,
            elevation_m_grid=fire.elevation_m,
            conifer_percent_grid=conifer_grid,
            dead_fir_percent_grid=dead_grid,
            crown_closure_percent_grid=closure_grid,
        )
        growth = grow_fire(
            grid,
            GrowthConfig(
                ignition_cells=tuple(
                    (int(row), int(col)) for row, col in np.argwhere(seed)
                ),
                max_time_min=end - start,
                snapshot_interval_min=end - start,
                neighbor_radius=2,
                weather_steps=chunk_weather,
            ),
        )
        return burned | np.isfinite(growth.ignition_time_min)

    checkpoint_set = {
        0.0,
        60.0,
        240.0,
        720.0,
        1440.0,
        1441.0,
        duration,
        scenario.timeline_end_min,
    }
    for line in scenario.lines:
        checkpoint_set.update(
            {
                line.constructed_start_min,
                line.constructed_end_min,
            }
        )
        if line.breached_at_min is not None:
            checkpoint_set.add(line.breached_at_min)
            checkpoint_set.add(max(0.0, line.breached_at_min - args.step_min))
    for drop in scenario.drops:
        checkpoint_set.add(drop.start_min)
        checkpoint_set.add(drop.end_min)
        checkpoint_set.add(drop.end_min + drop.effect_duration_min)
    checkpoints = sorted({time for time in checkpoint_set if 0 <= time <= duration})
    areas: dict[str, float] = {
        "0.0": float(burned.sum() * fire.grid.cell_size_m**2 / 10_000)
    }
    line_cells: dict[str, int] = {
        "0.0": line_cells_at(
            scenario,
            0.0,
            xll=fire.grid.xll,
            yll=fire.grid.yll,
            nrows=rows,
            ncols=cols,
            cell_size_m=fire.grid.cell_size_m,
        )
    }
    time = 0.0
    chunk_index = 0
    while time < duration - 1e-9:
        end = min(time + args.step_min, duration)
        burned = run_chunk(time, end)
        time = end
        chunk_index += 1
        if chunk_index % 60 == 0:
            print(f"  stepped to {time:.0f} min, {burned.sum() * fire.grid.cell_size_m**2 / 10_000:.1f} ha")
        for checkpoint in checkpoints:
            if abs(checkpoint - time) < 1e-9:
                areas[str(checkpoint)] = float(
                    burned.sum() * fire.grid.cell_size_m**2 / 10_000
                )
                line_cells[str(checkpoint)] = line_cells_at(
                    scenario,
                    checkpoint,
                    xll=fire.grid.xll,
                    yll=fire.grid.yll,
                    nrows=rows,
                    ncols=cols,
                    cell_size_m=fire.grid.cell_size_m,
                )

    metrics = compare_masks(burned, observed, fire.grid)
    static_path = ROOT / "suppression/proofs/2003-526.json"
    static = json.loads(static_path.read_text(encoding="utf-8")) if static_path.exists() else None
    payload = {
        "proof": "P179.2 time-aware line construction",
        "case_id": metadata["case_id"],
        "scenario_id": scenario.scenario_id,
        "method": {
            "chunk_min": args.step_min,
            "seed": "all previously burned cells",
            "line_mask": "active at the start of each chunk",
            "drop_growth": "not coupled in this proof",
        },
        "grid": {
            "crs": fire.grid.crs,
            "xll": fire.grid.xll,
            "yll": fire.grid.yll,
            "ncols": cols,
            "nrows": rows,
            "cell_size_m": fire.grid.cell_size_m,
        },
        "free_burn": free.metrics.to_dict(),
        "temporal": metrics.to_dict(),
        "static_full_line": static["contained"] if static else None,
        "area_by_time_ha": areas,
        "line_cells_by_time": line_cells,
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
        "delta_vs_static": (
            {
                "area_difference_ha": metrics.area_sim_ha - static["contained"]["area_sim_ha"],
                "iou_change": metrics.iou - static["contained"]["iou"],
            }
            if static
            else None
        ),
        "limits": [
            "The line is synthetic and built over 24 hours.",
            "The P177 kernel is static; this harness rebuilds its seed every chunk.",
            "Seeding the whole burned area at each chunk is an approximation.",
            "Drop moisture and decay are scheduled but not fed into growth.",
            "This is a diagnostic contract proof, not a calibrated suppression result.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"free burn: {free.metrics.area_sim_ha:.1f} ha, IoU {free.metrics.iou:.3f}")
    print(
        f"temporal line: {metrics.area_sim_ha:.1f} ha, IoU {metrics.iou:.3f}, "
        f"area reduction {payload['delta_vs_free']['area_reduction_pct']:.1f}%"
    )
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
