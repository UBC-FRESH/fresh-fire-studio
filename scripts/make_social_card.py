"""Render the FRESH Fire Studio social preview card.

Usage:
    python scripts/make_social_card.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SCENE_URL = "http://127.0.0.1:8898/scenes/cfsds-2003-526/viewer.html"
OUT = ROOT / "portal" / "static" / "social-card.jpg"
RAW = ROOT / ".opencode" / "tmp" / "social-card-raw.png"


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def main() -> None:
    RAW.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"],
        )
        page = browser.new_page(viewport={"width": 1200, "height": 630})
        page.goto(SCENE_URL + "?autoplay=1", wait_until="load", timeout=180_000)
        page.wait_for_timeout(2800)
        page.add_style_tag(content=".hud{display:none!important}")
        page.evaluate(
            """() => {
              const d = window.__ff.DATA;
              const s = document.getElementById('slider');
              s.value = d.hero_time;
              s.dispatchEvent(new Event('input', {bubbles: true}));
              document.getElementById('focus').click();
            }"""
        )
        page.wait_for_timeout(1200)
        page.evaluate(
            """() => {
              const f = window.__ff;
              const t = f.controls.target;
              f.camera.position.set(t.x + 120, t.y + 220, t.z + 280);
              f.controls.update();
            }"""
        )
        page.wait_for_timeout(2200)
        page.screenshot(path=str(RAW))
        browser.close()

    base = Image.open(RAW).convert("RGB").resize((1200, 630))
    # Darken the left side so the title remains legible over the scene.
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for x in range(0, 820):
        alpha = int(218 * (1 - x / 820) ** 0.72)
        draw.rectangle((x, 0, x + 1, 630), fill=(3, 10, 9, alpha))
    base = Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(base)

    title = _font(74, bold=True)
    kicker = _font(20, bold=True)
    body = _font(27)
    small = _font(18)
    draw.text((64, 78), "UBC FRESH LAB  ·  PUBLIC FIRE MODELLING", font=kicker, fill="#ffb347")
    draw.multiline_text(
        (64, 132),
        "FRESH Fire\nStudio",
        font=title,
        fill="#f4efe7",
        spacing=-8,
    )
    draw.multiline_text(
        (66, 336),
        "Walk through a wildfire.\nSee the model. See the limits.",
        font=body,
        fill="#d7cdbf",
        spacing=6,
    )
    draw.text(
        (66, 500),
        "Public benchmark fires · terrain · weather · synthetic tree LOD",
        font=small,
        fill="#a99e90",
    )
    draw.text((66, 566), "fresh-fire.01101.dev", font=kicker, fill="#ffb347")
    draw.text(
        (1136, 574),
        "UBC Forestry & Environmental Stewardship",
        font=_font(15),
        fill="#d7cdbf",
        anchor="rs",
    )
    base.save(OUT, quality=92)


if __name__ == "__main__":
    main()
