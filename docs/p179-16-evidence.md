# P179.16 evidence-based suppression parameters

Status: diagnostic. This replaces the previous arbitrary wetness-to-ROS mapping
with documented empirical values where the water depth reaches the required
threshold.

## Evidence used

### Wheatley 2024, Chapter 5

IR-monitored experimental burns, 22 fires, direct and indirect water
suppression:

- mean rate-of-spread reduction: **0.5 m/min** (SD 0.7);
- mean fireline-intensity reduction: **72 kW/m** (SD 159);
- mean suppression-induced hold: **123 s** (SD 117);
- high water added **64 s** of hold on average;
- indirect high water added **120 s**;
- direct water depths: **1.4 mm** low, **2.3 mm** high;
- indirect water depths: **0.7 mm** low, **1.1 mm** high;
- no strong evidence that water amount changed the ROS reduction after the
  fire was already reduced near the measurement floor.

### McFayden et al. 2023

- effective aerial drops are assumed to hold for at least **60 minutes**;
- the guide treats the operational intensity limit as an aircraft/drop-pattern
  condition, not a single global threshold;
- Wheatley argues the common 4,000 kW/m limit may be conservative and that
  **10,000 kW/m** may be more realistic for C-2 fuels.

## Code

`suppression/evidence.py` contains the constants and hold-time helpers.
`grow_fire_with_containment(..., ros_reduction_m_min=0.5)` now applies an
**absolute** ROS reduction when a target cell is fully wet:

```text
pre_ROS = distance / (arrival - time)
post_ROS = max(0, pre_ROS - 0.5 m/min)
arrival = time + distance / post_ROS
```

This is more defensible than the previous `1 - wetness` multiplier. It is still
a diagnostic use of a mean experimental estimate, not a validated operational
model.

## Scenarios

Two evidence scenarios use the same 21-drop line:

- `2003-526-wheatley-evidence.json` — 123 s hold;
- `2003-526-mcfayden-evidence.json` — 60 min assumed aerial hold.

## Result

| Scenario | Final area | IoU |
| --- | ---: | ---: |
| Free burn | 5,325 ha | 0.096 |
| Wheatley 123 s hold | 5,325 ha | 0.096 |
| McFayden 60 min hold | 5,325 ha | 0.096 |

Neither changes the final perimeter. The 21-drop line still leaves gaps and
open ends; the evidence parameters do not turn a finite line into containment.

Artifacts:

- `suppression/proofs/2003-526-native-wheatley-evidence.json`
- `suppression/proofs/2003-526-native-mcfayden-evidence.json`

## What this proves

- The model can consume measured parameters rather than an invented factor.
- The absolute ROS reduction is implemented at the fire edge.
- The hold-time choice can be varied and reported explicitly.
- A finite line still fails for geometric reasons.

## Limits

- The Wheatley experiments were low-intensity surface fires, not the
  `2003_526` fire.
- The mean 0.5 m/min reduction has SD 0.7 and can be negative in individual
  observations.
- The 123 s hold is a mean, not a guaranteed duration.
- The McFayden 60 min hold is an operational assumption, not a measured
  `2003_526` value.
- Water application efficiency, canopy interception and grid resolution remain
  uncertain.
- No re-ignition model.
