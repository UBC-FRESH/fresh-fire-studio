# P183 — Foveated tree LOD

## Problem

The original scene carried a 32,000-stem sample over the full observed extent.
That is about 62 stems/ha on a 520 ha fire and about 3 stems/ha on Dogrib. A
real stand is roughly 400–800 stems/ha, so the near field looked sparse even
though the tree geometry was approximately to scale.

Rendering every stem globally is not practical:

| case | observed area | 500 stems/ha |
|---|---:|---:|
| 2003_526 | 520 ha | 260,000 |
| Dogrib 2001 | 10,219 ha | 5.1 million |
| 2003_96 | ~25,000 ha | 12.5 million |

## Design

The scene now has two representations.

1. **Overview canopy.** The existing 32,000-stem sample is rendered as a
   canopy impostor. It is cheap, covers the whole observed extent, and is
   labelled as a visual sample — not an inventory.

2. **Near-field detail.** When the camera enters the detail LOD, the browser
   generates a local stand at **500 stems/ha** inside a radius around the
   camera target. The radius scales with camera distance (130–300 m) so the
   sharp patch covers the foveal view instead of ending abruptly on screen.

The detail patch contains full trunks, crowns, fire particles, smoke and
post-fire tree states. The far canopy stays visible at low opacity to carry the
periphery.

## Ignition without millions of records

A compact **burn-time field** (160 × 160) is built for each case:

- CFSDS observed-daily cases: nearest observed tree day;
- Dogrib / Hay River: WS4/FBP arrival time.

Each generated detail tree samples that field for its ignition time. A
deterministic hash assigns height, crown size, and post-fire class. No
per-tree records are stored for the detail population.

## Rendering budget

- near-field tree capacity: **12,000** instances;
- detail density: **500 stems/ha**;
- canopy impostor: 32,000 points;
- fire/smoke particles: shared pool, spawned only from active detail trees
  when the detail LOD is active.

The detail patch is regenerated when the camera target moves more than 30 m or
the radius changes by 22%.

## Limits

- The 500 stems/ha value is a visual density target, not a measured inventory.
- The burn-time field is a compact interpolation, not a per-tree simulation.
- The canopy is an impostor, not a canopy-radiative-transfer model.
- The detail patch is synthetic; tree outcomes remain visual classes.
