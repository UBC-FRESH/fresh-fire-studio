# Proposed P179 — Process-based suppression and response

Status: proposal only. Do not merge or present as operational capability.

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

Run:

```bash
python scripts/validate_suppression_scenario.py   suppression/scenarios/2003-526-demo.json --effects
pytest -q tests/test_suppression_models.py
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

Survival analysis of control time (Wheatley et al. 2015) found significant
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

- Line and drop footprints modify the fire grid.
- Compare free-burn vs containment mask vs dynamic suppression.
- One benchmark fire.
- No resource optimization.

### P179.2 — ground response

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
- Wheatley, M., et al. 2015. The use of survival analysis methods to model the
  control time of forest fires in Ontario. *International Journal of Wildland
  Fire*.
- Wheatley, M.J. 2024. *Forest Fire Suppression Effectiveness in the Canadian
  Boreal Forest*. PhD thesis, University of Toronto. Contains the detailed
  CL-415 drop, fire-rank, water-delivery and IR-hold results.
- McFayden, C., et al. 2023. Airtanker drop energetics.
- Van Wagner, C.E., and Taylor, S.W. 2022. Water-depth models for suppression.

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
