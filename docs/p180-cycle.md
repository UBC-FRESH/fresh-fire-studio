# P180.0 aircraft cycle contract

Status: implemented schematic cycle geometry.

## Contract

`suppression/cycle.py` defines:

- `FlightPhase` — kind, start/end and 3D from/to positions;
- `CyclePerformance` — cruise/drop speed, scoop/climb/descent/drop/turn times,
  altitudes and tank load;
- `Sortie` — one aircraft cycle with contiguous phases and water load;
- `build_cycle` — round-robin target assignment across aircraft;
- `cycle_summary` — sorties, water, cycle times and per-aircraft counts.

Phase order:

```text
scoop → climb → cruise_out → descent → drop → turn
      → climb_back → cruise_back → descent_back → repeat
```

The geometry is schematic. It is not a flight simulator and not a dispatch
reconstruction.

## Current mission

- 3 CL-415-style aircraft
- 21 sorties on a selected head segment about 5.3 km long
- 126,000 L total tank capacity delivered across sorties
- 247,731 L/h aggregate delivery rate
- mean cycle time **4.25 min**
- cycle range **3.53–4.74 min**
- active targets selected from the eastern head of the model front at minute
  600
- lake at a schematic location southwest of the target line

This is within the range suggested by published cycle-time work for a nearby
water source: roughly five minutes or less.

## Water balance

The selected head segment is about **5.3 km**. The 21 drops cover about
**105,000 m²** of a 50 m-wide strip; the full strip is about **266,000 m²**.

At 126,000 L delivered and 0.75 mm required depth:

- line-mean depth: **0.47 mm**;
- coverage: **39%** of the strip;
- required water: **199,630 L**;
- deficit: **73,630 L**;
- additional sorties: **13**.

A second pass delivers **252,000 L**, **0.95 mm**, **79%** coverage and closes
the nominal mass deficit; elapsed time is about **61 min**. The current
one-pass mission is short of demand. That is the first operationally meaningful
number in the cycle model.

## Coupling

`scripts/build_cycle_mission_2003_526.py` writes:

- `suppression/scenarios/2003-526-cycle-mission.json`;
- `portal/static/suppression-mission.json`.

The native growth run consumes the actual drop start/end times and target
coordinates from the cycle. The final result remains **5,325 ha**, because the
wet line is still too small and finite. That is a model result, not an
operational conclusion.

## Reproduce

```bash
python scripts/build_cycle_mission_2003_526.py \
  --ws4-root ../.opencode/tmp/opencode/ws4-p177

python scripts/prove_native_suppression_2003_526.py \
  --ws4-root ../.opencode/tmp/opencode/ws4-p177 \
  --scenario suppression/scenarios/2003-526-cycle-mission.json \
  --drops --subcell-cell-size-m 10 --ros-reduction-m-min 0.5 \
  --out suppression/proofs/2003-526-native-cycle-mission.json
```

## Limits

- lake, base, target line and phase times are schematic;
- no takeoff/landing, visibility, wind, smoke or airspace;
- no lake capacity or refill competition;
- water effect remains evidence-bounded and diagnostic.
