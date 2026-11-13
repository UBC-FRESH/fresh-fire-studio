# P179.5a water-depth requirements

Status: theoretical requirement module. It computes water depths from Van
Wagner and Taylor's heat-balance model. It does not yet model a real drop,
canopy interception or application efficiency on a fireline.

## What it does

`suppression/water.py` implements three mechanisms:

1. **Quenching the flame** — water depth to absorb flame energy.
2. **Cooling hot fuel** — water depth based on fuel load in the flaming zone.
3. **Wetting fuel ahead of the fire** — water depth based on fireline
   intensity, radiant intensity, rate of spread and fuel load.

The equations use fireline intensity in kcal/s·m. The module accepts kW/m and
converts internally. Returned depths are millimetres; 1 mm over 1 m² is
1 L/m², so the numeric value is also `coverage_l_m2`.

## Equations

With `I` in kcal/s·m:

```text
quench depth (mm) = 3.84 I^(2/3) × 10^-4
cool depth (mm)   = 0.226 W1
wet depth (mm)    = 6.39 I^(2/3) i × 10^-5 / R
```

- `W1` is fuel load in kg/m².
- `i` is radiant intensity in kcal/m²·s.
- `R` is rate of spread in m/s after converting m/min.

An `application_efficiency` in `(0, 1]` divides the theoretical depth. This is
the fraction of applied water that performs the intended heat transfer; the
required applied depth is therefore larger when efficiency is below one.

## Report check

The module reproduces the rounded values in Van Wagner and Taylor's Table 3:

| Intensity | Quench | Cool | Wet |
| ---: | ---: | ---: | ---: |
| 100 kcal/s·m (≈419 kW/m) | 0.008 mm | 0.28 mm | 0.31 mm |
| 1,000 kcal/s·m (≈4,184 kW/m) | 0.038 mm | 0.56 mm | 0.57 mm |
| 10,000 kcal/s·m (≈41,840 kW/m) | 0.18 mm | 1.13 mm | 1.07 mm |

The important result is the exponent: water depth grows roughly as
`I^(2/3)`, not linearly with fireline intensity.

## Interface

```python
from suppression.water import required_depths

result = required_depths(
    fireline_intensity_kw_m=4184.0,
    fuel_load_kg_m2=2.5,
    radiant_intensity_kw_m2=41.84,
    rate_of_spread_m_min=6.67,
)
result.quench_mm
result.cool_mm
result.wet_mm
result.burning_mm
```

CLI:

```bash
python scripts/water_requirement.py \
  --intensity-kw-m 4184 \
  --fuel-load-kg-m2 2.5 \
  --radiant-kw-m2 41.84 \
  --ros-m-min 6.67
```

## Limits

- These are theoretical values assuming perfect heat transfer.
- The equations do not include canopy interception, evaporation, runoff,
  downwash or drop-pattern non-uniformity.
- `application_efficiency` is a diagnostic input, not a measured constant.
- The cooling equation depends on fuel load, not fireline intensity.
- The wetting equation uses the report's radiant-intensity convention; do not
  mix units.
- McFayden et al.'s operational drop depths include canopy and stacking
  effects and are not interchangeable with these theoretical values.

## Next

Use `required_depths` as the target depth for a drop contour, then compare the
target with McFayden's effective contours, stacking rules and breach criteria.
Only after that should the model reduce local fuel availability in the native
growth run.
