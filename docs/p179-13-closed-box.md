# P179.13 closed-box mission

Status: diagnostic. A closed box around the active perimeter was tested to
remove the open-flank problem from P179.12. It also produced no final-area
change.

## Setup

- free-burn perimeter at minute 600;
- closed rectangle around the perimeter with a 300 m margin;
- drop spacing 100 m;
- 5 simulated CL-415s;
- 119 drops in one pass;
- 100 × 50 m, 1 mm drops;
- 240-minute decay;
- sub-cell mean depth and diagnostic ROS factor.

The box geometry closes the flanks. It does not solve the time dimension: the
box is built once, and the water decays before the fire reaches the later
perimeter.

## Result

| Run | Final area | IoU |
| --- | ---: | ---: |
| Free burn | 5,325 ha | 0.096 |
| Closed box, 5 aircraft | 5,325 ha | 0.096 |

Artifact:

- `suppression/scenarios/2003-526-box-5air-1pass.json`
- `suppression/proofs/2003-526-native-box-5air-1pass.json`

## Interpretation

Closing the flanks is necessary but not sufficient. A single finite mission can
be bypassed after the water decays. The model needs either:

- a receding-horizon mission that re-wets the active perimeter; or
- a longer-lived retardant/effect model with explicit re-ignition; or
- a different suppression objective than a one-time geometric line.

This is not evidence that a closed box would fail operationally. It is evidence
that the current one-pass, finite-duration effect model does not produce
containment on `2003_526`.

## Limits

- The box is built once from the 600-minute free-burn perimeter.
- No re-planning as the fire moves.
- No refill, turn-around, visibility or competing incidents.
- The wetness/ROS mapping remains diagnostic.
- The box includes some non-burnable and already-burned cells.
- The 100 m fire grid and sub-cell aggregation still limit drop geometry.

## Next

Implement a receding-horizon policy: after each pass, query the current
perimeter and place the next mission where the fire is actually spreading.
