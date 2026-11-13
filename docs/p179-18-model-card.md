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

A scenario where the wet line actually intersects the active front with
sufficient depth and overlap. If the ensemble still has zero variance there,
the effect model itself is the limiting factor. That is the next diagnostic to
run, not another field campaign.

## Licensing and provenance

The model code is public. Local PDFs are not committed. The evidence citations
and limits are in `docs/martell-pdf-notes.md`, `docs/p179-16-evidence.md`, and
the suppression plan.
