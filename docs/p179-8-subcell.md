# P179.8 sub-cell drop raster

Status: geometry/aggregation layer. It preserves a drop at 10 m resolution and
aggregates it back to the 100 m fire grid. It does not yet change the native
fire kernel.

## Why

A CL-415 C-2 drop is about 90 × 40 m. A 100 m fire cell is 10,000 m², while the
ellipse covers only about 2,800 m². Treating the drop as a full cell overstates
its coverage; treating it as a point loses its shape.

## What it does

`suppression/subcell.py` provides:

- `rasterize_pattern(pattern, center, cell_size_m=10)`;
- nested depth layers at the sub-cell resolution;
- `aggregate_mean()` for mean depth per fire cell;
- `aggregate_max()` for the deepest sub-cell in a fire cell;
- `aggregate_coverage()` for the wetted fraction of a fire cell.

The aggregate functions require the fire cell size to be an integer multiple of
the sub-cell size. A 100 m fire cell with 10 m sub-cells is a 10 × 10 block.

## Example

For a 90 × 40 m, 0.5 mm CL-415 contour at 10 m resolution:

- sub-cell raster: about 6 × 12 including padding;
- occupied sub-cells: about 28;
- area: about 0.28 ha;
- mean depth in the containing 100 m cell: about **0.14 mm**;
- wetted fraction of that cell: about **0.28**.

Only one 100 m cell is touched. This is the correct sub-cell result: a drop is
not a full 100 m cell.

## What this fixes

- Drops are no longer smeared over a whole fire cell.
- Nested contours keep their shallow/deep structure.
- Mean, maximum and coverage fraction are available for different effect
  models.
- The 100 m fire grid receives a physically smaller quantity than a binary
  “wet cell” flag.

## What this does not fix

- The native growth kernel still operates on 100 m cells.
- A single drop still affects only one or two cells.
- No ignition or ROS modifier is applied from the sub-cell depth.
- No wind drift, canopy interception, evaporation or terrain.
- No fine-resolution fire growth.

## Next

Use `aggregate_mean()` or `aggregate_coverage()` to drive a **local ROS or
ignition modifier** in the native growth run, or run a finer fire grid. A binary
wet-cell threshold cannot represent partial-cell water depth. The diagnostic
ROS factor is implemented in
[`p179-9-wetness-ros.md`](p179-9-wetness-ros.md).
