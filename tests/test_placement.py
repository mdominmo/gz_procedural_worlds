import math
import random

from gz_procedural_worlds.config import (
    AreaConfig,
    ObstacleGroupConfig,
    SpawnZoneConfig,
)
from gz_procedural_worlds.placement import PlacementContext, place_obstacles


def _make_ctx(seed=42, area_size=100.0, spawn_radius=5.0):
    return PlacementContext(
        area=AreaConfig(size_x=area_size, size_y=area_size),
        spawn_zone=SpawnZoneConfig(center=[0.0, 0.0], radius=spawn_radius),
        rng=random.Random(seed),
    )


def test_random_count():
    ctx = _make_ctx()
    group = ObstacleGroupConfig(
        model="Pine Tree", count=15, distribution="random",
        min_spacing=3.0, bbox_radius=1.5, height=8.0,
    )
    result = place_obstacles(group, ctx, [])
    assert len(result) == 15


def test_spawn_zone_exclusion():
    ctx = _make_ctx(spawn_radius=10.0)
    group = ObstacleGroupConfig(
        model="Pine Tree", count=20, distribution="random",
        min_spacing=2.0, bbox_radius=1.5, height=8.0,
    )
    result = place_obstacles(group, ctx, [])
    for obs in result:
        dist = math.sqrt(obs.x**2 + obs.y**2)
        assert dist >= 10.0


def test_min_spacing_respected():
    ctx = _make_ctx()
    group = ObstacleGroupConfig(
        model="Pine Tree", count=10, distribution="random",
        min_spacing=5.0, bbox_radius=1.5, height=8.0,
    )
    result = place_obstacles(group, ctx, [])
    for i, a in enumerate(result):
        for b in result[i + 1:]:
            dist = math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)
            assert dist >= 5.0


def test_within_bounds():
    ctx = _make_ctx(area_size=50.0)
    group = ObstacleGroupConfig(
        model="Pine Tree", count=10, distribution="random",
        min_spacing=2.0, bbox_radius=1.5, height=8.0,
    )
    result = place_obstacles(group, ctx, [])
    for obs in result:
        assert -25.0 <= obs.x <= 25.0
        assert -25.0 <= obs.y <= 25.0


def test_clustered_produces_obstacles():
    ctx = _make_ctx()
    group = ObstacleGroupConfig(
        model="Pine Tree", count=20, distribution="clustered",
        min_spacing=3.0, bbox_radius=1.5, height=8.0,
    )
    result = place_obstacles(group, ctx, [])
    assert len(result) > 0


def test_grid_jitter_produces_obstacles():
    ctx = _make_ctx()
    group = ObstacleGroupConfig(
        model="pole", count=9, distribution="grid_jitter",
        min_spacing=5.0, bbox_radius=0.15, height=4.0,
    )
    result = place_obstacles(group, ctx, [])
    assert len(result) > 0


def test_perimeter_produces_obstacles():
    from gz_procedural_worlds.config import PerimeterConfig

    ctx = _make_ctx()
    group = ObstacleGroupConfig(
        model="concrete_barrier", count=8, distribution="perimeter",
        min_spacing=3.0, bbox_radius=1.1, height=1.0,
        perimeter=PerimeterConfig(offset=5.0),
    )
    result = place_obstacles(group, ctx, [])
    assert len(result) > 0


def test_unknown_distribution_raises():
    import pytest

    ctx = _make_ctx()
    group = ObstacleGroupConfig(
        model="Pine Tree", count=5, distribution="nonexistent",
        min_spacing=3.0, bbox_radius=1.5, height=8.0,
    )
    with pytest.raises(ValueError, match="Unknown distribution"):
        place_obstacles(group, ctx, [])
