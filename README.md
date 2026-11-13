# FRESH Fire Studio

A public 3D benchmark-fire portal from the UBC FRESH Lab.

## Live surfaces

- Permanent portal: <https://ubc-fresh.github.io/fresh-fire-studio/>
- Reel: <https://ubc-fresh.github.io/fresh-fire-studio/reel/>
- BC framing: <https://ubc-fresh.github.io/fresh-fire-studio/bc.html>
- CFS framing: <https://ubc-fresh.github.io/fresh-fire-studio/cfs.html>
- VRI pilot prototype: <https://ubc-fresh.github.io/fresh-fire-studio/pilot-vri.html>
- VRI build: `python scripts/build_vri_pilot.py` (public TSA 24 geometry + SRTM terrain)
- VRI notes: [`docs/vri-pilot.md`](docs/vri-pilot.md)
- G50872 VRI pilot: <https://ubc-fresh.github.io/fresh-fire-studio/pilot-g50872.html>
- G50872 notes: [`docs/g50872-pilot.md`](docs/g50872-pilot.md)
- Anonymous counters: [`docs/analytics.md`](docs/analytics.md)
- Assistant: [`docs/assistant.md`](docs/assistant.md) (`+ Ask` on the main pages)
- Suppression plan and P179.0 contract: [`docs/suppression-module-plan.md`](docs/suppression-module-plan.md)
- P179.1 static line-effect proof: [`docs/p179-1-proof.md`](docs/p179-1-proof.md)
- P179.2 time-aware effect proof: [`docs/p179-2-proof.md`](docs/p179-2-proof.md)
- P179.2b breach and late-arrival proofs: [`docs/p179-2b-failure-proofs.md`](docs/p179-2b-failure-proofs.md)
- P179.3 native containment proof: [`docs/p179-3-native-proof.md`](docs/p179-3-native-proof.md)
- P179.4 dispatch prototype: [`docs/p179-4-dispatch.md`](docs/p179-4-dispatch.md)
- Extracted suppression PDF notes: [`docs/martell-pdf-notes.md`](docs/martell-pdf-notes.md)
- P179.5 water requirements: [`docs/p179-5-water.md`](docs/p179-5-water.md)
- Canadian wildfire studies notes: [`docs/ws4-canadian-wildfire-notes.md`](docs/ws4-canadian-wildfire-notes.md)
- Current edge: <https://fresh-fire.01101.dev/>
- Local portal: <http://127.0.0.1:8800/>
- Lab preview: <https://fresh01.01101.dev/jupyterhub18/user/gep/proxy/8791/fire-studio/index.html>
- Static export: `public/` (GitHub-Pages-style, no server required)

The preview host is behind the lab Cloudflare Access gate.

## What it does

- six public benchmark fires, from Dogrib 2001 to the 2023 Hay River event;
- one standalone 3D fire studio per case;
- Nemora-derived synthetic individual-tree layer with **foveated LOD**:
  - canopy impostors over the full observed extent;
  - a generated near-field stand at **500 stems/ha** around the camera target;
  - an overlapping mid-field ring of **tree-silhouette impostors** so the
    detail patch does not end in a keyhole;
  - fixed 160 m world-space detail tiles, cached across navigation;
  - individual trunks, crowns, flames and smoke only in the near-field tiles;
  - local crown-to-crown ignition advance inside the detail tiles;
- FBP/WS4 fire behaviour replay with surface, crown and post-fire tree states;
- DEM-derived terrain hillshade;
- public-data provenance and a methods page.

## Run

```bash
cd fresh-fire
PORT=8800 ./run_portal.sh
# http://127.0.0.1:8800/
```

Rebuild scenes:

```bash
python scripts/build_scenes.py
python scripts/export_static.py
```

Port 8800 is deliberate: community forests 8796, woodlots 8795, Nemora 8799.

## Caveats

The tree layer is synthetic. The 500 stems/ha near-field stand is a visual
density target, not a measured inventory; the browser generates it from the
stand footprint and samples ignition from a compact burn-time field. The 3D
scene is a model replay, not an operational prediction. Small suppressed fires
are not ROS-skill evidence. See `/methods` and the WS4 P164–P178 reports.
