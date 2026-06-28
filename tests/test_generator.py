import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from gz_procedural_worlds.config import load_config
from gz_procedural_worlds.generator import generate_world


YAML_CONTENT = """\
world:
  name: "test_gen"
  seed: 99

area:
  size_x: 50.0
  size_y: 50.0
  ground_plane_size: 50

spawn_zone:
  center: [0.0, 0.0]
  radius: 3.0

connectivity:
  enabled: true
  check_altitude: 3.0
  safety_margin: 1.0
  start: [0.0, 0.0]
  goals:
    - [20.0, 20.0]

obstacles:
  - model: "Pine Tree"
    count: 10
    distribution: "random"
    min_spacing: 3.0
"""


def _load_test_config():
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        f.write(YAML_CONTENT)
        f.flush()
        return load_config(f.name)


def test_end_to_end_generation():
    config = _load_test_config()
    with tempfile.TemporaryDirectory() as tmp:
        output_path, obstacles = generate_world(
            config, output_dir=Path(tmp), sync_models=False
        )
        assert output_path.exists()
        assert output_path.name == "test_gen.sdf"
        assert len(obstacles) > 0

        root = ET.parse(str(output_path)).getroot()
        assert root.tag == "sdf"
        world = root.find("world")
        assert world.get("name") == "test_gen"


def test_deterministic_output():
    config = _load_test_config()
    with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
        _, obs1 = generate_world(
            config, output_dir=Path(tmp1), sync_models=False
        )
        _, obs2 = generate_world(
            config, output_dir=Path(tmp2), sync_models=False
        )
        assert len(obs1) == len(obs2)
        for a, b in zip(obs1, obs2):
            assert a.x == b.x
            assert a.y == b.y


def test_seed_override():
    config = _load_test_config()
    with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
        _, obs1 = generate_world(
            config, output_dir=Path(tmp1), sync_models=False, seed_override=1
        )
        _, obs2 = generate_world(
            config, output_dir=Path(tmp2), sync_models=False, seed_override=2
        )
        positions1 = [(o.x, o.y) for o in obs1]
        positions2 = [(o.x, o.y) for o in obs2]
        assert positions1 != positions2
