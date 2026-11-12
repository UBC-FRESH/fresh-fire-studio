"""Build the benchmark fire scenes for the FRESH Fire portal.

Each scene is a standalone WS4 3D viewer plus a summary JSON. The tree layer is a
Nemora-derived synthetic stem population, not a measured inventory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import rasterio
from PIL import Image
from pyproj import Transformer
from rasterio.features import shapes
from rasterio.transform import from_origin
from scipy.spatial import cKDTree
from shapely.geometry import Polygon
from shapely.ops import unary_union

PORTAL = Path(__file__).resolve().parents[1]
DEFAULT_WS4 = Path("/srv/shared-data/gep/ws4/.opencode/tmp/opencode/ws4-p176")
DEFAULT_NEMORA = Path("/srv/shared-data/gep/ws4/nemora/src")
DEFAULT_CFSDS = Path("/srv/shared-data/gep/ws4/.opencode/tmp/opencode/cfsds")
sys.path.insert(0, str(DEFAULT_WS4))
sys.path.insert(0, str(DEFAULT_NEMORA))

from nemora.synthesis.stems import (
    TreeAttributeConfig,
    attach_tree_attributes,
    place_trees,
)  # type: ignore[import-untyped]
from ws4.ecosystem.fire import FireConfig, FireRun, synthetic_grid  # type: ignore[import-not-found]
from ws4.fire.comparison import observed_mask, reference_weather, run_observed_case  # type: ignore[import-not-found]
from ws4.fire.observed import (  # type: ignore[import-not-found]
    ObservedFire,
    load_cfsds_reanalysis_case,
    load_dogrib,
    load_hay_river,
)
from ws4.scene import (  # type: ignore[import-not-found]
    compile_fire_scene,
    load_nemora_scene,
    sample_tree_ignition,
)

BLOCKS_X = 6
BLOCKS_Y = 6
MAX_TREES = 32000
TREE_BURN_MINUTES = 15.0
OBSERVED_BURN_MINUTES = 45.0
SUBCELL_JITTER_MINUTES = 240.0


def _hillshade(fire: ObservedFire, path: Path) -> None:
    """Write a small hillshade/terrain texture for the flat ground plane."""
    elevation = np.asarray(fire.elevation_m, dtype=float)
    elevation = np.where(np.isfinite(elevation) & (elevation > 0), elevation, np.nan)
    if not np.isfinite(elevation).any():
        Image.new("RGB", (128, 128), (44, 74, 56)).save(path)
        return
    low = float(np.nanmin(elevation))
    high = float(np.nanmax(elevation))
    span = max(1.0, high - low)
    normalized = np.nan_to_num((elevation - low) / span, nan=0.0)
    gy, gx = np.gradient(normalized)
    shade = 0.5 + 0.5 * np.clip((-gx - gy) * 4.0, -1.0, 1.0)
    # Resample to a compact texture with PIL.
    h, w = normalized.shape
    scale = min(1.0, 256.0 / max(h, w))
    size = (max(2, int(w * scale)), max(2, int(h * scale)))
    shade_img = Image.fromarray((np.clip(shade, 0, 1) * 255).astype(np.uint8)).resize(
        size
    )
    elev_img = Image.fromarray(
        (np.clip(normalized, 0, 1) * 255).astype(np.uint8)
    ).resize(size)
    shade_arr = np.asarray(shade_img, dtype=float) / 255.0
    elev_arr = np.asarray(elev_img, dtype=float) / 255.0
    rgb = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    rgb[:, :, 0] = np.clip(70 + 92 * elev_arr + 42 * shade_arr, 0, 255)
    rgb[:, :, 1] = np.clip(92 + 108 * elev_arr + 56 * shade_arr, 0, 255)
    rgb[:, :, 2] = np.clip(54 + 64 * elev_arr + 28 * shade_arr, 0, 255)
    Image.fromarray(rgb).save(path)


def _terrain_payload(
    fire: ObservedFire,
    min_x: float,
    min_y: float,
    max_x: float,
    max_y: float,
    trees: list[dict[str, object]],
    nx: int = 72,
    ny: int = 72,
) -> dict[str, object]:
    """Return a local terrain grid and set tree elevations."""
    width = max(1.0, max_x - min_x)
    depth = max(1.0, max_y - min_y)
    elevation = np.asarray(fire.elevation_m, dtype=float)
    valid = np.isfinite(elevation) & (elevation > 0)
    base = float(np.nanmin(elevation[valid])) if valid.any() else 0.0
    cell = float(fire.grid.cell_size_m)
    xll = float(fire.grid.xll)
    yll = float(fire.grid.yll)
    nrows, ncols = elevation.shape

    def sample(x: float, y: float) -> float:
        col = int(np.floor((x - xll) / cell))
        row = nrows - 1 - int(np.floor((y - yll) / cell))
        if 0 <= row < nrows and 0 <= col < ncols and valid[row, col]:
            return float(elevation[row, col] - base)
        return 0.0

    heights: list[list[float]] = []
    for j in range(ny):
        y = min_y + (j / (ny - 1)) * depth
        row: list[float] = []
        for i in range(nx):
            x = min_x + (i / (nx - 1)) * width
            row.append(sample(x, y))
        heights.append(row)

    def surface(x: float, y: float) -> float:
        fx = min(max((x - min_x) / width, 0.0), 1.0) * (nx - 1)
        fy = min(max((y - min_y) / depth, 0.0), 1.0) * (ny - 1)
        i0 = int(np.floor(fx))
        j0 = int(np.floor(fy))
        i1 = min(i0 + 1, nx - 1)
        j1 = min(j0 + 1, ny - 1)
        tx = fx - i0
        ty = fy - j0
        a = heights[j0][i0] * (1 - tx) + heights[j0][i1] * tx
        b = heights[j1][i0] * (1 - tx) + heights[j1][i1] * tx
        return float(a * (1 - ty) + b * ty)

    for tree in trees:
        tree["z"] = surface(float(tree["x"]) + min_x, float(tree["y"]) + min_y) + 0.15
    return {
        "nx": nx,
        "ny": ny,
        "dx": width / (nx - 1),
        "dy": depth / (ny - 1),
        "heights": heights,
    }


def _model_extent_rings(fire: ObservedFire, growth: Any) -> list[list[list[float]]]:
    """Return the simulated free-burn extent as projected rings."""
    mask = np.isfinite(growth.ignition_time_min)
    if not mask.any():
        return []
    transform = from_origin(
        fire.grid.xll,
        fire.grid.yll + fire.grid.nrows * fire.grid.cell_size_m,
        fire.grid.cell_size_m,
        fire.grid.cell_size_m,
    )
    rings: list[list[list[float]]] = []
    for geometry, value in shapes(
        mask.astype(np.uint8), mask=mask, transform=transform
    ):
        if value != 1:
            continue
        coords = geometry["coordinates"]
        polygons = coords if geometry["type"] == "MultiPolygon" else [coords]
        for polygon in polygons:
            ring = [[float(x), float(y)] for x, y in polygon[0]]
            if len(ring) >= 3:
                rings.append(ring)
    return rings


def _observed_burn_times(
    fire: ObservedFire,
    trees: object,
    cfsds_root: Path,
) -> dict[str, float]:
    """Map CFSDS day-of-burn cells to tree ignition times, when available."""
    case_id = fire.fire_id
    if "_" not in case_id:
        return {}
    year = case_id.split("_", 1)[0]
    archive = cfsds_root / f"{year}_fireDOYrasters.zip"
    if not archive.is_file():
        return {}
    try:
        source = rasterio.open(f"/vsizip/{archive.resolve()}/{case_id}_krig.tif")
    except rasterio.errors.RasterioIOError:
        return {}
    transformer = Transformer.from_crs("EPSG:26911", source.crs, always_xy=True)
    valid = source.read(1)
    days = valid[(valid > 0) & (valid != np.iinfo(valid.dtype).max)]
    if not len(days):
        source.close()
        return {}
    first_day = int(days.min())
    times: dict[str, float] = {}
    for tree in trees.trees:  # type: ignore[attr-defined]
        lon, lat = transformer.transform(tree.x, tree.y)
        try:
            row, col = source.index(lon, lat)
            value = int(source.read(1, window=((row, row + 1), (col, col + 1)))[0, 0])
        except (IndexError, ValueError):
            continue
        if 1 <= value <= 366:
            times[tree.tree_id] = (value - first_day) * 1440.0 + 12.0 * 60.0
    source.close()
    return times


def _radial_observed_times(
    fire: ObservedFire,
    trees: object,
    observed_times: dict[str, float],
) -> dict[str, float]:
    """Order observed tree ignitions radially within each mapped burn day."""
    if not observed_times:
        return {}
    ignition_x, ignition_y = fire.ignition_xy
    groups: dict[int, list[tuple[object, float]]] = {}
    for tree in trees.trees:  # type: ignore[attr-defined]
        value = observed_times.get(tree.tree_id)
        if value is None:
            continue
        day = int(value // 1440.0)
        distance = float(np.hypot(tree.x - ignition_x, tree.y - ignition_y))
        groups.setdefault(day, []).append((tree, distance))
    ordered: dict[str, float] = {}
    for day, items in groups.items():
        distances = [distance for _, distance in items]
        low, high = min(distances), max(distances)
        span = max(1.0, high - low)
        for tree, distance in items:
            fraction = (distance - low) / span
            ordered[tree.tree_id] = day * 1440.0 + 6.0 * 60.0 + fraction * 12.0 * 60.0
    return ordered


def _burn_time_field(
    fire: ObservedFire,
    growth: Any,
    trees: object,
    observed_times: dict[str, float],
    min_x: float,
    min_y: float,
    max_x: float,
    max_y: float,
    nx: int = 384,
    ny: int = 384,
) -> dict[str, object]:
    """Write a compact arrival-time raster for the near-field tree LOD.

    Observed CFSDS scenes use the nearest observed tree day; Dogrib/Hay River
    use the WS4/FBP arrival field. The detail layer samples this raster instead
    of storing millions of individual tree records.
    """
    width = max(1.0, max_x - min_x)
    depth = max(1.0, max_y - min_y)
    values = np.full((ny, nx), np.nan, dtype=float)
    if observed_times:
        points: list[tuple[float, float]] = []
        times: list[float] = []
        for tree in trees.trees:  # type: ignore[attr-defined]
            value = observed_times.get(tree.tree_id)
            if value is None:
                continue
            points.append((float(tree.x) - min_x, float(tree.y) - min_y))
            times.append(float(value))
        if points:
            tree = cKDTree(np.asarray(points, dtype=float))
            for j in range(ny):
                y = min_y + (j / (ny - 1)) * depth
                for i in range(nx):
                    x = min_x + (i / (nx - 1)) * width
                    _, index = tree.query((x - min_x, y - min_y))
                    values[j, i] = times[int(index)]
        mode = "observed_daily"
    else:
        arrival = np.asarray(growth.ignition_time_min, dtype=float)
        nrows, ncols = arrival.shape
        cell = float(fire.grid.cell_size_m)
        xll = float(fire.grid.xll)
        yll = float(fire.grid.yll)
        for j in range(ny):
            y = min_y + (j / (ny - 1)) * depth
            row = nrows - 1 - int(np.floor((y - yll) / cell))
            if not (0 <= row < nrows):
                continue
            for i in range(nx):
                x = min_x + (i / (nx - 1)) * width
                col = int(np.floor((x - xll) / cell))
                if 0 <= col < ncols and np.isfinite(arrival[row, col]):
                    values[j, i] = float(arrival[row, col])
        mode = "model_arrival"
    times_payload = [
        [None if not np.isfinite(value) else round(float(value), 2) for value in row]
        for row in values
    ]
    return {
        "nx": nx,
        "ny": ny,
        "dx": width / (nx - 1),
        "dy": depth / (ny - 1),
        "times": times_payload,
        "duration_min": OBSERVED_BURN_MINUTES if observed_times else TREE_BURN_MINUTES,
        "mode": mode,
    }


def _case_specs() -> list[dict[str, object]]:
    """Return the scene build recipes."""
    return [
        {
            "slug": "dogrib-2001",
            "title": "Dogrib 2001",
            "loader": "dogrib",
            "path": DEFAULT_WS4 / "tests" / "fixtures" / "fire" / "dogrib",
            "seed": 20011016,
        },
        {
            "slug": "hay-river-2023",
            "title": "Hay River 2023",
            "loader": "hay",
            "path": DEFAULT_WS4 / "tests" / "fixtures" / "fire" / "hay_river_2023",
            "seed": 20230514,
        },
        {
            "slug": "cfsds-2003-526",
            "title": "2003_526",
            "loader": "cfsds",
            "path": DEFAULT_WS4 / "tests" / "fixtures" / "fire" / "cfsds_2003_526",
            "seed": 20030820,
        },
        {
            "slug": "cfsds-2023-786",
            "title": "2023_786",
            "loader": "cfsds",
            "path": DEFAULT_WS4 / "tests" / "fixtures" / "fire" / "cfsds_2023_786",
            "seed": 20230722,
        },
        {
            "slug": "cfsds-2003-96-large",
            "title": "2003_96",
            "loader": "cfsds",
            "path": DEFAULT_WS4 / "tests" / "fixtures" / "fire" / "large_2003_96",
            "seed": 20030801,
        },
        {
            "slug": "cfsds-2003-663-large",
            "title": "2003_663",
            "loader": "cfsds",
            "path": DEFAULT_WS4 / "tests" / "fixtures" / "fire" / "large_2003_663",
            "seed": 20030816,
        },
    ]


def _load(spec: dict[str, object]) -> tuple[ObservedFire, float, float, float]:
    """Load a fixture and return the observed fire, FFMC, BUI, and duration."""
    loader = str(spec["loader"])
    path = Path(str(spec["path"]))
    if loader == "dogrib":
        fire = load_dogrib(path)
        weather = reference_weather(fire)
        duration = (fire.event_end - fire.event_start).total_seconds() / 60.0
        return fire, float(weather["ffmc"]), float(weather["bui"]), duration
    if loader == "hay":
        fire = load_hay_river(path)
        duration = (fire.event_end - fire.event_start).total_seconds() / 60.0
        return fire, 92.92, 73.28, duration
    fire = load_cfsds_reanalysis_case(path)
    metadata = json.loads((path / "metadata.json").read_text(encoding="utf-8"))
    return (
        fire,
        float(metadata["ffmc"]),
        float(metadata["bui"]),
        float(metadata["duration_min"]),
    )


def _block_polygons(
    fire: object,
) -> list[tuple[int, tuple[tuple[float, float], ...], float]]:
    """Split the fire bounds into a block mosaic."""
    final_rings = fire.perimeters[-1].rings_projected if fire.perimeters else ()
    if final_rings:
        final_polygon = unary_union([Polygon(ring) for ring in final_rings])
    else:
        final_polygon = Polygon(
            [
                (fire.grid.xll, fire.grid.yll),
                (
                    fire.grid.xll + fire.grid.ncols * fire.grid.cell_size_m,
                    fire.grid.yll,
                ),
                (
                    fire.grid.xll + fire.grid.ncols * fire.grid.cell_size_m,
                    fire.grid.yll + fire.grid.nrows * fire.grid.cell_size_m,
                ),
                (
                    fire.grid.xll,
                    fire.grid.yll + fire.grid.nrows * fire.grid.cell_size_m,
                ),
            ]
        )
    min_x, min_y, max_x, max_y = final_polygon.bounds
    step_x = max(1.0, (max_x - min_x) / BLOCKS_X)
    step_y = max(1.0, (max_y - min_y) / BLOCKS_Y)
    xll = float(min_x)
    yll = float(min_y)
    result: list[tuple[int, tuple[tuple[float, float], ...], float]] = []
    fragment = 1
    for row in range(BLOCKS_Y):
        for col in range(BLOCKS_X):
            x0 = xll + col * step_x
            y0 = yll + row * step_y
            x1 = x0 + step_x
            y1 = y0 + step_y
            ring = ((x0, y0), (x1, y0), (x1, y1), (x0, y1))
            block = Polygon(ring)
            clipped = block.intersection(final_polygon)
            if clipped.is_empty:
                continue
            if clipped.geom_type == "MultiPolygon":
                clipped = max(clipped.geoms, key=lambda item: item.area)
            if clipped.geom_type != "Polygon" or clipped.area <= 0.0:
                continue
            clipped_ring = tuple(
                (float(x), float(y)) for x, y in list(clipped.exterior.coords)[:-1]
            )
            result.append((fragment, clipped_ring, clipped.area / 10_000.0))
            fragment += 1
    return result


def _write_trees(
    blocks: list[tuple[int, tuple[tuple[float, float], ...], float]],
    rng: np.random.Generator,
    tree_path: Path,
    polygon_path: Path,
) -> None:
    """Generate synthetic stems with Nemora placement and write the scene inputs."""
    total_area = sum(item[2] for item in blocks)
    density = min(80.0, MAX_TREES / max(total_area, 1.0))
    frame_rows: list[dict[str, object]] = []
    features: list[dict[str, object]] = []
    for fragment, ring, area_ha in blocks:
        count = max(0, round(area_ha * density))
        polygon = np.array(ring, dtype=float)
        points = place_trees(polygon, count, rng=rng)
        records: list[dict[str, object]] = []
        for index, (x, y) in enumerate(points):
            dbh = float(rng.lognormal(mean=2.85, sigma=0.32))
            records.append(
                {
                    "tree_id": f"{fragment}-{index:05d}",
                    "fragment_id": fragment,
                    "x": float(x),
                    "y": float(y),
                    "dbh": dbh,
                    "species": "Pl" if fragment % 3 else "At",
                    "live": True,
                    "decay_class": 0,
                }
            )
        enriched = attach_tree_attributes(
            records,
            config=TreeAttributeConfig(
                height_a=3.8,
                height_b=0.45,
                crown_ratio=0.45,
                biomass_a=0.05,
                biomass_b=2.35,
            ),
        )
        for record in enriched:
            attrs = record["attributes"]
            height = float(attrs.height_m)
            frame_rows.append(
                {
                    "fragment_id": fragment,
                    "x": record["x"],
                    "y": record["y"],
                    "dbh": record["dbh"],
                    "height": height,
                    "crown_ratio": float(attrs.crown_ratio),
                    "species": record["species"],
                    "biomass": float(attrs.biomass_tonnes) * 1000.0,
                    "live": True,
                    "decay_class": 0,
                    "tree_tag": record["tree_id"],
                }
            )
        features.append(
            {
                "type": "Feature",
                "properties": {"fragment_id": fragment, "area_ha": area_ha},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[list(point) for point in ring] + [list(ring[0])]],
                },
            }
        )
    pd.DataFrame(frame_rows).to_csv(tree_path, index=False)
    polygon_path.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, indent=2)
        + "\n",
        encoding="utf-8",
    )


def build_case(
    spec: dict[str, object], out_root: Path, cfsds_root: Path
) -> dict[str, object]:
    """Build one scene and return its summary."""
    fire, ffmc, bui, duration = _load(spec)
    slug = str(spec["slug"])
    out = out_root / slug
    out.mkdir(parents=True, exist_ok=True)
    start = observed_mask(fire, 0)
    result = run_observed_case(
        fire,
        scenario=slug,
        ffmc=ffmc,
        bui=bui,
        duration_min=duration,
        initial_mask=start,
        neighbor_radius=2,
    )
    blocks = _block_polygons(fire)
    rng = np.random.default_rng(int(str(spec["seed"])))
    tree_csv = out / "nemora_trees.csv"
    polygons_json = out / "stands.geojson"
    _write_trees(blocks, rng, tree_csv, polygons_json)
    trees = load_nemora_scene(
        tree_csv,
        polygons_json,
        seed=int(str(spec["seed"])),
        source="synthetic block mosaic over a public benchmark fire; Nemora stem placement",
        crs="local",
        nemora_version="nemora",
    )
    observed_times = _observed_burn_times(fire, trees, cfsds_root)
    observed_times = _radial_observed_times(fire, trees, observed_times)
    total_area = sum(item[2] for item in blocks)
    _, state, edges = synthetic_grid(
        BLOCKS_Y,
        BLOCKS_X,
        fragment_area_ha=total_area / (BLOCKS_X * BLOCKS_Y),
    )
    fire_run = FireRun(
        state,
        edges,
        FireConfig(ignition_rate_per_fragment_year=0.2, base_spread_probability=0.6),
        scenario_id=slug,
        seed=int(str(spec["seed"])),
    ).run(1)
    scene = compile_fire_scene(
        fire_run,
        trees,
        scene_id=slug,
        particle_budget=7000,
        burn_duration_years=TREE_BURN_MINUTES,
        time_unit="minutes",
    )
    animation = sample_tree_ignition(
        trees,
        result.growth,
        cell_size_m=fire.grid.cell_size_m,
        margin_m=0.0,
        origin_xy=(fire.grid.xll, fire.grid.yll),
        flame_length_m=8.0,
        smoke_strength=0.65,
        burn_duration=TREE_BURN_MINUTES,
    )
    fragment_times = (
        animation.dropna(subset=["ignition_time"])
        .groupby("fragment_id")["ignition_time"]
        .min()
    )
    fires = scene.fires.copy()
    fires["time"] = fires["fragment_id"].map(fragment_times).fillna(0.0)
    fires["year"] = 0
    stands = scene.stands.copy()
    stands["burn_time"] = stands["fragment_id"].map(fragment_times)
    scene = replace(
        scene,
        stands=stands,
        fires=fires,
        animation=animation,
        manifest=replace(
            scene.manifest,
            burn_duration_years=TREE_BURN_MINUTES,
            time_unit="minutes",
            attributes={
                "case": slug,
                "synthetic": True,
                "grid_m": fire.grid.cell_size_m,
            },
        ),
    )
    paths = scene.write(out)
    viewer = paths.viewer.read_text(encoding="utf-8")
    viewer = viewer.replace(
        "<title>WS4 fire scene</title>",
        f"<title>{spec['title']} · FRESH Fire Studio</title>",
    )
    viewer = viewer.replace("<h1>WS4 fire scene</h1>", f"<h1>{spec['title']}</h1>")
    viewer = viewer.replace(
        "renderer.toneMappingExposure = 1.25;", "renderer.toneMappingExposure = 1.35;"
    )
    viewer = viewer.replace(
        "scene.add(new THREE.HemisphereLight(0x9fc8ff, 0x1b140d, 1.2));",
        "scene.add(new THREE.HemisphereLight(0xd8f0ff, 0x52402a, 1.9));",
    )
    viewer = viewer.replace(
        "scene.add(new THREE.AmbientLight(0x9fb8c8, 0.25));",
        "scene.add(new THREE.AmbientLight(0xd0e6ee, 0.65));",
    )
    viewer = viewer.replace(
        "const sun = new THREE.DirectionalLight(0xffe2b8, 1.45);",
        "const sun = new THREE.DirectionalLight(0xffe2b8, 2.0);",
    )
    viewer = viewer.replace(
        "const liveCrown = new THREE.Color(0x4f8f55);",
        "const liveCrown = new THREE.Color(0x9be87e);",
    )
    viewer = viewer.replace(
        "const liveTrunk = new THREE.Color(0x5b3e28);",
        "const liveTrunk = new THREE.Color(0xa87645);",
    )
    viewer = viewer.replace("0.16 / maxDim", "0.08 / maxDim")
    viewer = viewer.replace(
        'const useBloom = new URLSearchParams(location.search).get("bloom") !== "0";',
        'const useBloom = new URLSearchParams(location.search).get("bloom") === "1";',
    )
    viewer = viewer.replace(
        "Synthetic trees over a VRI polygon cluster. P156 FBP growth field; each tree samples the local arrival time.",
        "Synthetic Nemora stems over a public benchmark fire. P156/FBP growth field; each tree samples the local arrival time.",
    )
    viewer = viewer.replace(
        "camera.position.set(cx - maxDim * 0.22, maxDim * 0.12, cz + maxDim * 0.28);",
        "const viewDist = Math.min(maxDim * 0.05, 240); camera.position.set(cx - viewDist * 0.40, viewDist * 2.1, cz + viewDist * 0.75);",
    )
    viewer = viewer.replace(
        "scene.add(trunks, crowns);",
        "trunks.frustumCulled = false; crowns.frustumCulled = false; scene.add(trunks, crowns);",
    )
    viewer = viewer.replace(
        "new THREE.MeshLambertMaterial({ color: 0x2c4a38 })",
        "new THREE.MeshLambertMaterial({ color: DATA.ground_texture ? 0xffffff : 0x2c4a38, map: DATA.ground_texture ? new THREE.TextureLoader().load(DATA.ground_texture) : null })",
    )
    _hillshade(fire, out / "terrain.png")
    import re

    match = re.search(
        r'(<script id="scene-data" type="application/json">)(.*?)(</script>)',
        viewer,
        re.DOTALL,
    )
    if match:
        payload = json.loads(match.group(2))
        min_x = float(payload["bounds"]["min_x"])
        min_y = float(payload["bounds"]["min_y"])
        max_x = float(payload["bounds"]["max_x"])
        max_y = float(payload["bounds"]["max_y"])
        for stand in payload.get("stands", []):
            stand["x"] = float(stand["x"]) - min_x
            stand["y"] = float(stand["y"]) - min_y
            if isinstance(stand.get("polygon"), list):
                stand["polygon"] = [
                    [float(point[0]) - min_x, float(point[1]) - min_y]
                    for point in stand["polygon"]
                ]
        for tree in payload.get("trees", []):
            tree["x"] = float(tree["x"]) - min_x
            tree["y"] = float(tree["y"]) - min_y
        payload["bounds"] = {
            "min_x": 0.0,
            "max_x": max_x - min_x,
            "min_y": 0.0,
            "max_y": max_y - min_y,
        }
        payload["origin_projected"] = [min_x, min_y]
        payload["observed_ha"] = float(result.metrics.area_obs_ha)
        payload["visual_stems_per_ha"] = float(
            len(trees.trees) / max(1.0, result.metrics.area_obs_ha)
        )
        payload["model_ha"] = float(
            np.isfinite(result.growth.ignition_time_min).sum()
            * (fire.grid.cell_size_m**2)
            / 10_000.0
        )
        metadata_path = Path(str(spec["path"])) / "metadata.json"
        observed_daily: list[float] = []
        if metadata_path.is_file():
            observed_daily = [
                float(value)
                for value in json.loads(metadata_path.read_text(encoding="utf-8")).get(
                    "daily_cumuarea_ha", []
                )
            ]
        model_days = int(np.ceil(duration / 1440.0)) + 1
        arrival = result.growth.ignition_time_min
        model_daily = [
            float(
                (np.isfinite(arrival) & (arrival <= day * 1440.0)).sum()
                * (fire.grid.cell_size_m**2)
                / 10_000.0
            )
            for day in range(model_days)
        ]
        payload["observed_daily_area_ha"] = observed_daily
        payload["model_daily_area_ha"] = model_daily
        if observed_daily:
            count = min(len(observed_daily), len(model_daily))
            divergence = next(
                (
                    index + 1
                    for index in range(count)
                    if model_daily[index] > 1.5 * observed_daily[index] + 25.0
                ),
                None,
            )
            payload["divergence_day"] = divergence
        if observed_times:
            for tree in payload.get("trees", []):
                observed = observed_times.get(str(tree["tree_id"]))
                if observed is not None:
                    tree["burn_time"] = observed
                    tree["burn_duration"] = OBSERVED_BURN_MINUTES
            payload["observed_mode"] = "daily_raster"
        else:
            payload["observed_mode"] = "model_timing"
        jitter_span = 0.0 if observed_times else 30.0
        for tree in payload.get("trees", []):
            base = tree.get("burn_time")
            if base is None:
                continue
            digest = int.from_bytes(
                hashlib.blake2b(str(tree["tree_id"]).encode(), digest_size=4).digest(),
                "big",
            )
            if jitter_span > 0:
                tree["burn_time"] = float(base) + (digest % int(jitter_span))
            if observed_times:
                tree["burn_duration"] = OBSERVED_BURN_MINUTES
        ignition_values = [
            float(tree["burn_time"])
            for tree in payload.get("trees", [])
            if tree.get("burn_time") is not None
        ]
        if ignition_values:
            payload["timeline"]["end"] = (
                max(ignition_values) + OBSERVED_BURN_MINUTES * 2.0
            )
            payload["hero_time"] = float(np.quantile(ignition_values, 0.55))
        else:
            payload["hero_time"] = float(payload["timeline"]["end"] * 0.3)
        payload["domain"] = [
            [[float(x) - min_x, float(y) - min_y] for x, y in ring]
            for ring in (fire.perimeters[-1].rings_projected if fire.perimeters else ())
        ]
        payload["model_extent"] = [
            [[float(x) - min_x, float(y) - min_y] for x, y in ring]
            for ring in _model_extent_rings(fire, result.growth)
        ]
        payload["terrain"] = _terrain_payload(
            fire, min_x, min_y, max_x, max_y, payload.get("trees", [])
        )
        payload["burn_field"] = _burn_time_field(
            fire,
            result.growth,
            trees,
            observed_times,
            min_x,
            min_y,
            max_x,
            max_y,
        )
        payload["detail"] = {
            "stems_per_ha": 500,
            "radius_m": 200,
            "min_radius_m": 130,
            "max_radius_m": 300,
            "radius_fraction": 0.65,
            "capacity": 12000,
            "lod_distance_fraction": 0.22,
        }
        # The viewer only needs these tree attributes. Keep the embedded scene
        # compact; the model-side records remain in the build output.
        keep_tree = {
            "x", "y", "z", "height_m", "crown_radius_m",
            "burn_time", "burn_duration", "post_fire_state",
        }
        for tree in payload.get("trees", []):
            for key in list(tree.keys()):
                if key not in keep_tree:
                    del tree[key]
        payload["ground_texture"] = "terrain.png"
        viewer = (
            viewer[: match.start(2)]
            + json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
            + viewer[match.end(2) :]
        )
    paths.viewer.write_text(viewer, encoding="utf-8")
    if match:
        template = PORTAL / "portal" / "viewer-template.html"
        if template.is_file():
            payload_json = json.dumps(payload, separators=(",", ":")).replace(
                "</", "<\\/"
            )
            portal_viewer = template.read_text(encoding="utf-8")
            portal_viewer = portal_viewer.replace("__CASE_TITLE__", str(spec["title"]))
            portal_viewer = portal_viewer.replace("__SCENE_DATA__", payload_json)
            paths.viewer.write_text(portal_viewer, encoding="utf-8")
    for extra in (
        "payload.json",
        "trees.parquet",
        "stands.parquet",
        "animation.parquet",
        "event_log.json",
        "fires.csv",
        "nemora_trees.csv",
        "stands.geojson",
    ):
        candidate = out / extra
        if candidate.is_file():
            candidate.unlink()
    summary = {
        "slug": slug,
        "title": spec["title"],
        "trees": len(trees.trees),
        "fragments": len(blocks),
        "grid_m": fire.grid.cell_size_m,
        "area_ha": float(result.metrics.area_obs_ha),
        "sim_area_ha": float(result.metrics.area_sim_ha),
        "iou": float(result.metrics.iou),
        "duration_min": duration,
        "ffmc": ffmc,
        "bui": bui,
        "viewer": f"/static/scenes/{slug}/viewer.html",
        "observed_mode": "daily_raster" if observed_times else "model_timing",
        "visual_stems_per_ha": float(
            len(trees.trees) / max(1.0, result.metrics.area_obs_ha)
        ),
        "model_area_ha": float(
            np.isfinite(result.growth.ignition_time_min).sum()
            * (fire.grid.cell_size_m**2)
            / 10_000.0
        ),
    }
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    """Build all configured scenes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", type=Path, default=PORTAL / "portal" / "static" / "scenes"
    )
    parser.add_argument("--only", nargs="*", default=None)
    parser.add_argument("--cfsds-root", type=Path, default=DEFAULT_CFSDS)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    summaries = []
    for spec in _case_specs():
        if args.only and spec["slug"] not in args.only:
            continue
        print(f"building {spec['slug']}...", flush=True)
        summaries.append(build_case(spec, args.out, args.cfsds_root))
    (PORTAL / "config" / "scene_summaries.json").write_text(
        json.dumps({"scenes": summaries}, indent=2) + "\n", encoding="utf-8"
    )
    for summary in summaries:
        print(
            f"{summary['slug']}: {summary['trees']} trees, {summary['fragments']} stands, "
            f"IoU {summary['iou']:.3f}"
        )


if __name__ == "__main__":
    main()
