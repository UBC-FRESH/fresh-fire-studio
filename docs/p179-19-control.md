# P179.19 evidence control barrier

Status: diagnostic control. This is deliberately not a realistic suppression
mission. It tests whether the evidence parameters affect the model when the
geometry is sufficient.

## Control design

- synthetic wet band at x = 493600 m;
- **20 cells wide** (2,000 m);
- every cell treated as wet for the full run;
- 2 mm water depth;
- absolute ROS reduction sampled from the Wheatley evidence range;
- same 32-sample ensemble, same native kernel.

The barrier is permanent and unrealistically wide. It exists to separate
**effect-model sensitivity** from **placement failure**.

## Result

| Run | Mean area | Range | Containment probability |
| --- | ---: | ---: | ---: |
| Free burn | 5,325 ha | — | — |
| Evidence control barrier | 3,574.7 ha | 3,570–3,575 ha | 1.0 |

Parameter correlations with final area:

- ROS reduction: **−0.777**
- canopy penetration: −0.222
- required depth: −0.107
- hold: 0.088
- water depth: 0.013

## Interpretation

When the wet geometry intersects the fire, the sampled absolute ROS reduction
has a strong effect on final area. The control reduces the simulated area by
about **1,750 ha**, and higher ROS reduction tends to produce lower final area.

The hold/depth correlations are weak because this control is permanently wet;
those parameters are not being exercised. The control is a test of the ROS
branch, not a water-balance validation.

The base 21-drop ensemble remains all **5,325 ha** because its line does not
intersect the active front strongly enough. Together, the two runs separate two
different failures:

- the base mission fails on placement;
- the control shows the effect model can respond when placement is sufficient.

## Artifact

- `suppression/proofs/2003-526-evidence-control.json`

## Limits

- The control barrier is permanent and 2 km wide; it is not a real drop line.
- It uses a single fixed wet band rather than an operational mission.
- The 100 m fire grid remains coarse.
- The Wheatley evidence is from low-intensity surface fires.
- The control is not an operational prediction and should not be shown as one.

## Next

Use this control as the sensitivity baseline. A realistic mission should be
compared against it, not against zero effect. The next useful engineering step
is a 3D replay that shows both:

1. the failed realistic mission; and
2. the control effect envelope, clearly labelled.
