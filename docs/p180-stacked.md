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

## Results

| Aircraft | Stack | Targets | Wet cells | Wet at arrival | Burned before wet | Native area |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 6 | 2 | 21 | 21 | **0** | 0 | 5,325 ha |
| 12 | 3 | 21 | 21 | **4** | 17 | 5,325 ha |
| 12 | 3 | 5 | 5 | **5** | 0 | 5,325 ha |
| 30 | 3 | 54 | 54 | **10** | 44 | 5,325 ha |
| 100 | 3 | 54 | 54 | **54** | 0 | 5,325 ha |
| 100 | 3 | 154 | 154 | **90** | 58 | 5,325 ha |

The 5-target case is the first case where every treated target is **wet at
arrival**, with combined cell depth about **1.045 mm**. The 100-aircraft,
54-target case is the first full segment where every treated target is wet at
arrival. The native area is still **5,325 ha**.

Even a 154-target all-front mission with 90 wet-at-arrival cells leaves the
native area at **5,325 ha**. The remaining limitation is now the effect/growth
coupling, not delivery, stacking, or arrival timing.

## Artifacts

- `suppression/scenarios/2003-526-arrival-stacked-6air.json`
- `suppression/scenarios/2003-526-arrival-stacked-3x-12air.json`
- `suppression/scenarios/2003-526-arrival-stacked-5targets.json`
- `suppression/scenarios/2003-526-arrival-stacked-fullfront.json`
- corresponding wet-interaction, trace and native artifacts

## Limits

- The scheduler assumes the first available aircraft; it does not optimize
  pairing.
- Full-front treated cells are still lost to lateness when the target count
  grows.
- The five-target result proves wet-at-arrival is possible, but not that a
  contiguous barrier is possible with the current scheduler.
- The native model remains baseline even when wet-at-arrival is achieved.
