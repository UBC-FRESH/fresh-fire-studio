#!/usr/bin/env python3
"""Evaluate a closed 20-cell-wide barrier with the benchmark WS4 kernel."""

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
    parser.add_argument("--barrier-x", type=float, default=493600.0)
    parser.add_argument("--width-cells", type=int, default=20)
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "suppression/proofs/2003-526-closed-barrier-metrics.json",
    )
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(args.ws4_root))

    from ws4.fire.comparison import observed_mask, run_observed_case
    from ws4.fire.observed import load_cfsds_reanalysis_case

    fixture = args.ws4_root / "tests/fixtures/fire/cfsds_2003_526"
    fire = load_cfsds_reanalysis_case(fixture)
    metadata = json.loads((fixture / "metadata.json").read_text(encoding="utf-8"))
    common = {
        "ffmc": float(metadata["ffmc"]),
        "bui": float(metadata["bui"]),
        "duration_min": float(metadata["duration_min"]),
        "initial_mask": observed_mask(fire, 0),
        "neighbor_radius": 2,
    }
    free = run_observed_case(fire, scenario="free-burn", **common)
    col = int(round((args.barrier_x - fire.grid.xll) / fire.grid.cell_size_m))
    mask = np.zeros((fire.grid.nrows, fire.grid.ncols), dtype=bool)
    mask[:, max(0, col) : min(fire.grid.ncols, col + args.width_cells)] = True
    contained = run_observed_case(
        fire,
        scenario="closed-barrier",
        containment_mask=mask,
        **common,
    )
    free_times = free.growth.ignition_time_min
    contained_times = contained.growth.ignition_time_min
    cells = np.argwhere(mask)
    never = sum(1 for row, col_index in cells if not np.isfinite(contained_times[row, col_index]))
    delays = [
        float(contained_times[row, col_index] - free_times[row, col_index])
        for row, col_index in cells
        if np.isfinite(free_times[row, col_index]) and np.isfinite(contained_times[row, col_index])
    ]
    payload = {
        "case": "2003_526",
        "barrier_x": args.barrier_x,
        "width_cells": args.width_cells,
        "barrier_cells": int(mask.sum()),
        "free_area_ha": free.metrics.area_sim_ha,
        "contained_area_ha": contained.metrics.area_sim_ha,
        "observed_area_ha": free.metrics.area_obs_ha,
        "free_iou": free.metrics.iou,
        "contained_iou": contained.metrics.iou,
        "area_reduction_ha": free.metrics.area_sim_ha - contained.metrics.area_sim_ha,
        "barrier_cells_never_burned": never,
        "barrier_cells_with_delay": len(delays),
        "mean_delay_min": float(np.mean(delays)) if delays else 0.0,
        "max_delay_min": float(np.max(delays)) if delays else 0.0,
        "limits": [
            "The barrier is a static non-burnable strip, not water.",
            "It is a control for geometry and containment, not an operational fuel break.",
            "The 100 m fire grid remains coarse.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
