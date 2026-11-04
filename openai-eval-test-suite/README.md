# Agent Improvement Loop

A local setup for OpenAI's [Build an Agent Improvement Loop with Traces, Evals, and Codex](https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop). The example generates five agent traces on fictional diligence data, adds example human feedback and live model feedback, creates Promptfoo evals, grades saved trace answers, and runs HALO to write improvement recommendations.

All source and setup files for this example live in this folder. Synthetic data, validators, and eval configuration are generated at runtime; other Cookbook examples are not required.

## Setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and Node.js with `npx` available on your path. From the repository root, install the Python dependencies and check the setup:

```sh
cd openai-eval-test-suite
./setup.sh
```

`pyproject.toml` selects Python 3.15 and declares the project's dependencies; `uv.lock` pins the resolved versions. Use uv 0.13.7 or newer. `uv sync` creates or updates `.venv`; no activation or separate pip installation is needed. uv can download Python 3.15 if it is not installed. Use `uv sync --locked` to require the checked-in lockfile without updating it. The Python requirement lives in `pyproject.toml` so pyenv does not intercept a project `.python-version` file.

`openai`, `openai-agents`, and `halo-engine` are the core packages used by the official example. The project also includes the notebook runner and `.env` dependencies. The previous `requirements*.txt` files are retained as a pip-compatible snapshot; uv uses `pyproject.toml` and `uv.lock`.

The setup script syncs the environment, checks package compatibility, creates `.env` from `.env.example` when missing, and runs readiness checks without model calls. After this initial setup, sync the locked environment directly with:

```sh
uv sync --locked
```

HALO's pinned NumPy and Pandas versions build from source on Python 3.15. This first setup needs a C/C++ compiler and Rust; on macOS, install the Xcode Command Line Tools. `setup.sh` configures the installed macOS C++ header path. The project also disables Pydantic Core's release stripping step to avoid a macOS binary-alignment issue. Subsequent syncs reuse the built packages from the local cache.

Set your API key in `.env`:

```dotenv
OPENAI_API_KEY=your_key_here
```

The file is ignored by Git. Environment variables take precedence over values in `.env`. Optional model settings are listed in [.env.example](.env.example). All model defaults remain `gpt-5.5`, and Promptfoo remains `0.121.9`.

## Run

From this folder, check dependencies, notebook code, and the local sandbox without making model calls:

```sh
uv run --locked python run_experiment.py --check
```

After adding your API key, start the live experiment:

```sh
uv run --locked python run_experiment.py
```

The live stages use the OpenAI API and incur usage charges. The Cookbook estimates about 20 minutes with the default five traces; model access and latency depend on your account and network.

`./run_experiment.sh` is a wrapper for the same `uv run --locked` command and works from any directory. For interactive notebook use, select `.venv/bin/python` (Python 3.15) as the kernel after setup; dependencies are managed outside the notebook. On macOS, the launcher adds a read-only grant for `.venv` to the agent sandbox in the execution copy so Python can read its configuration and installed packages. The `.env` file is outside that grant.

uv uses `.local/uv-cache/` for downloads unless `UV_CACHE_DIR` is already set. Runtime caches also live under `.local/`; the next live run downloads Promptfoo as needed.

## Results

All paths below are relative to this folder:

- Full report: `agent_improvement_loop_artifacts/codex_handoff.md`.
- Traces, synthetic data, eval configuration, and results: `agent_improvement_loop_artifacts/`.
- Executed notebook and run status: `runs/<UTC-timestamp>/`.

Before rerunning, the launcher archives existing artifacts in the new run's `previous_artifacts/` folder. Notebook outputs are checkpointed during execution, including on failure. The default timeout is 3600 seconds per cell; use `--cell-timeout SECONDS` to change it.

## Source and license

The notebook comes from [OpenAI Cookbook commit `0f38c4a3c6cff6ae72da564a153e4bb7fd5b7636`](https://github.com/openai/openai-cookbook/blob/0f38c4a3c6cff6ae72da564a153e4bb7fd5b7636/examples/agents_sdk/agent_improvement_loop.ipynb). It is adapted for standalone paths and the pinned local setup, with upstream sample outputs cleared. OpenAI's [MIT license and attribution](LICENSE) are preserved.
