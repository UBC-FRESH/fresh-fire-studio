#!/usr/bin/env python3
"""Run an evidence-bounded native suppression ensemble on 2003_526."""

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
        default=ROOT / "suppression/scenarios/2003-526-drop-line-proof.json",
    )
    parser.add_argument("--samples", type=int, default=32)
    parser.add_argument("--seed", type=int, default=20261113)
    parser.add_argument("--subcell-cell-size-m", type=float, default=10.0)
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "suppression/proofs/2003-526-evidence-ensemble.json",
    )
    args = parser.parse_args()

    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(args.ws4_root))

    from ws4.fire.comparison import compare_masks, hourly_weather_steps, observed_mask
    from ws4.fire.growth import GrowthConfig, SiteGrid, slope_aspect_from_elevation
    from ws4.fire.observed import load_cfsds_reanalysis_case

    from suppression.models import Scenario
    from suppression.native_growth import ContainmentSchedule, grow_fire_with_containment
    from suppression.uncertainty import (
        apply_sample_to_scenario,
        sample_evidence,
        summarize_ensemble,
    )
    from suppression.wet import build_wet_schedule

    fixture = args.ws4_root / "tests/fixtures/fire/cfsds_2003_526"
    fire = load_cfsds_reanalysis_case(fixture)
    metadata = json.loads((fixture / "metadata.json").read_text(encoding="utf-8"))
    base_scenario = Scenario.model_validate_json(args.scenario.read_text(encoding="utf-8"))
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

    def run(wet, ros_reduction: float | None):
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
            ros_reduction_m_min=ros_reduction,
        )
        simulated = np.isfinite(growth.ignition_time_min)
        return growth, compare_masks(simulated, observed, fire.grid)

    _, free_metrics = run(None, None)
    rng = np.random.default_rng(args.seed)
    samples = [sample_evidence(rng) for _ in range(args.samples)]
    outcomes = []
    for index, sample in enumerate(samples, start=1):
        scenario = apply_sample_to_scenario(base_scenario, sample)
        wet = build_wet_schedule(
            scenario,
            required_depth_mm=sample.required_depth_mm,
            xll=fire.grid.xll,
            yll=fire.grid.yll,
            nrows=rows,
            ncols=cols,
            cell_size_m=fire.grid.cell_size_m,
            subcell_cell_size_m=args.subcell_cell_size_m,
        )
        _, metrics = run(wet, sample.ros_reduction_m_min)
        outcomes.append(metrics.to_dict())
        print(f"sample {index:02d}/{args.samples}: {metrics.area_sim_ha:.0f} ha")
    areas = [outcome["area_sim_ha"] for outcome in outcomes]
    summary = summarize_ensemble(areas, free_metrics.area_sim_ha, samples=samples)
    payload = {
        "proof": "P179.18 evidence-bounded suppression ensemble",
        "scenario_id": base_scenario.scenario_id,
        "seed": args.seed,
        "n": len(samples),
        "free_burn": free_metrics.to_dict(),
        "samples": [sample.to_dict() for sample in samples],
        "outcomes": outcomes,
        "summary": summary,
        "limits": [
            "Parameters are sampled from published means and SDs, not local validation data.",
            "The drop geometry and 100 m fire grid are fixed within the ensemble.",
            "The Wheatley experiments are low-intensity surface fires, not 2003_526.",
            "Zero containment probability is a model result, not an operational conclusion.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
