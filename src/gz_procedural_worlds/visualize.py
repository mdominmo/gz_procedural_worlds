from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from .renderer import PlacedObstacle


MODEL_COLORS = {
    "Pine Tree": "#228B22",
    "Standing person": "#FF6347",
    "Walking person": "#FF4500",
    "wall_segment": "#808080",
    "wall_segment_tall": "#505050",
    "concrete_barrier": "#A0A0A0",
    "pole": "#333333",
}


def visualize_world(
    obstacles: list[PlacedObstacle],
    size_x: float,
    size_y: float,
    spawn_zone_center: tuple[float, float] = (0.0, 0.0),
    spawn_zone_radius: float = 5.0,
    start: tuple[float, float] = (0.0, 0.0),
    goals: list[tuple[float, float]] | None = None,
    output_path: str | Path = "world_layout.png",
) -> None:
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    half_x = size_x / 2
    half_y = size_y / 2
    ax.set_xlim(-half_x, half_x)
    ax.set_ylim(-half_y, half_y)
    ax.set_aspect("equal")
    ax.set_facecolor("#F5F5DC")
    ax.grid(True, alpha=0.3)
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_title("Procedural World Layout (top-down)")

    spawn = plt.Circle(
        spawn_zone_center,
        spawn_zone_radius,
        fill=True,
        facecolor="#ADD8E6",
        edgecolor="#4169E1",
        alpha=0.4,
        linewidth=2,
        label="Spawn zone",
    )
    ax.add_patch(spawn)

    legend_entries: dict[str, mpatches.Patch] = {}
    for obs in obstacles:
        color = MODEL_COLORS.get(obs.model_name, "#888888")
        circle = plt.Circle(
            (obs.x, obs.y),
            obs.bbox_radius,
            fill=True,
            facecolor=color,
            edgecolor="black",
            alpha=0.7,
            linewidth=0.5,
        )
        ax.add_patch(circle)
        if obs.model_name not in legend_entries:
            legend_entries[obs.model_name] = mpatches.Patch(
                color=color, label=obs.model_name
            )

    ax.plot(
        start[0], start[1], "^", color="blue", markersize=12, label="Start"
    )

    if goals:
        for i, goal in enumerate(goals):
            label = "Goal" if i == 0 else None
            ax.plot(
                goal[0], goal[1], "*", color="red", markersize=14, label=label
            )

    handles = [
        mpatches.Patch(color="#ADD8E6", alpha=0.4, label="Spawn zone"),
        plt.Line2D([], [], marker="^", color="blue", linestyle="None",
                   markersize=10, label="Start"),
        plt.Line2D([], [], marker="*", color="red", linestyle="None",
                   markersize=10, label="Goal"),
    ]
    handles.extend(legend_entries.values())
    ax.legend(handles=handles, loc="upper right", fontsize=8)

    plt.tight_layout()
    plt.savefig(str(output_path), dpi=150)
    plt.close(fig)
