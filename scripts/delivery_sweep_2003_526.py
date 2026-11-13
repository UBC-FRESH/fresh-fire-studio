#!/usr/bin/env python3
"""Sweep aircraft count, passes and lake distance for the cycle mission."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mission",
        type=Path,
        default=ROOT / "portal/static/suppression-mission.json",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "suppression/proofs/2003-526-delivery-sweep.json",
    )
    parser.add_argument("--required-depth-mm", type=float, default=0.75)
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))

    from suppression.cycle import CyclePerformance
    from suppression.delivery import delivery_sweep

    mission = json.loads(args.mission.read_text(encoding="utf-8"))
    targets = tuple((float(x), float(y)) for x, y in mission["fire_line"])
    current_lake = (float(mission["lake"]["x"]), float(mission["lake"]["y"]))
    lakes = {
        "current": current_lake,
        "near": (490500.0, 5725800.0),
        "far": (488500.0, 5724000.0),
    }
    sweep = delivery_sweep(
        targets=targets,
        lakes=lakes,
        aircraft_counts=(1, 3, 5),
        passes_values=(1, 2, 3),
        performance=CyclePerformance(),
        required_depth_mm=args.required_depth_mm,
    )
    payload = {
        "scenario": mission.get("case", "cfsds-2003-526"),
        "required_depth_mm": args.required_depth_mm,
        "lakes": {name: {"x": lake[0], "y": lake[1]} for name, lake in lakes.items()},
        "sweep": sweep,
        "selected": {
            "one_pass_three_aircraft": next(
                row for row in sweep["current"] if row["passes"] == 1 and row["aircraft_count"] == 3
            ),
            "two_pass_three_aircraft": next(
                row for row in sweep["current"] if row["passes"] == 2 and row["aircraft_count"] == 3
            ),
            "three_pass_three_aircraft": next(
                row for row in sweep["current"] if row["passes"] == 3 and row["aircraft_count"] == 3
            ),
        },
        "note": "Mass and cycle-time sweep only. It does not rerun fire growth for each case.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    for passes in (1, 2, 3):
        row = next(r for r in sweep["current"] if r["passes"] == passes and r["aircraft_count"] == 3)
        print(
            f"{passes} pass(es), 3 aircraft: {row['delivered_l']:.0f} L, "
            f"{row['line_mean_depth_mm']:.2f} mm, {row['coverage_fraction']:.0%} coverage, "
            f"{row['deficit_l']:.0f} L deficit, {row['elapsed_min']:.1f} min"
        )
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
