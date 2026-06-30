#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
IMAGE_NAME="oa_worldgen"

usage() {
    echo "Usage: $0 --config <config.yaml> [--seed <N>] [--output-dir <dir>]"
    echo ""
    echo "Generates a procedural world inside a Docker container."
    echo ""
    echo "Options:"
    echo "  --config, -c      Path to YAML world config (required)"
    echo "  --seed, -s        Override random seed"
    echo "  --output-dir, -o  Output directory (default: project output/)"
}

CONFIG=""
SEED=""
OUTPUT_DIR="$PROJECT_ROOT/output"

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
        --output-dir|-o)
            OUTPUT_DIR="$(cd "$2" 2>/dev/null && pwd || echo "$2")"
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

if [[ -z "$CONFIG" ]]; then
    echo "Error: --config is required"
    usage
    exit 1
fi

CONFIG_ABSPATH="$(cd "$(dirname "$CONFIG")" && pwd)/$(basename "$CONFIG")"
if [[ ! -f "$CONFIG_ABSPATH" ]]; then
    echo "Error: config file not found: $CONFIG"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

if ! docker image inspect "$IMAGE_NAME" &>/dev/null; then
    echo "Building $IMAGE_NAME image..."
    docker build -t "$IMAGE_NAME" -f "$PROJECT_ROOT/Dockerfile.worldgen" "$PROJECT_ROOT"
fi

CONFIG_DIR="$(dirname "$CONFIG_ABSPATH")"
CONFIG_FILE="$(basename "$CONFIG_ABSPATH")"

GEN_ARGS="--config /configs/$CONFIG_FILE --output-dir /output --no-sync"
[[ -n "$SEED" ]] && GEN_ARGS="$GEN_ARGS --seed $SEED"

docker run --rm \
    -v "$CONFIG_DIR:/configs:ro" \
    -v "$OUTPUT_DIR:/output" \
    "$IMAGE_NAME" generate $GEN_ARGS

echo "World generated in: $OUTPUT_DIR"
