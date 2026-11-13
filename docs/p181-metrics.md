# P181.1 suppression metrics: local effect, not final area

Status: diagnostic comparison using the parity-tested native free-burn kernel.

## Setup

- full 200-aircraft, 154-target ring
- all targets wet at arrival in the interaction diagnostic
- native free burn vs native wet run
- same grid, seed and weather

## Result

| Metric | Value |
| --- | ---: |
| treated targets | 154 |
| treated targets burned in both runs | 154 |
| targets delayed >1 min | **124** |
| mean arrival delay | **3.83 min** |
| maximum arrival delay | **34.92 min** |
| targets unchanged | 30 |
| targets never burned after treatment | 0 |

Area comparison:

| Time | Free burn | Wet ring |
| ---: | ---: | ---: |
| 1,800 min | 3,286 ha | 3,286 ha |
| 2,100 min | 5,012 ha | **4,955 ha** |
| 22,200 min | 5,325 ha | 5,325 ha |

## Interpretation

The wet ring **does** alter local arrival times: 124 of 154 treated targets are
delayed, with a mean delay of 3.8 minutes and a maximum of 35 minutes. The final
basin area still converges to 5,325 ha.

This is the correct scale of effect for the published evidence. A mean
0.5 m/min ROS reduction does not imply final-area containment of a 5,325 ha
basin-filling fire. The previous final-area endpoint was the wrong metric.

## Artifacts

- `suppression/proofs/2003-526-suppression-metrics.json`

## Next

Use local arrival delay, hold and area-at-time as the suppression metrics.
Only claim containment when a closed barrier actually prevents arrival at a
closed set of cells.
