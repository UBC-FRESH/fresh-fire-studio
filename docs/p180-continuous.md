# P180.7 continuous target line

Status: diagnostic. Targets were resampled at 100 m spacing along the selected
front segment, instead of repeating drops on 21 discrete targets.

## Geometry

- target segment: about **5.3 km**
- target spacing: **100 m**
- targets/sorties: **54**
- aircraft: 3
- delivered: **324,000 L**
- mean cycle: **4.40 min**
- **243,955 L/h**
- unique target coverage: **100%** of the 50 m strip

## Native result

**5,325 ha** — unchanged from free burn.

Artifacts:

- `suppression/scenarios/2003-526-cycle-continuous.json`
- `suppression/proofs/2003-526-native-cycle-continuous.json`

## What this rules out

The discrete-target gap is now closed. The remaining failure is not:

- number of sorties;
- total water;
- target spacing;
- repeated passes on the same cells;
- fire-grid resolution.

It is the local water-to-fire effect and/or the 100 m coupled growth model.

## Limits

- The target line is a resampled version of the selected front segment.
- The lake, phase times and water depth are schematic.
- The evidence mapping remains a mean absolute ROS reduction.
- The native model still fills the burnable basin.
