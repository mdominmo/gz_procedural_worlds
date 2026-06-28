import tempfile
from pathlib import Path

import pytest

from gz_procedural_worlds.config import load_config


MINIMAL_YAML = """\
world:
  name: "test_world"
  seed: 1

obstacles:
  - model: "Pine Tree"
    count: 5
"""


def test_load_minimal_config():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(MINIMAL_YAML)
        f.flush()
        config = load_config(f.name)

    assert config.world.name == "test_world"
    assert config.world.seed == 1
    assert len(config.obstacles) == 1
    assert config.obstacles[0].model == "Pine Tree"
    assert config.obstacles[0].count == 5
    assert config.obstacles[0].bbox_radius == 1.5
    assert config.obstacles[0].height == 8.0


def test_defaults_applied():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("obstacles: []\n")
        f.flush()
        config = load_config(f.name)

    assert config.area.size_x == 100.0
    assert config.spawn_zone.radius == 5.0
    assert config.connectivity.enabled is True
    assert config.lighting.sun_intensity == 1.0


def test_unknown_model_raises():
    bad_yaml = """\
obstacles:
  - model: "NonExistentModel"
    count: 1
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(bad_yaml)
        f.flush()
        with pytest.raises(ValueError, match="Unknown model"):
            load_config(f.name)


def test_area_bounds_parsed():
    yaml_content = """\
obstacles:
  - model: "Pine Tree"
    count: 3
    area_bounds:
      x_min: -10.0
      x_max: 10.0
      y_min: -20.0
      y_max: 20.0
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        f.flush()
        config = load_config(f.name)

    assert config.obstacles[0].area_bounds.x_min == -10.0
    assert config.obstacles[0].area_bounds.y_max == 20.0
