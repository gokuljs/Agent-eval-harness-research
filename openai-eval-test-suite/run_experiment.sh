#!/bin/sh
set -eu
experiment_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if ! command -v uv >/dev/null 2>&1; then
    echo "Install uv first: https://docs.astral.sh/uv/getting-started/installation/" >&2
    exit 1
fi
export UV_CACHE_DIR="${UV_CACHE_DIR:-$experiment_root/.local/uv-cache}"
exec uv --directory "$experiment_root" run --locked python run_experiment.py "$@"
