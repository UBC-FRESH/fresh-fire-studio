# P181.2 closed-barrier control

Status: positive control using the benchmark WS4 kernel.

A 20-cell-wide static non-burnable strip was placed across the full height of
the 2003_526 grid at x = 493,600 m.

## Result

| Metric | Free burn | Closed barrier |
| --- | ---: | ---: |
| Simulated area | 5,325 ha | **3,504 ha** |
| IoU | 0.096 | **0.132** |
| Area reduction | — | **1,821 ha** |
| Barrier cells never burned | — | **1,520 / 1,520** |

The barrier is static and non-burnable. It is not water and not an operational
fuel break. It is the positive control that confirms the benchmark kernel
responds to a genuinely closed barrier.

## Why the water ring did not do this

The scheduled water ring had 154 wet cells, all wet at arrival, but it was
one cell thick and partially covered each 100 m cell. It delayed 124 targets
locally but left bypass paths. The static barrier is 20 cells wide and closes
the burnable grid completely.

The difference between the two cases is **geometry and coverage**, not a
failure of the benchmark fire model.

## Artifacts

- `suppression/proofs/2003-526-closed-barrier-metrics.json`

## Next

Use the closed-barrier result as the containment control. Any claim that a
water mission contains the fire must show an equivalent closed barrier in the
effect grid. A one-cell water line cannot make that claim.
