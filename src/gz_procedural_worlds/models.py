from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelInfo:
    bbox_radius: float
    height: float
    source: str  # "submodule" or "local"


MODEL_REGISTRY: dict[str, ModelInfo] = {
    "Pine Tree": ModelInfo(bbox_radius=1.5, height=8.0, source="submodule"),
    "Standing person": ModelInfo(bbox_radius=0.4, height=1.8, source="submodule"),
    "Walking person": ModelInfo(bbox_radius=0.4, height=1.8, source="submodule"),
    "wall_segment": ModelInfo(bbox_radius=2.1, height=2.5, source="local"),
    "wall_segment_tall": ModelInfo(bbox_radius=2.1, height=5.0, source="local"),
    "concrete_barrier": ModelInfo(bbox_radius=1.1, height=1.0, source="local"),
    "pole": ModelInfo(bbox_radius=0.15, height=4.0, source="local"),
}


def get_model_info(name: str) -> ModelInfo:
    if name not in MODEL_REGISTRY:
        raise ValueError(
            f"Unknown model '{name}'. Available: {list(MODEL_REGISTRY.keys())}"
        )
    return MODEL_REGISTRY[name]
