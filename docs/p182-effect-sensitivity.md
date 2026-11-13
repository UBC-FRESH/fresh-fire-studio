# P182.2 local effect sensitivity

Status: diagnostic effect-model sensitivity on the five-target arrival mission.

## Setup

- five targets, all wet at arrival
- 3 stacked drops per target
- required depth varied from 0.25 to 1.0 mm
- absolute ROS reduction varied from none to 1.0 m/min
- same native fire kernel and free-burn seed

## Results

| Required depth | ROS reduction | Delayed targets | Mean delay | Max delay | Final area |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.25 mm | none | 5/5 | 67.50 min | 74.11 | 5,325 ha |
| 0.50 mm | none | 5/5 | 59.33 min | 61.87 | 5,325 ha |
| 0.75 mm | none | 5/5 | 52.45 min | 55.21 | 5,325 ha |
| 1.00 mm | none | 5/5 | 37.54 min | 52.89 | 5,325 ha |
| 0.25/0.50/0.75 mm | 0.5 m/min | 1/5 | 1.28 min | 4.43 | 5,325 ha |
| 0.25/0.50/0.75 mm | 1.0 m/min | 4/5 | 1.97 min | 5.68 | 5,325 ha |
| 1.00 mm | 0.5 m/min | 1/5 | 6.16 min | 28.84 | 5,325 ha |
| 1.00 mm | 1.0 m/min | 4/5 | 6.60 min | 28.84 | 5,325 ha |

## Interpretation

- The no-reduction case is a full wet-cell hold; it produces the largest local
  delays.
- A 0.5 m/min absolute reduction is too weak to delay most targets by more than
  one minute.
- A 1.0 m/min reduction delays four of five targets.
- Final area never changes, even when local delays reach tens of minutes.

This confirms that the local effect model and the final-area endpoint are
different questions. The published mean 0.5 m/min reduction is a local effect,
not a containment guarantee.

## Artifacts

- `suppression/proofs/2003-526-effect-sensitivity-5targets.json`

## Next

Use the local delay/hold envelope, not final area, for the line-hold and
breach experiment.
