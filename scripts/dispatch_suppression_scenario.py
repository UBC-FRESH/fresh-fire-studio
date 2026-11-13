#!/usr/bin/env python3
"""Derive task timings and travel from a P179 suppression scenario."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from suppression.dispatch import dispatch_scenario  # noqa: E402
from suppression.models import Scenario  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", type=Path)
    parser.add_argument("--out", type=Path, help="write the full result JSON")
    parser.add_argument("--json", action="store_true", help="print only JSON")
    args = parser.parse_args()

    scenario = Scenario.model_validate_json(args.scenario.read_text(encoding="utf-8"))
    result = dispatch_scenario(scenario)
    payload = {
        "scenario_id": scenario.scenario_id,
        "fire_slug": scenario.fire_slug,
        **result.to_dict(),
    }
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(payload, indent=2))
        return
    for assignment in result.assignments:
        print(
            f"{assignment.task_id:16s} {assignment.resource_id:14s} "
            f"start {assignment.actual_start_min:7.1f} end {assignment.actual_end_min:7.1f} "
            f"travel {assignment.travel_min:5.1f} service {assignment.service_min:6.1f}"
            + (" LATE" if assignment.late else "")
        )
    print("\nutilization:")
    for resource_id, value in sorted(result.utilization.items()):
        print(f"  {resource_id:14s} {value:6.1%}")
    if result.warnings:
        print("\nwarnings:")
        for warning in result.warnings:
            print(f"  - {warning}")


if __name__ == "__main__":
    main()
