# P179.10 fine-grid drop experiment

Status: resolution experiment. It runs the native growth kernel at 50 m instead
of 100 m and applies the same repeated-drop line. It does not produce a
containment change.

## Setup

- Source case: CFSDS `2003_526`.
- Fine grid: 180 × 152 cells at 50 m.
- Fuel, blend and elevation grids: nearest-neighbour upsampled from 100 m.
- Observed first-day and final masks: nearest-neighbour upsampled.
- Weather: the same hourly Open-Meteo/FireSTARR stream.
- Drop line: the P179.7 21-drop line.
- Wet coupling: sub-cell mean depth and the diagnostic ROS factor.

## Result

| Grid | Run | Simulated area | IoU |
| --- | --- | ---: | ---: |
| 100 m | Free burn | 5,325 ha | 0.096 |
| 100 m | Repeated-drop line | 5,325 ha | 0.096 |
| 50 m | Free burn | 5,325 ha | 0.096 |
| 50 m | Repeated-drop line | 5,325 ha | 0.096 |

The fine grid does not change the final area. The drop line is still not
continuous across the active fire front, and the fire bypasses it.

Artifact: `suppression/proofs/2003-526-fine-grid.json`.

## What this shows

- The native kernel runs at 50 m without a code change.
- Upsampling the 100 m fuel and terrain does not create new information.
- Finer cells alone do not solve placement.
- A wet line must be placed across the active perimeter, with enough overlap
  and depth, to affect the fire.

## Limits

- Fuel and terrain are nearest-neighbour upsampled, not remapped from source
  polygons.
- The observed masks are upsampled, not re-digitized.
- The 50 m grid is still coarse relative to a 100 × 50 m drop.
- The wet ROS mapping remains diagnostic.
- The drop line is scripted, not dispatched against the simulated perimeter.

## Next

Place drops against the **active simulated perimeter**, not a fixed geographic
line. That requires a perimeter query at drop time and a placement policy. It
is a more important next step than reducing the cell size again.
