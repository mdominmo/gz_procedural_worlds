import xml.etree.ElementTree as ET

from gz_procedural_worlds.renderer import PlacedObstacle, render_world


def _make_obstacles(n=3):
    return [
        PlacedObstacle(
            model_name="Pine Tree",
            instance_name=f"Pine Tree_{i}",
            x=float(i * 10),
            y=float(i * 5),
        )
        for i in range(n)
    ]


def test_renders_valid_xml():
    sdf = render_world(
        world_name="test",
        seed=42,
        ground_plane_size=100,
        spherical_coordinates={
            "latitude_deg": 52.0,
            "longitude_deg": -6.0,
            "elevation": 2,
            "heading_deg": 0,
        },
        obstacles=_make_obstacles(3),
        sun_direction=[-0.5, 0.1, -0.9],
        sun_intensity=1.0,
        ambient=[0.4, 0.4, 0.4, 1.0],
    )
    root = ET.fromstring(sdf)
    assert root.tag == "sdf"


def test_correct_world_name():
    sdf = render_world(
        world_name="my_world",
        seed=1,
        ground_plane_size=100,
        spherical_coordinates={
            "latitude_deg": 52.0,
            "longitude_deg": -6.0,
            "elevation": 2,
            "heading_deg": 0,
        },
        obstacles=[],
        sun_direction=[-0.5, 0.1, -0.9],
        sun_intensity=1.0,
        ambient=[0.4, 0.4, 0.4, 1.0],
    )
    root = ET.fromstring(sdf)
    world = root.find("world")
    assert world.get("name") == "my_world"


def test_correct_include_count():
    sdf = render_world(
        world_name="test",
        seed=42,
        ground_plane_size=100,
        spherical_coordinates={
            "latitude_deg": 52.0,
            "longitude_deg": -6.0,
            "elevation": 2,
            "heading_deg": 0,
        },
        obstacles=_make_obstacles(5),
        sun_direction=[-0.5, 0.1, -0.9],
        sun_intensity=1.0,
        ambient=[0.4, 0.4, 0.4, 1.0],
    )
    root = ET.fromstring(sdf)
    includes = root.findall(".//include")
    assert len(includes) == 5


def test_include_has_correct_uri():
    sdf = render_world(
        world_name="test",
        seed=42,
        ground_plane_size=100,
        spherical_coordinates={
            "latitude_deg": 52.0,
            "longitude_deg": -6.0,
            "elevation": 2,
            "heading_deg": 0,
        },
        obstacles=_make_obstacles(1),
        sun_direction=[-0.5, 0.1, -0.9],
        sun_intensity=1.0,
        ambient=[0.4, 0.4, 0.4, 1.0],
    )
    root = ET.fromstring(sdf)
    uri = root.find(".//include/uri").text
    assert uri == "model://Pine Tree"
