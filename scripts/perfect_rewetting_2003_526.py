"""P185: perfect periodic re-wetting interval and depth envelope.

This test replaces the aircraft-dependent drop schedule with a full-cell
periodic application. It asks a narrow question: if the line could be re-wetted
perfectly, what interval and depth keep it closed?
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


def _line_summary(
    *,
    ignition: np.ndarray,
    free_ignition: np.ndarray,
    burnable: np.ndarray,
    line_cells: list[tuple[int, int]],
    wet: Any,
) -> dict[str, object]:
    cells = [
        (row, col)
        for row, col in line_cells
        if bool(burnable[row, col])
    ]
    arrivals = [float(free_ignition[row, col]) for row, col in cells]
    finite_arrivals = [value for value in arrivals if math.isfinite(value)]
    breached = [
        (row, col, float(ignition[row, col]))
        for row, col in cells
        if math.isfinite(float(ignition[row, col]))
    ]
    wet_at_arrival = sum(
        1
        for (row, col), arrival in zip(cells, arrivals)
        if math.isfinite(arrival) and wet.is_suppressed(row, col, arrival)
    )
    first = min(breached, key=lambda value: value[2]) if breached else None
    return {
        "burnable_line_cells": len(cells),
        "held_cells": len(cells) - len(breached),
        "breached_cells": len(breached),
        "wet_at_free_arrival": wet_at_arrival,
        "free_arrival_min": (
            {"min": min(finite_arrivals), "max": max(finite_arrivals)}
            if finite_arrivals
            else None
        ),
        "first_breach": (
            {
                "row": first[0],
                "col": first[1],
                "ignition_min": first[2],
            }
            if first is not None
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
        default=ROOT / "suppression/proofs/2003-526-perfect-rewetting.json",
    )
    parser.add_argument("--required-depth-mm", type=float, default=0.75)
    parser.add_argument("--decay-min", type=float, default=60.0)
    parser.add_argument("--step-min", type=float, default=60.0)
    parser.add_argument("--subcell-cell-size-m", type=float, default=10.0)
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

    from suppression.models import Scenario
    from suppression.native_growth import (
        build_containment_schedule,
        grow_fire_with_containment,
    )
    from suppression.periodic import PeriodicWetSchedule
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
    free_ignition = free.growth.ignition_time_min

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
    line_cells = _line_cells(
        scenario,
        xll=fire.grid.xll,
        yll=fire.grid.yll,
        nrows=rows,
        cell_size_m=fire.grid.cell_size_m,
    )
    mask = np.zeros((rows, cols), dtype=bool)
    for row, col in line_cells:
        mask[row, col] = True

    actual_wet = build_wet_schedule(
        scenario,
        required_depth_mm=args.required_depth_mm,
        xll=fire.grid.xll,
        yll=fire.grid.yll,
        nrows=rows,
        ncols=cols,
        cell_size_m=fire.grid.cell_size_m,
        subcell_cell_size_m=args.subcell_cell_size_m,
    )
    reference_depths = [
        _depth_at(actual_wet, row, col, float(free_ignition[row, col]))
        for row, col in line_cells
        if base_burnable[row, col] and math.isfinite(float(free_ignition[row, col]))
    ]
    reference_depth = float(np.mean(reference_depths))
    cases = [
        (15.0, reference_depth),
        (18.0, reference_depth),
        (30.0, reference_depth),
        (60.0, reference_depth),
        (30.0, 1.5),
        (30.0, 2.0),
        (30.0, 3.0),
        (60.0, 3.0),
    ]

    reference_stacks = len(scenario.drops) / len(line_cells)
    line_count = len(line_cells)
    cycle_min = 4.25
    payload_l = 6000.0

    results = []
    for interval, depth in cases:
        wet = PeriodicWetSchedule(
            mask=mask,
            depth_mm=depth,
            required_depth_mm=args.required_depth_mm,
            decay_min=args.decay_min,
            interval_min=interval,
            start_min=600.0,
            end_min=duration,
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
        summary = _line_summary(
            ignition=growth.ignition_time_min,
            free_ignition=free_ignition,
            burnable=base_burnable,
            line_cells=line_cells,
            wet=wet,
        )
        stacks = max(
            1,
            math.ceil(
                reference_stacks * depth / reference_depth - 1e-9
            ),
        )
        sorties_per_application = line_count * stacks
        sorties_per_hour = sorties_per_application * 60.0 / interval
        aircraft_lower_bound = math.ceil(
            sorties_per_hour * cycle_min / 60.0
        )
        summary.update(
            {
                "interval_min": interval,
                "depth_mm": round(depth, 6),
                "effective_hold_min": round(wet.effective_hold_min, 3),
                "native_area_ha": growth.burned_area_ha,
                "feasible": summary["held_cells"] == summary["burnable_line_cells"],
                "drops_per_cell": stacks,
                "sorties_per_application": sorties_per_application,
                "sorties_per_hour": round(sorties_per_hour, 1),
                "aircraft_lower_bound": aircraft_lower_bound,
                "water_l_per_hour": round(sorties_per_hour * payload_l, 1),
            }
        )
        results.append(summary)
        print(
            f"interval={interval:g} depth={depth:.3f} "
            f"hold={wet.effective_hold_min:.1f} area={growth.burned_area_ha:.1f} "
            f"held={summary['held_cells']}/{summary['burnable_line_cells']} "
            f"aircraft>={aircraft_lower_bound}"
        )

    feasible_results = [
        result for result in results if bool(result["feasible"])
    ]
    minimum = (
        min(
            feasible_results,
            key=lambda result: int(result["aircraft_lower_bound"]),
        )
        if feasible_results
        else None
    )
    payload = {
        "proof": "P185 perfect periodic re-wetting",
        "case_id": metadata["case_id"],
        "scenario": str(args.scenario),
        "reference_depth_mm": round(reference_depth, 6),
        "free_area_ha": free.metrics.area_sim_ha,
        "required_depth_mm": args.required_depth_mm,
        "decay_min": args.decay_min,
        "fleet_assumptions": {
            "line_cells": line_count,
            "reference_drops_per_cell": reference_stacks,
            "cycle_min": cycle_min,
            "payload_l": payload_l,
            "note": "continuous perfect dispatch lower bound; not an operational plan",
        },
        "minimum_feasible": minimum,
        "results": results,
        "limits": [
            "Perfect full-cell wetting, not an aircraft schedule.",
            "No partial coverage, turn time, water supply or dispatch constraints.",
            "The synthetic interval is a diagnostic bound, not an operational plan.",
            "A successful interval must still be converted to sorties and fleet.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
