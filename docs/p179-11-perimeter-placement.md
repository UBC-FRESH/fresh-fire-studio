# P179.11 perimeter query and head-line placement

Status: diagnostic groundwork and negative placement result.

## Added

`suppression/perimeter.py` provides:

- `perimeter_mask()` — burned cells with an unburned four-neighbour;
- `perimeter_cells()` — row/column pairs;
- `leading_edge_cells()` — north, south, east or west band;
- `cells_to_centers()` — projected cell centers;
- burnable-mask handling.

This is a query layer. It does not choose a tactic or optimize drop placement.

## Head-line experiments

The free run at minute 600 had a head perimeter near:

```text
x ≈ 492,750 m
y ≈ 5,725,750–5,727,750 m
```

Two diagnostic head lines were tested:

1. one helicopter, 21 drops at 5-minute cycle;
2. five helicopters, 105 drops, covering the same 2 km line.

Both used 100 × 50 m, 1 mm drops with a 240-minute decay and the P179.9
sub-cell/ROS coupling.

## Result

| Mission | Final area | IoU |
| --- | ---: | ---: |
| Free burn | 5,325 ha | 0.096 |
| One-helicopter head line | 5,325 ha | 0.096 |
| Five-helicopter head line | 5,325 ha | 0.096 |

Neither head line changed the final perimeter. The fire bypassed the ends of
the finite line.

Artifacts:

- `suppression/proofs/2003-526-native-head-line.json`
- `suppression/proofs/2003-526-native-head-line-5heli.json`

Scenarios:

- `suppression/scenarios/2003-526-head-line-proof.json`
- `suppression/scenarios/2003-526-head-line-5heli-proof.json`

## Interpretation

A line that covers only part of the active perimeter leaves flanks. More water
on the same finite segment does not close those flanks. The next placement
policy must address:

- the full active perimeter or a deliberately closed segment;
- drop overlap beyond the line ends;
- line depth and decay;
- the time the fire takes to reach the line;
- the number of aircraft and their cycle times.

The five-helicopter case is a resource-saturation diagnostic, not a realistic
deployment recommendation.

## Limits

- The line is scripted from inspected perimeter coordinates, not selected
  dynamically during the run.
- No optimization or dispatch model chooses the line.
- The wet ROS factor remains diagnostic.
- The drop line is finite and has no end caps.
- No terrain, wind drift, canopy interception or re-ignition model.

## Next

Use `perimeter_cells()` to build a **full-perimeter allocation** or a closed
head-and-flank line. Only then compare resource levels. A finite segment is not
a containment test.
