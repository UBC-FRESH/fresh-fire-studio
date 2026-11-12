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

1. **Overview canopy.** The existing 32,000-stem sample is rendered as
   tree-silhouette impostors. It is cheap, covers the whole observed extent,
   and is labelled as a visual sample — not an inventory.

2. **Near-field detail.** The browser generates **160 m world-space tiles**
   at **500 stems/ha**. Tiles within 280 m of the camera target are loaded,
   up to a 12,000-instance cap; the outer active ring is stochastically
   thinned. Tiles and per-tree ignition times are cached, so zooming or
   revisiting an area does not rebuild or reset the stand.

3. **Mid-field impostors.** A wider field of **140 stems/ha tree silhouettes**
   overlaps the detail patch and extends out to roughly **800 m**. It uses the
   same burn-time field, so background patches change colour with the fire.
   The outer 28% of the mid-field is stochastically thinned to blend into the
   canopy. This is the layer that removes the keyhole.

The detail patch contains full trunks, crowns, fire particles, smoke and
post-fire tree states. The mid-field and canopy impostors carry the periphery
without adding millions of triangles.

## Ignition without millions of records

A compact **burn-time field** (384 × 384) is built for each case:

- CFSDS observed-daily cases: nearest observed tree day;
- Dogrib / Hay River: WS4/FBP arrival time.

Each generated tree samples the field bilinearly and adds a deterministic
per-tree ignition jitter. A local neighbour graph then lets ignition advance
crown-to-crown: trees within 12 m pass ignition to neighbours with a
distance-dependent delay plus a deterministic resistance term. Two passes are
used, and ignition can advance at most 120 minutes ahead of the coarse field.
This avoids whole raster cells flipping at once without letting the local rule
overwhelm the observed/model timing. A deterministic hash assigns height,
crown size, and post-fire class. No per-tree records are stored for the detail
population.

The scene uses the standard right-handed geographic mapping: east `+X`,
north `−Z`. The earlier viewer mapped north to `+Z`, which mirrored the scene
east–west under a normal Three.js camera.

## Rendering budget

- near-field tree capacity: **12,000** instances;
- detail density: **500 stems/ha**;
- mid-field impostors: up to **40,000** silhouettes at **140 stems/ha**;
- overview canopy: 32,000 points;
- fire/smoke particles: shared pool, spawned only from active detail trees
  when the detail LOD is active.

Detail is stored in fixed **160 m world-space tiles** with a **280 m** active
radius, not in a radius that changes with zoom. Ignition times are cached by
world grid key, so panning, focusing, zooming out and zooming back in preserve
the burn state of a tree instead of creating a new unburned population. The
**Overview** button returns smoothly to the full-extent camera.

The LOD now fades between **1400 m and 800 m** camera distance rather than
switching at a hard threshold. Detail material opacity, mid-field opacity and
canopy opacity are blended over that band. Focus, North-up and model-extent
camera moves are animated over 850 ms instead of jumping.

The detail patch is regenerated only when the camera target moves more than
60 m. The mid-field ring uses a wider 80 m threshold.

## Limits

- The 500 stems/ha value is a visual density target, not a measured inventory.
- The burn-time field is a compact interpolation; the local detail graph is a
  visual propagation rule, not a coupled fire-atmosphere simulation.
- The local spread advances ignition by at most 120 minutes ahead of the
  coarse field; it is not an independent ROS model.
- The detail footprint follows the camera target when it moves more than 60 m;
  ignition times are cached, but newly revealed ground is generated at the
  current coarse-field timing.
- The canopy and mid-field are impostors, not a canopy-radiative-transfer model.
- The mid-field forest continues beyond the observed perimeter for visual
  continuity; it is unburned impostor vegetation, not an observed fuel map.
- The detail patch is synthetic; tree outcomes remain visual classes.
