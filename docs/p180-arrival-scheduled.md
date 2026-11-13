# P180.9 arrival-scheduled drops

Status: diagnostic scheduling experiment.

The previous mission started at a clock time. This one schedules each drop
around the target's predicted free-burn arrival time:

```text
desired drop = arrival - hold / 2
```

## Results

Three aircraft, 21 targets, two replicates per target:

| Aircraft | Targets | Wet cells | Wet at arrival | Burned before wet | No wet window | Mean lateness |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 21 | 21 | **0** | 13 | 8 | 37.8 min |
| 6 | 21 | 21 | **0** | 0 | 21 | — |
| 9 | 21 | 21 | **0** | 0 | 21 | — |

More aircraft reduce lateness, but the result is still:

- zero cells wet at arrival at the required depth;
- every wet cell in the 6- and 9-aircraft cases has no qualifying wet window;
- native area remains **5,325 ha**.

## Why

A single 100 × 50 m drop with 1 mm depth has a **cell-mean depth of about
0.39 mm** on a 100 m cell. The required depth is 0.75 mm. Repeating the target
at a different time does not stack the two drops inside the hold window.

The next requirement is **overlapping drops on the same cell**: at least two
aircraft or two consecutive drops timed within the hold, not one drop repeated
far apart.

## Artifacts

- `suppression/scenarios/2003-526-arrival-scheduled.json`
- `suppression/scenarios/2003-526-arrival-scheduled-2x.json`
- `suppression/scenarios/2003-526-arrival-scheduled-2x-6air.json`
- `suppression/scenarios/2003-526-arrival-scheduled-2x-9air.json`
- corresponding `2003-526-wet-interaction-arrival*.json`
- `2003-526-native-arrival-scheduled.json`
- `2003-526-native-arrival-scheduled-2x.json`
- `2003-526-native-arrival-6air.json`
- `2003-526-native-arrival-9air.json`

## Next

Implement **stacking**: assign two aircraft to the same target with overlapping
drop windows, then rerun the interaction analysis. More aircraft without
overlap only add lateness.
