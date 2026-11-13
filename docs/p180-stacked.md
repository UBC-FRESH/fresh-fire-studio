# P180.10 stacked arrival mission

Status: diagnostic. Two aircraft were assigned to each target with overlapping
drop windows around predicted arrival.

## Setup

- 21 targets from the 1,800-minute front
- 6 aircraft
- 2 drops per target
- 42 sorties
- 60-minute hold
- drops scheduled around `arrival - hold/2`

## Result

- mean drop lateness: **14.62 min**
- wet cells: **21**
- wet at arrival: **0**
- burned before wet: **0**
- burned after wet: **0**
- no qualifying wet window: **21**
- native area: **5,325 ha**

The scheduler produces two drops per target, but the per-cell depth at arrival
still does not reach the required threshold. The next diagnostic must print the
actual drop intervals and total depth for a sample target rather than assuming
the two sorties overlap.

## Artifacts

- `suppression/scenarios/2003-526-arrival-stacked-6air.json`
- `suppression/proofs/2003-526-wet-interaction-stacked-6air.json`
- `suppression/proofs/2003-526-native-arrival-stacked-6air.json`

## Limits

- The scheduler assumes the first available aircraft; it does not optimize
  pairing.
- Two drops are not guaranteed to fall within the same hold interval.
- The cell-mean depth is still below the required depth in all targets.
- The native model remains baseline.
