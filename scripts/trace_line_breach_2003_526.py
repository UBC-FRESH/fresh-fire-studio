"""P184: trace where and when the 12-aircraft wet line breaches.

The P183 result closes all burnable barrier cells at their free-burn arrival
time, yet the coupled run still ends at the free-burn area. This script exports
the coupled ignition times of the barrier cells and compares them with the
arrival time, wet interval and water depth at the actual ignition.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def _cell_for_point(
    x: float,
    y: float,
    *,
    xll: float,
    yll: float,
    nrows: int,
    cell_size_m: float,
) -> tuple[int, int]:
    col = int((x - xll) // cell_size_m)
    row = nrows - 1 - int((y - yll) // cell_size_m)
    return row, col


def _line_cells(
    scenario: Any,
    *,
    xll: float,
    yll: float,
    nrows: int,
    cell_size_m: float,
) -> list[tuple[int, int]]:
    cells: set[tuple[int, int]] = set()
    for drop in scenario.drops:
        x, y = drop.center
        cells.add(
            _cell_for_point(
                float(x),
                float(y),
                xll=xll,
                yll=yll,
                nrows=nrows,
                cell_size_m=cell_size_m,
            )
        )
    return sorted(cells)


def _depth_at(wet: Any, row: int, col: int, time_min: float) -> float:
    if not math.isfinite(time_min):
        return 0.0
    return max(
        0.0,
        sum(drop.depth_at(row, col, time_min) for drop in wet.drops),
    )


def _wet_window(
    wet: Any,
    row: int,
    col: int,
    required_depth_mm: float,
    *,
    resolution_min: float = 0.5,
) -> tuple[float, float]:
    covering = [
        drop
        for drop in wet.drops
        if float(drop.fraction[row, col]) > 0.0
        or (
            drop.mean_depth_grid_mm is not None
            and float(drop.mean_depth_grid_mm[row, col]) > 0.0
        )
    ]
    if not covering:
        return math.inf, math.inf
    start = min(drop.start_min for drop in covering)
    limit = max(drop.end_min + drop.duration_min for drop in covering)
    first = math.inf
    last = -math.inf
    time_min = start
    while time_min <= limit + 1e-9:
        if _depth_at(wet, row, col, time_min) >= required_depth_mm:
            if not math.isfinite(first):
                first = time_min
            last = time_min
        time_min += resolution_min
    return first, last


def _finite(value: object) -> bool:
    return value is not None and math.isfinite(float(value))


def _summarize(cells: list[dict[str, object]]) -> dict[str, object]:
    classes: dict[str, int] = {}
    for cell in cells:
        name = str(cell["class"])
        classes[name] = classes.get(name, 0) + 1
    burned = [cell for cell in cells if _finite(cell["ignition_min"])]
    burnable = [cell for cell in cells if bool(cell["burnable"])]
    arrivals = [
        float(cell["free_arrival_min"])
        for cell in cells
        if _finite(cell["free_arrival_min"])
    ]
    first_wet = [
        float(cell["first_wet_min"])
        for cell in cells
        if _finite(cell["first_wet_min"])
    ]
    last_wet = [
        float(cell["last_wet_min"])
        for cell in cells
        if _finite(cell["last_wet_min"])
    ]
    first_breach = (
        min(burned, key=lambda cell: float(cell["ignition_min"])) if burned else None
    )
    return {
        "line_cells": len(cells),
        "burnable_cells": len(burnable),
        "held_cells": sum(1 for cell in cells if cell["class"] == "held"),
        "breached_cells": len(burned),
        "classes": classes,
        "free_arrival_min": (
            {"min": min(arrivals), "max": max(arrivals)} if arrivals else None
        ),
        "first_wet_min": (
            {"min": min(first_wet), "max": max(first_wet)} if first_wet else None
        ),
        "last_wet_min": (
            {"min": min(last_wet), "max": max(last_wet)} if last_wet else None
        ),
        "first_breach": (
            {
                "row": first_breach["row"],
                "col": first_breach["col"],
                "ignition_min": first_breach["ignition_min"],
                "free_arrival_min": first_breach["free_arrival_min"],
                "last_wet_min": first_breach["last_wet_min"],
                "depth_at_ignition_mm": first_breach["depth_at_ignition_mm"],
                "class": first_breach["class"],
            }
            if first_breach is not None
            else None
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ws4-root", type=Path, required=True)
    parser.add_argument(
        "--scenario",
        type=Path,
        default=ROOT / "suppression/scenarios/2003-526-fleet3-12air.json",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "suppression/proofs/2003-526-line-breach-forensics.json",
    )
    parser.add_argument("--required-depth-mm", type=float, default=0.75)
    parser.add_argument("--subcell-cell-size-m", type=float, default=10.0)
    parser.add_argument("--step-min", type=float, default=60.0)
    args = parser.parse_args()

    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(args.ws4_root))

    from ws4.fire.comparison import (
        hourly_weather_steps,
        observed_mask,
        run_observed_case,
    )
    from ws4.fire.growth import GrowthConfig, SiteGrid, slope_aspect_from_elevation
    from ws4.fire.observed import load_cfsds_reanalysis_case

    from suppression.forensics import classify_breach
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
    wet = build_wet_schedule(
        scenario,
        required_depth_mm=args.required_depth_mm,
        xll=fire.grid.xll,
        yll=fire.grid.yll,
        nrows=rows,
        ncols=cols,
        cell_size_m=fire.grid.cell_size_m,
        subcell_cell_size_m=args.subcell_cell_size_m,
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

    free_ignition = free.growth.ignition_time_min
    native_ignition = growth.ignition_time_min
    line_cells = _line_cells(
        scenario,
        xll=fire.grid.xll,
        yll=fire.grid.yll,
        nrows=rows,
        cell_size_m=fire.grid.cell_size_m,
    )
    cells: list[dict[str, object]] = []
    for row, col in line_cells:
        free_arrival = float(free_ignition[row, col])
        ignition = float(native_ignition[row, col])
        first_wet, last_wet = _wet_window(
            wet,
            row,
            col,
            args.required_depth_mm,
        )
        depth_at_ignition = _depth_at(wet, row, col, ignition)
        depth_at_free_arrival = _depth_at(wet, row, col, free_arrival)
        suppressed_at_ignition = bool(
            wet.is_suppressed(row, col, ignition) if math.isfinite(ignition) else False
        )
        burnable = bool(base_burnable[row, col])
        cells.append(
            {
                "row": row,
                "col": col,
                "x": fire.grid.xll + (col + 0.5) * fire.grid.cell_size_m,
                "y": fire.grid.yll + (rows - 1 - row + 0.5) * fire.grid.cell_size_m,
                "edge_row": row in (0, rows - 1),
                "burnable": burnable,
                "free_arrival_min": free_arrival if math.isfinite(free_arrival) else None,
                "ignition_min": ignition if math.isfinite(ignition) else None,
                "first_wet_min": first_wet if math.isfinite(first_wet) else None,
                "last_wet_min": last_wet if math.isfinite(last_wet) else None,
                "depth_at_free_arrival_mm": round(depth_at_free_arrival, 6),
                "depth_at_ignition_mm": round(depth_at_ignition, 6),
                "suppressed_at_ignition": suppressed_at_ignition,
                "class": classify_breach(
                    burnable=burnable,
                    first_wet_min=first_wet,
                    last_wet_min=last_wet,
                    free_arrival_min=free_arrival,
                    ignition_min=ignition,
                    suppressed_at_ignition=suppressed_at_ignition,
                ),
            }
        )

    summary = _summarize(cells)
    summary.update(
        {
            "free_area_ha": free.metrics.area_sim_ha,
            "native_area_ha": growth.burned_area_ha,
            "observed_area_ha": free.metrics.area_obs_ha,
            "required_depth_mm": args.required_depth_mm,
            "scenario_id": scenario.scenario_id,
            "drops": len(scenario.drops),
        }
    )
    payload = {
        "proof": "P184 line-breach forensics",
        "case_id": metadata["case_id"],
        "scenario": str(args.scenario),
        "summary": summary,
        "cells": cells,
        "limits": [
            "Barrier cells are derived from drop centres, not from a surveyed line.",
            "The wet interval is sampled at 0.5 min for classification.",
            "Ignition time is the first coupled ignition; it is not an observed fire time.",
            "A post-expiry breach is a model-duration result, not an operational hold estimate.",
            "The 12-aircraft scenario is diagnostic, not a deployment recommendation.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
