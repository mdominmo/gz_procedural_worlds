from __future__ import annotations

import heapq
import math

import numpy as np

from .renderer import PlacedObstacle


class OccupancyGrid:
    def __init__(
        self,
        size_x: float,
        size_y: float,
        resolution: float = 0.5,
        origin_x: float = 0.0,
        origin_y: float = 0.0,
    ):
        self.size_x = size_x
        self.size_y = size_y
        self.resolution = resolution
        self.origin_x = origin_x
        self.origin_y = origin_y
        self.cols = int(math.ceil(size_x / resolution))
        self.rows = int(math.ceil(size_y / resolution))
        self.grid = np.zeros((self.rows, self.cols), dtype=bool)

    def world_to_grid(self, x: float, y: float) -> tuple[int, int]:
        col = int((x - self.origin_x + self.size_x / 2) / self.resolution)
        row = int((y - self.origin_y + self.size_y / 2) / self.resolution)
        return row, col

    def grid_to_world(self, row: int, col: int) -> tuple[float, float]:
        x = col * self.resolution + self.origin_x - self.size_x / 2 + self.resolution / 2
        y = row * self.resolution + self.origin_y - self.size_y / 2 + self.resolution / 2
        return x, y

    def mark_obstacle(
        self, x: float, y: float, radius: float
    ) -> None:
        r_cells = int(math.ceil(radius / self.resolution))
        center_row, center_col = self.world_to_grid(x, y)
        for dr in range(-r_cells, r_cells + 1):
            for dc in range(-r_cells, r_cells + 1):
                r = center_row + dr
                c = center_col + dc
                if 0 <= r < self.rows and 0 <= c < self.cols:
                    dist = math.sqrt(dr**2 + dc**2) * self.resolution
                    if dist <= radius:
                        self.grid[r, c] = True

    def clear_obstacle(
        self, x: float, y: float, radius: float
    ) -> None:
        r_cells = int(math.ceil(radius / self.resolution))
        center_row, center_col = self.world_to_grid(x, y)
        for dr in range(-r_cells, r_cells + 1):
            for dc in range(-r_cells, r_cells + 1):
                r = center_row + dr
                c = center_col + dc
                if 0 <= r < self.rows and 0 <= c < self.cols:
                    dist = math.sqrt(dr**2 + dc**2) * self.resolution
                    if dist <= radius:
                        self.grid[r, c] = False

    def is_free(self, row: int, col: int) -> bool:
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return not self.grid[row, col]
        return False


def astar(
    grid: OccupancyGrid,
    start: tuple[float, float],
    goal: tuple[float, float],
) -> list[tuple[int, int]] | None:
    sr, sc = grid.world_to_grid(*start)
    gr, gc = grid.world_to_grid(*goal)

    if not grid.is_free(sr, sc) or not grid.is_free(gr, gc):
        return None

    def heuristic(r: int, c: int) -> float:
        return math.sqrt((r - gr) ** 2 + (c - gc) ** 2)

    open_set: list[tuple[float, int, int]] = [(heuristic(sr, sc), sr, sc)]
    g_score: dict[tuple[int, int], float] = {(sr, sc): 0}
    came_from: dict[tuple[int, int], tuple[int, int]] = {}

    neighbors = [(-1, 0), (1, 0), (0, -1), (0, 1),
                 (-1, -1), (-1, 1), (1, -1), (1, 1)]

    while open_set:
        _, cr, cc = heapq.heappop(open_set)

        if cr == gr and cc == gc:
            path = [(cr, cc)]
            while (cr, cc) in came_from:
                cr, cc = came_from[(cr, cc)]
                path.append((cr, cc))
            path.reverse()
            return path

        current_g = g_score.get((cr, cc), float("inf"))

        for dr, dc in neighbors:
            nr, nc = cr + dr, cc + dc
            if not grid.is_free(nr, nc):
                continue
            move_cost = 1.414 if (dr != 0 and dc != 0) else 1.0
            tentative_g = current_g + move_cost
            if tentative_g < g_score.get((nr, nc), float("inf")):
                g_score[(nr, nc)] = tentative_g
                came_from[(nr, nc)] = (cr, cc)
                f = tentative_g + heuristic(nr, nc)
                heapq.heappush(open_set, (f, nr, nc))

    return None


def validate_connectivity(
    obstacles: list[PlacedObstacle],
    size_x: float,
    size_y: float,
    check_altitude: float,
    safety_margin: float,
    start: tuple[float, float],
    goals: list[tuple[float, float]],
    max_removal_iterations: int = 50,
    resolution: float = 0.5,
) -> tuple[list[PlacedObstacle], OccupancyGrid]:
    grid = OccupancyGrid(size_x, size_y, resolution)

    blocking: list[int] = []
    for i, obs in enumerate(obstacles):
        if obs.height > check_altitude:
            effective_radius = obs.bbox_radius + safety_margin
            grid.mark_obstacle(obs.x, obs.y, effective_radius)
            blocking.append(i)

    remaining = list(obstacles)
    removed_count = 0

    for _ in range(max_removal_iterations):
        all_reachable = True
        worst_goal = None

        for goal in goals:
            path = astar(grid, start, goal)
            if path is None:
                all_reachable = False
                worst_goal = goal
                break

        if all_reachable:
            break

        best_idx = None
        best_dist = float("inf")
        mid_x = (start[0] + worst_goal[0]) / 2
        mid_y = (start[1] + worst_goal[1]) / 2

        for i, obs in enumerate(remaining):
            if obs.height <= check_altitude:
                continue
            dist = math.sqrt((obs.x - mid_x) ** 2 + (obs.y - mid_y) ** 2)
            if dist < best_dist:
                best_dist = dist
                best_idx = i

        if best_idx is None:
            break

        removed = remaining[best_idx]
        effective_radius = removed.bbox_radius + safety_margin
        grid.clear_obstacle(removed.x, removed.y, effective_radius)
        remaining.pop(best_idx)
        removed_count += 1

    if removed_count > 0:
        for goal in goals:
            if astar(grid, start, goal) is None:
                raise RuntimeError(
                    f"Could not establish connectivity to goal {goal} "
                    f"after removing {removed_count} obstacles"
                )

    return remaining, grid
