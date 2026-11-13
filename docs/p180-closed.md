# P180.11 scheduled full-height barrier

Status: diagnostic control. A scheduled vertical line was placed across the
burnable column at x = 493,600 m and timed to each cell's predicted arrival.

## Result

- 71 target cells
- 213 sorties
- 100 aircraft
- 3 stacked drops per target
- all **71/71 cells wet at arrival**
- native area: **5,325 ha**

The full-height line still does not alter the native burn area.

## What this isolates

Delivery, stacking, target spacing, arrival timing and water-at-arrival are no
longer the explanation. The line is one 100 m cell wide, with 50 m effective
drop width and partial-cell coverage. The remaining issue is the native
effect/growth geometry, not the drop mission.

## Artifacts

- `suppression/scenarios/2003-526-closed-barrier.json`
- `suppression/proofs/2003-526-wet-interaction-closed-barrier.json`
- `suppression/proofs/2003-526-native-closed-barrier.json`

## Decision

Stop generating delivery missions. The next change must be in the coupled fire
kernel or in a barrier geometry that explicitly closes the burnable grid.
