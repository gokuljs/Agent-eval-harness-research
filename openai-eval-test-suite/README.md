# Agent Improvement Loop

A local setup for OpenAI's [Build an Agent Improvement Loop with Traces, Evals, and Codex](https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop). The example generates five agent traces on fictional diligence data, adds example human feedback and live model feedback, creates Promptfoo evals, grades saved trace answers, and runs HALO to write improvement recommendations.

All source and setup files for this example live in this folder. Synthetic data, validators, and eval configuration are generated at runtime; other Cookbook examples are not required.

## Setup

Use Python 3.12 and Node.js with `npx` available on your path. From the repository root, install the pinned Python dependencies:

```sh
cd openai-eval-test-suite
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-experiment.lock.txt
```

The existing local `.venv` and private `.env` are retained. Skip environment creation and installation if that setup is already ready to use.

For a fresh clone only, create the private configuration file. Skip this command if `.env` already exists; do not overwrite existing configuration:

```sh
cp .env.example .env
```

Set your API key in `.env`:

```dotenv
OPENAI_API_KEY=your_key_here
```

The file is ignored by Git. Environment variables take precedence over values in `.env`. Optional model settings are listed in [.env.example](.env.example). All model defaults remain `gpt-5.5`, and Promptfoo remains `0.121.9`.

## Run

From this folder, check dependencies, notebook code, and the local sandbox without making model calls:

```sh
./run_experiment.sh --check
```

After adding your API key, start the live experiment:

```sh
./run_experiment.sh
```

The live stages use the OpenAI API and incur usage charges. The Cookbook estimates about 20 minutes with the default five traces; model access and latency depend on your account and network.

The launcher uses this folder's Python environment and skips the notebook's package-installation cell. On macOS, it adds a read-only grant for `.venv` to the agent sandbox in the execution copy so Python can read its configuration and installed packages. The `.env` file is outside that grant.

Download caches were removed during cleanup. Local caches under `.local/` regenerate as needed, and the next live run downloads Promptfoo again.

## Results

All paths below are relative to this folder:

- Full report: `agent_improvement_loop_artifacts/codex_handoff.md`.
- Traces, synthetic data, eval configuration, and results: `agent_improvement_loop_artifacts/`.
- Executed notebook and run status: `runs/<UTC-timestamp>/`.

Before rerunning, the launcher archives existing artifacts in the new run's `previous_artifacts/` folder. Notebook outputs are checkpointed during execution, including on failure. The default timeout is 3600 seconds per cell; use `--cell-timeout SECONDS` to change it.

## Source and license

The notebook comes from [OpenAI Cookbook commit `0f38c4a3c6cff6ae72da564a153e4bb7fd5b7636`](https://github.com/openai/openai-cookbook/blob/0f38c4a3c6cff6ae72da564a153e4bb7fd5b7636/examples/agents_sdk/agent_improvement_loop.ipynb). It is adapted for standalone paths and the pinned local setup, with upstream sample outputs cleared. OpenAI's [MIT license and attribution](LICENSE) are preserved.
