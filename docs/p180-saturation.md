# P180.4 mass and target-lead saturation

Status: diagnostic native-growth comparison.

The cycle mission was repeated for 1, 2, 3 and 4 passes, and with targets
selected from a front 60 minutes ahead of the drop time.

## Native result

| Case | Water | Line-mean depth | Coverage | Native area |
| --- | ---: | ---: | ---: | ---: |
| 1 pass | 126,000 L | 0.47 mm | 39% | 5,325 ha |
| 2 passes | 252,000 L | 0.95 mm | 39% | 5,325 ha |
| 3 passes | 378,000 L | 1.42 mm | 39% | 5,325 ha |
| 4 passes | 504,000 L | 1.89 mm | 39% | 5,325 ha |
| 1 pass, 60-min target lead | 126,000 L | 0.47 mm | 39% | 5,325 ha |

The two-pass case closes the **nominal mass deficit**, but the native burn area
does not change. Three and four passes do not change it either. Selecting
targets from a front 60 minutes ahead also does not change the final result.

## Interpretation

The remaining barrier is not water mass. It is the combination of:

- drop footprints that are sub-cell on the 100 m grid;
- a finite line of target cells;
- the diagnostic 0.5 m/min absolute ROS reduction;
- the free-burn model's basin-filling behaviour.

This is a stronger and more useful failure result than another single pass:
water quantity and target lookahead are both varied, and the native outcome is
still insensitive.

## Artifacts

- `suppression/proofs/2003-526-native-cycle-2pass.json`
- `suppression/proofs/2003-526-native-cycle-3pass.json`
- `suppression/proofs/2003-526-native-cycle-4pass.json`
- `suppression/proofs/2003-526-native-cycle-lead60.json`

## Limits

- Mass-only sweep and native runs use the same schematic lake and target
  geometry.
- Target lead is a single snapshot, not a receding-horizon policy.
- The wetness/ROS mapping remains diagnostic.
- The 100 m grid remains a hard resolution limit.

## Arrival-time follow-up

Re-selecting targets at each sortie's drop time produced a mean cycle of
**4.21 min** and **254,464 L/h**, but the native outcome remained **5,325 ha**.
See [`p180-arrival.md`](p180-arrival.md).

## Continuous-target follow-up

Resampling the selected front at 100 m spacing produced **54 distinct targets**,
**324,000 L**, 100% target coverage and still **5,325 ha**. See
[`p180-continuous.md`](p180-continuous.md).

## Next

If the aim is to make the fire respond, the next change must be structural:
a finer coupled fire/effect grid, or a different local water-effect model.
More sorties on the same 100 m grid are not informative.
