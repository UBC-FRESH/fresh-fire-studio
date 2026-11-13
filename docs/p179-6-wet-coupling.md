# P179.6 temporary wet-cell coupling

Status: diagnostic threshold coupling. It connects a P179 drop to the native
growth run as a temporary wet cell. It is not a validated water-effects model.

## What changed

Added `suppression/wet.py`:

- `DropPattern` → one `WetDrop` per scenario drop;
- fractional cell coverage via `suppression.effects.coverage_fraction`;
- cell-average water depth, not an all-or-nothing raster mask;
- linear decay after the drop window;
- multiple drops stack additively by cell;
- `WetSchedule.is_suppressed()` checks the required depth.

`grow_fire_with_containment` now accepts an optional `WetSchedule`. A wet cell
is unavailable for ignition while its depth remains at or above the required
depth. Wet-start and wet-end times are inserted as growth events, so the fire
front is re-expanded when water disappears.

## Proof scenario

`suppression/scenarios/2003-526-drop-proof.json` has three 1 mm drops stacked at
the 600-minute fire front:

- each drop is 100 × 50 m;
- each carries 5,000 L, within the 6,000 L resource capacity;
- each has a 240-minute decay window;
- the required depth is 0.75 mm.

At the 100 m fire-grid resolution, one drop covers **0.392 of one cell**. Three
stacked drops reach **1.176 mm** in that cell, so the cell becomes temporarily
non-ignitable around minutes 620–760.

## Result

The native run is **5,325 ha**, exactly the free-burn result. The temporary
wet cell does not change the final perimeter because the fire bypasses a single
100 m cell.

| Time | Free burn | With drops |
| ---: | ---: | ---: |
| 600 min | 291 ha | 291 ha |
| 660 min | 327 ha | 327 ha |
| 1,800 min | 3,286 ha | 3,286 ha |
| 22,200 min | 5,325 ha | 5,325 ha |

Artifacts:

- `suppression/proofs/2003-526-native-drop-free.json`
- `suppression/proofs/2003-526-native-drop.json`

## The important finding

A CL-415-sized drop is **sub-cell** on a 100 m fire grid. A 100 × 50 m drop
covers less than half of one cell. Stacking three drops makes one cell wet, but
the fire can go around it.

This is a resolution problem, not a code failure. A 100 m cell cannot represent
a real drop footprint or a partial-cell water depth without sub-cell logic.

## Limits

- Wet cells are a threshold rule, not a continuous ROS or fuel-moisture model.
- The threshold is an input, not a validated constant.
- The drop is treated as one uniform contour; real drops have nested contours.
- The scenario uses three identical stacked drops for diagnosis.
- No canopy interception, wind drift, evaporation, downwash or terrain.
- The fire grid remains 100 m.

## Next

1. Add a **sub-cell effect grid** or a finer nested effect raster for drops.
2. Use the coverage fraction to modify local ROS or ignition probability instead
   of a binary wet cell.
3. Compare the threshold model with the Van Wagner theoretical depth and the
   McFayden operational contours.
4. Only then promote the wet layer into the public scene.
