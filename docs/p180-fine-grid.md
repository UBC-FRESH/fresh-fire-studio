# P180.5 fine-grid two-pass test

Status: diagnostic resolution test.

The two-pass cycle mission was rerun at 50 m and 25 m fire-cell resolution.
Fuel and terrain were nearest-neighbour upsampled from the 100 m fixture; the
observed masks were upsampled; drop sub-cells were 10 m and 5 m respectively.

## Result

| Fire grid | Free burn | Two-pass mission |
| --- | ---: | ---: |
| 100 m | 5,325 ha | 5,325 ha |
| 50 m | 5,325 ha | 5,325 ha |
| 25 m | 5,325 ha | 5,325 ha |

The two-pass mission still does not change the final area.

Artifacts:

- `suppression/proofs/2003-526-fine-grid-2pass.json`
- `suppression/proofs/2003-526-fine-grid-2pass-25m.json`

## What this tells us

Reducing the fire-cell size alone does not make the wet line effective. The
remaining candidates are:

- source fuel/terrain remapping rather than nearest-neighbour upsampling;
- a different local water-to-ROS model;
- target selection tied to the actual arrival time of the front;
- a wet line that is continuous in the effect grid and wide enough to survive
  the fire's route around its ends.

## Limits

- Upsampling is not a true fine-resolution landscape.
- The same schematic lake and target geometry are reused.
- The native fire model still fills the burnable basin.
- The observed masks are not re-digitized at fine resolution.
