# P179.5b drop contours, stacking and breach

Status: operational-drop representation. It is a small, explicit model of the
McFayden et al. (2023) drop concepts, not a complete reproduction of GLC-X-35.

## What it does

`suppression/drop.py` provides:

- `DropContour` — one elliptical water-depth contour;
- `DropPattern` — nested contours ordered shallow to deep;
- `effective_contour(required_depth)` — smallest contour meeting the target;
- `drops_to_uniform` — stacking count from the fractional coverage;
- `ellipse_geometry` — rotated footprint geometry;
- `to_effect_events` — one effect event per depth layer;
- `is_breached` — the half-drop-width breach test;
- a small CL-415 / C-2 / full-canopy catalogue.

The depth unit is millimetres, which is numerically the same as litres per
square metre when water is spread uniformly: `1 mm = 1 L/m²`.

## CL-415 C-2 full-canopy catalogue

This encodes the effective dimensions and required depths from McFayden et al.
Tables 8-2 and 8-3.

| Fireline intensity | Required depth | Effective L × W | Drops to hold 100 m | Status |
| ---: | ---: | ---: | ---: | --- |
| ≤ 10 kW/m | 0.25 mm | 130 × 50 m | 1 | hold |
| 300–900 kW/m | 0.50 mm | 90 × 40 m | 1 | hold |
| 1,300 kW/m | 0.75 mm | 70 × 30 m | 2 | hold with stacking |
| 3,200 kW/m | 1.50 mm | — | — | breached |
| 7,700 kW/m | 2.50 mm | — | — | breached |

The guide's broader table also includes other aircraft, sparse canopy, C-3,
O-1a and S-1 fuels. Those are not in this catalogue yet.

## Breach test

The guide treats a drop as breached when the active flame front is wider than
half the drop width, or when flame length exceeds half the drop width on the
unburned side. The module uses:

```python
is_breached(
    flame_length_m=...,
    flame_front_depth_m=...,
    drop_width_m=...,
)
```

This is a geometric model, not a validated transition probability.

## Effect events

Each contour becomes a separate effect event:

```python
pattern = cl415_c2_full_pattern(1_300)
events = pattern.to_effect_events(
    (x, y),
    start_min=120,
    end_min=135,
    effect_duration_min=8,
)
```

The events carry `coverage_l_m2` equal to the contour depth. A fire kernel can
rasterize the nested layers in order and apply the deepest coverage last.

## Limits

- Only the CL-415, C-2, full-canopy catalogue is encoded.
- The catalogue uses one effective contour per intensity; generic nested
  patterns are supported but not populated for every fuel/canopy case.
- Drop dimensions are steady-state averages, not a measured individual drop.
- No wind drift, canopy interception, evaporation, downwash or terrain
  deflection.
- Stacking assumes perfect alignment.
- The breach test is geometric and deterministic.
- The operational depths are not interchangeable with Van Wagner–Taylor's
  theoretical water depths; one is a guide for actual drops, the other is a
  heat-balance requirement.

## Next

1. Convert an existing `Drop` scenario entry into a `DropPattern`.
2. Rasterize the nested contours into a coverage field.
3. Feed water depth and decay into the native growth run as a local fuel
   moisture or ROS modifier.
4. Add sparse-canopy and additional aircraft catalogues only when needed.
5. Add aircraft cycle time from dispatch before 3D playback.
MD
