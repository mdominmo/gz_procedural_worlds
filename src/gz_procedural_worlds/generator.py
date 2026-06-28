from __future__ import annotations

import random
import shutil
from dataclasses import asdict
from pathlib import Path

from .config import WorldGenerationConfig, load_config
from .connectivity import validate_connectivity
from .placement import PlacementContext, place_obstacles
from .renderer import PlacedObstacle, render_world
from .models import MODEL_REGISTRY


def _resolve_output_dir(project_root: Path) -> Path:
    submodule_worlds = project_root / "px4-sitl-docker-sim" / "gz_assets" / "worlds"
    if submodule_worlds.parent.exists():
        submodule_worlds.mkdir(parents=True, exist_ok=True)
        return submodule_worlds
    output = project_root / "output"
    output.mkdir(parents=True, exist_ok=True)
    return output


def _sync_models(project_root: Path) -> None:
    local_models = project_root / "models"
    target_models = project_root / "px4-sitl-docker-sim" / "gz_assets" / "models"

    if not target_models.exists():
        return

    for model_dir in local_models.iterdir():
        if not model_dir.is_dir():
            continue
        dest = target_models / model_dir.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(model_dir, dest)


def generate_world(
    config: WorldGenerationConfig,
    output_dir: Path | None = None,
    project_root: Path | None = None,
    sync_models: bool = True,
    seed_override: int | None = None,
) -> tuple[Path, list[PlacedObstacle]]:
    if project_root is None:
        project_root = Path(__file__).resolve().parent.parent.parent

    if output_dir is None:
        output_dir = _resolve_output_dir(project_root)

    seed = seed_override if seed_override is not None else config.world.seed
    if seed is None:
        seed = random.randint(0, 2**31 - 1)

    rng = random.Random(seed)

    ctx = PlacementContext(
        area=config.area,
        spawn_zone=config.spawn_zone,
        rng=rng,
    )

    all_obstacles: list[PlacedObstacle] = []
    for group in config.obstacles:
        new_obstacles = place_obstacles(group, ctx, all_obstacles)
        all_obstacles.extend(new_obstacles)

    if config.connectivity.enabled:
        start = tuple(config.connectivity.start)
        goals = [tuple(g) for g in config.connectivity.goals]
        all_obstacles, _ = validate_connectivity(
            obstacles=all_obstacles,
            size_x=config.area.size_x,
            size_y=config.area.size_y,
            check_altitude=config.connectivity.check_altitude,
            safety_margin=config.connectivity.safety_margin,
            start=start,
            goals=goals,
            max_removal_iterations=config.connectivity.max_removal_iterations,
        )

    if sync_models:
        _sync_models(project_root)

    sdf_content = render_world(
        world_name=config.world.name,
        seed=seed,
        ground_plane_size=config.area.ground_plane_size,
        spherical_coordinates=asdict(config.spherical_coordinates),
        obstacles=all_obstacles,
        sun_direction=config.lighting.sun_direction,
        sun_intensity=config.lighting.sun_intensity,
        ambient=config.lighting.ambient,
        template_dir=project_root / "templates",
    )

    output_path = output_dir / f"{config.world.name}.sdf"
    output_path.write_text(sdf_content)

    return output_path, all_obstacles


def generate_from_config_file(
    config_path: str | Path,
    output_dir: Path | None = None,
    seed_override: int | None = None,
    sync_models: bool = True,
) -> tuple[Path, list[PlacedObstacle]]:
    config = load_config(config_path)
    return generate_world(
        config,
        output_dir=output_dir,
        sync_models=sync_models,
        seed_override=seed_override,
    )
