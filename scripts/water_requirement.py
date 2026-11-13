#!/usr/bin/env python3
"""Print Van Wagner-Taylor water depths for one fire behaviour state."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from suppression.water import required_depths  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intensity-kw-m", type=float, required=True)
    parser.add_argument("--fuel-load-kg-m2", type=float, required=True)
    parser.add_argument("--radiant-kw-m2", type=float, required=True)
    parser.add_argument("--ros-m-min", type=float, required=True)
    parser.add_argument("--efficiency", type=float, default=1.0)
    args = parser.parse_args()
    result = required_depths(
        args.intensity_kw_m,
        args.fuel_load_kg_m2,
        args.radiant_kw_m2,
        args.ros_m_min,
        application_efficiency=args.efficiency,
    )
    print(f"quench:  {result.quench_mm:.3f} mm = {result.quench_mm:.3f} L/m2")
    print(f"cool:    {result.cool_mm:.3f} mm = {result.cool_mm:.3f} L/m2")
    print(f"wet:     {result.wet_mm:.3f} mm = {result.wet_mm:.3f} L/m2")
    print(f"burning: {result.burning_mm:.3f} mm = {result.burning_mm:.3f} L/m2")


if __name__ == "__main__":
    main()
