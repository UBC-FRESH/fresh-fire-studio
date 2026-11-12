# P179.1 static line-effect proof

Status: diagnostic. This proves the P179 effect contract reaches the fire grid.
It is not a calibrated suppression reconstruction.

## Input

- Case: CFSDS `2003_526`, 90 × 76 cells at 100 m, EPSG:26911.
- Weather: the existing Open-Meteo/FireSTARR reanalysis fixture.
- Free-burn setup: first-day observed mask, FFMC 90.83, BUI 74.12,
  22,200 minutes, neighbour radius 2.
- Suppression scenario:
  `suppression/scenarios/2003-526-proof.json`.
- Synthetic line: one north–south line at x = 493,200 m, 100 m wide,
  spanning the grid.
- Line task: built between minute 0 and 60 by a diagnostic four-person crew.

The line is deliberately simple. It exists to test rasterization and the
fire-kernel hand-off, not to represent a real dispatch decision.

## Method

1. Run the P177 kernel on `2003_526` with no containment mask.
2. Convert the scenario's line and drop effects to `EffectEvent` objects.
3. Rasterize those events onto the fire grid with
   `suppression.effects.rasterize_effects`.
4. Run the same kernel again with the line cells as the P177
   `containment_mask`.
5. Compare the free-burn and contained perimeters against the observed
   perimeter.

The 100 m line covers 152 cells, or two 100 m columns over all 76 rows.

## Results

| Run | Simulated area | Perimeter sim | Centroid error | IoU |
| --- | ---: | ---: | ---: | ---: |
| Free burn | 5,325 ha | 116,800 m | 175 m | 0.096 |
| Static line | 3,113 ha | 72,200 m | 1,908 m | 0.134 |
| Observed | 520 ha | 19,600 m | — | — |

The line reduces simulated area by **2,212 ha, or 41.5%**. IoU rises from
**0.096 to 0.134** and area bias falls from **9.24 to 4.99**.

The improvement is not uniform. Centroid error rises from 175 m to 1,908 m and
orientation error rises from 21.6° to 72.2°. The containment mask truncates the
basin on one side; it does not make the simulated fire match the observed
perimeter. The free-burn simulation still fills much more of the basin than the
observed 520 ha fire.

## What this proves

- The suppression scenario produces time-bounded effect events.
- The line geometry is rasterized onto the same grid as the fire model.
- Suppression changes the simulated perimeter, not just a visualization.
- The P177 containment contract can consume a P179 effect layer without a new
  fire kernel.

## What this does not prove

- It does not validate suppression effectiveness.
- It does not solve the P176 burnable-basin stopping problem.
- It does not test time-varying line construction, breaches or re-ignition.
- Drop effects are rasterized into separate water/foam/retardant layers, but
  they are not yet fed into fire growth.
- The line is synthetic and applied for the whole run, not from minute 60.

## Reproduce

```bash
python scripts/prove_suppression_2003_526.py \
  --ws4-root ../.opencode/tmp/opencode/ws4-p177
pytest -q tests/
```

Artifact: `suppression/proofs/2003-526.json`.

## Next

P179.2 should make the effect mask time-aware:

1. build line cells between `constructed_start_min` and
   `constructed_end_min`;
2. allow held, breached and abandoned states;
3. apply drop moisture/coverage with decay and re-ignition;
4. add a time-stepped containment mask to the growth kernel;
5. only then add resource queueing and 3D playback.
