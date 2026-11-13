# Proposed P179 — Process-based suppression and response

Status: P179.0 contract, P179.1 static proof, P179.2a schedule, P179.2b failure proofs, P179.3a native containment adapter, P179.4a dispatch prototype, P179.5a water requirements, P179.5b drop contours, P179.6 wet coupling, P179.7 aircraft cycles, P179.8 sub-cell raster, P179.9 wetness/ROS factor, P179.10 fine-grid experiment, P179.11 perimeter queries, P179.12 perimeter mission, P179.13 closed box, P179.14 receding horizon, P179.15 canopy penetration, P179.16 evidence parameters and P179.17 queue implemented. Not operational.

Five local PDFs were mined on 2026-11-13; see
[`martell-pdf-notes.md`](martell-pdf-notes.md). The 2015 control-time paper is
Morin et al., not Wheatley et al.

## Open containment issues

### P176 — burnable-basin stopping

The current model fills the connected burnable basin:

- median simulated area / burnable basin: **0.995**
- median observed area / burnable basin: **0.130**
- 8 of 12 cases fill at least 95% of the basin
- all 12 observed fires burn less than 50%

This is a **stopping/containment** problem, not a weather, fuel or terrain
calibration problem. A global ROS multiplier is not justified.

### P177 — containment contract

P177 added an optional boolean containment mask to `run_observed_case`:

- `False` = normal fuel
- `True` = contained/non-burnable
- absent = free-burn

This is a **static management boundary**. It has no time dimension, no
resources, no line production, no water or retardant, and no dispatch.

### P164.3 — validation remains paused

Burn-probability/occurrence validation still needs public data and a
pre-registered skill target. The suppression module must not become a way to
hide that missing evidence.

### P178 — free-burn ensemble

P178 perturbs weather for large free-burn cases. It is not a containment or
suppression ensemble.

## What is missing

There is currently no model of:

- initial attack (IA) crews or dispatch;
- crew travel, setup, line production, rest, safety or span of control;
- hose lays, pumps, water sources, friction loss or water supply;
- dozers, engines, water tenders or structure protection;
- helicopter bucketing, cycle time, water sources or drop patterns;
- air-tanker retardant/water drops, coverage level, evaporation or canopy
  penetration;
- containment lines that are built, held, breached or abandoned over time;
- mop-up, patrol, hotspotting or demobilization;
- command, prioritization, escalation or resource constraints;
- 3D suppression entities and task animation.

## P179.0 contract status

Implemented in this repository:

- `suppression/models.py` — resource, task, line, drop and effect contract.
- `suppression/scenario.schema.json` — generated JSON schema.
- `suppression/scenarios/2003-526-demo.json` — schematic six-resource scenario.
- `scripts/validate_suppression_scenario.py` — validates a scenario and prints effects.
- `scripts/export_suppression_schema.py` — regenerates the schema.
- `tests/test_suppression_models.py` — validation and effect-contract tests.
- `suppression/effects.py` — rasterizes effect events onto the fire grid.
- `suppression/scenarios/2003-526-proof.json` — diagnostic static line.
- `scripts/prove_suppression_2003_526.py` — P179.1 proof runner.
- `suppression/proofs/2003-526.json` — proof artifact.
- `docs/p179-1-proof.md` — method, results and limits.
- `suppression/temporal.py` — time-aware line/drop schedule.
- `suppression/scenarios/2003-526-temporal-proof.json` — 24-hour line build.
- `scripts/prove_temporal_suppression_2003_526.py` — chunked temporal proof.
- `suppression/proofs/2003-526-temporal.json` — temporal artifact.
- `tests/test_suppression_temporal.py` — schedule, decay and artifact tests.
- `docs/p179-2-proof.md` — temporal method, results and limits.
- `suppression/scenarios/2003-526-breach-proof.json` — held-then-breached line.
- `suppression/scenarios/2003-526-late-line-proof.json` — late-arrival line.
- `suppression/proofs/2003-526-breach.json` — breach artifact.
- `suppression/proofs/2003-526-late-line.json` — late-arrival artifact.
- `docs/p179-2b-failure-proofs.md` — failure results and limits.
- `suppression/native_growth.py` — native per-cell containment schedule adapter.
- `scripts/prove_native_suppression_2003_526.py` — native proof runner.
- `suppression/proofs/2003-526-native*.json` — native fast, slow, breach and late artifacts.
- `docs/p179-3-native-proof.md` — native method, results and limits.
- `suppression/dispatch.py` — deterministic travel, service and task-timing prototype.
- `scripts/dispatch_suppression_scenario.py` — dispatch CLI.
- `suppression/proofs/2003-526-dispatch.json` — demo dispatch artifact.
- `tests/test_dispatch.py` — travel, line service, utilization tests.
- `docs/p179-4-dispatch.md` — dispatch method, demo and limits.
- `suppression/water.py` — Van Wagner–Taylor water-depth equations.
- `scripts/water_requirement.py` — water-depth CLI.
- `tests/test_water.py` — Table 3 and scaling tests.
- `docs/p179-5-water.md` — equations, report check and limits.
- `suppression/drop.py` — drop contours, stacking, breach and CL-415 catalogue.
- `tests/test_drop.py` — contour, geometry, breach and catalogue tests.
- `docs/p179-5b-drop-contours.md` — drop-pattern method, catalogue and limits.
- `suppression/wet.py` — fractional wet-cell schedule and decay.
- `suppression/effects.py` — effect rasterization and coverage-fraction helper.
- `suppression/scenarios/2003-526-drop-proof.json` — stacked-drop proof.
- `suppression/proofs/2003-526-native-drop*.json` — free/wet artifacts.
- `tests/test_wet.py` — coverage, stacking, decay and artifact tests.
- `docs/p179-6-wet-coupling.md` — temporary wet coupling and resolution result.
- `suppression/aircraft.py` — CL-415 delivery-rate and cycle model.
- `suppression/scenarios/2003-526-drop-line-proof.json` — repeated-drop line.
- `suppression/proofs/2003-526-native-drop-line.json` — repeated-drop artifact.
- `tests/test_aircraft.py` — delivery-rate, interval and artifact tests.
- `docs/p179-7-aircraft-cycles.md` — cycle model and repeated-drop result.
- `suppression/subcell.py` — 10 m drop raster and fire-cell aggregation.
- `tests/test_subcell.py` — nested depth and aggregation tests.
- `docs/p179-8-subcell.md` — resolution problem, aggregation and limits.
- `suppression/wet.py` — wetness and local ROS factor.
- `suppression/proofs/2003-526-native-drop-line-subcell.json` — sub-cell wet-line artifact.
- `docs/p179-9-wetness-ros.md` — wetness/ROS method and limits.
- `scripts/prove_fine_grid_2003_526.py` — 50 m resolution experiment.
- `suppression/proofs/2003-526-fine-grid.json` — fine-grid artifact.
- `docs/p179-10-fine-grid.md` — 50 m result and placement lesson.
- `suppression/perimeter.py` — perimeter and leading-edge queries.
- `tests/test_perimeter.py` — perimeter-query tests.
- `docs/p179-11-perimeter-placement.md` — head-line experiments and limits.
- `suppression/mission.py` — perimeter targets across aircraft and passes.
- `scripts/build_perimeter_mission_2003_526.py` — mission scenario builder.
- `suppression/scenarios/2003-526-perimeter-5air-*.json` — 1/2-pass missions.
- `suppression/proofs/2003-526-native-perimeter-5air-*.json` — results.
- `docs/p179-12-perimeter-mission.md` — mission result and open-flank limit.
- `suppression/scenarios/2003-526-box-5air-1pass.json` — closed-box mission.
- `suppression/proofs/2003-526-native-box-5air-1pass.json` — closed-box result.
- `docs/p179-13-closed-box.md` — closed-box result and time-decay limit.
- `scripts/recede_horizon_2003_526.py` — 4-epoch receding-horizon experiment.
- `suppression/proofs/2003-526-receding-horizon.json` — result artifact.
- `docs/p179-14-receding-horizon.md` — method, negative result and limits.
- `suppression/wet.py` — applies canopy penetration to effective depth.
- `docs/p179-15-canopy-penetration.md` — parameter and limits.
- `suppression/evidence.py` — Wheatley/McFayden constants and hold helpers.
- `suppression/scenarios/2003-526-wheatley-evidence.json` — 123 s hold.
- `suppression/scenarios/2003-526-mcfayden-evidence.json` — 60 min hold.
- `docs/p179-16-evidence.md` — evidence, absolute ROS reduction and result.
- `suppression/queue.py` — non-preemptive resource queue.
- `tests/test_queue.py` — queue tests.
- `docs/p179-17-queue.md` — queue scope and limits.

Run:

```bash
python scripts/validate_suppression_scenario.py \
  suppression/scenarios/2003-526-demo.json --effects
pytest -q tests/
```

The contract enforces:

- unique resource/task/line/drop ids;
- known bases and resources;
- resource availability windows;
- no double-booked resource tasks;
- line construction inside its task window;
- drops inside their task window;
- drop volume against aircraft capacity;
- a time-bounded spatial effect event for every line and drop.

The effect event is the hand-off to the fire kernel. A consumer can rasterize
the line/drop geometry at its cell size, apply `fuel_removed`, `moisture`,
`coverage_l_m2`, `strength` and `decay_min`, and update the fire grid.

## P179.1 static effect-raster proof

The first proof applies one synthetic 100 m north–south line to the `2003_526`
grid and reruns the P177 kernel with that line as a containment mask.

- free burn: **5,325 ha**, IoU **0.096**
- static line: **3,113 ha**, IoU **0.134**
- observed: **520 ha**
- area reduction: **2,212 ha (41.5%)**
- line cells: **152**

This is a contract proof, not a calibrated suppression result. Centroid error
and orientation error get worse; the mask truncates the basin but does not
reproduce the observed perimeter. See [`p179-1-proof.md`](p179-1-proof.md).

## P179.2a time-aware effect schedule

P179.2a adds a schedule layer without changing the P177 kernel:

- lines grow by length between `constructed_start_min` and
  `constructed_end_min`;
- held lines remain, breached/abandoned lines stop containing;
- drops decay linearly after `end_min`;
- `effects_at(t)` rasterizes only the effects active at time `t`.

The diagnostic temporal run builds a synthetic 100 m line over 24 hours and
steps the fire in 60-minute chunks. It reduces area from **5,325 ha** to
**3,112 ha (41.6%)**, within **1 ha** of the static P179.1 line. The line is
complete before most growth, so this validates the schedule and chunk hand-off,
not a late-arrival failure case.

The chunked harness is an approximation: it seeds each chunk with all
previously burned cells and the P177 kernel has no native time-dependent mask.
Drop moisture is scheduled but not yet coupled to growth. See
[`p179-2-proof.md`](p179-2-proof.md).

## P179.2b failure proofs: breach and late arrival

Two diagnostic cases show that the schedule can represent failure:

- **Breach:** the line holds through minute 7,140, then is breached at 7,200.
  Final area is **5,323 ha**, within 2 ha of the 5,325 ha free burn. The line
  delays growth but does not contain the fire after the breach.
- **Late arrival:** the line is built from 18,000 to 19,440 minutes, after the
  fire has crossed the barrier. Final area is **5,323 ha**, a 2 ha reduction
  from free burn.

These are not effectiveness estimates; the 2 ha difference is a chunking
artifact. They do show that the same event stream can model held, breached and
late lines. See [`p179-2b-failure-proofs.md`](p179-2b-failure-proofs.md).

## P179.3a native time-dependent containment

The chunked P179.2 harness was replaced by a prototype native adapter in
`suppression/native_growth.py`. It checks a per-cell containment start/end
schedule during a single WS4 growth run and re-expands the burned front when a
containment event occurs.

Results on `2003_526`:

| Scenario | Native area | IoU | Change vs free |
| --- | ---: | ---: | ---: |
| Fast line, built 0–60 min | 3,113 ha | 0.134 | −41.5% |
| Slow line, built 0–1,440 min | 5,183 ha | 0.097 | −2.7% |
| Fast line, breached at 7,200 min | 5,325 ha | 0.096 | 0 |
| Late line, built 18,000–19,440 min | 5,325 ha | 0.096 | 0 |

The fast line matches the P179.1 static result exactly. The slow-build line
fails to contain because the fire crosses while it is being built; the chunked
harness overestimated that case by 2,071 ha. Breach and late arrival return to
free burn.

This is still diagnostic: drops are not coupled, and spotting, wind grids and
burning-condition gates are not supported. See
[`p179-3-native-proof.md`](p179-3-native-proof.md).

## P179.4a deterministic dispatch prototype

`suppression/dispatch.py` follows the scenario's existing resource assignments
and derives travel, readiness, service time and actual task windows. Line
service time comes from line length and `line_rate_m_h`; drop service time is
the requested task duration.

The schematic demo yields a 300.7 m crew line in 100.2 minutes and a 344.1 m
dozer line in 59.0 minutes. It also reports delay, late tasks, availability
warnings and utilization.

This is not an optimizer and not an aircraft-cycle model. Travel is straight
line; there are no roads, rest rules, refills or multi-incident queues. See
[`p179-4-dispatch.md`](p179-4-dispatch.md).

## P179.5a water-depth requirements

`suppression/water.py` implements the Van Wagner–Taylor heat-balance depths:

- quenching depth from fireline intensity;
- cooling depth from fuel load;
- wetting depth from intensity, radiant intensity and rate of spread;
- an application-efficiency divisor.

The module reproduces the report's Table 3 rounded values, including the
`I^(2/3)` scaling. At about 4,184 kW/m the theoretical cooling and wetting
depths are about **0.56–0.57 mm**, or **0.56–0.57 L/m²** when spread uniformly.

These are theoretical requirements, not measured drop effectiveness. Canopy
interception, stacking and breach remain for the next layer. See
[`p179-5-water.md`](p179-5-water.md).

## P179.5b drop contours

`suppression/drop.py` adds nested `DropContour` layers, `DropPattern`, effective
contour selection, stacking counts, elliptical geometry and the half-drop-width
breach test.

The small catalogue covers the CL-415, C-2, full-canopy cases in McFayden et
al. Tables 8-2/8-3: 130 × 50 m at 0.25 mm, 90 × 40 m at 0.5 mm, 70 × 30 m at
0.75 mm with two drops for 100 m, and breach at 3,200 kW/m and above.

This remains operational guidance encoded as geometry, not a calibrated drop
model. See [`p179-5b-drop-contours.md`](p179-5b-drop-contours.md).

## P179.6 temporary wet-cell coupling

`suppression/wet.py` converts each scenario drop into a fractional-coverage
`WetDrop` and builds a temporary wet-cell schedule. The native growth run now
consults that schedule and re-expands the front when water disappears.

The proof stacks three 1 mm, 100 × 50 m drops at the 600-minute front. At 100 m
resolution one drop covers 0.392 of one cell; three stacked drops reach
1.176 mm. The cell is temporarily non-ignitable, but the final area remains
**5,325 ha** because the fire bypasses a single cell.

This exposes a resolution limit: a real CL-415 drop is sub-cell on the current
100 m fire grid. The threshold is diagnostic, not a validated ROS model. See
[`p179-6-wet-coupling.md`](p179-6-wet-coupling.md).

## P179.7 aircraft cycles and repeated drops

`suppression/aircraft.py` encodes the CL-415 delivery table from McFayden et
al.: 12 drops/hour and 60,000 L/hour at 9 km, with a 5-minute cycle.

A diagnostic 21-drop line at 60 m spacing produces no final area change. At
100 m resolution each 100 × 50 m drop covers two cells with a fractional depth
below the wet threshold; the fire bypasses the discontinuous cells.

This is a delivery/placement result, not an effectiveness claim. See
[`p179-7-aircraft-cycles.md`](p179-7-aircraft-cycles.md).

## P179.8 sub-cell drop raster

`suppression/subcell.py` preserves drop contours at 10 m, then aggregates mean
depth, maximum depth and coverage fraction to the 100 m fire grid.

A 90 × 40 m, 0.5 mm contour covers about 0.28 ha. Its containing 100 m fire cell
receives a mean depth of about **0.14 mm** and a wetted fraction of about
**0.28**, not a full-cell wet flag.

This is a geometry fix, not a fire-kernel fix. See
[`p179-8-subcell.md`](p179-8-subcell.md).

## P179.9 wetness and local ROS factor

`WetSchedule` now turns active depth into `wetness = depth / required_depth`
and a diagnostic `ros_factor = 1 - wetness`. The native kernel stretches edge
travel time by that factor instead of using a binary wet mask.

The 21-drop line still leaves final area at **5,325 ha**. The fire bypasses the
small wetted cells. This confirms that sub-cell depth plus a scalar ROS factor
does not solve the 100 m grid/placement problem.

The ROS mapping is a placeholder, not a validated model. See
[`p179-9-wetness-ros.md`](p179-9-wetness-ros.md).

## P179.10 fine-grid experiment

The native kernel runs unchanged on a 50 m grid. At 50 m, a 21-drop line still
leaves final area at **5,325 ha**. The fire bypasses the line, so finer cells
alone do not solve the placement problem.

Nearest-neighbour upsampling does not add source information. The next useful
step is dropping against the active simulated perimeter rather than a fixed
line. See [`p179-10-fine-grid.md`](p179-10-fine-grid.md).

## P179.11 perimeter query and head-line tests

`suppression/perimeter.py` now extracts perimeter cells and leading-edge bands.
Two diagnostic head lines were tested: one helicopter with 21 drops and five
helicopters with 105 drops.

Both left final area at **5,325 ha**. The finite 2 km line had open flanks and
the fire bypassed its ends. More water on the same segment did not close the
flanks.

This is a placement result, not an effectiveness claim. See
[`p179-11-perimeter-placement.md`](p179-11-perimeter-placement.md).

## P179.12 perimeter-target mission

`suppression/mission.py` distributes targets across aircraft and passes.
`front_target_cells()` selects unburned cells adjacent to the active perimeter,
so drops land ahead of the front rather than on burned cells.

At minute 600 the free-burn front has **39 unburned front targets** and 106
perimeter cells. Five simulated CL-415s drop on all 39 targets in one pass; a
second pass repeats them.

Both final areas remain **5,325 ha**. The 39 targets do not form a closed
perimeter, and the fire bypasses the treated cells. This is an open-flank
mission, not a containment test. See
[`p179-12-perimeter-mission.md`](p179-12-perimeter-mission.md).

## P179.13 closed-box mission

A closed rectangle with a 300 m margin, 100 m drop spacing and 5 aircraft
produced 119 drops. Final area remained **5,325 ha**.

Closing the flanks is necessary but not sufficient. The water decays before the
fire reaches the later perimeter, so a one-pass finite mission is bypassed. See
[`p179-13-closed-box.md`](p179-13-closed-box.md).

## P179.14 receding-horizon mission

A four-epoch receding-horizon experiment re-reads the front at 600, 900, 1,200
and 1,500 minutes, builds a five-aircraft perimeter mission at each epoch, and
reruns the native growth with all missions.

It uses **266 drops** across four missions and still ends at **5,325 ha**.
Re-planning alone does not solve the finite-duration, placement and resolution
problems. See [`p179-14-receding-horizon.md`](p179-14-receding-horizon.md).

## P179.15 canopy penetration

The `Drop.canopy_penetration` field is now applied to the wet-cell depth. A
value of 0.5 halves the effective water depth and scales the wetness/ROS factor
accordingly.

It is still an input, not a measured interception model. See
[`p179-15-canopy-penetration.md`](p179-15-canopy-penetration.md).

## P179.16 evidence parameters

`suppression/evidence.py` records the Wheatley 2024 experimental values:
0.5 m/min mean ROS reduction, 72 kW/m intensity reduction, 123 s mean hold,
+64 s with high water, and +120 s for indirect high water. It also records the
McFayden 60-minute operational hold and the 10,000 kW/m discussion.

The native kernel can now apply an **absolute** 0.5 m/min ROS reduction when a
target is fully wet, rather than the previous arbitrary `1 - wetness` factor.

Both the 123 s and 60 min scenarios still finish at **5,325 ha**. A finite
21-drop line remains geometrically incomplete; the evidence changes the effect
calculation, not the placement problem. See
[`p179-16-evidence.md`](p179-16-evidence.md).

## P179.17 deterministic queue

`suppression/queue.py` is a non-preemptive queue for requests and available
servers. It orders by priority and arrival, assigns the earliest feasible
server, reports wait/utilization and leaves infeasible requests unserved.

It is a scheduling primitive for the eventual IA/aircraft dispatch layer. See
[`p179-17-queue.md`](p179-17-queue.md).

## Adjacent Canadian planning layers

Four open-access Canadian studies provide adjacent capability, not P179
suppression physics:

- **FireLossRate** — structure loss from fireline intensity and distance from
  the fire edge;
- **Brunet et al. 2026** — maximal-covering helitack base deployment;
- **Moreno et al. 2026** — evacuation network design with traffic congestion;
- **Nicoletta et al. 2026** — strategic fuel-break placement.

These should stay separate from the suppression effect kernel. Shared inputs
are fireline intensity, fire perimeter and the road/base network. See
[`ws4-canadian-wildfire-notes.md`](ws4-canadian-wildfire-notes.md).

## Evidence base: Martell and collaborators

David Martell's work gives us a mature operations-research spine, not a single
fire-spread equation. The useful ideas are:

### 1. Four scales of suppression effectiveness

The current literature, synthesized in Wheatley's 2024 thesis, separates:

- **flame scale** — water delivery, quenching, fuel cooling;
- **fireline scale** — line production, holding, drop placement, re-ignition;
- **incident scale** — IA success, control time, resources, dispatch;
- **landscape scale** — annual area burned, resource levels, season outcomes.

The module should expose the same separation in its data model. A visual water
drop is not an incident-scale containment result.

### 2. Initial-attack system simulation

Martell et al. (1984) built a simulation model of Ontario IA fires and
resources. Podur and Martell (2007) extended this into a discrete-event model
of large-fire growth and suppression with three components:

1. a logistic model for the probability that a fire escapes IA and exceeds
   100 ha;
2. a weather- and vegetation-driven large-fire growth model;
3. a simulation of suppression by firefighters and aircraft.

They used it to compare area burned under mild/severe weather and different
resource levels. Suppression reduced area burned, but severe weather limited
effectiveness and produced diminishing returns.

**Implication:** build the response engine as a **discrete-event simulation**
with a fast escape/containment probability layer, not as a monolithic 3D game.

### 3. IA success and control time are statistical, not deterministic

Wheatley et al. (2022) modelled IA success with logistic models. The strongest
covariates included:

- fire size when IA begins;
- observed fire rank / behaviour;
- ignition cause;
- for air attack, suppression effort variables.

The IA model reached an ROC area of about **0.84**; the full model about
**0.85**. A fire at rank 3 and 0.1 ha had a high chance of containment; at 5 ha
the probability dropped sharply.

Survival analysis of control time (Morin et al. 2015) found significant
covariates including fire size at IA, FFMC, ISI and response time.

**Implication:** the first containment model should predict:

- probability of IA success;
- a distribution of control time;
- not a single “contained at minute N” value.

### 4. Crew productivity and effectiveness

Hirsch, Corey and Martell (1998) used expert judgment to encode IA crew
effectiveness. Related work on crew productivity estimated line-construction
time as a function of fire intensity; the thesis notes that a standard
four-person crew producing 610 m of line was perceived to take about 13% longer
at moderate intensity (1,500 kW/m) than at low intensity (500 kW/m).

**Implication:** line production must depend on:

- crew type and size;
- terrain and fuel;
- fireline intensity;
- travel/setup time;
- rest and safety constraints.

Do not model a crew as a constant metres-per-hour machine.

### 5. Airtanker dispatch and effectiveness

Wheatley et al. (2022) used hurdle models for airtanker dispatch. The most
influential covariates were FWI, fuel volatility, observed rate of spread,
fire size at IA and ignition cause. The IA-stage model outperformed the
fire-report model. This is a **dispatch decision model**, not a drop-physics
model.

The CL-415 analysis found:

- ~6,000 L per drop;
- roughly 11 drops/hour in Ontario's water-rich environment;
- increased drop count and stacking increased the probability of reducing
  fire rank;
- even rank 4–5 fires showed potential for reduction to rank 1–2;
- the common 4,000 kW/m upper limit may be conservative; the thesis suggests
  ~10,000 kW/m may be a more realistic upper bound for C-2 fuels.

The “suppression effort paradox” matters: more water delivered was associated
with **lower** IA success in observational models because harder fires receive
more effort. A naive model will get the causal sign wrong.

**Implication:** use a structural model with fire difficulty as a latent
variable, or condition on observed fire behaviour. Do not regress success on
water volume and call it effectiveness.

### 6. Basing, queueing and deployment

- Bookbinder and Martell (1979) modelled helicopter allocation as a
  time-dependent queue.
- MacLellan and Martell (1996) optimized airtanker home basing.
- Later GPS-tracking work modelled airtankers as spatial queueing servers with
  travel, drop and service times.
- The same logic can be extended to helicopters, trucks and heavy equipment.

**Implication:** resource deployment should be a **queueing/logistics layer**:
travel time, service time, water-source distance, turn-around, availability
and competing incidents.

### 7. Water delivery and fireline hold

Wheatley's field experiments found:

- suppression reduced rate of spread by about **0.5 m/min** on average;
- fireline intensity dropped by about **70 kW/m**;
- average suppression-induced hold was about **123 seconds**;
- high water treatment added about **64 seconds** of hold, mainly for indirect
  suppression;
- some treatments extinguished the fire; others held for zero seconds.

**Implication:** water/retardant effects are **temporary and local**. The
module needs an effect-decay and re-ignition model, not a permanent “wet” flag.

### 8. DSS lessons

Martell's 2011 reflections on Ontario DSS projects are directly relevant:

- work on a problem senior managers consider important;
- embed with field staff and observe real decision-making;
- expect multi-year development;
- design for maintenance and junior staff, not just the champion;
- do not let political pressure turn expensive resources into a substitute
  for effectiveness.

This is a strong argument for a **small, auditable scenario module** before a
large game-like simulator.

## Design principle

Do **not** build the 3D game layer first. Build a **suppression effect contract**
that the fire model can consume.

The existing fire model is grid/arrival-based. Suppression should modify a small
set of fields:

- `burnable`
- `fuel_remaining`
- `fuel_moisture`
- `arrival_time`
- `heat_intensity`
- `suppression_effect` (line, water, retardant, mop-up)

The 3D layer then visualizes the same event stream. It must not invent fire
behaviour that the simulation did not produce.

## Proposed architecture

### 1. Scenario contract

Inputs:

- fire and weather case;
- containment objective;
- resources and arrival times;
- water sources, helipads, drop bases;
- hose/pump inventories;
- command priorities;
- safety and visibility constraints.

### 2. Discrete-event response engine

Entities:

- incident command;
- IA crew;
- ground crew;
- engine;
- dozer;
- helicopter;
- air tanker;
- water tender;
- pump;
- hose lay;
- water source;
- drop;
- containment line segment;
- structure protection group.

Tasks:

- mobilize / travel;
- assess;
- anchor;
- construct line;
- lay hose;
- set pump;
- drop water/retardant;
- patrol;
- mop up;
- demobilize;
- reassign.

### 3. Fire-effect interface

Ground line:

- remove fuel along a segment;
- increase fuel moisture in a wet line;
- line production rate by crew, fuel, slope, terrain and obstructions;
- holding probability and breach;
- burnout support.

Water/retardant:

- drop footprint and coverage level;
- water vs long-term retardant;
- evaporation and canopy penetration;
- fuel-moisture increase;
- temporary ROS reduction or local extinction;
- re-ignition after effectiveness decays.

Hose/pump:

- pump capacity and pressure;
- friction loss with hose length and elevation;
- water-source reliability;
- setup and lay time;
- coverage along the line.

The first version should be **empirical and scenario-based**, not a coupled
fire–atmosphere–suppression CFD model.

### 4. 3D visual layer

Reuse the current Three.js scene and timeline. Add:

- low-poly helicopters, air tankers, engines, dozers and tenders;
- rotor and flight animation;
- bucket/retardant drop plumes and ground coverage;
- hose lines, pumps and water sources;
- crew markers and task labels;
- containment line construction and breach;
- mop-up and patrol states;
- resource panel, task log and playback controls;
- foveated LOD for vehicles and crews.

Visual labels must distinguish:

- actual fire behaviour from the simulation;
- suppression effect from visual effects;
- scenario assumptions from validated operations.

## Proposed phase breakdown

### P179.0 — contract and ontology

- Resource/task/drop/line schemas.
- Fire-effect field contract.
- Scenario JSON.
- No 3D assets yet.

### P179.1 — containment effect proof

- Status: static line proof on `2003_526`; drop rasterization exists but is not
  yet coupled to growth.
- Line and drop footprints modify the fire grid.
- Compare free-burn vs containment mask vs dynamic suppression.
- One benchmark fire.
- No resource optimization.

### P179.2 — ground response

- Status: time-aware line/drop schedule, failure proofs, native containment
  adapter and deterministic dispatch prototype implemented
  (P179.2a/P179.2b/P179.3a/P179.4a); queueing, rest rules and aircraft cycles
  pending.
- IA crew, engine, dozer, pump and hose.
- Travel, setup, line production, water supply, holding/breach.
- Discrete-event playback.

### P179.3 — aerial response

- Helicopter bucket cycles and air-tanker drops.
- Coverage level, drop pattern, wind, visibility and turn-around time.
- Temporary effect and re-ignition.

### P179.4 — command and dispatch

- Initial attack, escalation, prioritization, span of control and constraints.
- Scenario inputs, not a fitted dispatch policy.

### P179.5 — 3D suppression scene

- Unit models, routes, drops, hose/pump assets, line construction and status.
- Side-by-side free-burn vs suppression playback.
- Reuse the current viewer, not a second game engine.

### P179.6 — validation and limits

- Public data only until a partner supplies dispatch/line/drop records.
- Report resource productivity, water/retardant use, containment time and area.
- Label as a scenario simulator, not an operational prediction.
- No merge without maintainer approval.

## First prototype

Use **2003_526** because it is compact and already has a clear
observed-vs-free-burn divergence.

Scripted scenario:

- one IA crew;
- one engine;
- one dozer;
- one pump and hose lay;
- two helicopters;
- one air tanker;
- one water source;
- a single containment objective.

Outputs:

- time to line construction;
- line held/breached;
- area contained;
- water and retardant used;
- re-ignition events;
- free-burn vs suppression area;
- 3D playback of every task and drop.

## Validation and data needs

Potentially public:

- fire perimeters and weather;
- terrain, fuel and water sources;
- aircraft types and published performance;
- literature line-production and coverage rates.

Usually not public:

- dispatch logs;
- crew line-production records;
- actual drop logs and coverage;
- containment times and line locations;
- safety and operational constraints.

Without partner data, the module is an **illustrative scenario simulator**.
It must not be described as validated suppression prediction.

## Key decisions needed

1. Is the goal training/communication, scenario planning, or operational
   decision support?
2. Which fire and landscape is the first case?
3. Which resources are in scope for v1?
4. Do we have a BCWS/CFS partner for dispatch, line and drop validation?
5. Is the first deliverable a 2D event playback or the full 3D scene?
6. What is explicitly out of scope: structure loss, evacuation, injury,
   suppression effectiveness claims?

## Recommended modelling stack

### Fast path

Use this for the first prototype:

- fire growth from the existing WS4/FBP kernel;
- a logistic IA-success probability calibrated to published covariates;
- a control-time distribution (survival model) conditional on fire size,
  fire rank, FFMI/ISI, response time and resource type;
- a queueing/logistics model for crews and aircraft;
- local fireline/drop effect fields with decay and re-ignition.

### Detailed path

Use this once the fast path is stable:

- discrete-event resource agents;
- spatial line construction and hose/pump networks;
- aircraft flight cycles and drop footprints;
- command and dispatch policies;
- 3D playback of the same event stream.

### Causal guardrails

- Never infer effectiveness from total suppression effort alone.
- Model fire difficulty explicitly.
- Separate *decision to suppress* from *effect of suppression*.
- Separate *perimeter held* from *fire extinguished*.
- Report uncertainty and data provenance.
- Do not use the module to retroactively “fix” a failed benchmark.

## References and sources to read

- Martell, D.L. 1982. A review of operational research studies in forest fire
  management. *Canadian Journal of Forest Research* 12: 119–140.
- Bookbinder, J.H., and Martell, D.L. 1979. Time-dependent queueing approach to
  helicopter allocation for forest fire initial attack. *INFOR*.
- Martell, D.L., Drysdale, R.J., Doan, G.E., and Boychuk, D. 1984. An
  evaluation of forest fire initial attack resources. *Interfaces* 14(5): 20–32.
- MacLellan, J.I., and Martell, D.L. 1996. Basing airtankers for forest fire
  control in Ontario. *Operations Research* 44(5): 677–686.
- Hirsch, K.G., Corey, P.N., and Martell, D.L. 1998. Using expert judgment to
  model initial attack fire crew effectiveness. *Forest Science* 44(4):
  539–549.
- Hirsch, K.G., and Martell, D.L. 1996. A review of initial attack fire crew
  productivity and effectiveness. *International Journal of Wildland Fire*
  6: 199–215.
- Podur, J.J., and Martell, D.L. 2007. A simulation model of the growth and
  suppression of large forest fires in Ontario. *International Journal of
  Wildland Fire* 16: 285–294.
- Martell, D.L. 2011. The development and implementation of forest fire
  management decision support systems in Ontario: personal reflections.
  *Mathematical and Computational Forestry & Natural-Resource Sciences* 3(1):
  18–26.
- Martell, D.L. 2015. A review of recent forest and wildland fire management
  decision support systems research. *Current Forestry Reports* 1: 128–137.
- Wheatley, M., Wotton, B.M., Woolford, D.G., Martell, D.L., and Johnston, J.M.
  2022. Modelling decisions concerning the dispatch of airtankers for initial
  attack on forest fires in Ontario. *Canadian Journal of Forest Research*.
- Wheatley, M., et al. 2022. Modelling initial attack success on forest fires
  suppressed by air attack in Ontario. *International Journal of Wildland
  Fire*.
- Morin, A.A., Albert-Green, A., Woolford, D.G., and Martell, D.L. 2015. The
  use of survival analysis methods to model the control time of forest fires
  in Ontario. *International Journal of Wildland Fire*.
  DOI: `10.1071/WF14158`.
- Wheatley, M.J. 2024. *Forest Fire Suppression Effectiveness in the Canadian
  Boreal Forest*. PhD thesis, University of Toronto. Contains the detailed
  CL-415 drop, fire-rank, water-delivery and IR-hold results.
- McFayden, C.B., Wotton, B.M., Robinson, J.W., et al. 2023. *Reference Guide
  to the Drop Effectiveness of Skimmer and Rotary Wing Airtankers.* Canadian
  Forest Service Information Report GLC-X-35.
- Van Wagner, C.E., and Taylor, S.W. 2022. *Theoretical Amounts of Water to
  Put Out Forest Fires.* Canadian Forest Service Information Report BC-X-458.

## Recommendation

Start with **P179.0/P179.1 only**: a containment-effect contract and a
line/drop proof on one fire. Do not start with helicopter models or a game
loop. The visuals should follow a suppression model that can be inspected,
tested and labelled honestly.

The Martell evidence supports a **hybrid model**:

1. fast statistical IA/containment layer;
2. queueing/logistics resource layer;
3. spatial fireline/drop effect layer;
4. 3D event playback last.

That order preserves the operational-research value while still giving us the
3D suppression scene the user wants.
