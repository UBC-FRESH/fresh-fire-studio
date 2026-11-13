# P184 line-breach forensics

Status: diagnostic. The 12-aircraft line was closed at free-burn arrival but all
burnable line cells later breached after the water expired.

## Setup

- scenario: `2003-526-fleet3-12air.json`
- 76-cell full-height line at x = 493,600 m
- 3 stacked drops per cell
- 228 sorties, 12 aircraft
- required depth: 0.75 mm
- 5 non-burnable cells, 71 burnable cells

## Result

| Measure | Value |
| --- | ---: |
| Burnable line cells | 71 |
| Held cells | 0 |
| Breached cells | 71 |
| Pre-wet breaches | 0 |
| Burned while wet | 0 |
| Post-expiry breaches | **71** |

Free-burn arrival at the line spans **1,345.7 to 1,851.0 min**. Coupled
ignition spans **1,409.5 to 1,916.9 min**.

First breach:

- row 23, column 59
- free arrival: 1,345.7 min
- last wet time: 1,361.7 min
- ignition: 1,409.5 min
- depth at ignition: 0.0 mm

Across all 71 cells:

- arrival delay: mean **55.3 min**, range **39.0–67.5 min**
- ignition after last wet time: mean **39.2 min**, range **23.0–51.5 min**
- every breach occurred after the cell was last wet

## Why the hold is shorter than 60 minutes

The 60-minute value is the decay duration, not the time above the suppression
threshold. Three 1 mm drops at about 0.39 cell coverage give roughly **1.17 mm**
at the cell centre. With linear decay to zero over 60 minutes, the cell remains
above the required **0.75 mm** for only about **17–18 minutes**.

The line therefore closes at arrival, but is effective for only 18 minutes. The
coupled fire reaches the line later and crosses after expiry.

## Interpretation

This is not a wet-branch or geometry failure. It is a persistence failure:

- water timing was correct for free-burn arrival;
- all line cells were wet at that arrival;
- the effective hold was about 18 minutes;
- the fire crossed only after expiry.

The next requirement is not a larger one-time mission. It is either:

1. re-wetting at an interval no longer than the effective hold; or
2. more water per drop/footprint to extend the effective hold.

## Artifact

- `suppression/proofs/2003-526-line-breach-forensics.json`

## Next

P185 will compare a perfect periodic re-wetting schedule at 15, 18 and 30
minutes against increased depth, then convert only the successful interval
into a fleet requirement. No open-loop aircraft sweep is planned.
