from __future__ import annotations

import math
import random
from dataclasses import dataclass

from .config import (
    AreaBoundsConfig,
    AreaConfig,
    CorridorConfig,
    ObstacleGroupConfig,
    PerimeterConfig,
    SpawnZoneConfig,
)
from .renderer import PlacedObstacle


@dataclass
class PlacementContext:
    area: AreaConfig
    spawn_zone: SpawnZoneConfig
    rng: random.Random


def _in_spawn_zone(x: float, y: float, ctx: PlacementContext) -> bool:
    cx, cy = ctx.spawn_zone.center
    dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    return dist < ctx.spawn_zone.radius


def _respects_spacing(
    x: float,
    y: float,
    placed: list[PlacedObstacle],
    min_spacing: float,
) -> bool:
    for obs in placed:
        dist = math.sqrt((x - obs.x) ** 2 + (y - obs.y) ** 2)
        if dist < min_spacing:
            return False
    return True


def _get_bounds(
    area: AreaConfig, area_bounds: AreaBoundsConfig | None
) -> tuple[float, float, float, float]:
    half_x = area.size_x / 2
    half_y = area.size_y / 2
    if area_bounds:
        return (
            max(area_bounds.x_min, -half_x),
            min(area_bounds.x_max, half_x),
            max(area_bounds.y_min, -half_y),
            min(area_bounds.y_max, half_y),
        )
    return (-half_x, half_x, -half_y, half_y)


def place_random(
    group: ObstacleGroupConfig,
    ctx: PlacementContext,
    existing: list[PlacedObstacle],
) -> list[PlacedObstacle]:
    x_min, x_max, y_min, y_max = _get_bounds(ctx.area, group.area_bounds)
    placed: list[PlacedObstacle] = []
    max_attempts = group.count * 100

    for attempt in range(max_attempts):
        if len(placed) >= group.count:
            break
        x = ctx.rng.uniform(x_min, x_max)
        y = ctx.rng.uniform(y_min, y_max)
        if _in_spawn_zone(x, y, ctx):
            continue
        if not _respects_spacing(x, y, existing + placed, group.min_spacing):
            continue
        yaw = ctx.rng.uniform(0, 2 * math.pi) if group.yaw_random else 0.0
        idx = len(existing) + len(placed)
        placed.append(
            PlacedObstacle(
                model_name=group.model,
                instance_name=f"{group.model}_{idx}",
                x=x,
                y=y,
                z=0.0,
                yaw=yaw,
                bbox_radius=group.bbox_radius,
                height=group.height,
            )
        )
    return placed


def place_clustered(
    group: ObstacleGroupConfig,
    ctx: PlacementContext,
    existing: list[PlacedObstacle],
) -> list[PlacedObstacle]:
    """Poisson disk-like sampling: pick cluster centers, then scatter around them."""
    x_min, x_max, y_min, y_max = _get_bounds(ctx.area, group.area_bounds)
    placed: list[PlacedObstacle] = []

    num_clusters = max(1, group.count // 5)
    cluster_radius = min(
        (x_max - x_min) / (num_clusters + 1),
        (y_max - y_min) / (num_clusters + 1),
    ) * 0.6

    centers = []
    for _ in range(num_clusters * 20):
        if len(centers) >= num_clusters:
            break
        cx = ctx.rng.uniform(x_min + cluster_radius, x_max - cluster_radius)
        cy = ctx.rng.uniform(y_min + cluster_radius, y_max - cluster_radius)
        if _in_spawn_zone(cx, cy, ctx):
            continue
        if all(
            math.sqrt((cx - c[0]) ** 2 + (cy - c[1]) ** 2) > cluster_radius * 2
            for c in centers
        ):
            centers.append((cx, cy))

    if not centers:
        centers = [(0.0, 0.0)]

    max_attempts = group.count * 100
    for attempt in range(max_attempts):
        if len(placed) >= group.count:
            break
        cx, cy = ctx.rng.choice(centers)
        angle = ctx.rng.uniform(0, 2 * math.pi)
        radius = ctx.rng.gauss(0, cluster_radius / 2)
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        x = max(x_min, min(x_max, x))
        y = max(y_min, min(y_max, y))
        if _in_spawn_zone(x, y, ctx):
            continue
        if not _respects_spacing(x, y, existing + placed, group.min_spacing):
            continue
        yaw = ctx.rng.uniform(0, 2 * math.pi) if group.yaw_random else 0.0
        idx = len(existing) + len(placed)
        placed.append(
            PlacedObstacle(
                model_name=group.model,
                instance_name=f"{group.model}_{idx}",
                x=x,
                y=y,
                z=0.0,
                yaw=yaw,
                bbox_radius=group.bbox_radius,
                height=group.height,
            )
        )
    return placed


def place_grid_jitter(
    group: ObstacleGroupConfig,
    ctx: PlacementContext,
    existing: list[PlacedObstacle],
) -> list[PlacedObstacle]:
    x_min, x_max, y_min, y_max = _get_bounds(ctx.area, group.area_bounds)
    cols = max(1, int(math.sqrt(group.count * (x_max - x_min) / (y_max - y_min))))
    rows = max(1, int(math.ceil(group.count / cols)))
    dx = (x_max - x_min) / (cols + 1)
    dy = (y_max - y_min) / (rows + 1)
    jitter = min(dx, dy) * 0.3

    placed: list[PlacedObstacle] = []
    for row in range(rows):
        for col in range(cols):
            if len(placed) >= group.count:
                break
            base_x = x_min + dx * (col + 1)
            base_y = y_min + dy * (row + 1)
            x = base_x + ctx.rng.uniform(-jitter, jitter)
            y = base_y + ctx.rng.uniform(-jitter, jitter)
            if _in_spawn_zone(x, y, ctx):
                continue
            if not _respects_spacing(x, y, existing + placed, group.min_spacing):
                continue
            yaw = ctx.rng.uniform(0, 2 * math.pi) if group.yaw_random else 0.0
            idx = len(existing) + len(placed)
            placed.append(
                PlacedObstacle(
                    model_name=group.model,
                    instance_name=f"{group.model}_{idx}",
                    x=x,
                    y=y,
                    z=0.0,
                    yaw=yaw,
                    bbox_radius=group.bbox_radius,
                    height=group.height,
                )
            )
    return placed


def place_perimeter(
    group: ObstacleGroupConfig,
    ctx: PlacementContext,
    existing: list[PlacedObstacle],
) -> list[PlacedObstacle]:
    x_min, x_max, y_min, y_max = _get_bounds(ctx.area, group.area_bounds)
    offset = group.perimeter.offset if group.perimeter else 5.0

    ix_min = x_min + offset
    ix_max = x_max - offset
    iy_min = y_min + offset
    iy_max = y_max - offset
    perimeter = 2 * (ix_max - ix_min) + 2 * (iy_max - iy_min)
    step = perimeter / group.count

    placed: list[PlacedObstacle] = []
    for i in range(group.count):
        d = step * i
        w = ix_max - ix_min
        h = iy_max - iy_min
        if d < w:
            x, y = ix_min + d, iy_min
        elif d < w + h:
            x, y = ix_max, iy_min + (d - w)
        elif d < 2 * w + h:
            x, y = ix_max - (d - w - h), iy_max
        else:
            x, y = ix_min, iy_max - (d - 2 * w - h)

        if _in_spawn_zone(x, y, ctx):
            continue
        yaw = ctx.rng.uniform(0, 2 * math.pi) if group.yaw_random else 0.0
        idx = len(existing) + len(placed)
        placed.append(
            PlacedObstacle(
                model_name=group.model,
                instance_name=f"{group.model}_{idx}",
                x=x,
                y=y,
                z=0.0,
                yaw=yaw,
                bbox_radius=group.bbox_radius,
                height=group.height,
            )
        )
    return placed


def place_corridor(
    group: ObstacleGroupConfig,
    ctx: PlacementContext,
    existing: list[PlacedObstacle],
) -> list[PlacedObstacle]:
    """Place wall segments along randomly generated corridor paths."""
    x_min, x_max, y_min, y_max = _get_bounds(ctx.area, group.area_bounds)
    corridor_cfg = group.corridor or CorridorConfig()
    half_width = corridor_cfg.width / 2
    num_segments = corridor_cfg.segments

    placed: list[PlacedObstacle] = []
    walls_per_segment = max(1, group.count // num_segments)

    for seg in range(num_segments):
        if len(placed) >= group.count:
            break

        if corridor_cfg.direction == "random":
            angle = ctx.rng.uniform(0, math.pi)
        else:
            angle = float(corridor_cfg.direction)

        cx = ctx.rng.uniform(x_min * 0.5, x_max * 0.5)
        cy = ctx.rng.uniform(y_min * 0.5, y_max * 0.5)
        if _in_spawn_zone(cx, cy, ctx):
            continue

        dx = math.cos(angle)
        dy = math.sin(angle)
        nx, ny = -dy, dx

        wall_length = 4.0
        total_length = walls_per_segment * (wall_length + group.min_spacing)

        for i in range(walls_per_segment):
            if len(placed) >= group.count:
                break
            t = -total_length / 2 + i * (wall_length + group.min_spacing)
            for side in [1, -1]:
                wx = cx + t * dx + side * half_width * nx
                wy = cy + t * dy + side * half_width * ny
                if wx < x_min or wx > x_max or wy < y_min or wy > y_max:
                    continue
                if _in_spawn_zone(wx, wy, ctx):
                    continue
                if not _respects_spacing(
                    wx, wy, existing + placed, group.min_spacing
                ):
                    continue
                idx = len(existing) + len(placed)
                placed.append(
                    PlacedObstacle(
                        model_name=group.model,
                        instance_name=f"{group.model}_{idx}",
                        x=wx,
                        y=wy,
                        z=0.0,
                        yaw=angle,
                        bbox_radius=group.bbox_radius,
                        height=group.height,
                    )
                )
                if len(placed) >= group.count:
                    break
    return placed


DISTRIBUTION_STRATEGIES = {
    "random": place_random,
    "clustered": place_clustered,
    "grid_jitter": place_grid_jitter,
    "perimeter": place_perimeter,
    "corridor": place_corridor,
}


def place_obstacles(
    group: ObstacleGroupConfig,
    ctx: PlacementContext,
    existing: list[PlacedObstacle],
) -> list[PlacedObstacle]:
    strategy = DISTRIBUTION_STRATEGIES.get(group.distribution)
    if strategy is None:
        raise ValueError(
            f"Unknown distribution '{group.distribution}'. "
            f"Available: {list(DISTRIBUTION_STRATEGIES.keys())}"
        )
    return strategy(group, ctx, existing)
