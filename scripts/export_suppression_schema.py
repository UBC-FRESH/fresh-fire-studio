#!/usr/bin/env python3
"""Write the P179 suppression JSON schema."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from suppression.models import Scenario  # noqa: E402


def main() -> None:
    path = ROOT / "suppression" / "scenario.schema.json"
    path.write_text(json.dumps(Scenario.model_json_schema(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
