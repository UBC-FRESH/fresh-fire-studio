# P180.6 arrival-time target selection

Status: diagnostic. Targets were re-selected from the predicted free-burn front
at each sortie's drop time.

## Method

1. Build the initial cycle from the 600-minute front.
2. For each sortie, read the free-burn front at that sortie's drop time.
3. Replace the target with the corresponding unburned front cell.
4. Rebuild the cycle and repeat twice.
5. Run native growth with the final sortie stream.

## Result

- 3 aircraft
- 21 sorties
- mean cycle **4.21 min**
- **254,464 L/h**
- 126,000 L delivered
- native outcome: **5,325 ha**

Arrival-time target selection does not change the final area.

## Interpretation

The target is now tied to the predicted front at drop time rather than a single
600-minute snapshot. It still does not produce containment.

This rules out the simplest placement error: using a stale target line. The
remaining limitations are the local water-effect model, the continuous wet-line
geometry, and the 100 m coupled grid.

## Artifacts

- `suppression/scenarios/2003-526-cycle-adaptive.json`
- `suppression/proofs/2003-526-native-cycle-adaptive.json`

## Limits

- The front comes from the free-burn prediction, not the actual suppressed run.
- The target selector takes the easternmost front cells, not an optimized line.
- Two iterations do not guarantee convergence of cycle times and targets.
- The wetness/ROS mapping remains diagnostic.
