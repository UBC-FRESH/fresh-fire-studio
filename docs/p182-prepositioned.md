# P182.5 prepositioned water line

Status: positive diagnostic control.

A full-height 76-cell water line was placed at x = 493,600 m before the fire
arrived and held for the full run.

## Setup

- 76 target cells
- 3 stacked drops per cell
- 228 sorties
- 200 diagnostic aircraft
- drop time: 600 min
- hold: 22,200 min
- required depth: 0.75 mm

## Result

| Metric | Free burn | Prepositioned water line |
| --- | ---: | ---: |
| Native area | 5,325 ha | **3,504 ha** |
| IoU | 0.096 | **0.132** |
| Wet cells | — | 76 |
| Wet at arrival | — | 71 |
| Burned before wet | — | 0 |

The water line reproduces the static-barrier area exactly.

## What this proves

The native wet branch works. The previous arrival-timed missions failed because
the water was not present early enough or did not persist long enough. A
full-height water line that exists before first arrival and remains through the
run contains the fire in this benchmark.

The 200-aircraft prepositioning is diagnostic, not an operational
recommendation.

## Artifacts

- `suppression/scenarios/2003-526-prepositioned-line.json`
- `suppression/proofs/2003-526-wet-interaction-prepositioned-line.json`
- `suppression/proofs/2003-526-native-prepositioned-line.json`

## Next

The operational question is now concrete: can a realistic aircraft fleet
sustain a closed line through the arrival window? Not whether water can affect
the kernel.
