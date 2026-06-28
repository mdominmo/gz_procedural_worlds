#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT/src:${PYTHONPATH:-}"

if [ -z "$1" ]; then
    echo "Usage: $0 --config <config.yaml> [--seed <N>] [--visualize] [--no-sync]"
    exit 1
fi

python3 -m gz_procedural_worlds generate "$@"
