from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


@dataclass
class PlacedObstacle:
    model_name: str
    instance_name: str
    x: float
    y: float
    z: float = 0.0
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0
    bbox_radius: float = 1.0
    height: float = 1.0


def render_world(
    *,
    world_name: str,
    seed: int | None,
    ground_plane_size: float,
    spherical_coordinates: dict,
    obstacles: list[PlacedObstacle],
    sun_direction: list[float],
    sun_intensity: float,
    ambient: list[float],
    template_dir: str | Path | None = None,
    template_name: str = "world_base.sdf.j2",
) -> str:
    if template_dir is None:
        template_dir = Path(__file__).resolve().parent.parent.parent / "templates"

    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        keep_trailing_newline=True,
    )
    template = env.get_template(template_name)

    return template.render(
        world_name=world_name,
        seed=seed,
        ground_plane_size=ground_plane_size,
        spherical_coordinates=spherical_coordinates,
        obstacles=obstacles,
        sun_direction=sun_direction,
        sun_intensity=sun_intensity,
        ambient=ambient,
    )
