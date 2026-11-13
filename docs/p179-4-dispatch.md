# P179.4a deterministic dispatch prototype

Status: diagnostic. This is a deterministic feasibility calculator, not an
optimizer and not an operational dispatch model.

## What it does

`suppression/dispatch.py` consumes the existing P179 resources and tasks and
derives:

- Euclidean travel from the resource's current location to the task target;
- resource readiness after the previous task;
- line-construction service time from line length and `line_rate_m_h`;
- actual start and end times;
- delay against the requested task start;
- late-task and availability warnings;
- per-resource service utilization.

It does not choose resources. It follows the `resource_id` already present in
each task, like a dispatch feasibility check.

Run:

```bash
python scripts/dispatch_suppression_scenario.py \
  suppression/scenarios/2003-526-demo.json \
  --out suppression/proofs/2003-526-dispatch.json
```

## Demo result

The schematic `2003-526-demo` scenario produces:

| Task | Resource | Start | End | Travel | Service |
| --- | --- | ---: | ---: | ---: | ---: |
| `t-assess` | `ia-crew-1` | 20.0 | 50.0 | 0.9 | 30.0 |
| `t-line-crew` | `ia-crew-1` | 50.2 | 150.4 | 0.2 | 100.2 |
| `t-line-dozer` | `dozer-1` | 80.0 | 139.0 | 2.0 | 59.0 |
| `t-hose` | `engine-1` | 50.0 | 200.0 | 0.7 | 150.0 |
| `t-air1` | `heli-1` | 120.0 | 140.0 | 0.7 | 20.0 |
| `t-air2` | `heli-1` | 180.0 | 200.0 | 0.0 | 20.0 |
| `t-tanker` | `airtanker-1` | 150.0 | 165.0 | 0.3 | 15.0 |
| `t-pump` | `pump-1` | 45.0 | 80.0 | 0.0 | 35.0 |

The crew line is 300.7 m and takes 100.2 minutes at 180 m/h. The dozer line is
344.1 m and takes 59.0 minutes at 350 m/h. The scenario's requested line
windows were longer; the derived times show the production-limited timing.

Artifact: `suppression/proofs/2003-526-dispatch.json`.

## Why this layer matters

Martell's queueing and assignment work treats resources as time-dependent
servers. This prototype is the minimum version of that idea:

- a resource cannot start a second task before it finishes the first;
- travel consumes time;
- line production consumes time;
- the requested task window can be missed;
- utilization is visible.

It is deliberately before aircraft cycle models, water-source refills and
multi-incident queues.

## Limits

- Travel is straight-line distance, not roads or terrain.
- No crew rest, span of control, safety or shift rules.
- No resource selection or optimization.
- No overlapping task requests; the P179 contract currently rejects them.
- Aircraft service time is the requested task duration, not a full cycle with
  fill, transit, drop, return and turnaround.
- Drop capacity and coverage are not integrated into the task duration.
- No weather, visibility, smoke or night restrictions.
- The scenario is schematic; these are not real dispatch times.

## Next

1. Use the derived line construction times in the native containment proof
   instead of the scripted line windows.
2. Add aircraft cycles with water-source refill and turn-around.
3. Add a priority queue and multi-task resource contention.
4. Add drop coverage and decay to the growth kernel.
