# Suppression scenario laboratory: case study and failure modes

Status: public methods note. Not an operational fire-suppression model.

## 1. What this is

FRESH Fire Studio is a public 3D benchmark-fire portal from the UBC FRESH Lab.
The suppression add-on asks a narrow software and methods question:

> Given published suppression evidence and a public fire benchmark, what can an
> open, auditable scenario model show, and where does it fail?

It is not a forecast of what a real suppression operation would achieve.

## 2. Evidence base

We use published evidence rather than a bespoke field campaign.

**Wheatley (2024), Chapter 5** — IR-monitored experimental burns:

- mean ROS reduction: **0.5 ± 0.7 m/min**
- mean fireline-intensity reduction: **72 ± 159 kW/m**
- mean suppression hold: **123 ± 117 s**
- high-water hold: **187 s**
- indirect high-water hold: **243 s**
- direct water depths: **1.4–2.3 mm**
- indirect water depths: **0.7–1.1 mm**

**McFayden et al. (2023)** — aerial drop guide:

- effective aerial drop hold: **60 min**
- nested water-depth contours, stacking and breach criteria
- operational intensity discussion up to **10,000 kW/m**

**Van Wagner & Taylor (2022)** — water requirements:

- theoretical depth for quenching, cooling and wetting as a function of
  fireline intensity, fuel load and rate of spread.

The benchmark is CFSDS `2003_526`: 520 ha observed, 5,325 ha free-burn model,
public fuel/terrain, Open-Meteo/FireSTARR reanalysis weather.

## 3. What we built

- a native time-dependent containment adapter;
- an evidence-bounded uncertainty sampler;
- a 32-member ensemble;
- a realistic 21-drop mission;
- a synthetic control barrier;
- dispatch, queueing, sub-cell drop geometry and water-depth modules;
- a public diagnostic replay at `/suppression/`.

## 4. Results

| Case | Area | Meaning |
| --- | ---: | --- |
| Observed final extent | **520 ha** | public CFSDS perimeter |
| Free burn | **5,325 ha** | model basin-filling result |
| Realistic 21-drop line | **5,325 ha** | all 32 evidence samples; 0% containment |
| Synthetic control barrier | **3,574.7 ha** | 3,570–3,575 ha; ROS correlation −0.78 |

The realistic mission is **placement-limited**. The control barrier is a
deliberately permanent, 20-cell-wide synthetic wet band. It is not an
operational plan. Its purpose is to test whether the evidence branch responds
when the geometry is sufficient.

It does: the control reduces area by about 1,750 ha and the sampled absolute ROS
reduction has a strong negative correlation with final area.

## 5. Failure modes

1. **Placement** — finite lines leave open flanks; the fire bypasses them.
2. **Resolution** — a 100 m cell cannot resolve a 50–100 m drop footprint.
3. **Transferability** — the experiments are low-intensity surface fires, not
   `2003_526`.
4. **Effect mapping** — the water-depth/ROS mapping is diagnostic.
5. **Free-burn bias** — the model burns 10× the observed area before suppression.
6. **Time** — water decays; a single mission is not a sustained response.

## 6. What would change the conclusion

- a realistic wet barrier that intersects the active front continuously;
- a validated water-depth-to-fuel-moisture/ROS relationship;
- a finer fire grid with source fuel data;
- an operational partner with a specific decision and data-sharing agreement.

A field campaign is not a prerequisite for publishing the software or the
failure-mode analysis. It is a prerequisite for an operational claim.

## 7. Reproduce

- replay: <https://ubc-fresh.github.io/fresh-fire-studio/suppression/>
- model card: `docs/p179-18-model-card.md`
- evidence notes: `docs/martell-pdf-notes.md`
- ensemble: `suppression/proofs/2003-526-evidence-ensemble.json`
- control: `suppression/proofs/2003-526-evidence-control.json`

No operational use. No regional calibration. No claim of measured suppression
effectiveness for `2003_526`.
