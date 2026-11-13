# P179.9 wetness and local ROS factor

Status: diagnostic. This couples sub-cell mean water depth to a linear local
ROS factor. It is not a validated fire-suppression model.

## What changed

`WetSchedule` now exposes:

- `wetness_at(row, col, t)` — total active depth divided by the required depth,
  capped at 1;
- `ros_factor_at(row, col, t)` — `1 - wetness` for the diagnostic coupling;
- `is_suppressed(...)` — true only when wetness reaches 1.

`build_wet_schedule(..., subcell_cell_size_m=10)` uses the sub-cell raster to
compute mean depth per fire cell. The native growth kernel applies the local
factor to the travel time of an ignition edge:

```text
arrival = time + (arrival - time) / ros_factor
```

A fully wet target is still non-ignitable. A partially wet target slows the
edge rather than blocking it completely.

## Example

A 100 × 50 m, 1 mm drop at 10 m sub-cell resolution has a mean depth of about
0.36 mm in its containing fire cell. With a required depth of 0.75 mm:

- wetness ≈ 0.48;
- ROS factor ≈ 0.52;
- travel time is roughly doubled.

Three stacked drops bring the cell close to saturation.

## Repeated-drop result

The 21-drop line from P179.7 was rerun with the sub-cell mean and ROS factor:

| Run | Final area | IoU |
| --- | ---: | ---: |
| Free burn | 5,325 ha | 0.096 |
| Sub-cell wet line | 5,325 ha | 0.096 |

The final perimeter is unchanged. The fire bypasses the small wetted cells.
This is a resolution/placement result, not proof that water does nothing.

Artifact: `suppression/proofs/2003-526-native-drop-line-subcell.json`.

## What this fixes

- Water depth is no longer an all-or-nothing flag.
- A partially wetted cell can slow spread.
- Sub-cell depth is used rather than a full-cell average.
- The native kernel receives the effect through its normal arrival calculation.

## What this does not fix

- The linear `1 - wetness` ROS factor is a diagnostic placeholder.
- The factor is applied from the target cell at the source expansion time, not
  integrated across the edge travel.
- The fire grid is still 100 m.
- A 100 × 50 m drop still touches only one or two cells.
- No wind drift, canopy interception, evaporation, terrain or suppression
  re-ignition model.
- The 21-drop line is scripted, not dispatched.

## Next

Move from a scalar ROS factor to a physically grounded local fuel-moisture or
ignition model, or introduce a finer fire grid. The current result is useful
because it shows that sub-cell depth alone does not solve the 100 m resolution
problem.
