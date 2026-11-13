# P183 fleet sizing for a closed wet line

Status: diagnostic fleet-sizing experiment.

## Setup

- full-height 76-cell line at x = 493,600 m
- 3 stacked drops per cell
- arrival-timed drops
- 60-minute hold
- aircraft counts 3, 6, 12, 20, 50 and 100

## Closure result

| Aircraft | Wet cells | Wet at arrival | Burned before wet | No wet window |
| ---: | ---: | ---: | ---: | ---: |
| 3 | 76 | 19 | 52 | 0 |
| 6 | 76 | 54 | 17 | 0 |
| 12 | 76 | **71** | **0** | 0 |
| 20 | 76 | 71 | 0 | 0 |
| 50 | 76 | 71 | 0 | 0 |
| 100 | 76 | 71 | 0 | 0 |

**12 aircraft** is the smallest tested fleet that gets every burnable target
wet before arrival. The five unburned cells are non-burnable.

## Native result

12 aircraft, 228 sorties, 60-minute hold:

- native area: **5,325 ha**
- IoU: 0.096
- same as free burn

The line is closed at arrival, but the water expires before the later growth.

## What this establishes

- The earlier failures were partly fleet/timing constraints.
- A 12-aircraft fleet can lay a full-height, 3-stack line before arrival in
  this diagnostic.
- A 60-minute hold is insufficient for the full `2003_526` run.
- The prepositioned, full-duration line is the positive control:
  **3,504 ha**.

## Artifacts

- `suppression/scenarios/2003-526-fleet3-*.json`
- `suppression/proofs/2003-526-wet-interaction-fleet3-*.json`
- `suppression/proofs/2003-526-native-fleet3-12air.json`

## Next

Estimate the **re-wetting interval** and fleet required to keep the line closed
through the arrival window. This is now an operational persistence calculation,
not a water-effect question.
