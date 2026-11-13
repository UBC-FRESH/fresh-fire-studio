# P182 research plan: evidence-bounded suppression integration

Status: proposed. Replaces the delivery/aircraft sweep loop.

## 1. Research question

Can an open, evidence-bounded coupling of a benchmark fire-growth kernel with
tactical suppression operations:

1. reproduce published **local** suppression effects;
2. predict when a wet line holds or breaches;
3. remain honest about uncertainty and scale; and
4. avoid claiming final-area containment that the evidence does not support?

This is an integration and evaluation question, not a request for a new
operational fire model.

## 2. What is already established

- The benchmark WS4 free-burn kernel is the reference.
- `native_growth` free burn matches it exactly on `2003_526`:
  - 5,325 ha;
  - 0 mismatched cells;
  - 0.0 min arrival-time difference.
- A 20-cell-wide static barrier reduces the benchmark area to 3,504 ha and
  leaves all 1,520 barrier cells unburned.
- A 154-target water ring delays **124/154** treated targets, mean delay
  **3.83 min**, maximum **34.92 min**, but leaves final area at 5,325 ha.
- Repeated passes do not cover new area; only unique target cells do.
- The current water ring is one cell thick and partial-cell, so it is not a
  closed barrier.

## 3. Claims we will and will not make

### Will claim

- the software couples the benchmark spread kernel with a documented
  suppression event layer;
- local arrival delay, hold and breach can be measured reproducibly;
- the evidence envelope and failure modes are explicit;
- the static barrier is a containment control.

### Will not claim

- operational containment prediction;
- validated water-drop effectiveness for `2003_526` or BC;
- equivalence between a water line and a permanent firebreak;
- final-area reduction as the primary success metric;
- field validation.

## 4. Hypotheses

Before running the main experiments, freeze these hypotheses.

- **H1 — parity:** the native free-burn kernel is numerically identical to the
  benchmark kernel. *Already accepted on `2003_526`.*
- **H2 — local effect:** cells that are wet when the fire arrives have a later
  arrival time than the paired dry cells.
- **H3 — hold:** a continuous wet segment with adequate depth and overlap holds
  for a finite interval consistent with the published hold range.
- **H4 — breach:** increasing fireline intensity or decreasing coverage
  increases breach probability.
- **H5 — endpoint:** final basin area is insensitive to local temporary
  suppression; area-at-time and local delay are the appropriate endpoints.

## 5. Study design

### 5.1 Reference and treatment

- Reference: WS4 benchmark kernel on the public fire.
- Treatment: a wet-cell field derived from drop geometry, depth, canopy
  penetration and decay.
- No global ROS or fuel multiplier.
- No tuning to the observed perimeter.

### 5.2 Units of analysis

- treated cell;
- target line segment;
- fixed-time area;
- paired dry/wet cell difference.

Not just whole-fire final area.

### 5.3 Controls

1. free burn;
2. static 20-cell barrier;
3. realistic one-cell water line;
4. continuous wet line with unique targets;
5. stacked wet line with overlapping drop windows;
6. synthetic control barrier labelled as such.

### 5.4 Metrics

For each treated cell:

- free arrival time;
- wet arrival time;
- arrival delay;
- whether the cell burned at all;
- per-cell combined depth at arrival;
- wet interval vs arrival.

For each line segment:

- length treated;
- fraction of segment with unique coverage;
- minimum/mean depth;
- hold duration;
- breach time and location.

For the fire:

- area at fixed times;
- final area only as a secondary endpoint;
- IoU/perimeter only as secondary context.

### 5.5 Evidence ranges

- ROS reduction: 0.5 ± 0.7 m/min.
- Intensity reduction: 72 ± 159 kW/m.
- Hold: 123 ± 117 s.
- High-water hold: 187 s.
- Indirect high-water hold: 243 s.
- Operational effective drop hold: 60 min.
- Required depth and breach criteria from McFayden.
- Theoretical water depth from Van Wagner and Taylor.

## 6. Experiments

### P182.0 — parity and numerical checks

- Free-burn parity: complete.
- Grid convergence: 100 m vs 50 m, with source data where possible.
- Snapshot interval sensitivity.
- Mass/coverage accounting.

### P182.1 — local effect

- paired dry/wet cells;
- delay distributions;
- area at 1,800, 2,000 and 2,200 min;
- confirm H2 and H5.

### P182.2 — line hold and breach

Positive control: a full-height 76-cell water line present from minute 600 and
held through the run reduced the benchmark from 5,325 to **3,504 ha**. The
native wet branch works when water is present before arrival and persists. See
[`p182-prepositioned.md`](p182-prepositioned.md).

Timing result: a full-height 76-cell water line with 60 or 600 min hold still
ends at 5,325 ha; a nominal 22,200 min hold reaches 5,254 ha. A static
non-burnable barrier from the start reaches 3,504 ha. The requirement is
sustained pre-arrival persistence, not width. See
[`p182-timing.md`](p182-timing.md).

Result: a one-cell, full-height, permanent wet band reduces the benchmark from
5,325 to **3,504 ha**; widths 1, 5, 10 and 20 all give the same area. The native
wet branch works. The earlier scheduled line was not closed for the full height
or duration. See [`p182-width.md`](p182-width.md).

Result: the 71-cell full-height water line delayed 71/71 targets under a full
wet-cell hold (mean 55.2 min), and 58/71 under the published 0.5 m/min
reduction (mean 13.8 min). Final area remained 5,325 ha. The 20-cell static
barrier reduced area to 3,504 ha. See
[`p182-line-hold.md`](p182-line-hold.md).

- continuous unique-target lines;
- varying width, depth, hold and intensity;
- measure held length and time-to-breach;
- compare against McFayden line-building tables.

### P182.3 — uncertainty

- sample the published ranges;
- report arrival-delay and hold envelopes;
- no single “best” parameter set.

### P182.4 — closed-barrier control

P184 breach forensics: the 12-aircraft, 3-stack line was wet at free-burn
arrival, but all 71 burnable cells breached after expiry. The effective hold was
about 18 minutes, not 60, because the stacked depth was only about 1.17 mm
against a 0.75 mm threshold. This is a persistence result, not a wet-branch
failure. See [`p184-breach.md`](p184-breach.md).

- static 20-cell barrier as positive control;
- confirm containment is possible only when the effect grid is closed;
- never describe the static control as water.

## 7. Falsification criteria

- If wet-at-arrival cells show no delay, the local effect model is wrong.
- If a closed static barrier does not reduce area, the comparison or kernel is
  wrong.
- If a continuous wet line with unique coverage and adequate depth never holds,
  the effect coupling is wrong.
- If results depend on final-area tuning, the experiment is invalid.

## 8. Data and reproducibility

- public fire, weather, fuel and terrain;
- published suppression parameters;
- fixed seeds;
- JSON artifacts for every run;
- unit tests for parity, mass balance, coverage and scheduling;
- no licensed PDFs or credentials in the repository.

## 9. Deliverables

1. parity report;
2. local-effect report;
3. line-hold/breach report;
4. uncertainty artifact;
5. public model card;
6. software methods note with explicit negative results.

## 10. Stop rules

Stop adding delivery scenarios when:

- free-burn parity is established;
- unique-target coverage is measured;
- local delay is observed;
- a closed barrier control is established.

Further aircraft counts, passes or stack counts are not informative without a
new effect-model hypothesis.

## 11. Publication framing

Working title:

> An open, evidence-bounded testbed for coupling fire growth and suppression
> operations: local effects, closed-barrier controls and failure modes.

The contribution is the integration, provenance and evaluation protocol — not
a claim of validated tactical suppression.
