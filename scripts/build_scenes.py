"""Build the benchmark fire scenes for the Fresh Fire portal.

Each scene is a standalone WS4 3D viewer plus a summary JSON. The tree layer is a
Nemora-derived synthetic stem population, not a measured inventory.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from shapely.geometry import Polygon
from shapely.ops import unary_union

PORTAL = Path(__file__).resolve().parents[1]
DEFAULT_WS4 = Path("/srv/shared-data/gep/ws4/.opencode/tmp/opencode/ws4-p176")
DEFAULT_NEMORA = Path("/srv/shared-data/gep/ws4/nemora/src")
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
MAX_TREES = 16000
TREE_BURN_MINUTES = 2.0


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
    for tree in trees:
        tree["z"] = sample(float(tree["x"]) + min_x, float(tree["y"]) + min_y)
    return {
        "nx": nx,
        "ny": ny,
        "dx": width / (nx - 1),
        "dy": depth / (ny - 1),
        "heights": heights,
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
    centre = final_polygon.centroid
    half = 900.0  # 1.8 km stand-scale detail window; case metrics still describe the full fire
    xll = float(centre.x - half)
    yll = float(centre.y - half)
    step_x = (half * 2.0) / BLOCKS_X
    step_y = (half * 2.0) / BLOCKS_Y
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


def build_case(spec: dict[str, object], out_root: Path) -> dict[str, object]:
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
        "<title>WS4 fire scene</title>", f"<title>{spec['title']} · Fresh Fire</title>"
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
        payload["domain"] = [
            [[float(x) - min_x, float(y) - min_y] for x, y in ring]
            for ring in (fire.perimeters[-1].rings_projected if fire.perimeters else ())
        ]
        payload["terrain"] = _terrain_payload(
            fire, min_x, min_y, max_x, max_y, payload.get("trees", [])
        )
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
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    summaries = []
    for spec in _case_specs():
        if args.only and spec["slug"] not in args.only:
            continue
        print(f"building {spec['slug']}...", flush=True)
        summaries.append(build_case(spec, args.out))
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
