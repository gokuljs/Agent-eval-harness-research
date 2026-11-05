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
# HALO's pinned NumPy/Pandas releases need source builds on Python 3.15.
# Point Apple's compiler at its installed C++ headers when needed.
if [ "$(uname -s)" = "Darwin" ] && command -v xcrun >/dev/null 2>&1; then
    experiment_sdk=$(xcrun --show-sdk-path)
    if [ -d "$experiment_sdk/usr/include/c++/v1" ]; then
        export CXXFLAGS="${CXXFLAGS:+$CXXFLAGS }-isystem $experiment_sdk/usr/include/c++/v1"
    fi
fi
uv --directory "$experiment_root" sync --locked
uv pip check --python "$experiment_root/.venv/bin/python"

if [ ! -e "$experiment_root/.env" ]; then
    cp "$experiment_root/.env.example" "$experiment_root/.env"
    echo "Created .env. Set OPENAI_API_KEY there before starting a live run."
fi

exec "$experiment_root/run_experiment.sh" --check
