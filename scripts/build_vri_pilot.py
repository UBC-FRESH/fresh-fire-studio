"""Build the VRI pilot scene in the current FRESH Fire Studio viewer.

The source is the public TSA 24 VRI block cluster fixture with synthetic Nemora
stems and a synthetic C3 fire. Terrain is flat; this is a pilot prototype, not
an observed fire.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
from pyproj import Transformer
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "vri-pilot" / "payload.json"
TEMPLATE = ROOT / "portal" / "viewer-template.html"
OUT = ROOT / "portal" / "static" / "scenes" / "vri-pilot" / "viewer.html"
DEM = ROOT / "data" / "vri-pilot" / "dem" / "N55W125.hgt.gz"
# The VRI fixture is the TSA 24 source geometry translated to a local origin.
LOCAL_ORIGIN = (1088291.2231, 1124190.4741)


def _burn_field(trees: list[dict], min_x: float, min_y: float, max_x: float, max_y: float) -> dict:
    points: list[tuple[float, float]] = []
    values: list[float] = []
    for tree in trees:
        if tree.get("burn_time") is None:
            continue
        points.append((float(tree["x"]), float(tree["y"])))
        values.append(float(tree["burn_time"]))
    tree = cKDTree(np.asarray(points, dtype=float))
    nx = ny = 384
    width = max(1.0, max_x - min_x)
    depth = max(1.0, max_y - min_y)
    times: list[list[float | None]] = []
    for j in range(ny):
        y = min_y + (j / (ny - 1)) * depth
        row: list[float | None] = []
        for i in range(nx):
            x = min_x + (i / (nx - 1)) * width
            _, index = tree.query((x, y))
            row.append(round(float(values[int(index)]), 2))
        times.append(row)
    return {
        "nx": nx,
        "ny": ny,
        "dx": width / (nx - 1),
        "dy": depth / (ny - 1),
        "times": times,
        "duration_min": 2.0,
        "mode": "synthetic_pilot",
    }


def _terrain_sampler() -> tuple[callable, str]:
    """Return a local-elevation sampler backed by the public SRTM tile."""
    if not DEM.is_file():
        return (lambda x, y: 0.0), "flat fallback"
    with gzip.open(DEM, "rb") as handle:
        raw = handle.read()
    elevation = np.frombuffer(raw, dtype=">i2").reshape(3601, 3601).astype(float)
    transformer = Transformer.from_crs("EPSG:3005", "EPSG:4326", always_xy=True)

    def sample(x: float, y: float) -> float:
        lon, lat = transformer.transform(LOCAL_ORIGIN[0] + x, LOCAL_ORIGIN[1] + y)
        col = int(round((lon + 125.0) * 3600.0))
        row = int(round((56.0 - lat) * 3600.0))
        col = max(0, min(3600, col))
        row = max(0, min(3600, row))
        value = float(elevation[row, col])
        return value if value > -1000 else 0.0

    return sample, "SRTM 1 arcsec N55W125"


def main() -> None:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    trees = source["trees"]
    stands = source["stands"]
    bounds = source["bounds"]
    min_x = float(bounds["min_x"])
    min_y = float(bounds["min_y"])
    max_x = float(bounds["max_x"])
    max_y = float(bounds["max_y"])
    area_ha = sum(float(stand.get("area_ha", 0.0)) for stand in stands)
    domain = [
        [[float(point[0]), float(point[1])] for point in stand["polygon"]]
        for stand in stands
        if isinstance(stand.get("polygon"), list)
    ]
    burn_times = [
        float(tree["burn_time"])
        for tree in trees
        if tree.get("burn_time") is not None
    ]
    timeline_end = max(burn_times) + 10.0 if burn_times else 240.0
    daily = []
    for day in range(2):
        cutoff = (day + 1) * 1440.0
        fraction = sum(1 for value in burn_times if value <= cutoff) / max(1, len(burn_times))
        daily.append(area_ha * fraction)
    # Keep only fields consumed by the viewer.
    keep = {
        "x", "y", "z", "height_m", "crown_radius_m",
        "burn_time", "burn_duration", "post_fire_state",
    }
    for tree in trees:
        for key in list(tree.keys()):
            if key not in keep:
                del tree[key]
        if tree.get("post_fire_state") == "burned":
            tree["post_fire_state"] = "scorched"
    sample, dem_source = _terrain_sampler()
    nx = ny = 72
    width = max(1.0, max_x - min_x)
    depth = max(1.0, max_y - min_y)
    raw_heights = []
    for j in range(ny):
        y = min_y + (j / (ny - 1)) * depth
        row = []
        for i in range(nx):
            x = min_x + (i / (nx - 1)) * width
            row.append(sample(x, y))
        raw_heights.append(row)
    base = min(value for row in raw_heights for value in row)
    heights = [[value - base for value in row] for row in raw_heights]
    for tree in trees:
        tree["z"] = sample(float(tree["x"]), float(tree["y"])) - base + 0.15
    terrain = {
        "nx": nx,
        "ny": ny,
        "dx": width / (nx - 1),
        "dy": depth / (ny - 1),
        "heights": heights,
    }
    payload = {
        "schema_version": "ws4.fire.scene.v1",
        "manifest": {
            "scene_id": "vri-pilot-tsa24",
            "source": f"public TSA 24 block geometry; synthetic Nemora stems; synthetic C3 fire; {dem_source}",
            "synthetic_trees": True,
            "time_unit": "minutes",
        },
        "bounds": bounds,
        "stands": stands,
        "trees": trees,
        "timeline": {"start": 0.0, "end": timeline_end, "unit": "minutes"},
        "observed_ha": area_ha,
        "model_ha": area_ha,
        "visual_stems_per_ha": len(trees) / max(1.0, area_ha),
        "observed_daily_area_ha": [],
        "model_daily_area_ha": daily,
        "hero_time": float(np.quantile(burn_times, 0.55)) if burn_times else timeline_end * 0.55,
        "observed_mode": "synthetic_pilot",
        "domain": domain,
        "model_extent": domain,
        "terrain": terrain,
        "burn_field": _burn_field(trees, min_x, min_y, max_x, max_y),
        "detail": {
            "stems_per_ha": 500,
            "radius_m": 260,
            "capacity": 20000,
            "lod_distance_fraction": 0.22,
        },
    }
    template = TEMPLATE.read_text(encoding="utf-8")
    payload_json = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
    viewer = template.replace("__CASE_TITLE__", "VRI pilot · TSA 24")
    viewer = viewer.replace("__SCENE_DATA__", payload_json)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(viewer, encoding="utf-8")
    print(f"wrote {OUT} ({len(viewer) / 1e6:.2f} MB), {len(trees)} trees, {area_ha:.1f} ha, {dem_source}")


if __name__ == "__main__":
    main()
