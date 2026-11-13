# P179.14 receding-horizon perimeter mission

Status: diagnostic closed-loop experiment. It re-plans the drop mission after
each epoch, but still produces no final-area change.

## What it does

`scripts/recede_horizon_2003_526.py`:

1. runs the native fire to the first planning epoch;
2. reads the current burned mask;
3. selects unburned cells adjacent to the active perimeter;
4. builds one perimeter-target mission with the CL-415 cycle model;
5. appends all missions and reruns the native growth;
6. repeats at the next epoch.

Planning epochs: **600, 900, 1,200 and 1,500 minutes**. Five aircraft per
mission. Each drop is 100 × 50 m, 1 mm, with 240-minute decay. Wet coupling is
sub-cell mean depth plus the diagnostic ROS factor.

## Result

| Run | Final area | IoU |
| --- | ---: | ---: |
| Free burn | 5,325 ha | 0.096 |
| Receding horizon, 4 missions | 5,325 ha | 0.096 |

- missions: 4
- total drops: 266
- final area change: none

Artifact: `suppression/proofs/2003-526-receding-horizon.json`.

## What this shows

Re-planning alone does not solve the containment problem in this model. The
missions still target a small set of front cells, the fire bypasses or crosses
after the water decays, and the final burnable basin is reached.

The result is a combination of:

- 100 m fire cells;
- finite 240-minute water duration;
- 39 front targets per epoch;
- incomplete overlap and no closed line;
- a diagnostic wetness/ROS mapping;
- a fire that continues to spread between missions.

This is not an operational conclusion about receding-horizon planning. It is a
limitation of this implementation and effect model.

## Limits

- Missions are re-planned every 300 minutes, not continuously.
- Aircraft do not refill, turn around or compete with other incidents.
- Drop placement is not optimized.
- The wet ROS mapping is not validated.
- Fuel and terrain remain 100 m.
- No terrain, wind drift, canopy interception or re-ignition.

## Next

A stronger test needs one of:

1. sustained re-wetting with short replan intervals;
2. a continuous wet line around the full perimeter;
3. a validated water-depth-to-ROS model;
4. a finer fire grid that can resolve the drop footprint and partial-cell
   ignition.

The current loop is useful as a failure diagnostic, not as a containment model.
