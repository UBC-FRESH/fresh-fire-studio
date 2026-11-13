# P179.7 aircraft delivery cycles and repeated drops

Status: diagnostic. This adds the CL-415 delivery-rate table and a repeated-drop
line. It does not model a full aircraft mission, water-source constraints or a
validated suppression effect.

## Delivery-rate model

`suppression/aircraft.py` encodes the CL-415 rows from McFayden et al. (2023)
Tables 7-2/7-3, linearly interpolated between tabulated distances:

| Distance | Drops/hour | Litres/hour | Cycle |
| ---: | ---: | ---: | ---: |
| 0 km | 20 | 98,000 | 3.0 min |
| 9 km | 12 | 60,000 | 5.0 min |
| 19 km | 9 | 43,000 | 6.7 min |
| 37 km | 6 | 28,000 | 10.0 min |

The model exposes:

- `drops_per_hour_at(distance_km)`;
- `litres_per_hour_at(distance_km)`;
- `cycle_minutes_at(distance_km)`;
- `drop_intervals(...)`;
- `line_centers(...)`.

This is a delivery-rate calculator, not a flight simulator.

## Repeated-drop line

`suppression/scenarios/2003-526-drop-line-proof.json` uses one helicopter to
place 21 drops along a 1,200 m line near the 600-minute fire front:

- spacing: 60 m;
- each drop: 100 × 50 m, 1 mm, 5,000 L;
- CL-415 cycle at 9 km: 5 minutes;
- drop windows: 600–701 minutes;
- effect duration: 240 minutes;
- required wet depth: 0.75 mm.

At the 100 m fire-grid resolution each drop covers two cells with a fractional
average depth well below 0.75 mm. The line does not produce a continuous
blocking wet cell.

## Result

| Run | Final area | IoU |
| --- | ---: | ---: |
| Free burn | 5,325 ha | 0.096 |
| Repeated-drop line | 5,325 ha | 0.096 |

The final perimeter is unchanged. The fire bypasses the discontinuous wet
cells, and the drops are sub-cell relative to the 100 m grid.

Artifact: `suppression/proofs/2003-526-native-drop-line.json`.

## What this shows

- The aircraft delivery-rate table is usable for scheduling repeated drops.
- A 5-minute cycle at 9 km gives 12 drops/hour and roughly 60,000 L/hour.
- Repeated 100 × 50 m drops at 60 m spacing still do not form a continuous
  wet barrier on a 100 m grid.
- Delivery volume alone is not an effectiveness result; placement, overlap,
  depth and fire behaviour matter.

## Limits

- No water-source refill or actual flight path.
- No wind drift, canopy interception or evaporation.
- No drop-pattern contour variation or stacking beyond one uniform contour.
- No terrain effects.
- The drop line is scripted, not produced by a dispatch optimizer.
- The native effect is still a temporary wet-cell threshold.

## Next

The repeated-drop result makes the sub-cell problem unavoidable. The next step
is a nested effect raster or a finer fire/effect grid that can represent
partial-cell water depth and overlapping drop contours before the plume reaches
the 100 m fire cells.
