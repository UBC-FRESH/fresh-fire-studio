# VRI pilot prototype

The first pilot landscape is a 12-block cluster from the public TSA 24 VRI
geometry. It is deliberately separate from the six benchmark-fire cases.

## Inputs

| Input | Source | Status |
|---|---|---|
| Block polygons | Public TSA 24 stand geometry, EPSG:3005 | real |
| Tree stems | Nemora synthetic placement | synthetic |
| Terrain | SRTM 1 arcsec tile N55W125 | public |
| Fuel | FBP C3 | scenario |
| Fire growth | WS4/FBP synthetic run | synthetic |
| Observed perimeter | none | not applicable |
| Weather | C3 scenario conditions | synthetic |

The fixture is translation-only relative to EPSG:3005:

```
local origin = (1088291.2231, 1124190.4741)
```

That lets the builder georeference the local VRI coordinates and sample the
public SRTM tile for the terrain mesh and tree bases.

## Build

```bash
python scripts/build_vri_pilot.py
```

The output is `portal/static/scenes/vri-pilot/viewer.html`.

## Limitations

- No observed fire perimeter.
- No measured fuel inventory or local weather station.
- Synthetic stems and synthetic fire timing.
- The scene is a UI and terrain-integration prototype, not an operational
  prediction.
