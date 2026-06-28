from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .models import MODEL_REGISTRY


@dataclass
class WorldConfig:
    name: str = "procedural_world"
    seed: int | None = None
    description: str = ""


@dataclass
class AreaConfig:
    size_x: float = 100.0
    size_y: float = 100.0
    ground_plane_size: float = 100.0
    origin_offset: list[float] = field(default_factory=lambda: [0.0, 0.0])


@dataclass
class SpawnZoneConfig:
    center: list[float] = field(default_factory=lambda: [0.0, 0.0])
    radius: float = 5.0


@dataclass
class SphericalCoordinatesConfig:
    latitude_deg: float = 52.11486
    longitude_deg: float = -6.613
    elevation: float = 2.0
    heading_deg: float = 0.0


@dataclass
class ConnectivityConfig:
    enabled: bool = True
    check_altitude: float = 3.0
    safety_margin: float = 1.5
    start: list[float] = field(default_factory=lambda: [0.0, 0.0])
    goals: list[list[float]] = field(
        default_factory=lambda: [[40.0, 40.0], [-40.0, -40.0]]
    )
    max_removal_iterations: int = 50


@dataclass
class CorridorConfig:
    width: float = 4.0
    segments: int = 3
    direction: str = "random"


@dataclass
class PerimeterConfig:
    offset: float = 5.0


@dataclass
class AreaBoundsConfig:
    x_min: float = -45.0
    x_max: float = 45.0
    y_min: float = -45.0
    y_max: float = 45.0


@dataclass
class ObstacleGroupConfig:
    model: str = ""
    count: int = 10
    distribution: str = "random"
    min_spacing: float = 3.0
    bbox_radius: float | None = None
    height: float | None = None
    yaw_random: bool = True
    area_bounds: AreaBoundsConfig | None = None
    corridor: CorridorConfig | None = None
    perimeter: PerimeterConfig | None = None


@dataclass
class LightingConfig:
    sun_direction: list[float] = field(
        default_factory=lambda: [-0.5, 0.1, -0.9]
    )
    sun_intensity: float = 1.0
    ambient: list[float] = field(
        default_factory=lambda: [0.4, 0.4, 0.4, 1.0]
    )


@dataclass
class WorldGenerationConfig:
    world: WorldConfig = field(default_factory=WorldConfig)
    area: AreaConfig = field(default_factory=AreaConfig)
    spawn_zone: SpawnZoneConfig = field(default_factory=SpawnZoneConfig)
    spherical_coordinates: SphericalCoordinatesConfig = field(
        default_factory=SphericalCoordinatesConfig
    )
    connectivity: ConnectivityConfig = field(default_factory=ConnectivityConfig)
    obstacles: list[ObstacleGroupConfig] = field(default_factory=list)
    lighting: LightingConfig = field(default_factory=LightingConfig)


def _parse_obstacle_group(data: dict) -> ObstacleGroupConfig:
    group = ObstacleGroupConfig(
        model=data["model"],
        count=data.get("count", 10),
        distribution=data.get("distribution", "random"),
        min_spacing=data.get("min_spacing", 3.0),
        bbox_radius=data.get("bbox_radius"),
        height=data.get("height"),
        yaw_random=data.get("yaw_random", True),
    )

    if group.model not in MODEL_REGISTRY:
        raise ValueError(
            f"Unknown model '{group.model}'. "
            f"Available: {list(MODEL_REGISTRY.keys())}"
        )

    from .models import get_model_info

    info = get_model_info(group.model)
    if group.bbox_radius is None:
        group.bbox_radius = info.bbox_radius
    if group.height is None:
        group.height = info.height

    if "area_bounds" in data:
        ab = data["area_bounds"]
        group.area_bounds = AreaBoundsConfig(
            x_min=ab.get("x_min", -45.0),
            x_max=ab.get("x_max", 45.0),
            y_min=ab.get("y_min", -45.0),
            y_max=ab.get("y_max", 45.0),
        )

    if "corridor" in data:
        c = data["corridor"]
        group.corridor = CorridorConfig(
            width=c.get("width", 4.0),
            segments=c.get("segments", 3),
            direction=c.get("direction", "random"),
        )

    if "perimeter" in data:
        p = data["perimeter"]
        group.perimeter = PerimeterConfig(offset=p.get("offset", 5.0))

    return group


def load_config(path: str | Path) -> WorldGenerationConfig:
    path = Path(path)
    with open(path) as f:
        data = yaml.safe_load(f)

    config = WorldGenerationConfig()

    if "world" in data:
        w = data["world"]
        config.world = WorldConfig(
            name=w.get("name", "procedural_world"),
            seed=w.get("seed"),
            description=w.get("description", ""),
        )

    if "area" in data:
        a = data["area"]
        config.area = AreaConfig(
            size_x=a.get("size_x", 100.0),
            size_y=a.get("size_y", 100.0),
            ground_plane_size=a.get("ground_plane_size", 100.0),
            origin_offset=a.get("origin_offset", [0.0, 0.0]),
        )

    if "spawn_zone" in data:
        sz = data["spawn_zone"]
        config.spawn_zone = SpawnZoneConfig(
            center=sz.get("center", [0.0, 0.0]),
            radius=sz.get("radius", 5.0),
        )

    if "spherical_coordinates" in data:
        sc = data["spherical_coordinates"]
        config.spherical_coordinates = SphericalCoordinatesConfig(
            latitude_deg=sc.get("latitude_deg", 52.11486),
            longitude_deg=sc.get("longitude_deg", -6.613),
            elevation=sc.get("elevation", 2.0),
            heading_deg=sc.get("heading_deg", 0.0),
        )

    if "connectivity" in data:
        cn = data["connectivity"]
        config.connectivity = ConnectivityConfig(
            enabled=cn.get("enabled", True),
            check_altitude=cn.get("check_altitude", 3.0),
            safety_margin=cn.get("safety_margin", 1.5),
            start=cn.get("start", [0.0, 0.0]),
            goals=cn.get("goals", [[40.0, 40.0], [-40.0, -40.0]]),
            max_removal_iterations=cn.get("max_removal_iterations", 50),
        )

    if "obstacles" in data:
        config.obstacles = [
            _parse_obstacle_group(og) for og in data["obstacles"]
        ]

    if "lighting" in data:
        lt = data["lighting"]
        config.lighting = LightingConfig(
            sun_direction=lt.get("sun_direction", [-0.5, 0.1, -0.9]),
            sun_intensity=lt.get("sun_intensity", 1.0),
            ambient=lt.get("ambient", [0.4, 0.4, 0.4, 1.0]),
        )

    return config
