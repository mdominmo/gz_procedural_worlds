#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SIM_DIR="$PROJECT_ROOT/px4-sitl-docker-sim"

usage() {
    echo "Usage: $0 --config <config.yaml> [--seed <N>] [--model <MODEL>] [--vehicles <N>]"
    echo ""
    echo "World generation options:"
    echo "  --config, -c    Path to YAML world config (required)"
    echo "  --seed, -s      Override random seed"
    echo "  --visualize     Generate top-down layout PNG"
    echo ""
    echo "Simulation options:"
    echo "  --model, -m     Drone model: x500, x500_mono_cam, rc_cessna (default: x500_mono_cam)"
    echo "  --vehicles, -n  Number of vehicles (default: 1)"
}

CONFIG=""
SEED=""
VISUALIZE=""
MODEL="x500_mono_cam"
VEHICLES="1"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --config|-c)
            CONFIG="$2"
            shift 2
            ;;
        --seed|-s)
            SEED="$2"
            shift 2
            ;;
        --visualize)
            VISUALIZE="--visualize"
            shift
            ;;
        --model|-m)
            MODEL="$2"
            shift 2
            ;;
        --vehicles|-n)
            VEHICLES="$2"
            shift 2
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            echo "Unknown argument: $1"
            usage
            exit 1
            ;;
    esac
done

if [ -z "$CONFIG" ]; then
    echo "Error: --config is required"
    usage
    exit 1
fi

if [ ! -f "$SIM_DIR/scripts/run_docker.sh" ]; then
    echo "Error: px4-sitl-docker-sim submodule not found."
    echo "Run: git submodule update --init"
    exit 1
fi

if [ ! -d "$SIM_DIR/gz_assets" ]; then
    echo "Extracting gz_assets from zip..."
    (cd "$SIM_DIR" && unzip -o gz_assets.zip)
fi

cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT/src:${PYTHONPATH:-}"

GEN_ARGS="--config $CONFIG"
[ -n "$SEED" ] && GEN_ARGS="$GEN_ARGS --seed $SEED"
[ -n "$VISUALIZE" ] && GEN_ARGS="$GEN_ARGS $VISUALIZE"

echo "Generating world..."
python3 -m gz_procedural_worlds generate $GEN_ARGS

WORLD_NAME=$(python3 -c "
import yaml
with open('$CONFIG') as f:
    data = yaml.safe_load(f)
print(data.get('world', {}).get('name', 'procedural_world'))
")

echo "Launching simulation with world: $WORLD_NAME"
"$SIM_DIR/scripts/run_docker.sh" --world "$WORLD_NAME" --model "$MODEL" --vehicles "$VEHICLES"
