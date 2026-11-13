# P182.2 line-hold metrics

Status: diagnostic line-hold comparison on the scheduled full-height water line.

## Setup

- 71 target cells on a full-height line at x = 493,600 m
- 3 stacked drops per target
- all targets wet at arrival in the water-interaction diagnostic
- native free burn vs native wet run
- two effect models:
  - full wet-cell hold (`no-absolute`)
  - published 0.5 m/min absolute ROS reduction

## Results

| Effect model | Targets | Delayed >1 min | Mean delay | Max delay | Final area |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full wet-cell hold | 71 | **71/71** | **55.21 min** | 67.46 min | 5,325 ha |
| 0.5 m/min reduction | 71 | **58/71** | **13.76 min** | 64.31 min | 5,325 ha |

All 71 cells burn eventually. The line delays arrival but does not create a
closed non-burnable barrier.

## Positive control

The 20-cell-wide static barrier reduced the same benchmark from **5,325** to
**3,504 ha**, with all 1,520 barrier cells unburned.

That is the containment control. The one-cell water line is a local treatment,
not an equivalent barrier.

## Interpretation

- The full wet-cell hold produces substantial local delay: mean **55 min**.
- The published mean **0.5 m/min** absolute reduction produces less delay:
  mean **13.8 min**, with 58/71 cells delayed.
- Neither changes final basin area.
- The full-height water line is still one cell wide and partial-cell at the
  drop footprint. It is not a closed effect barrier.

## Artifacts

- `suppression/proofs/2003-526-line-hold-full.json`
- `suppression/proofs/2003-526-line-hold-absolute.json`
- `suppression/proofs/2003-526-closed-barrier-metrics.json`

## Next

The next comparison is **effect-grid width**: expand the wet line to the same
20-cell width as the static control and see whether it closes the burnable grid.
That is the direct geometry question, not another sortie count.
