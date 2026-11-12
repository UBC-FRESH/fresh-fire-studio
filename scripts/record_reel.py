"""Record the FRESH Fire Studio screen-capture reel.

Requires the local portal on port 8800:
    PORT=8800 ./run_portal.sh

Usage:
    python scripts/record_reel.py
"""

from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "reel" / "fresh-fire-studio-reel.webm"
RAW_DIR = ROOT / ".opencode" / "tmp" / "reel-raw"
PORTAL = "http://127.0.0.1:8800"


def _wait(seconds: float) -> None:
    time.sleep(seconds)


def _viewer(page: Page):
    for frame in page.frames:
        if "/viewer.html" in frame.url:
            return frame
    return None


def _set_time(frame, fraction: float = 0.55) -> None:
    frame.evaluate(
        """(fraction) => {
          const d = window.__ff.DATA;
          const s = document.getElementById('slider');
          s.value = d.hero_time * fraction;
          s.dispatchEvent(new Event('input', {bubbles: true}));
        }""",
        fraction,
    )


def _orbit(frame, distance: float, seconds: float = 1.6) -> None:
    frame.evaluate(
        """({distance, seconds}) => new Promise((resolve) => {
          const f = window.__ff;
          const target = f.controls.target.clone();
          const from = f.camera.position.clone();
          const dir = from.clone().sub(target).normalize();
          const to = target.clone().add(dir.multiplyScalar(distance));
          const start = performance.now();
          function step(now) {
            const u = Math.min(1, (now - start) / (seconds * 1000));
            const e = u < .5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2;
            f.camera.position.lerpVectors(from, to, e);
            f.controls.update();
            if (u < 1) requestAnimationFrame(step); else resolve();
          }
          requestAnimationFrame(step);
        })""",
        {"distance": distance, "seconds": seconds},
    )


def main() -> None:
    if RAW_DIR.exists():
        shutil.rmtree(RAW_DIR)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"],
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=str(RAW_DIR),
            record_video_size={"width": 1280, "height": 720},
        )
        page = context.new_page()

        # 00:00 — landing
        page.goto(PORTAL, wait_until="load", timeout=120_000)
        _wait(5)
        page.evaluate("window.scrollTo({top: 560, behavior: 'smooth'})")
        _wait(3.5)
        page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        _wait(2)

        # 00:10 — 3D case
        page.goto(f"{PORTAL}/case/cfsds-2003-526", wait_until="load", timeout=120_000)
        _wait(6)
        frame = _viewer(page)
        if frame:
            _set_time(frame, 0.95)
            _wait(1.5)
            try:
                frame.evaluate("document.getElementById('focus').click()")
            except Exception:
                pass
            _wait(2)
            _orbit(frame, 650, 2.0)
            _wait(1)
            _set_time(frame, 0.95)
            _wait(1)
            _orbit(frame, 260, 2.2)
            _wait(3)
            # model-extent comparison
            try:
                frame.evaluate("document.getElementById('model').click()")
                _wait(2.2)
                frame.evaluate("document.getElementById('model').click()")
            except Exception:
                pass
            _wait(2)
            # pull back out
            _orbit(frame, 900, 1.8)
            _wait(1.5)

        # 00:32 — methods
        page.goto(f"{PORTAL}/methods", wait_until="load", timeout=120_000)
        _wait(2)
        page.evaluate("window.scrollTo({top: 900, behavior: 'smooth'})")
        _wait(2.5)
        page.evaluate("window.scrollTo({top: 1800, behavior: 'smooth'})")
        _wait(3)
        page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        _wait(1)

        # 00:40 — pilot
        page.goto(f"{PORTAL}/pilot", wait_until="load", timeout=120_000)
        _wait(3)
        page.evaluate("window.scrollTo({top: 700, behavior: 'smooth'})")
        _wait(2.5)

        # 00:47 — close
        page.goto(PORTAL, wait_until="load", timeout=120_000)
        _wait(4)

        context.close()
        browser.close()

    videos = sorted(RAW_DIR.glob("*.webm"), key=lambda path: path.stat().st_mtime)
    if not videos:
        raise SystemExit("No reel video was produced")
    source = videos[-1]

    ffmpeg_candidates = sorted(
        (Path.home() / ".cache" / "ms-playwright").glob("ffmpeg-*/ffmpeg-linux")
    )
    if not ffmpeg_candidates:
        shutil.copy2(source, OUT.with_suffix(".webm"))
        print(f"wrote {OUT.with_suffix('.webm')}")
        return
    ffmpeg = ffmpeg_candidates[-1]
    try:
        subprocess.run(
            [
                str(ffmpeg),
                "-y",
                "-i",
                str(source),
                "-c:v",
                "libvpx-vp9",
                "-b:v",
                "2M",
                "-crf",
                "32",
                "-deadline",
                "good",
                "-cpu-used",
                "2",
                "-an",
                str(OUT),
            ],
            check=True,
        )
    except subprocess.CalledProcessError:
        shutil.copy2(source, OUT)
    print(f"wrote {OUT} ({OUT.stat().st_size / 1_000_000:.1f} MB)")


if __name__ == "__main__":
    main()
