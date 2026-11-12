# G50872 / TSA 24 VRI pilot

This is the larger VRI pilot: a real BC historical fire perimeter over public
TSA 24 VRI blocks.

## Inputs

| Input | Source | Status |
|---|---|---|
| Fire perimeter | BC G50872 (2023), final observed polygon | real |
| VRI blocks | Public TSA 24 stand geometry, EPSG:3005 | real |
| Terrain | SRTM 1 arcsec tile N55W125 | public |
| Fuel | FireSTARR 2023 100 m sample, dominant C3 | public |
| Weather | Open-Meteo reanalysis, 2023-06-24 | public |
| Tree stems | Synthetic sample, 32,000 stems | synthetic |
| Ignition timing | Synthetic radial progression | synthetic |
| Daily progression | Not available | not claimed |

The observed final extent is about **17,338 ha**. There are **871 VRI blocks**
inside it and **32,001 sample stems**.

## Build

```bash
python scripts/build_g50872_pilot.py
```

Output: `portal/static/scenes/g50872-vri/viewer.html`

## Limitations

- The observed perimeter is a final polygon, not a daily progression.
- The ignition point and timing are synthetic.
- Tree stems are a visual sample, not an inventory.
- The scene is a pilot prototype, not an operational prediction.
