#!/usr/bin/env python3
"""Trace per-target drop depth and fire arrival for a scenario."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ws4-root", type=Path, required=True)
    parser.add_argument(
        "--scenario",
        type=Path,
        default=ROOT / "suppression/scenarios/2003-526-arrival-stacked-6air.json",
    )
    parser.add_argument("--required-depth-mm", type=float, default=0.75)
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "suppression/proofs/2003-526-target-wetness-trace.json",
    )
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(args.ws4_root))

    from ws4.fire.comparison import observed_mask, run_observed_case
    from ws4.fire.observed import load_cfsds_reanalysis_case

    from suppression.models import Scenario
    from suppression.trace import trace_targets
    from suppression.wet import build_wet_schedule

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
    scenario = Scenario.model_validate_json(args.scenario.read_text(encoding="utf-8"))
    centers = []
    seen = set()
    for drop in scenario.drops:
        key = (drop.center[0], drop.center[1])
        if key not in seen:
            seen.add(key)
            centers.append(key)
    wet = build_wet_schedule(
        scenario,
        required_depth_mm=args.required_depth_mm,
        xll=fire.grid.xll,
        yll=fire.grid.yll,
        nrows=fire.grid.nrows,
        ncols=fire.grid.ncols,
        cell_size_m=fire.grid.cell_size_m,
        subcell_cell_size_m=10.0,
    )
    traces = trace_targets(
        wet,
        free.growth.ignition_time_min,
        centers,
        xll=fire.grid.xll,
        yll=fire.grid.yll,
        nrows=fire.grid.nrows,
        ncols=fire.grid.ncols,
        cell_size_m=fire.grid.cell_size_m,
    )
    payload = {
        "scenario_id": scenario.scenario_id,
        "required_depth_mm": args.required_depth_mm,
        "targets": [trace.to_dict() for trace in traces],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    for trace in traces[:5]:
        print(
            f"target ({trace.x:.0f},{trace.y:.0f}) arrival={trace.arrival_min:.1f} "
            f"combined={trace.combined_at_arrival_mm:.3f} max={trace.max_combined_mm:.3f} "
            f"wet={trace.wet_at_arrival} drops={len(trace.drops)}"
        )
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
