#!/usr/bin/env python3
"""P179.1 diagnostic: rasterize a suppression line and compare 2003_526 runs.

This is intentionally a static containment-line proof, not an operational
suppression reconstruction. It uses the P177 WS4 kernel that accepts a
``containment_mask`` and the P179.0 suppression contract in this repository.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

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
        default=ROOT / "suppression/scenarios/2003-526-proof.json",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "suppression/proofs/2003-526.json",
    )
    args = parser.parse_args()

    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(args.ws4_root))

    from ws4.fire.comparison import observed_mask, run_observed_case
    from ws4.fire.observed import load_cfsds_reanalysis_case

    from suppression.effects import rasterize_effects
    from suppression.models import Scenario

    fixture = args.ws4_root / "tests/fixtures/fire/cfsds_2003_526"
    fire = load_cfsds_reanalysis_case(fixture)
    metadata = json.loads((fixture / "metadata.json").read_text(encoding="utf-8"))
    scenario = Scenario.model_validate_json(args.scenario.read_text(encoding="utf-8"))

    start_mask = observed_mask(fire, 0)
    common = {
        "ffmc": float(metadata["ffmc"]),
        "bui": float(metadata["bui"]),
        "duration_min": float(metadata["duration_min"]),
        "initial_mask": start_mask,
        "neighbor_radius": 2,
    }
    free = run_observed_case(fire, scenario="free-burn", **common)

    effects = rasterize_effects(
        scenario.effect_events(),
        xll=fire.grid.xll,
        yll=fire.grid.yll,
        nrows=fire.grid.nrows,
        ncols=fire.grid.ncols,
        cell_size_m=fire.grid.cell_size_m,
    )
    if not effects.containment.any():
        raise SystemExit("suppression scenario rasterized to an empty containment mask")

    contained = run_observed_case(
        fire,
        scenario="suppression-line",
        containment_mask=effects.containment,
        **common,
    )

    free_area = free.metrics.area_sim_ha
    contained_area = contained.metrics.area_sim_ha
    payload = {
        "proof": "P179.1 static line-effect raster",
        "case_id": metadata["case_id"],
        "scenario_id": scenario.scenario_id,
        "grid": {
            "crs": fire.grid.crs,
            "xll": fire.grid.xll,
            "yll": fire.grid.yll,
            "ncols": fire.grid.ncols,
            "nrows": fire.grid.nrows,
            "cell_size_m": fire.grid.cell_size_m,
        },
        "effect_layers": {
            "line_cells": int(effects.line.sum()),
            "water_cells": int(effects.water.sum()),
            "foam_cells": int(effects.foam.sum()),
            "retardant_cells": int(effects.retardant.sum()),
        },
        "free_burn": free.metrics.to_dict(),
        "contained": contained.metrics.to_dict(),
        "delta": {
            "area_reduction_ha": free_area - contained_area,
            "area_reduction_pct": (free_area - contained_area) / free_area * 100.0 if free_area else 0.0,
            "iou_change": contained.metrics.iou - free.metrics.iou,
        },
        "limits": [
            "The line is synthetic and applied statically for the whole run.",
            "Drop effects are rasterized but not yet fed into the fire kernel.",
            "This is a diagnostic contract proof, not a calibrated suppression result.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"free-burn area: {free_area:.1f} ha, IoU {free.metrics.iou:.3f}")
    print(f"contained area: {contained_area:.1f} ha, IoU {contained.metrics.iou:.3f}")
    print(
        f"reduction: {payload['delta']['area_reduction_ha']:.1f} ha "
        f"({payload['delta']['area_reduction_pct']:.1f}%)"
    )
    print(f"line cells: {payload['effect_layers']['line_cells']}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
