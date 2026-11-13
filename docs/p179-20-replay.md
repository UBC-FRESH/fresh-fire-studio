# P179.20 diagnostic suppression replay

Status: public-facing diagnostic replay. It is not a fire-effect prediction.

## Route

`/suppression/` (and `/suppression.html`)

Static export: `suppression/index.html` and `suppression.html`.

## What it shows

- 21 drop cycles across three independent aircraft on 21 selected head targets, including scoop, climb, cruise, descent, drop, turn and return;
- 126,000 L total tank capacity, mean cycle 4.25 min;
- mission timeline and active-drop count;
- three stable aircraft markers that follow phase-based lake-to-fire cycles;
- a lake, fire line and 3D flight paths;
- automatic playback from the 600-minute mission start;
- a focused default camera with `Focus mission` and `Overview` controls;
- an evidence-results panel;
- a **Realistic / Control** mode switch;
- an optional **synthetic 20-cell control barrier**;
- an optional free-burn model extent overlay;
- the observed final extent in teal;
- a 1 km grid and north-up compass;
- a permanent banner: **diagnostic mission geometry, not an operational
  prediction**;
- an `+ Ask` assistant drawer for evidence and model-limit questions;
- an in-page **Model card** panel covering evidence, results, synthetic inputs
  and limits;
- a downloadable two-page case study PDF.

The results panel reports:

- cycle logistics: 3 aircraft, 21 sorties, mean 4.25 min, 126,000 L, 247,731 L/h;
- water balance: 0.47 mm line-mean, 39% coverage, 13 additional sorties needed;

- observed final extent: 520 ha;
- realistic cycle mission: 5,325 ha, 0% containment, placement-limited;
- synthetic control barrier: 3,574.7 ha, 3,570–3,575 ha, ROS correlation
  −0.78, effect model responds but is not operational.

Data: `portal/static/suppression-mission.json`.

Download links on the page:

- `static/suppression-mission.json`
- `static/suppression-evidence-ensemble.json`
- `static/suppression-evidence-control.json`
- public model card in the GitHub repository

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
