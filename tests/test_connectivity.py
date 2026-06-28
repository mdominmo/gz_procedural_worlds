import pytest

from gz_procedural_worlds.connectivity import (
    OccupancyGrid,
    astar,
    validate_connectivity,
)
from gz_procedural_worlds.renderer import PlacedObstacle


def test_empty_grid_finds_path():
    grid = OccupancyGrid(50.0, 50.0, resolution=1.0)
    path = astar(grid, (0.0, 0.0), (20.0, 20.0))
    assert path is not None
    assert len(path) > 0


def test_blocked_start_returns_none():
    grid = OccupancyGrid(50.0, 50.0, resolution=1.0)
    grid.mark_obstacle(0.0, 0.0, 3.0)
    path = astar(grid, (0.0, 0.0), (20.0, 20.0))
    assert path is None


def test_mark_and_clear():
    grid = OccupancyGrid(50.0, 50.0, resolution=1.0)
    grid.mark_obstacle(10.0, 10.0, 5.0)
    r, c = grid.world_to_grid(10.0, 10.0)
    assert not grid.is_free(r, c)
    grid.clear_obstacle(10.0, 10.0, 5.0)
    assert grid.is_free(r, c)


def test_validate_removes_blocking_obstacles():
    obstacles = [
        PlacedObstacle(
            model_name="Pine Tree",
            instance_name=f"tree_{i}",
            x=float(i * 2 - 50),
            y=0.0,
            bbox_radius=2.0,
            height=8.0,
        )
        for i in range(51)
    ]
    remaining, grid = validate_connectivity(
        obstacles=obstacles,
        size_x=100.0,
        size_y=100.0,
        check_altitude=3.0,
        safety_margin=1.5,
        start=(0.0, -20.0),
        goals=[(0.0, 20.0)],
        max_removal_iterations=30,
    )
    assert len(remaining) < len(obstacles)


def test_short_obstacles_not_blocking():
    obstacles = [
        PlacedObstacle(
            model_name="concrete_barrier",
            instance_name=f"barrier_{i}",
            x=float(i * 2 - 10),
            y=0.0,
            bbox_radius=1.1,
            height=1.0,
        )
        for i in range(11)
    ]
    remaining, _ = validate_connectivity(
        obstacles=obstacles,
        size_x=100.0,
        size_y=100.0,
        check_altitude=3.0,
        safety_margin=1.0,
        start=(0.0, -20.0),
        goals=[(0.0, 20.0)],
    )
    assert len(remaining) == len(obstacles)
