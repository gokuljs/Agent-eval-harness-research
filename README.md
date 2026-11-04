# Agent eval harness research

Each example lives in its own folder with its source, configuration, dependencies file, and instructions.

- [Agent Improvement Loop](openai-eval-test-suite/README.md): traces, feedback, Promptfoo evals, and a HALO handoff for Codex.

Install dependencies and check the environment with uv:

```sh
cd openai-eval-test-suite
uv sync
uv run --locked python run_experiment.py --check
```

`./setup.sh` also creates `.env` from its template when needed and runs the same checks. See the example's README for configuration and live execution.
