#!/bin/sh
set -eu

experiment_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if ! command -v uv >/dev/null 2>&1; then
    echo "Install uv first: https://docs.astral.sh/uv/getting-started/installation/" >&2
    exit 1
fi
if ! command -v npx >/dev/null 2>&1; then
    echo "Install Node.js with npx before setting up the experiment." >&2
    exit 1
fi

export UV_CACHE_DIR="${UV_CACHE_DIR:-$experiment_root/.local/uv-cache}"
uv --directory "$experiment_root" sync --locked
uv pip check --python "$experiment_root/.venv/bin/python"

if [ ! -e "$experiment_root/.env" ]; then
    cp "$experiment_root/.env.example" "$experiment_root/.env"
    echo "Created .env. Set OPENAI_API_KEY there before starting a live run."
fi

exec "$experiment_root/run_experiment.sh" --check
