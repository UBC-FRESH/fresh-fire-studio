#!/usr/bin/env python3
"""Validate a P179 suppression scenario and print its effect contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from suppression.models import Scenario  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", type=Path)
    parser.add_argument("--effects", action="store_true", help="print effect events")
    args = parser.parse_args()
    scenario = Scenario.model_validate_json(args.scenario.read_text(encoding="utf-8"))
    print(f"valid: {scenario.scenario_id} · {scenario.fire_slug}")
    print(f"resources: {len(scenario.resources)} · tasks: {len(scenario.tasks)}")
    print(f"lines: {len(scenario.lines)} · drops: {len(scenario.drops)}")
    print(f"effects: {len(scenario.effect_events())}")
    if args.effects:
        print(json.dumps([event.model_dump(mode="json") for event in scenario.effect_events()], indent=2))


if __name__ == "__main__":
    main()
