"""Build the VRI pilot scene in the current FRESH Fire Studio viewer.

The source is the public TSA 24 VRI block cluster fixture with synthetic Nemora
stems and a synthetic C3 fire. Terrain is flat; this is a pilot prototype, not
an observed fire.
"""

from __future__ import annotations

import gzip
import json
import math
import sys
from pathlib import Path

import numpy as np
from pyproj import Transformer
from scipy.spatial import cKDTree
from shapely.geometry import Point, Polygon, shape

WS4_GPU = Path("/srv/shared-data/gep/ws4/ws4-gpu")
if str(WS4_GPU) not in sys.path:
    sys.path.insert(0, str(WS4_GPU))

from ws4.fire import GrowthConfig, SiteGrid, grow_fire  # noqa: E402
from ws4.scene import load_nemora_scene, sample_tree_ignition  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data" / "vri-pilot" / "fixture"
TEMPLATE = ROOT / "portal" / "viewer-template.html"
OUT = ROOT / "portal" / "static" / "scenes" / "vri-pilot" / "viewer.html"
DEM = ROOT / "data" / "vri-pilot" / "dem" / "N55W125.hgt.gz"
OBSERVED = ROOT / "data" / "vri-pilot" / "observed-g50266.geojson"
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


FUEL_SAMPLE = json.loads(
    (ROOT / "data" / "vri-pilot" / "fuel_sample.json").read_text(encoding="utf-8")
)
FUEL_TYPE = str(FUEL_SAMPLE["dominant_fuel_type"])
WEATHER = json.loads(
    (ROOT / "data" / "vri-pilot" / "weather.json").read_text(encoding="utf-8")
)


def _observed_extent() -> tuple[list[list[list[float]]], float, str]:
    if not OBSERVED.is_file():
        return [], 0.0, ""
    data = json.loads(OBSERVED.read_text(encoding="utf-8"))
    feature = data["features"][0]
    geometry = shape(feature["geometry"])
    polygons = list(geometry.geoms) if hasattr(geometry, "geoms") else [geometry]
    rings: list[list[list[float]]] = []
    for polygon in polygons:
        ring = [
            [float(x) - LOCAL_ORIGIN[0], float(y) - LOCAL_ORIGIN[1]]
            for x, y in list(polygon.exterior.coords)[:-1]
        ]
        rings.append(ring)
    props = feature["properties"]
    return rings, float(props.get("FIRE_SIZE_HECTARES", 0.0)), str(props.get("FIRE_LABEL", "G50266"))


def main() -> None:
    inventory = load_nemora_scene(
        FIXTURE / "nemora_trees.csv",
        FIXTURE / "vri_polygons.geojson",
        seed=20261108,
        source="public TSA 24 block geometry (femic-tsa24-instance)",
        crs="local",
        nemora_version="ws4-fixture",
    )
    margin = 30.0
    min_x = min(tree.x for tree in inventory.trees) - margin
    min_y = min(tree.y for tree in inventory.trees) - margin
    max_x = max(tree.x for tree in inventory.trees) + margin
    max_y = max(tree.y for tree in inventory.trees) + margin
    cell = 5.0
    cols = max(1, math.ceil((max_x - min_x) / cell))
    rows = max(1, math.ceil((max_y - min_y) / cell))
    polygons = [Polygon(ring).buffer(1.5) for ring in inventory.fragment_polygons.values()]
    burnable = np.zeros((rows, cols), dtype=bool)
    for row in range(rows):
        y = min_y + (row + 0.5) * cell
        for col in range(cols):
            x = min_x + (col + 0.5) * cell
            burnable[row, col] = any(polygon.contains(Point(x, y)) for polygon in polygons)
    center_x = sum(tree.x for tree in inventory.trees) / len(inventory.trees)
    center_y = sum(tree.y for tree in inventory.trees) / len(inventory.trees)
    start = min(
        inventory.trees,
        key=lambda tree: (tree.x - center_x) ** 2 + (tree.y - center_y) ** 2,
    )
    ignition_col = min(cols - 1, max(0, int((start.x - min_x) / cell)))
    ignition_row = min(rows - 1, max(0, int((start.y - min_y) / cell)))
    if not burnable[ignition_row, ignition_col]:
        candidates = np.argwhere(burnable)
        if len(candidates) == 0:
            raise RuntimeError("no burnable cell in the VRI polygons")
        ignition_row, ignition_col = (int(value) for value in candidates[0])
    grid = SiteGrid(
        fuel_type=FUEL_TYPE,
        rows=rows,
        cols=cols,
        cell_size_m=cell,
        ffmc=float(WEATHER["ffmc"]),
        bui=float(WEATHER["bui"]),
        wind_kmh=float(WEATHER["wind_kmh"]),
        wind_direction_deg=float(WEATHER["wind_direction_deg"]),
        slope_percent=10.0,
        aspect_deg=float(WEATHER["wind_direction_deg"]),
        burnable=burnable,
    )
    growth = grow_fire(
        grid,
        GrowthConfig(
            ignition_cells=((ignition_row, ignition_col),),
            max_time_min=240.0,
            snapshot_interval_min=240.0,
            neighbor_radius=2,
        ),
    )
    animation = sample_tree_ignition(
        inventory,
        growth,
        cell_size_m=cell,
        margin_m=margin,
        flame_length_m=5.0,
        smoke_strength=0.5,
        burn_duration=2.0,
    )
    ignition = dict(zip(animation["tree_id"], animation["ignition_time"]))
    states = dict(zip(animation["tree_id"], animation["post_fire_state"]))
    trees = []
    for tree in inventory.trees:
        burn = ignition.get(tree.tree_id)
        trees.append(
            {
                "tree_id": tree.tree_id,
                "x": float(tree.x),
                "y": float(tree.y),
                "z": 0.0,
                "height_m": float(tree.height_m),
                "crown_radius_m": float(tree.crown_radius_m),
                "burn_time": None if burn is None or not np.isfinite(burn) else float(burn),
                "burn_duration": 2.0,
                "post_fire_state": states.get(tree.tree_id, "unburned"),
            }
        )
    bounds = {"min_x": min_x, "min_y": min_y, "max_x": max_x, "max_y": max_y}
    stands = []
    for fragment_id, raw_polygon in inventory.fragment_polygons.items():
        polygon = raw_polygon if hasattr(raw_polygon, "exterior") else Polygon(raw_polygon)
        ring = [[float(x), float(y)] for x, y in list(polygon.exterior.coords)[:-1]]
        stands.append(
            {
                "fragment_id": fragment_id,
                "area_ha": float(inventory.fragment_areas.get(fragment_id, 0.0)),
                "polygon": ring,
            }
        )
    area_ha = sum(float(stand["area_ha"]) for stand in stands)
    domain = [stand["polygon"] for stand in stands]
    burn_times = [tree["burn_time"] for tree in trees if tree["burn_time"] is not None]
    timeline_end = max(burn_times) + 10.0 if burn_times else 240.0
    daily = []
    for day in range(2):
        cutoff = (day + 1) * 1440.0
        fraction = sum(1 for value in burn_times if value <= cutoff) / max(1, len(burn_times))
        daily.append(area_ha * fraction)
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
    observed_extent, observed_fire_ha, observed_fire_id = _observed_extent()
    payload = {
        "schema_version": "ws4.fire.scene.v1",
        "manifest": {
            "scene_id": "vri-pilot-tsa24",
            "source": (
                "public TSA 24 block geometry; public SRTM terrain; "
                f"public fuel sample {FUEL_TYPE}; Open-Meteo reanalysis; synthetic Nemora stems"
            ),
            "synthetic_trees": True,
            "time_unit": "minutes",
        },
        "bounds": bounds,
        "stands": stands,
        "trees": trees,
        "timeline": {"start": 0.0, "end": timeline_end, "unit": "minutes"},
        "observed_ha": area_ha,
        "model_ha": float(growth.burned_area_ha),
        "visual_stems_per_ha": len(trees) / max(1.0, area_ha),
        "observed_daily_area_ha": [],
        "model_daily_area_ha": daily,
        "hero_time": float(np.quantile(burn_times, 0.55)) if burn_times else timeline_end * 0.55,
        "observed_mode": "synthetic_pilot",
        "observed_extent": observed_extent,
        "observed_fire_ha": observed_fire_ha,
        "observed_fire_id": observed_fire_id,
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
        "pilot": {
            "fuel_type": FUEL_TYPE,
            "weather": WEATHER,
            "dem_source": dem_source,
            "fire_model": "WS4/FBP synthetic growth run",
            "observed_perimeter": bool(observed_extent),
            "observed_fire_id": observed_fire_id,
            "observed_fire_ha": observed_fire_ha,
        },
    }
    template = TEMPLATE.read_text(encoding="utf-8")
    payload_json = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
    viewer = template.replace("__CASE_TITLE__", "VRI pilot · TSA 24")
    viewer = viewer.replace("__SCENE_DATA__", payload_json)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(viewer, encoding="utf-8")
    print(
        f"wrote {OUT} ({len(viewer) / 1e6:.2f} MB), {len(trees)} trees, "
        f"{area_ha:.1f} ha, {dem_source}, {FUEL_TYPE}, "
        f"model {growth.burned_area_ha:.1f} ha"
    )


if __name__ == "__main__":
    main()
