# P179.18 suppression model card

Status: evidence-bounded diagnostic. Not an operational model.

## What this is

A research instrument for asking how published suppression evidence and its
uncertainty affect fire outcomes in a public benchmark scene.

It is not a calibrated prediction of `2003_526`, BC, or any real suppression
operation.

## Evidence inputs

- Wheatley 2024 experimental burns: ROS reduction **0.5 ± 0.7 m/min**, intensity
  reduction **72 ± 159 kW/m**, hold **123 ± 117 s**, high-water hold **187 s**,
  indirect high-water hold **243 s**.
- McFayden et al. 2023: **60 min** effective aerial hold; drop-depth contours
  and breach criteria; operational intensity discussion up to **10,000 kW/m**.
- Van Wagner & Taylor 2022: theoretical water depth from fireline intensity,
  fuel load and wetting.
- Open case inputs: CFSDS `2003_526`, Open-Meteo/FireSTARR weather, public fuel
  and terrain.

## What was implemented

`suppression/uncertainty.py`:

- bounded `EvidenceRange` distributions;
- reproducible sampling;
- `EvidenceSample`;
- scenario projection onto drop depth, hold and canopy penetration;
- ensemble summaries and parameter correlations.

`scripts/evidence_ensemble_2003_526.py`:

- runs the native growth kernel for each sample;
- uses the sampled absolute ROS reduction;
- aggregates final area, percentiles and containment probability.

## Current ensemble result

32 samples on the 21-drop line scenario:

- every sample ended at **5,325 ha**;
- containment probability: **0**;
- area standard deviation: **0**;
- no parameter correlation.

That looks uninformative, but it is a real result: the drop line does not
intersect the active front strongly enough for any evidence sample to change
the final basin-filling outcome. The geometry dominates the effect parameters.

## Persistence follow-up (P183–P185)

The evidence ensemble above tests the 21-drop head line. A separate diagnostic
line was built across the full 76-cell height of the `2003_526` grid:

- 12 aircraft, 3 stacked drops per cell, 228 sorties;
- all 71 burnable line cells were wet at their free-burn arrival;
- all 71 cells later breached, every one after the water expired;
- the effective hold was about **17–18 minutes**, not 60;
- final area stayed at **5,325 ha**, the free-burn result.

The breach was a persistence failure, not a wet-branch failure. A perfect
full-cell re-wetting test then showed:

- 15-minute re-wetting at the current **1.047 mm** depth holds at **3,504 ha**;
- an 18-minute interval fails;
- a 30-minute interval needs at least **1.5 mm**; 1.5 mm gives a
  **54-aircraft** lower bound with no duration margin;
- 2.0 mm at 30 minutes gives **65 aircraft** with about 7.5 minutes of margin;
- the successful tested cases require **760–912 sorties/h**, versus about
  **169 sorties/h** for 12 aircraft.

These are perfect-dispatch lower bounds, not an operational plan. They assume
full-cell re-wetting, a 4.25-minute cycle, 6,000 L per sortie and no supply,
weather or maintenance limits. See [`p185-rewetting.md`](p185-rewetting.md).

## Intended use

- compare model assumptions;
- expose sensitivity, or the lack of it;
- generate diagnostic scenario envelopes;
- support software and methods research;
- communicate uncertainty to collaborators.

## Prohibited use

- operational dispatch;
- evacuation or structure-protection decisions;
- public claims that suppression is ineffective;
- claims of field validation;
- tuning to a single fire and calling it validation.

## Known failure modes

- The 100 m fire grid cannot resolve a real 50–100 m drop footprint.
- The drop line is not dynamically placed on the strongest front.
- The native fire model overpredicts the free burn on `2003_526`.
- Published means are from low-intensity surface experiments.
- The wetness/ROS mapping is only as good as those means.
- The ensemble fixes geometry, so it cannot test placement uncertainty.
- Water depth and contractor delivery rates vary widely.

## Reproduce

```bash
python scripts/evidence_ensemble_2003_526.py \
  --ws4-root ../.opencode/tmp/opencode/ws4-p177 \
  --samples 32
pytest -q tests/
```

Artifact: `suppression/proofs/2003-526-evidence-ensemble.json`.

## What would change the conclusion

A realistic dispatch simulation of the 30-minute, 2.0 mm case with about 65
aircraft and explicit water-supply, weather and maintenance limits. If that
lower-bound schedule still holds the line, the question becomes logistics. If
it fails, supply and dispatch dominate.

A different tactic — larger tankers, retardant, or a permanent fuel break —
would be a separate comparison. Another parameter ensemble or open-loop fleet
sweep would not change this conclusion.

## Licensing and provenance

The model code is public. Local PDFs are not committed. The evidence citations
and limits are in `docs/martell-pdf-notes.md`, `docs/p179-16-evidence.md`, and
the suppression plan.
