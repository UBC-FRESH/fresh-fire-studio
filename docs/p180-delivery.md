# P180.3 delivery sweep

Status: mass and cycle-time sweep. It does not rerun fire growth for each case.

## Question

Can the three-aircraft cycle mission actually deliver the water required for
the selected 5.3 km head segment?

Requirement used: **0.75 mm** over a 50 m-wide strip, about **199,630 L**.

## Results

Three aircraft, current lake, 21 targets per pass:

| Passes | Sorties | Delivered | Line-mean depth | Coverage | Deficit | Elapsed |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 21 | 126,000 L | 0.47 mm | 39% | 73,630 L | 30.5 min |
| 2 | 42 | 252,000 L | 0.95 mm | 79% | 0 | 61.0 min |
| 3 | 63 | 378,000 L | 1.42 mm | 100% | 0 | 91.5 min |

The two-pass case closes the **nominal mass deficit**. It does not establish
fire containment: the native growth run still ends at **5,325 ha**. Three and
four passes also remain at **5,325 ha**. The mass constraint is satisfied, but
the placement, grid and effect limitations remain. See
[`p180-saturation.md`](p180-saturation.md).

## Aircraft count

More aircraft shorten elapsed time, not total water delivered for a fixed
number of passes. The sweep includes 1, 3 and 5 aircraft and three lake
positions; all rows are in
`suppression/proofs/2003-526-delivery-sweep.json`.

## Interpretation

The first-pass mission is water-limited as well as placement-limited. A
two-pass mission is the minimum mass-only correction for the stated depth and
segment. Whether that is operationally sufficient is a separate question.

## Limits

- 50 m strip width and 100 × 50 m drops are assumptions.
- Coverage assumes no overlap and perfect application.
- Required depth is a selected nominal value, not a measured line requirement.
- Lake positions are schematic.
- No fire-growth rerun for the two-pass case yet.
