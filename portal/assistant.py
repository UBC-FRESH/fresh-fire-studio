"""Read-only, rate-limited assistant bridge for FRESH Fire Studio."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

MODEL = os.environ.get("FRESH_ASSISTANT_MODEL", "opencode-go/deepseek-v4.1-flash")
TIMEOUT = float(os.environ.get("FRESH_ASSISTANT_TIMEOUT", "75"))
MAX_QUESTION = 1200


def _portal_context(cases: list[dict[str, Any]]) -> str:
    rows = "\n".join(
        f"- {case['title']}: observed {case.get('area_ha', '—')} ha, "
        f"IoU {case.get('iou', '—')}, {case.get('weather', '')}"
        for case in cases
    )
    return f"""FRESH Fire Studio is a public demonstration of WS4/FBP fire
behaviour from the UBC FRESH Lab. It is a model replay, not an operational
forecast.

Portal facts:
- Six public benchmark fires: {', '.join(str(case['title']) for case in cases)}.
- Each benchmark scene uses public observed perimeters and event windows,
  public terrain/fuel/weather inputs, synthetic Nemora tree placement, and a
  browser-side foveated tree LOD.
- Observed extent is the default. The free-burn model extent is a separate
  comparison; it is not a prediction of the observed event.
- The G50872 VRI pilot uses a real 2023 BC final perimeter, 871 public TSA 24
  VRI blocks, public SRTM terrain, a public C3 fuel sample and Open-Meteo
  reanalysis. The observed final extent is real; stems and ignition timing are
  synthetic; no daily progression is available.
- The smaller VRI pilot uses a 1.8 ha G50266 (2013) observed perimeter overlay
  inside a 105 ha synthetic pilot cluster.
- Near-field trees are a visual 500 stems/ha sample, not an inventory. The
  overview canopy and mid-field are impostors.
- The model is not calibrated for BC. Small suppressed fires are not ROS
  evidence. A no-go validation tier is a valid result.
- `/suppression/` is a separate diagnostic mission replay. It shows suppression
  mission geometry, not a validated fire effect. The realistic 21-drop line is
  placement-limited: 32 evidence-ensemble members all end at 5,325 ha, with 0
  containment probability. A deliberately synthetic 20-cell control barrier
  ends at 3,574.7 ha and has ROS-reduction/area correlation about -0.78. The
  control is not operational and must not be described as a suppression plan.
- The suppression evidence comes from published sources: Wheatley 2024
  experimental burns, McFayden et al. 2023 aerial drop guide, and Van Wagner &
  Taylor 2022 water requirements. It is evidence-bounded, not field-validated
  for 2003_526 or BC.
- Public contact: Gregory Paradis, gregory.paradis@ubc.ca, UBC FRESH Lab.

Benchmark rows:
{rows}

Answer from this context. If asked for a number or status that is not here,
say it is not available rather than inventing it."""


def _extract_text(stdout: str) -> str:
    answer = ""
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        for key in ("text", "content", "message", "reply"):
            value = event.get(key)
            if isinstance(value, str) and value.strip():
                answer = value.strip()
        part = event.get("part")
        if isinstance(part, dict) and isinstance(part.get("text"), str):
            answer = part["text"].strip() or answer
    return answer or stdout.strip()[-12000:]


def ask(question: str, cases: list[dict[str, Any]], workspace: Path) -> dict[str, str]:
    """Answer a visitor question through the local read-only OpenCode agent."""
    cleaned = question.strip()
    if len(cleaned) < 3:
        raise ValueError("Please enter a longer question.")
    if len(cleaned) > MAX_QUESTION:
        raise ValueError("Question is too long.")
    executable = shutil.which("opencode")
    if executable is None:
        raise RuntimeError("The assistant is not available on this host.")
    prompt = (
        _portal_context(cases)
        + "\n\nVisitor question: "
        + cleaned
    )
    command = [
        executable,
        "run",
        "--standalone",
        "--agent",
        "fire-guide",
        "--model",
        MODEL,
        "--format",
        "json",
        prompt,
    ]
    completed = subprocess.run(
        command,
        cwd=str(workspace),
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
        check=False,
        env={**os.environ, "OPENCODE": "1"},
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()[-600:]
        raise RuntimeError(detail or "Assistant process failed.")
    answer = _extract_text(completed.stdout)
    answer = re.sub(r"\n{3,}", "\n\n", answer).strip()
    if not answer:
        raise RuntimeError("The assistant returned no answer.")
    return {"answer": answer, "model": MODEL}
