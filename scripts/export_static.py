"""Export the FastAPI portal as a static GitHub-Pages-style site."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from portal.app import CASES, VRI_CASE, _case_page, _landing, brief, case, home, methods, pilot

OUT = ROOT / "public"


def _rewrite_index(payload: str) -> str:
    payload = payload.replace('href="/case/', 'href="case/')
    payload = payload.replace('href="/methods"', 'href="methods.html"')
    payload = payload.replace('href="/pilot"', 'href="pilot.html"')
    payload = payload.replace('href="/bc"', 'href="bc.html"')
    payload = payload.replace('href="/cfs"', 'href="cfs.html"')
    payload = payload.replace('href="/reel"', 'href="reel/index.html"')
    payload = payload.replace('href="/briefs/bc"', 'href="briefs/bc.html"')
    payload = payload.replace('href="/briefs/cfs"', 'href="briefs/cfs.html"')
    payload = payload.replace('src="/static/', 'src="static/')
    # Cases are exported as .html files.
    for case_row in CASES:
        slug = str(case_row["slug"])
        payload = payload.replace(f'href="case/{slug}"', f'href="case/{slug}.html"')
    return payload


def main() -> None:
    """Write the static portal and copy scene assets."""
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "case").mkdir(parents=True)
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    (OUT / "index.html").write_text(_rewrite_index(home()), encoding="utf-8")
    for audience in ("bc", "cfs"):
        (OUT / f"{audience}.html").write_text(
            _rewrite_index(_landing(audience)), encoding="utf-8"
        )
    for case_row in CASES:
        slug = str(case_row["slug"])
        payload = case(slug)
        payload = payload.replace('href="/"', 'href="../index.html"')
        payload = payload.replace('href="/methods"', 'href="../methods.html"')
        payload = payload.replace(
            f'src="/static/scenes/{slug}/', f'src="../static/scenes/{slug}/'
        )
        (OUT / "case" / f"{slug}.html").write_text(payload, encoding="utf-8")
    methods_payload = methods()
    methods_payload = methods_payload.replace('href="/"', 'href="index.html"')
    (OUT / "methods.html").write_text(methods_payload, encoding="utf-8")
    pilot_payload = pilot()
    pilot_payload = pilot_payload.replace('href="/"', 'href="index.html"')
    pilot_payload = pilot_payload.replace('href="/methods"', 'href="methods.html"')
    pilot_payload = pilot_payload.replace('href="/pilot"', 'href="pilot.html"')
    pilot_payload = pilot_payload.replace('href="/pilot/vri"', 'href="pilot-vri.html"')
    pilot_payload = pilot_payload.replace('href="/static/', 'href="static/')
    (OUT / "pilot.html").write_text(pilot_payload, encoding="utf-8")
    vri_payload = _case_page(VRI_CASE)
    vri_payload = vri_payload.replace('href="/"', 'href="index.html"')
    vri_payload = vri_payload.replace('src="/static/scenes/vri-pilot/', 'src="static/scenes/vri-pilot/')
    (OUT / "pilot-vri.html").write_text(vri_payload, encoding="utf-8")
    (OUT / "briefs").mkdir(exist_ok=True)
    for name in ("bc", "cfs"):
        (OUT / "briefs" / f"{name}.html").write_text(brief(name), encoding="utf-8")
    shutil.copytree(ROOT / "portal" / "static", OUT / "static")
    shutil.copytree(ROOT / "docs" / "reel", OUT / "reel")
    print(f"exported {len(CASES)} cases to {OUT}")


if __name__ == "__main__":
    main()
