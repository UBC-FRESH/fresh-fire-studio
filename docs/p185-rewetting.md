# P185 perfect re-wetting and fleet lower bound

Status: diagnostic persistence envelope, not an operational plan.

The 12-aircraft line was correctly wet at arrival but held for only about 17–18
minutes. P185 replaces the aircraft schedule with a perfect full-cell periodic
application to isolate the required re-wetting interval and depth.

## Reference application

- 76-cell full-height line at x = 493,600 m
- 3 drops per cell
- mean cell depth at free arrival: **1.047 mm**
- required depth: **0.75 mm**
- decay duration: **60 min**
- effective time above threshold: **17.0 min**
- free-burn area: **5,325 ha**

## Perfect re-wetting result

| Interval | Depth | Effective hold | Area | Held | Feasible |
| ---: | ---: | ---: | ---: | ---: | :---: |
| 15 min | 1.047 mm | 17.0 min | 3,504 ha | 71/71 | yes |
| 18 min | 1.047 mm | 17.0 min | 5,325 ha | 0/71 | no |
| 30 min | 1.047 mm | 17.0 min | 5,325 ha | 0/71 | no |
| 60 min | 1.047 mm | 17.0 min | 5,325 ha | 0/71 | no |
| 30 min | 1.500 mm | 30.0 min | 3,504 ha | 71/71 | yes |
| 30 min | 2.000 mm | 37.5 min | 3,504 ha | 71/71 | yes |
| 30 min | 3.000 mm | 45.0 min | 3,504 ha | 71/71 | yes |
| 60 min | 3.000 mm | 45.0 min | 5,325 ha | 0/71 | no |

The current depth only closes the line if re-wetting occurs before the ~17
minute effective hold expires. A 30-minute interval requires at least about
**1.5 mm** per application. A 60-minute interval cannot work with a 60-minute
linear decay, regardless of depth.

## Fleet lower bound

Assumptions:

- 76-cell line, 3 drops per cell for the 1.047 mm reference;
- each additional depth increment is delivered by more 6,000 L sorties;
- 4.25-minute mean aircraft cycle from P180;
- perfect continuous dispatch, no supply, weather or maintenance limits.

| Case | Drops/cell | Sorties/h | Aircraft lower bound | Water/h |
| --- | ---: | ---: | ---: | ---: |
| 15 min, 1.047 mm | 3 | 912 | **65** | 5.47 ML/h |
| 30 min, 1.500 mm | 5 | 760 | **54** | 4.56 ML/h |
| 30 min, 2.000 mm | 6 | 912 | **65** | 5.47 ML/h |
| 30 min, 3.000 mm | 9 | 1,368 | 97 | 8.21 ML/h |
| 60 min, 3.000 mm | 9 | 684 | 49 | 4.10 ML/h — fails |

The 30-minute, 1.500 mm case is the smallest tested fleet, but its effective
hold exactly equals the interval: it has no duration margin. The 30-minute,
2.000 mm case needs 65 aircraft and leaves about 7.5 minutes of margin.

These are **lower bounds**. They assume the line can be re-wetted perfectly and
that every sortie is available at the required rate.

## Comparison with the actual fleet

A 12-aircraft fleet delivers at most about **169 sorties/h** at the P180 cycle
time. The successful tested cases require **760–912 sorties/h**, roughly
**4.5–5.4 times** that rate.

The diagnostic conclusion is therefore not “add a few aircraft.” Sustained
water-only containment of this benchmark line requires an operation far beyond
the 12-aircraft case, or a different tactic.

## Artifact

- `suppression/proofs/2003-526-perfect-rewetting.json`

## Stop rule

No more open-loop fleet sweeps. The next question is whether any realistic
water-only option should be presented as containment, or whether the public
result should report local delay and persistence limits instead.
