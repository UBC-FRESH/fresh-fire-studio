# P180.8 wet-cell / arrival interaction

Status: diagnostic instrumentation.

The model was instrumented to count:

- cells that ever receive water;
- cells already burned before water arrives;
- cells that burn after the water window;
- cells unburned at the end;
- cells where the wet window overlaps arrival but the depth never reaches the
  required threshold.

## Results

| Scenario | Wet cells | Burned before wet | Burned after wet | No wet window | Wet at arrival |
| --- | ---: | ---: | ---: | ---: | ---: |
| Continuous, 54 targets | 59 | 36 | 4 | 18 | **0** |
| Continuous two-pass, lead 150 min | 46 | 1 | 13 | 31 | **0** |
| Continuous, mission at 1,600 min | 106 | 20 | 45 | 40 | **0** |

No wet cell coincides with fire arrival at the required depth.

## What this means

The delivery experiments were not testing the suppression model: the water and
the fire front were not overlapping at the required depth. More water cannot
fix that. The next problem is **temporal and depth alignment**:

- target cells are burned before water arrives in the early mission;
- water expires before arrival in the late mission;
- in most remaining cells, the per-cell average depth is below the required
  threshold, even when total mission volume is large.

The relevant quantities are not just total litres and line length. They are:

- unique target cells;
- per-cell mean depth;
- wet interval;
- fire arrival time at that cell.

## Artifacts

- `suppression/proofs/2003-526-wet-interaction-continuous.json`
- `suppression/proofs/2003-526-wet-interaction-lead150.json`
- `suppression/proofs/2003-526-wet-interaction-arrival-timed.json`

## Next

Schedule drops against **arrival time minus hold**. The current cycle schedule
is still arranged around a mission start time, not around when each target
actually burns.
