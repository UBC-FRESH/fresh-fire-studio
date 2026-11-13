# P179.3a native time-dependent containment proof

Status: diagnostic. This replaces the chunked P179.2 harness with one
minimum-travel-time run that checks containment at each cell expansion.

It is a prototype adapter around the WS4 P177 growth loop, not a validated
operational suppression model.

## What changed

Added `suppression/native_growth.py`:

- `build_containment_schedule` samples each line's construction and stores a
  per-cell containment start and end time;
- `ContainmentSchedule` answers whether a cell is contained at time `t`;
- `grow_fire_with_containment` runs one WS4 growth pass and checks the schedule
  when expanding a source cell, a target cell, and the cells between them;
- containment-change events re-expand the burned front. This is required for a
  breach: simply removing the mask is not enough when the queue has already
  emptied.

`scripts/prove_native_suppression_2003_526.py` builds the grid, schedule and
weather once, then runs the native kernel.

## Results

All runs use the same free-burn baseline: **5,325 ha**, IoU **0.096**.

| Scenario | Native area | IoU | Change vs free |
| --- | ---: | ---: | ---: |
| Fast line, built 0–60 min | 3,113 ha | 0.134 | −2,212 ha (−41.5%) |
| Slow line, built 0–1,440 min | 5,183 ha | 0.097 | −142 ha (−2.7%) |
| Fast line, breached at 7,200 min | 5,325 ha | 0.096 | 0 |
| Late line, built 18,000–19,440 min | 5,325 ha | 0.096 | 0 |

### Fast-line validation

The fast line is complete in 60 minutes. The native run returns **3,113 ha**,
identical to the P179.1 static-line result. That validates the adapter: when the
line is present before the fire reaches it, the native and static masks agree.

### Slow-build result

The 24-hour line reaches only 8 cells at minute 60 and 152 cells at minute
1,440. The native run returns **5,183 ha**, a reduction of only **142 ha
(2.7%)**.

This is the key timing result. The fire crosses the barrier while it is still
being built. The chunked P179.2a harness returned 3,112 ha for the same
scenario, so it overestimated containment by **2,071 ha**. The chunk harness
seeded all burned cells and applied the line at chunk boundaries; the native
single run resolves expansion against the mask at the actual arrival time.

### Breach and late arrival

- The fast line holds through minute 7,140 and is breached at 7,200. Native
  final area returns to **5,325 ha**, the free-burn value.
- The late line starts at 18,000 minutes, after the fire has crossed the
  barrier. Native final area is **5,325 ha**.

The chunked artifacts are 5,323 ha for both cases; the 2 ha difference is the
expected chunk approximation.

## What this proves

- A single growth run can consume a time-dependent containment schedule.
- Line construction timing matters as much as final line length.
- A line that is fully built before arrival matches the static result.
- A slow-built, breached, or late line can fail to contain.
- The chunk harness was optimistic for the slow-build case.

## What this does not prove

- It does not validate suppression effectiveness.
- It does not solve the P176 burnable-basin overprediction.
- It does not couple drop moisture, coverage or decay to growth.
- It does not support spotting, wind grids or burning-condition gates.
- Line construction is sampled every 60 minutes.
- The line is synthetic and the scenarios are scripted.
- The free-burn simulation is still far larger than the 520 ha observed fire.

## Reproduce

```bash
python scripts/prove_native_suppression_2003_526.py \
  --ws4-root ../.opencode/tmp/opencode/ws4-p177 \
  --scenario suppression/scenarios/2003-526-proof.json \
  --out suppression/proofs/2003-526-native-fast.json

python scripts/prove_native_suppression_2003_526.py \
  --ws4-root ../.opencode/tmp/opencode/ws4-p177 \
  --scenario suppression/scenarios/2003-526-temporal-proof.json \
  --out suppression/proofs/2003-526-native.json

python scripts/prove_native_suppression_2003_526.py \
  --ws4-root ../.opencode/tmp/opencode/ws4-p177 \
  --scenario suppression/scenarios/2003-526-breach-proof.json \
  --out suppression/proofs/2003-526-native-breach.json

python scripts/prove_native_suppression_2003_526.py \
  --ws4-root ../.opencode/tmp/opencode/ws4-p177 \
  --scenario suppression/scenarios/2003-526-late-line-proof.json \
  --out suppression/proofs/2003-526-native-late-line.json

pytest -q tests/
```

## Next

- Couple drop moisture/coverage and decay to fuel availability.
- Add a late-line case where the barrier is completed just before the front,
  and one where it is completed just after.
- Add resource dispatch and queueing to produce the line schedule rather than
  scripting it.
- Then add the 3D playback layer.
