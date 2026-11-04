#!/bin/sh
set -eu
experiment_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
experiment_python="$experiment_root/openai-eval-test-suite/.venv/bin/python"
if [ ! -x "$experiment_python" ]; then
    echo "Missing experiment environment. See $experiment_root/README.md" >&2
    exit 1
fi
export PATH="$experiment_root/openai-eval-test-suite/.venv/bin:$PATH"
exec "$experiment_python" "$experiment_root/run_experiment.py" "$@"
