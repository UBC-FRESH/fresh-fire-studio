"""Print the anonymous FRESH Fire Studio event counters.

Usage:
    python scripts/analytics_report.py
    python scripts/analytics_report.py --watch 60
"""

from __future__ import annotations

import argparse
import json
import time
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from portal.app import CASES
from urllib.error import HTTPError

NAMESPACE = "ubc-fresh-fire-studio"
BASE = f"https://abacus.jasoncameron.dev/get/{NAMESPACE}"
EVENTS = [
    "portal",
    "bc-home",
    "cfs-home",
    "methods",
    "pilot",
    "reel",
    "ask",
    "scene-vri-pilot",
    "scene-g50872-vri",
]
for case in CASES:
    slug = str(case["slug"])
    EVENTS.extend([f"case-{slug}", f"scene-{slug}"])


def _get(event: str) -> int | None:
    try:
        with urllib.request.urlopen(f"{BASE}/{event}", timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return int(payload.get("value", 0))
    except HTTPError as error:
        # 404 = counter has not been created yet; a real service error is offline.
        if error.code == 404:
            return 0
        return None
    except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--watch", type=int, default=0, help="refresh interval in seconds")
    args = parser.parse_args()
    while True:
        print(f"\nFRESH Fire Studio · anonymous counters · {time.strftime('%Y-%m-%d %H:%M:%S')}")
        for event in EVENTS:
            value = _get(event)
            print(f"  {event:<32} {'offline' if value is None else value:>8}")
        if not args.watch:
            break
        time.sleep(args.watch)


if __name__ == "__main__":
    main()
