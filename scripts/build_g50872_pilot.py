"""Build the G50872 / TSA 24 observed-extent VRI pilot.

This is a larger pilot than the 12-block VRI cluster: the real BC G50872 final
perimeter is the observed extent. Tree placement and ignition timing are
synthetic. Terrain is public SRTM; fuel is a public 100 m C3 sample; weather is
Open-Meteo reanalysis.
"""

from __future__ import annotations

import gzip
import json
import math
import random
from pathlib import Path

import numpy as np
from pyproj import Transformer
from scipy.spatial import cKDTree
from shapely.geometry import Point, Polygon, shape

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "g50872-vri"
TEMPLATE = ROOT / "portal" / "viewer-template.html"
OUT = ROOT / "portal" / "static" / "scenes" / "g50872-vri" / "viewer.html"
DEM = ROOT / "data" / "vri-pilot" / "dem" / "N55W125.hgt.gz"
MAX_TREES = 32000


def _perimeter() -> tuple[list[list[float]], float, float, float, float]:
    source = json.loads((DATA / "perimeter.geojson").read_text(encoding="utf-8"))
    geometry = shape(source["features"][0]["geometry"])
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3005", always_xy=True)
    polygon = Polygon(
        [transformer.transform(x, y) for x, y in geometry.exterior.coords]
    )
    min_x, min_y, max_x, max_y = polygon.bounds
    ring = [
        [float(x) - min_x, float(y) - min_y]
        for x, y in list(polygon.exterior.coords)[:-1]
    ]
    return ring, float(polygon.area / 10000.0), min_x, min_y, max_x


def _terrain_sampler(origin_x: float, origin_y: float):
    with gzip.open(DEM, "rb") as handle:
        raw = handle.read()
    elevation = np.frombuffer(raw, dtype=">i2").reshape(3601, 3601).astype(float)
    transformer = Transformer.from_crs("EPSG:3005", "EPSG:4326", always_xy=True)

    def sample(x: float, y: float) -> float:
        lon, lat = transformer.transform(origin_x + x, origin_y + y)
        col = max(0, min(3600, int(round((lon + 125.0) * 3600.0))))
        row = max(0, min(3600, int(round((56.0 - lat) * 3600.0))))
        value = float(elevation[row, col])
        return value if value > -1000 else 0.0

    return sample


def _burn_field(trees: list[dict], width: float, depth: float) -> dict:
    points = [(tree["x"], tree["y"]) for tree in trees if tree["burn_time"] is not None]
    values = [tree["burn_time"] for tree in trees if tree["burn_time"] is not None]
    tree_index = cKDTree(np.asarray(points, dtype=float))
    nx = ny = 384
    times = []
    for j in range(ny):
        y = (j / (ny - 1)) * depth
        row = []
        for i in range(nx):
            x = (i / (nx - 1)) * width
            _, index = tree_index.query((x, y))
            row.append(round(float(values[int(index)]), 2))
        times.append(row)
    return {
        "nx": nx,
        "ny": ny,
        "dx": width / (nx - 1),
        "dy": depth / (ny - 1),
        "times": times,
        "duration_min": 30.0,
        "mode": "synthetic_timing",
    }


def main() -> None:
    ring, observed_ha, origin_x, origin_y, max_x = _perimeter()
    min_x = 0.0
    min_y = 0.0
    width = max(max(point[0] for point in ring), 1.0)
    depth = max(max(point[1] for point in ring), 1.0)
    blocks = json.loads((DATA / "blocks.geojson").read_text(encoding="utf-8"))["features"]
    total_block_ha = sum(float(feature["properties"].get("area_ha", 0.0)) for feature in blocks)
    density = MAX_TREES / max(1.0, total_block_ha)
    rng = random.Random(50872)
    trees = []
    stands = []
    for feature in blocks:
        props = feature["properties"]
        geometry = shape(feature["geometry"])
        local_ring = [
            [float(x) - origin_x, float(y) - origin_y]
            for x, y in list(geometry.exterior.coords)[:-1]
        ]
        polygon = Polygon(local_ring)
        stands.append(
            {
                "fragment_id": props.get("block_id"),
                "area_ha": float(props.get("area_ha", 0.0)),
                "polygon": local_ring,
            }
        )
        count = max(1, round(float(props.get("area_ha", 0.0)) * density))
        bx0, by0, bx1, by1 = polygon.bounds
        placed = 0
        while placed < count:
            x = rng.uniform(bx0, bx1)
            y = rng.uniform(by0, by1)
            if not polygon.contains(Point(x, y)):
                continue
            height = rng.uniform(8.0, 26.0)
            crown = rng.uniform(1.2, 3.6)
            trees.append(
                {
                    "x": x,
                    "y": y,
                    "z": 0.0,
                    "height_m": height,
                    "crown_radius_m": crown,
                    "burn_time": None,
                    "burn_duration": 30.0,
                    "post_fire_state": rng.choices(
                        ["consumed", "torched", "scorched"], [0.55, 0.25, 0.20]
                    )[0],
                }
            )
            placed += 1
    # Synthetic radial timing from the cluster centre. The observed extent is
    # real; this timing is not an observed progression.
    centre = (
        sum(tree["x"] for tree in trees) / len(trees),
        sum(tree["y"] for tree in trees) / len(trees),
    )
    max_distance = max(
        math.hypot(tree["x"] - centre[0], tree["y"] - centre[1]) for tree in trees
    )
    for tree in trees:
        distance = math.hypot(tree["x"] - centre[0], tree["y"] - centre[1])
        tree["burn_time"] = 20.0 + 220.0 * (distance / max_distance) + rng.uniform(-15, 15)
    sample = _terrain_sampler(origin_x, origin_y)
    nx = ny = 128
    raw_heights = []
    for j in range(ny):
        y = (j / (ny - 1)) * depth
        row = []
        for i in range(nx):
            x = (i / (nx - 1)) * width
            row.append(sample(x, y))
        raw_heights.append(row)
    base = min(value for row in raw_heights for value in row)
    heights = [[value - base for value in row] for row in raw_heights]
    for tree in trees:
        tree["z"] = sample(tree["x"], tree["y"]) - base + 0.15
    weather = json.loads((DATA / "weather.json").read_text(encoding="utf-8"))
    fuel = json.loads((DATA / "fuel.json").read_text(encoding="utf-8"))
    payload = {
        "schema_version": "ws4.fire.scene.v1",
        "manifest": {
            "scene_id": "g50872-tsa24-vri",
            "source": (
                "BC G50872 2023 observed final perimeter; public TSA 24 VRI blocks; "
                "SRTM terrain; sampled C3 fuel; Open-Meteo reanalysis; synthetic stems and timing"
            ),
            "synthetic_trees": True,
            "time_unit": "minutes",
        },
        "bounds": {"min_x": min_x, "min_y": min_y, "max_x": width, "max_y": depth},
        "stands": stands,
        "trees": trees,
        "timeline": {"start": 0.0, "end": 280.0, "unit": "minutes"},
        "observed_ha": observed_ha,
        "model_ha": observed_ha,
        "visual_stems_per_ha": len(trees) / max(1.0, observed_ha),
        "observed_daily_area_ha": [],
        "model_daily_area_ha": [],
        "hero_time": 160.0,
        "observed_mode": "observed_final",
        "domain": [ring],
        "model_extent": [],
        "terrain": {
            "nx": nx,
            "ny": ny,
            "dx": width / (nx - 1),
            "dy": depth / (ny - 1),
            "heights": heights,
        },
        "burn_field": _burn_field(trees, width, depth),
        "detail": {
            "stems_per_ha": 500,
            "radius_m": 260,
            "capacity": 20000,
            "lod_distance_fraction": 0.22,
        },
        "pilot": {
            "fire_id": "G50872",
            "observed_year": 2023,
            "fuel_type": fuel["dominant_fuel_type"],
            "weather": weather,
            "observed_perimeter": True,
            "synthetic_timing": True,
        },
    }
    template = TEMPLATE.read_text(encoding="utf-8")
    payload_json = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
    viewer = template.replace("__CASE_TITLE__", "G50872 · TSA 24 VRI")
    viewer = viewer.replace("__SCENE_DATA__", payload_json)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(viewer, encoding="utf-8")
    print(
        f"wrote {OUT} ({len(viewer) / 1e6:.2f} MB), {len(trees)} trees, "
        f"{observed_ha:.1f} ha observed, {len(stands)} blocks, {fuel['dominant_fuel_type']}"
    )


if __name__ == "__main__":
    main()
