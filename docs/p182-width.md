# P182.3 effect-width test

Status: diagnostic closed-barrier geometry test using the native wet branch.

A synthetic full-height wet band was placed at x = 493,600 m and held for the
full run. Width was varied from 1 to 20 cells.

## Result

| Band width | Wet cells | Final area |
| ---: | ---: | ---: |
| 1 cell | 76 | **3,504 ha** |
| 5 cells | 380 | 3,504 ha |
| 10 cells | 760 | 3,504 ha |
| 20 cells | 1,520 | 3,504 ha |

A **one-cell-wide, full-height, permanent** wet band is sufficient to reduce
the benchmark from **5,325** to **3,504 ha**.

## Interpretation

The native wet branch works. The earlier scheduled water line failed because it
was not a closed barrier for the full run:

- it had 71 targets where the full height is 76 cells;
- it was active for a finite hold window;
- its targets were partial-cell footprints;
- the fire could bypass the open or dry portions.

Width is not the limiting factor once the band is full-height and permanent.
The limiting factors are **closure, duration and coverage**, not 20-cell width.

## Artifacts

- `suppression/proofs/2003-526-effect-width.json`

## Next

Test a scheduled **full-height 76-cell** water line with overlapping drops and
sufficient hold to remain closed through the arrival window. The 1-cell
permanent result is the target.
