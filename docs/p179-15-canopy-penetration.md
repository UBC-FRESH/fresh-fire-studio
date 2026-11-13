# P179.15 canopy penetration in the wet schedule

Status: diagnostic. The P179 drop model already had a `canopy_penetration`
field; it was not being applied to the wet-cell depth. This fixes that input.

## Change

`WetDrop.depth_at()` now multiplies the active water depth by
`canopy_penetration`:

```text
effective depth = delivered depth × canopy penetration × decay
```

A value of 1.0 means all delivered water reaches the surface. A value of 0.5
means half is intercepted or otherwise unavailable.

`build_wet_schedule()` reads the field from each scenario `Drop`.

## Why

The earlier wet-coupling experiments used 1.0 everywhere, so the parameter had
no effect. This change makes the existing contract meaningful without adding a
new canopy model.

## Limits

- `canopy_penetration` is still an input, not a measured or modelled value.
- It does not distinguish interception storage, evaporation or re-release.
- It does not alter the drop footprint.
- The wetness/ROS mapping remains diagnostic.
- No validation against field water-depth measurements.

## Next

Use measured canopy interception or a species/structure-dependent penetration
model. Until then, treat this as an explicit sensitivity parameter.
