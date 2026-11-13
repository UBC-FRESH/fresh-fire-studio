# P181 integration and evaluation plan

Status: next phase. The delivery experiments are frozen.

## Goal

Build an open, reproducible integration layer that connects:

- the benchmark fire-growth kernel;
- suppression resources and aircraft cycles;
- drop geometry and timing;
- evidence-bounded water effects;
- evaluation metrics that match the scale of the effect.

The claim is an **integration testbed and benchmark protocol**, not a validated
tactical suppression model.

## P181.0 — free-burn parity

Before any suppression result is trusted:

- run the benchmark `run_observed_case` free burn;
- run `native_growth` with the same grid, seed, weather and no wetness;
- compare burned masks, ignition times and metrics.

Acceptance: identical or explicitly explained differences. If parity fails,
fix `native_growth` before further suppression tests.

Result: **parity passed exactly** on `2003_526`:
- same 5,325 ha;
- 0 mismatched cells;
- maximum arrival-time difference 0.0 min;
- mean arrival-time difference 0.0 min.

See `suppression/proofs/2003-526-native-parity.json`.

## P181.1 — correct suppression metrics

Stop using final basin area as the primary endpoint.

Measure:

- burned area at fixed times;
- local arrival delay at treated cells;
- hold duration;
- treated-cell ROS or edge arrival changes;
- whether the front bypasses, breaches or extinguishes locally.

Result: the 154-target wet ring delayed **124/154** treated targets, mean
**3.83 min**, maximum **34.92 min**; area at 2,100 min fell from **5,012** to
**4,955 ha**, while the final area remained **5,325 ha**. See
[`p181-metrics.md`](p181-metrics.md).

## P181.2 — closed geometry, not more sorties

A wet line must be closed in the burnable grid:

- full-height or closed ring;
- width sufficient to avoid sub-cell bypass;
- no gaps from non-burnable or omitted cells;
- explicit target-cell coverage and per-cell depth.

## P181.2 — closed geometry, not more sorties

A 20-cell-wide static barrier reduced the benchmark area from **5,325** to
**3,504 ha** and left all 1,520 barrier cells unburned. This is the positive
containment control. The water ring was one cell wide and partially covered the
100 m cells, so it delayed targets but left bypass paths. See
[`p181-closed.md`](p181-closed.md).

## P181.3 — public evaluation artifact

Document:

- parity result;
- suppression metric definitions;
- evidence ranges;
- failure modes;
- what would change the conclusion.

## Non-goals

- no further aircraft-count or pass sweeps;
- no operational claim;
- no field campaign requirement;
- no new fire physics until parity and metrics are established.
