# FRESH Fire Studio

A public 3D benchmark-fire portal from the UBC FRESH Lab.

## Live surfaces

- Live portal: <https://fresh-fire.01101.dev/>
- Local portal: <http://127.0.0.1:8800/>
- Lab preview: <https://fresh01.01101.dev/jupyterhub18/user/gep/proxy/8791/fire-studio/index.html>
- Static export: `public/` (GitHub-Pages-style, no server required)

The preview host is behind the lab Cloudflare Access gate.

## What it does

- six public benchmark fires, from Dogrib 2001 to the 2023 Hay River event;
- one standalone 3D fire studio per case;
- Nemora-derived synthetic individual-tree layer;
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

The tree layer is synthetic. The 3D scene is a model replay, not an operational
prediction. Small suppressed fires are not ROS-skill evidence. See `/methods`
and the WS4 P164–P178 reports.
