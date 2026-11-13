# P179.12 perimeter-target mission

Status: diagnostic mission construction and negative result.

## What changed

`suppression/mission.py` distributes target centers across a fixed number of
aircraft and schedules drops at the CL-415 cycle time.

`suppression/perimeter.py` now also has `front_target_cells()`, which returns
**unburned burnable cells adjacent to the active perimeter**. This is the
correct target side for a drop; wetting already-burned cells does not stop the
front.

`scripts/build_perimeter_mission_2003_526.py` builds a scenario from the
free-burn perimeter at minute 600.

## Mission setup

At minute 600:

- active perimeter cells: 106;
- unburned adjacent front targets: **39**;
- aircraft: **5** simulated CL-415 profiles;
- distance to water: 9 km, 5-minute cycle;
- one and two passes over the front targets;
- drop: 100 × 50 m, 1 mm, 240-minute decay;
- wet coupling: sub-cell mean depth and diagnostic ROS factor.

## Result

| Mission | Drops | Final area | IoU |
| --- | ---: | ---: | ---: |
| Free burn | — | 5,325 ha | 0.096 |
| One pass, 5 aircraft | 39 | 5,325 ha | 0.096 |
| Two passes, 5 aircraft | 78 | 5,325 ha | 0.096 |

No final perimeter change.

## Interpretation

The mission targets the unburned side, but 39 targets are not a closed
perimeter. The drops do not form a continuous barrier, and the fire bypasses
the treated cells. Two passes improve depth in the same cells but do not close
the flanks.

The result is sensitive to:

- the number of front targets;
- drop overlap and spacing;
- the time required to complete the mission;
- the 100 m fire grid;
- the diagnostic wetness/ROS mapping.

It would be wrong to read this as an operational conclusion about aerial
suppression. It is a limitation of this placement and effect model.

## Artifacts

- `suppression/scenarios/2003-526-perimeter-5air-1pass.json`
- `suppression/scenarios/2003-526-perimeter-5air-2pass.json`
- `suppression/proofs/2003-526-native-perimeter-5air-1pass.json`
- `suppression/proofs/2003-526-native-perimeter-5air-2pass.json`

## Limits

- The mission is built once from the 600-minute free-burn front; it is not
  re-planned as the fire moves.
- No aircraft are lost to turn-around, refill, visibility or competing fires.
- The drop line is not optimized.
- The wetness/ROS mapping remains a placeholder.
- No terrain, wind drift, canopy interception or re-ignition.

## Next

A closed **head-and-flank** mission with adjacent overlap, or a receding-horizon
planner that re-reads the front after each pass. The current mission is not a
containment test because it leaves open flanks.
