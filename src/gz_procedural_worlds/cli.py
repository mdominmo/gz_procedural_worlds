from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .generator import generate_from_config_file
from .models import MODEL_REGISTRY


def cmd_generate(args: argparse.Namespace) -> None:
    output_dir = Path(args.output_dir) if args.output_dir else None

    output_path, obstacles = generate_from_config_file(
        config_path=args.config,
        output_dir=output_dir,
        seed_override=args.seed,
        sync_models=not args.no_sync,
    )

    print(f"Generated world: {output_path}")
    print(f"  Obstacles placed: {len(obstacles)}")

    if args.visualize:
        from .visualize import visualize_world

        config_path = Path(args.config)
        from .config import load_config

        config = load_config(config_path)
        png_path = output_path.with_suffix(".png")
        visualize_world(
            obstacles=obstacles,
            size_x=config.area.size_x,
            size_y=config.area.size_y,
            spawn_zone_center=tuple(config.spawn_zone.center),
            spawn_zone_radius=config.spawn_zone.radius,
            start=tuple(config.connectivity.start),
            goals=[tuple(g) for g in config.connectivity.goals],
            output_path=png_path,
        )
        print(f"  Visualization: {png_path}")


def cmd_list_models(args: argparse.Namespace) -> None:
    print(f"{'Model':<22} {'Radius':>7} {'Height':>7} {'Source':<10}")
    print("-" * 50)
    for name, info in MODEL_REGISTRY.items():
        print(
            f"{name:<22} {info.bbox_radius:>7.2f} {info.height:>7.1f} {info.source:<10}"
        )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="gz-procedural-worlds",
        description="Procedural world generator for Gazebo / PX4 SITL",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    gen_parser = subparsers.add_parser(
        "generate", help="Generate a world from a YAML config"
    )
    gen_parser.add_argument(
        "--config", "-c", required=True, help="Path to YAML config file"
    )
    gen_parser.add_argument(
        "--output-dir", "-o", help="Output directory (default: submodule worlds)"
    )
    gen_parser.add_argument(
        "--seed", "-s", type=int, help="Override random seed"
    )
    gen_parser.add_argument(
        "--visualize", "-v", action="store_true",
        help="Generate a top-down visualization PNG",
    )
    gen_parser.add_argument(
        "--no-sync", action="store_true",
        help="Skip syncing local models to submodule",
    )
    gen_parser.set_defaults(func=cmd_generate)

    models_parser = subparsers.add_parser(
        "list-models", help="List available obstacle models"
    )
    models_parser.set_defaults(func=cmd_list_models)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
