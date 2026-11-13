# P179.20 diagnostic suppression replay

Status: public-facing diagnostic replay. It is not a fire-effect prediction.

## Route

`/suppression/` (and `/suppression.html`)

Static export: `suppression/index.html` and `suppression.html`.

## What it shows

- 21 CL-415-style drop markers from the fixed 2003_526 drop-line scenario;
- mission timeline and active-drop count;
- a simple aircraft marker that moves toward the latest active drop;
- an evidence-results panel;
- a **Realistic / Control** mode switch;
- an optional **synthetic 20-cell control barrier**;
- an optional free-burn model extent overlay;
- a 1 km grid and north-up compass;
- a permanent banner: **diagnostic mission geometry, not an operational
  prediction**.

The results panel reports:

- realistic 21-drop mission: 5,325 ha, 0% containment, placement-limited;
- synthetic control barrier: 3,574.7 ha, 3,570–3,575 ha, ROS correlation
  −0.78, effect model responds but is not operational.

Data: `portal/static/suppression-mission.json`.

## What it does not show

- no observed or simulated fire perimeter;
- no validated water effect;
- no terrain elevation;
- no containment result;
- no operational dispatch recommendation.

The page exists to make the mission geometry and timing legible without
overstating the model.

## Why a separate page

The six benchmark scenes are observed-extent replays with synthetic tree layers.
Mixing a diagnostic suppression mission into those scenes would imply a level of
validation the suppression model does not have.

This page is deliberately separate and labelled.

## Limits

- The drop markers are points, not sub-cell water-depth contours.
- The control barrier is synthetic and permanent.
- The aircraft motion is illustrative.
- No smoke, fire, hose, crew or pump animation yet.
- The page does not consume a live simulation result.

## Next

A later replay can load a validated event stream with fire perimeter snapshots
and a clearly labelled effect envelope. That should happen only after the
placement/effect control question is settled.
