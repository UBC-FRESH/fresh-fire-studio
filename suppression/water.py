"""Water-depth requirements from Van Wagner and Taylor (2022).

The equations use a heat balance and assume perfect application. All returned
depths are millimetres; 1 mm spread over 1 m2 is 1 L/m2.
"""

from __future__ import annotations

from dataclasses import dataclass


def kw_m_to_kcal_s_m(value: float) -> float:
    """Convert fireline intensity from kW/m to kcal/s-m."""
    return value / 4.184


def kcal_s_m_to_kw_m(value: float) -> float:
    """Convert fireline intensity from kcal/s-m to kW/m."""
    return value * 4.184


def kw_m2_to_kcal_m2_s(value: float) -> float:
    """Convert radiant intensity from kW/m2 to kcal/m2-s."""
    return value / 4.184


def _positive(value: float, name: str) -> float:
    if value <= 0.0:
        raise ValueError(f"{name} must be positive")
    return float(value)


def _efficiency(value: float) -> float:
    if not 0.0 < value <= 1.0:
        raise ValueError("application_efficiency must be in (0, 1]")
    return float(value)


def quenching_depth_mm(
    fireline_intensity_kw_m: float,
    *,
    application_efficiency: float = 1.0,
) -> float:
    """Water depth needed to quench the flame, in mm."""
    intensity = kw_m_to_kcal_s_m(_positive(fireline_intensity_kw_m, "fireline_intensity_kw_m"))
    depth = 3.84 * intensity ** (2.0 / 3.0) * 1e-4
    return depth / _efficiency(application_efficiency)


def cooling_depth_mm(
    fuel_load_kg_m2: float,
    *,
    application_efficiency: float = 1.0,
) -> float:
    """Water depth needed to cool the hot fuel in the flaming zone, in mm."""
    fuel = _positive(fuel_load_kg_m2, "fuel_load_kg_m2")
    return 0.226 * fuel / _efficiency(application_efficiency)


def wetting_depth_mm(
    fireline_intensity_kw_m: float,
    radiant_intensity_kw_m2: float,
    rate_of_spread_m_min: float,
    *,
    application_efficiency: float = 1.0,
) -> float:
    """Water depth needed to wet fuel ahead of the fire, in mm."""
    intensity = kw_m_to_kcal_s_m(_positive(fireline_intensity_kw_m, "fireline_intensity_kw_m"))
    radiant = kw_m2_to_kcal_m2_s(_positive(radiant_intensity_kw_m2, "radiant_intensity_kw_m2"))
    rate = _positive(rate_of_spread_m_min, "rate_of_spread_m_min") / 60.0
    depth = 6.39 * intensity ** (2.0 / 3.0) * radiant * 1e-5 / rate
    return depth / _efficiency(application_efficiency)


@dataclass(frozen=True)
class WaterRequirement:
    """Theoretical water depths for the three extinguishing mechanisms."""

    quench_mm: float
    cool_mm: float
    wet_mm: float

    @property
    def burning_mm(self) -> float:
        """Depth required on the flaming zone (quench plus cool)."""
        return self.quench_mm + self.cool_mm

    @property
    def wetting_l_m2(self) -> float:
        """Wetting depth expressed as litres per square metre."""
        return self.wet_mm


def required_depths(
    fireline_intensity_kw_m: float,
    fuel_load_kg_m2: float,
    radiant_intensity_kw_m2: float,
    rate_of_spread_m_min: float,
    *,
    application_efficiency: float = 1.0,
) -> WaterRequirement:
    """Return the three theoretical water depths for one fire behaviour state."""
    efficiency = _efficiency(application_efficiency)
    return WaterRequirement(
        quench_mm=quenching_depth_mm(
            fireline_intensity_kw_m,
            application_efficiency=efficiency,
        ),
        cool_mm=cooling_depth_mm(
            fuel_load_kg_m2,
            application_efficiency=efficiency,
        ),
        wet_mm=wetting_depth_mm(
            fireline_intensity_kw_m,
            radiant_intensity_kw_m2,
            rate_of_spread_m_min,
            application_efficiency=efficiency,
        ),
    )


__all__ = [
    "WaterRequirement",
    "cooling_depth_mm",
    "kcal_s_m_to_kw_m",
    "kw_m2_to_kcal_m2_s",
    "kw_m_to_kcal_s_m",
    "quenching_depth_mm",
    "required_depths",
    "wetting_depth_mm",
]
