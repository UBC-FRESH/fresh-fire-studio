"""FRESH Fire Studio public portal.

A small FastAPI portal that serves a landing page, case briefs, and standalone
WS4 vector-fire scenes. It has no write path and requires no private data.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "portal" / "static"
CASES_PATH = ROOT / "config" / "cases.json"
SUMMARIES_PATH = ROOT / "config" / "scene_summaries.json"
PILOT_PATH = ROOT / "portal" / "pilot.html"
BRIEFS = ROOT / "portal" / "briefs"
REEL_PATH = ROOT / "docs" / "reel" / "index.html"

app = FastAPI(title="FRESH Fire Studio", docs_url=None, redoc_url=None)


def _load_cases() -> list[dict[str, Any]]:
    payload = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    cases = payload.get("cases", [])
    summaries: dict[str, dict[str, Any]] = {}
    if SUMMARIES_PATH.is_file():
        for row in json.loads(SUMMARIES_PATH.read_text(encoding="utf-8")).get(
            "scenes", []
        ):
            summaries[str(row["slug"])] = row
    for case in cases:
        case.update(summaries.get(str(case["slug"]), {}))
    return cases


CASES = _load_cases()
CASE_BY_SLUG = {str(case["slug"]): case for case in CASES}

VRI_CASE: dict[str, Any] = {
    "slug": "vri-pilot",
    "title": "VRI pilot · TSA 24",
    "subtitle": "Public VRI block geometry, SRTM terrain, public C2 fuel sample, and Open-Meteo reanalysis weather",
    "story": "A pilot prototype, not an observed fire. It exercises the real VRI geometry, public terrain, sampled C2 fuel and reanalysis weather; tree placement and ignition timing are synthetic.",
    "provenance": "Public TSA 24 block geometry; SRTM terrain; FireSTARR C2 fuel sample; Open-Meteo reanalysis; synthetic Nemora stems",
    "area_ha": 104.9,
    "area_label": "burnable cluster",
    "weather": "C2 · Open-Meteo 2023-07-08",
    "duration": "240 min",
    "region": "BC",
    "year": 2026,
    "tone": "community",
    "iou": None,
}


def _fmt(value: object, suffix: str = "") -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:,.0f}{suffix}"
    return f"{value}{suffix}"


def _case_card(case: dict[str, Any]) -> str:
    slug = html.escape(str(case["slug"]))
    title = html.escape(str(case["title"]))
    subtitle = html.escape(str(case["subtitle"]))
    region = html.escape(str(case["region"]))
    tone = html.escape(str(case.get("tone", "benchmark")))
    area = _fmt(case.get("area_ha"), " ha")
    area_label = html.escape(str(case.get("area_label", "observed")))
    return f"""
    <a class="case-card tone-{tone}" href="/case/{slug}">
      <div class="case-art">
        <img src="/static/thumbs/{slug}.jpg" alt="" loading="lazy">
        <span class="case-index">{region} · {case["year"]}</span>
        <span class="case-play">Open 3D studio ↗</span>
      </div>
      <div class="case-body">
        <h3>{title}</h3>
        <p>{subtitle}</p>
        <div class="case-meta"><span>{area}</span><span>3D replay</span><span>{html.escape(str(case["duration"]))}</span></div>
      </div>
    </a>"""


AUDIENCE_COPY: dict[str, dict[str, object]] = {
    "default": {
        "meta_title": "FRESH Fire Studio · UBC FRESH",
        "meta_desc": "Walk through public benchmark wildfires in 3D. Real terrain, public weather, and transparent model limits from the UBC FRESH Lab.",
        "eyebrow": "UBC FRESH Lab · public fire modelling",
        "headline": "See a wildfire <em>before</em> it happens.",
        "lede": "An interactive 3D fire studio built on public benchmark fires, real terrain, real weather, and audited Canadian fire behaviour — with synthetic trees you can walk through.",
        "primary_label": "Launch the studio ↗",
        "primary_href": "",
        "secondary_label": "How the science works",
        "secondary_href": "/methods",
        "section_eyebrow": "The evidence set",
        "section_title": "Walk through a fire.",
        "section_copy": "Each scene is a deterministic replay of a public event. Pick a fire, orbit the landscape, and scrub the front.",
        "cta_eyebrow": "For BC and CFS teams",
        "cta_title": "Bring your landscape.",
        "cta_copy": "We can stand up a private instance over your VRI, terrain, fuel and weather, or run a joint benchmark on a fire you already know. The public studio is the front door.",
        "cta_href": "/pilot",
        "status": "Research demo",
        "case_order": ["dogrib-2001", "hay-river-2023", "cfsds-2003-526", "cfsds-2023-786", "cfsds-2003-96-large", "cfsds-2003-663-large"],
    },
    "bc": {
        "meta_title": "FRESH Fire Studio · BC community forests",
        "meta_desc": "A 3D fire-behaviour studio for BC community forests: public benchmark fires, terrain, fuel and a transparent model-limits memo.",
        "eyebrow": "UBC FRESH Lab · BC community forests",
        "headline": "See the fuel. <em>See the risk.</em> Before the fire.",
        "lede": "A 3D fire-behaviour studio for community forest planning. Start with a public benchmark, inspect the terrain and fuel, and see where the model stops being useful.",
        "primary_label": "Open the compact case ↗",
        "primary_href": "/case/cfsds-2003-526",
        "secondary_label": "Printable BC brief",
        "secondary_href": "/briefs/bc",
        "section_eyebrow": "For BC teams",
        "section_title": "Start with a landscape you know.",
        "section_copy": "Compare the observed extent, the free-burn model and the suppression problem on public events before applying the same workflow to your VRI and fuel data.",
        "cta_eyebrow": "BC pilot",
        "cta_title": "Bring your community forest.",
        "cta_copy": "Use one VRI, terrain and fuel landscape. We will build the 3D case, observed-versus-model comparison and a model-limits memo with your team.",
        "cta_href": "/pilot",
        "status": "BC pilot framing",
        "case_order": ["cfsds-2003-526", "cfsds-2003-663-large", "hay-river-2023", "cfsds-2023-786", "dogrib-2001", "cfsds-2003-96-large"],
    },
    "cfs": {
        "meta_title": "FRESH Fire Studio · CFS benchmark validation",
        "meta_desc": "A public 3D benchmark harness for Canadian fire behaviour: observed perimeters, WS4/FBP replay and a transparent validation ladder.",
        "eyebrow": "UBC FRESH Lab · CFS benchmark validation",
        "headline": "Test the model. <em>See the limits.</em> Together.",
        "lede": "A public benchmark harness for Canadian fire behaviour. Inspect observed perimeters, free-burn model divergence, and the failure modes that should shape the next validation target.",
        "primary_label": "Open Dogrib 2001 ↗",
        "primary_href": "/case/dogrib-2001",
        "secondary_label": "Printable CFS brief",
        "secondary_href": "/briefs/cfs",
        "section_eyebrow": "For CFS teams",
        "section_title": "Compare the model to the record.",
        "section_copy": "The evidence set starts with Dogrib, then moves through large free-burn cases. The methods page records what is real, what is synthetic and what is not claimed.",
        "cta_eyebrow": "CFS pilot",
        "cta_title": "Bring one benchmark.",
        "cta_copy": "We will run the public harness on one of your known fires or landscapes, compare the observed and free-burn extents, and write down where the model fails.",
        "cta_href": "/pilot",
        "status": "CFS benchmark framing",
        "case_order": ["dogrib-2001", "cfsds-2003-96-large", "cfsds-2003-663-large", "cfsds-2023-786", "hay-river-2023", "cfsds-2003-526"],
    },
}


def _landing(audience: str | None = None) -> str:
    copy = AUDIENCE_COPY[audience or "default"]
    ordered = [CASE_BY_SLUG[slug] for slug in copy["case_order"] if slug in CASE_BY_SLUG]
    cards = "\n".join(_case_card(case) for case in ordered)
    first = html.escape(str(ordered[0]["slug"])) if ordered else ""
    primary_href = str(copy["primary_href"] or f"/case/{first}")
    meta_url = f"https://ubc-fresh.github.io/fresh-fire-studio/{audience}.html" if audience else "https://ubc-fresh.github.io/fresh-fire-studio/"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{copy["meta_title"]}</title>
<meta name="description" content="{copy["meta_desc"]}">
<meta property="og:type" content="website">
<meta property="og:title" content="{copy["meta_title"]}">
<meta property="og:description" content="{copy["lede"]}">
<meta property="og:url" content="{meta_url}">
<meta property="og:image" content="https://ubc-fresh.github.io/fresh-fire-studio/static/social-card.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{copy["meta_title"]}">
<meta name="twitter:description" content="{copy["lede"]}">
<meta name="twitter:image" content="https://ubc-fresh.github.io/fresh-fire-studio/static/social-card.jpg">
<script src="/static/analytics.js" defer></script>
<meta name="description" content="{copy["meta_desc"]}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root{{
  --ink:#f4efe7;--muted:#a99e90;--dim:#6f665e;--bg:#090b0c;--panel:#111416;
  --line:rgba(244,239,231,.12);--hot:#ff6b2c;--hot2:#ffb347;--cool:#9ad1c8;
}}
*{{box-sizing:border-box}} html{{scroll-behavior:smooth}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 Manrope,system-ui,sans-serif}}
body:before{{content:"";position:fixed;inset:0;pointer-events:none;z-index:0;
  background:radial-gradient(900px 500px at 20% -10%,rgba(255,107,44,.16),transparent 60%),
             radial-gradient(900px 600px at 90% 10%,rgba(154,209,200,.08),transparent 55%),
             linear-gradient(180deg,#090b0c 0%,#0b0e10 60%,#080a0b 100%)}}
a{{color:inherit;text-decoration:none}} .wrap{{position:relative;z-index:1;max-width:1240px;margin:0 auto;padding:0 28px}}
nav{{display:flex;align-items:center;justify-content:space-between;padding:20px 0;border-bottom:1px solid var(--line)}}
.brand{{display:flex;align-items:center;gap:10px;font-weight:800;letter-spacing:-.02em}}
.brand-mark{{width:26px;height:26px;border-radius:50%;background:conic-gradient(from 210deg,var(--hot),#ffd27a,var(--hot));box-shadow:0 0 28px rgba(255,107,44,.4)}}
.navlinks{{display:flex;gap:22px;color:var(--muted);font-size:13px}}
.navlinks a:hover{{color:var(--ink)}}
.hero{{display:grid;grid-template-columns:1.15fr .85fr;gap:40px;align-items:end;padding:86px 0 54px}}
.eyebrow{{font:12px/1.4 "DM Mono",monospace;letter-spacing:.16em;text-transform:uppercase;color:var(--hot2)}}
h1{{font-size:clamp(44px,7vw,96px);line-height:.94;letter-spacing:-.055em;margin:18px 0 24px;max-width:930px}}
h1 em{{font-style:normal;color:var(--hot)}}
.lede{{font-size:clamp(17px,2vw,22px);line-height:1.45;color:#d7cdc0;max-width:620px}}
.hero-actions{{display:flex;gap:12px;flex-wrap:wrap;margin-top:30px}}
.btn{{display:inline-flex;align-items:center;gap:9px;padding:12px 17px;border:1px solid var(--line);border-radius:999px;font-size:13px;font-weight:700}}
.btn.primary{{background:var(--hot);border-color:var(--hot);color:#1b0c05;box-shadow:0 12px 34px rgba(255,107,44,.25)}}
.btn:hover{{border-color:rgba(255,179,71,.7)}}
.hero-panel{{border:1px solid var(--line);background:rgba(17,20,22,.72);border-radius:20px;padding:20px;backdrop-filter:blur(12px)}}
.hero-panel .big{{font:500 38px/1 "DM Mono",monospace;letter-spacing:-.06em;color:var(--hot2)}}
.hero-panel .row{{display:flex;justify-content:space-between;gap:18px;padding:11px 0;border-bottom:1px solid var(--line);color:var(--muted);font-size:12px}}
.hero-panel .row:last-child{{border:0}} .hero-panel .row b{{color:var(--ink);font-weight:600;text-align:right}}
.strip{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);border:1px solid var(--line);border-radius:16px;overflow:hidden;margin:8px 0 64px}}
.strip div{{background:rgba(10,13,14,.82);padding:18px 20px}} .strip b{{display:block;font-size:22px;letter-spacing:-.04em}} .strip span{{font-size:12px;color:var(--muted)}}
.section-head{{display:flex;justify-content:space-between;align-items:end;gap:20px;margin:0 0 24px}}
.section-head h2{{font-size:clamp(28px,4vw,48px);line-height:1;letter-spacing:-.045em;margin:0}}
.section-head p{{max-width:450px;color:var(--muted);font-size:13px;margin:0}}
.case-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:20px}}
.case-card{{display:block;border:1px solid var(--line);border-radius:18px;overflow:hidden;background:rgba(17,20,22,.64);transition:transform .25s,border-color .25s}}
.case-card:hover{{transform:translateY(-4px);border-color:rgba(255,179,71,.5)}}
.case-art{{position:relative;aspect-ratio:16/9;overflow:hidden;background:#0b1113}}
.case-art img{{width:100%;height:100%;object-fit:cover;display:block;filter:saturate(1.1) contrast(1.05);transition:transform .5s}}
.case-card:hover .case-art img{{transform:scale(1.04)}}
.case-art:after{{content:"";position:absolute;inset:0;background:linear-gradient(180deg,transparent 35%,rgba(9,11,12,.86))}}
.case-index{{position:absolute;top:12px;left:12px;z-index:2;font:11px "DM Mono",monospace;letter-spacing:.1em;text-transform:uppercase;color:#e9dfd3;background:rgba(9,11,12,.6);border:1px solid rgba(255,255,255,.16);padding:5px 8px;border-radius:999px}}
.case-play{{position:absolute;right:12px;bottom:12px;z-index:2;font-size:12px;font-weight:700;color:#1b0c05;background:var(--hot2);padding:7px 10px;border-radius:999px}}
.case-body{{padding:16px 18px 18px}} .case-body h3{{margin:0 0 3px;font-size:24px;letter-spacing:-.04em}} .case-body p{{margin:0;color:var(--muted);font-size:13px}}
.case-meta{{display:flex;gap:14px;flex-wrap:wrap;margin-top:14px;color:var(--dim);font:11px "DM Mono",monospace}}
.tone-community .case-play{{background:var(--cool);color:#04201d}}
.tone-large .case-play{{background:#ffd27a;color:#2b1605}}
.split{{display:grid;grid-template-columns:.9fr 1.1fr;gap:32px;margin:72px 0}}
.split h2{{font-size:clamp(28px,4vw,46px);line-height:1;letter-spacing:-.045em;margin:0 0 18px}}
.split p{{color:var(--muted);max-width:520px}}
.points{{display:grid;gap:12px}} .point{{border-top:1px solid var(--line);padding-top:12px;display:grid;grid-template-columns:30px 1fr;gap:12px}}
.point b{{color:var(--hot2);font:12px "DM Mono",monospace}} .point span{{color:var(--muted);font-size:13px}}
.cta{{border:1px solid rgba(255,107,44,.4);background:linear-gradient(120deg,rgba(255,107,44,.13),rgba(154,209,200,.05));border-radius:22px;padding:34px;display:flex;justify-content:space-between;gap:24px;align-items:center;margin:38px 0 70px}}
.cta h2{{font-size:clamp(26px,4vw,42px);line-height:1;letter-spacing:-.045em;margin:0 0 8px}} .cta p{{margin:0;color:var(--muted);max-width:650px}}
footer{{border-top:1px solid var(--line);padding:26px 0 40px;color:var(--dim);font-size:12px;display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap}}
@media(max-width:850px){{.hero,.split{{grid-template-columns:1fr}}.hero{{padding-top:52px}}.case-grid{{grid-template-columns:1fr}}.strip{{grid-template-columns:repeat(2,1fr)}}.navlinks{{display:none}}.cta{{display:block}}}}
</style>
</head>
<body>
<div class="wrap">
<nav><div class="brand"><span class="brand-mark"></span> FRESH Fire Studio</div><div class="navlinks"><a href="#cases">Benchmark fires</a><a href="/methods">Science</a><a href="/pilot">Pilot</a><a href="/bc">BC</a><a href="/cfs">CFS</a><a href="/case/{first}">Launch demo ↗</a></div></nav>
<section class="hero">
  <div><div class="eyebrow">{copy["eyebrow"]}</div>
  <h1>{copy["headline"]}</h1>
  <p class="lede">{copy["lede"]}</p>
  <div class="hero-actions"><a class="btn primary" href="{primary_href}">{copy["primary_label"]}</a><a class="btn" href="{copy["secondary_href"]}">{copy["secondary_label"]}</a></div></div>
  <aside class="hero-panel"><div class="big">3D</div><div class="row"><span>Benchmark fires</span><b>{len(CASES)}</b></div><div class="row"><span>Near-field density</span><b>500 stems/ha</b></div><div class="row"><span>Model</span><b>WS4 · FBP · FWI</b></div><div class="row"><span>Data</span><b>Public only</b></div><div class="row"><span>Status</span><b>{copy["status"]}</b></div></aside>
</section>
<div class="strip"><div><b>{len(CASES)}</b><span>public benchmark fires</span></div><div><b>500/ha</b><span>foveated near-field stems</span></div><div><b>LOD</b><span>canopy overview + tree detail</span></div><div><b>0</b><span>proprietary inputs</span></div></div>
<div id="cases" class="section-head"><div><div class="eyebrow">{copy["section_eyebrow"]}</div><h2>{copy["section_title"]}</h2></div><p>{copy["section_copy"]}</p></div>
<div class="case-grid">{cards}</div>
<section class="split"><div><div class="eyebrow">What you are seeing</div><h2>Fire behaviour, not a video.</h2><p>The front is a model result. Trees are a plausible synthetic population placed inside public stand geometry; ground fuel and terrain drive the local spread.</p></div><div class="points"><div class="point"><b>01</b><span><b>Surface + crown fire.</b> Rothermel/FBP surface spread, crown initiation, and consumption are evaluated cell by cell.</span></div><div class="point"><b>02</b><span><b>Foveated tree detail.</b> The overview uses a canopy impostor; zoom in and the near field resolves to a synthetic 500 stems/ha stand, ringed by a wider tree-silhouette mid-field so there is no keyhole. Ignition is sampled from a compact burn-time field, then advanced locally from crown to crown.</span></div><div class="point"><b>03</b><span><b>Individual trees.</b> Nemora places and sizes stems; each tree samples the local arrival time and resolves to scorched, torched, or consumed.</span></div><div class="point"><b>04</b><span><b>Atmosphere.</b> Wind, slope, fuel moisture, smoke, embers, and a moving fire light are rendered in the browser.</span></div><div class="point"><b>05</b><span><b>Honest evidence.</b> Public perimeters, hourly weather, and a recorded validation ladder. No operational claim; no hidden tuning.</span></div></div></section>
<section class="cta"><div><div class="eyebrow">{copy["cta_eyebrow"]}</div><h2>{copy["cta_title"]}</h2><p>{copy["cta_copy"]}</p></div><a class="btn primary" href="{copy["cta_href"]}">Start a pilot ↗</a></section>
<footer><span><a href="https://fresh.forestry.ubc.ca">UBC FRESH Lab</a> · Forest Resources and Ecosystem Services Hub · UBC Faculty of Forestry & Environmental Stewardship</span><span><a href="/reel">70s reel</a> · <a href="/bc">BC</a> · <a href="/cfs">CFS</a> · synthetic tree layer · research use</span></footer>
</div></body></html>"""


def _case_page(case: dict[str, Any]) -> str:
    slug = html.escape(str(case["slug"]))
    title = html.escape(str(case["title"]))
    subtitle = html.escape(str(case["subtitle"]))
    story = html.escape(str(case["story"]))
    provenance = html.escape(str(case["provenance"]))
    area = _fmt(case.get("area_ha"), " ha")
    area_label = html.escape(str(case.get("area_label", "observed")))
    iou = case.get("iou")
    iou_text = "—" if iou is None else f"{float(iou):.3f}"
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{title} · FRESH Fire Studio</title><script src="../static/analytics.js" defer></script><style>
html,body{{margin:0;height:100%;background:#06090a;color:#f4efe7;font:13px/1.4 Manrope,system-ui,sans-serif;overflow:hidden}}
iframe{{position:fixed;inset:0;width:100%;height:100%;border:0;background:#06090a}}
.case-loading{{position:fixed;inset:0;z-index:2;display:grid;place-items:center;background:#07100f url('../static/thumbs/{slug}.jpg') center/cover;color:#f4efe7;font:12px "DM Mono",monospace;letter-spacing:.1em;transition:opacity .45s ease}}.case-loading:before{{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(5,12,11,.30),rgba(5,12,11,.72))}}.case-loading span{{position:relative;padding:10px 14px;border:1px solid rgba(255,255,255,.18);border-radius:999px;background:rgba(9,12,13,.72);backdrop-filter:blur(12px)}}.case-loading.hidden{{opacity:0;pointer-events:none}}.top{{position:fixed;z-index:4;top:14px;left:14px;right:14px;display:flex;justify-content:space-between;align-items:flex-start;gap:14px;pointer-events:none}}
.back{{pointer-events:auto;background:rgba(9,11,12,.76);border:1px solid rgba(255,255,255,.16);border-radius:999px;padding:9px 13px;color:#f4efe7;text-decoration:none;font-weight:700;backdrop-filter:blur(12px)}}
.brief{{pointer-events:auto;max-width:420px;background:rgba(9,11,12,.76);border:1px solid rgba(255,255,255,.14);border-radius:16px;padding:14px 16px;backdrop-filter:blur(14px)}}
.brief h1{{margin:0;font-size:22px;letter-spacing:-.04em}} .brief p{{margin:5px 0 10px;color:#b9afa1;font-size:12px}} .facts{{display:flex;gap:12px;flex-wrap:wrap;color:#80776d;font:10px "DM Mono",monospace}} .facts b{{color:#f4efe7}}
@media(max-width:700px){{.brief{{display:none}}}}
</style></head><body><div class="case-loading" id="case-loading"><span>LOADING 3D SCENE…</span></div><iframe src="/static/scenes/{slug}/viewer.html?autoplay=1&embedded=1" title="{title} 3D fire scene" allowfullscreen onload="document.getElementById('case-loading').classList.add('hidden')"></iframe>
<div class="top"><a class="back" href="/">← FRESH Fire Studio</a><div class="brief"><h1>{title}</h1><p>{subtitle}. {story}</p><div class="facts"><span><b>{area}</b> {area_label}</span><span><b>IoU {iou_text}</b></span><span><b>{html.escape(str(case["weather"]))}</b></span></div><div class="facts" style="margin-top:8px"><span>{provenance}</span></div></div></div></body></html>"""


def _methods_page() -> str:
    science = ROOT / "portal" / "science.html"
    if science.is_file():
        return science.read_text(encoding="utf-8")
    return """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Methods · FRESH Fire Studio</title><style>
body{margin:0;background:#090b0c;color:#f4efe7;font:15px/1.65 Manrope,system-ui,sans-serif}
.wrap{max-width:920px;margin:0 auto;padding:44px 28px 80px}a{color:#ffb347;text-decoration:none}
h1{font-size:clamp(38px,6vw,68px);line-height:.98;letter-spacing:-.055em;margin:18px 0 22px}h2{font-size:24px;letter-spacing:-.03em;margin:36px 0 10px}
p,li{color:#b9afa1}code{color:#ffcf8b;font:12px "DM Mono",monospace}.rule{border-top:1px solid rgba(255,255,255,.12);margin:26px 0}
.kicker{font:11px "DM Mono",monospace;letter-spacing:.15em;text-transform:uppercase;color:#ffb347}
</style></head><body><div class="wrap"><a href="/">← FRESH Fire Studio</a><div class="kicker" style="margin-top:28px">Methods and limits</div><h1>The model is the point.</h1>
<p>FRESH Fire is a public demonstration of the WS4 fire modelling stack from the UBC FRESH Lab. It is designed to make model behaviour inspectable, not to sell a black box.</p>
<h2>What is real</h2><ul><li>Public benchmark fire perimeters and event windows.</li><li>Hourly weather: ECCC stations or Open-Meteo reanalysis, recorded per case.</li><li>FBP fuel and FireSTARR/ NRCan terrain inputs.</li><li>WS4 surface fire, crown fire, FWI, growth, spotting, and perimeter comparison.</li></ul>
<h2>What is synthetic</h2><ul><li>The individual-tree layer. Nemora places plausible stems inside stand blocks; it is not a measured inventory.</li><li>The visual tree geometry and fire particles. Tree outcomes are visual classes derived from the model, not a validated mortality observation.</li></ul>
<h2>What this demo does not claim</h2><ul><li>Operational fire prediction.</li><li>Regional calibration.</li><li>That a free-burn model matches a suppressed fire. P176 shows the model fills the burnable basin; small fires are suppression-dominated.</li><li>That the 3D scene is a measurement product.</li></ul>
<div class="rule"></div><p>Evidence chain: P156–P178. Key reports live in the WS4 repository: <code>notes/reports/</code>. The scene schema is <code>ws4.fire.scene.v1</code>.</p><p><a href="/">Back to the studio ↗</a></p></div></body></html>"""


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return _landing()


@app.get("/bc", response_class=HTMLResponse)
def bc_landing() -> str:
    return _landing("bc")


@app.get("/cfs", response_class=HTMLResponse)
def cfs_landing() -> str:
    return _landing("cfs")


@app.get("/case/{slug}", response_class=HTMLResponse)
def case(slug: str) -> str:
    case_data = CASE_BY_SLUG.get(slug)
    if case_data is None:
        raise HTTPException(status_code=404, detail="case not found")
    return _case_page(case_data)


@app.get("/pilot/vri", response_class=HTMLResponse)
def pilot_vri() -> str:
    return _case_page(VRI_CASE)


@app.get("/pilot", response_class=HTMLResponse)
def pilot() -> str:
    if PILOT_PATH.is_file():
        return PILOT_PATH.read_text(encoding="utf-8")
    raise HTTPException(status_code=404, detail="pilot page unavailable")


@app.get("/briefs/{name}", response_class=HTMLResponse)
def brief(name: str) -> str:
    if name not in {"bc", "cfs"}:
        raise HTTPException(status_code=404, detail="brief not found")
    path = BRIEFS / f"{name}.html"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="brief not found")
    return path.read_text(encoding="utf-8")


@app.get("/methods", response_class=HTMLResponse)
def methods() -> str:
    return _methods_page()


@app.get("/api/cases")
def api_cases() -> JSONResponse:
    return JSONResponse({"cases": CASES})


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "cases": len(CASES),
            "scenes": sum(
                (STATIC / "scenes" / str(case["slug"]) / "viewer.html").is_file()
                for case in CASES
            ),
        }
    )


app.mount("/static", StaticFiles(directory=STATIC), name="static")
app.mount("/reel", StaticFiles(directory=ROOT / "docs" / "reel", html=True), name="reel")
