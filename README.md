# Agent eval harness research

A runnable local setup for OpenAI's [Build an Agent Improvement Loop with Traces, Evals, and Codex](https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop), based on the [original notebook](https://github.com/openai/openai-cookbook/blob/0f38c4a3c6cff6ae72da564a153e4bb7fd5b7636/examples/agents_sdk/agent_improvement_loop.ipynb).

The cookbook source lives in `openai-eval-test-suite/`. It was copied from a shallow, sparse checkout of `openai/openai-cookbook` at commit `0f38c4a3c6cff6ae72da564a153e4bb7fd5b7636`. It is a vendored snapshot, not a separate Git repository or submodule. The upstream notebook is unchanged, and the cookbook's [MIT license and attribution](openai-eval-test-suite/LICENSE) are preserved.

## Set up a fresh clone

Use Python 3.12 and Node.js with `npx` available on your path. The explicit `python3.12` command avoids selecting an incompatible interpreter when entering the cookbook folder.

```sh
git clone https://github.com/gokuljs/Agent-eval-harness-research.git
cd Agent-eval-harness-research
python3.12 -m venv openai-eval-test-suite/.venv
openai-eval-test-suite/.venv/bin/python -m pip install -r requirements-experiment.lock.txt
cp .env.example openai-eval-test-suite/.env
```

Add your key to `openai-eval-test-suite/.env`:

```dotenv
OPENAI_API_KEY=your_key_here
```

The `.env` file is ignored by Git. Environment variables take precedence over the file. For the existing local setup, the file is already created with an empty key; fill it in when ready.

Check the setup without making model calls:

```sh
./run_experiment.sh --check
```

Start the live experiment after adding your key:

```sh
./run_experiment.sh
```

The experiment generates five agent traces on fictional diligence data, adds example human feedback and live model feedback, generates evals, grades saved trace answers with Promptfoo, and runs HALO to write improvement recommendations. The cookbook estimates about 20 minutes with the default five traces. These stages use the OpenAI API and incur usage charges. Model access and live API behavior still need to be verified after a key is supplied.

All model defaults remain `gpt-5.5`; Promptfoo remains `0.121.9`. Optional environment settings are listed in [.env.example](.env.example). `OPENAI_ANALYSIS_MODEL` also controls the default eval-generation, judge, and HALO models unless those stages are overridden separately.

## Results

- Full report: `openai-eval-test-suite/examples/agents_sdk/agent_improvement_loop_artifacts/codex_handoff.md`.
- Traces, synthetic data, eval config and results: the same `agent_improvement_loop_artifacts/` folder.
- Executed notebook and run status: `runs/<UTC-timestamp>/`.

The launcher clears upstream sample outputs in its execution copy, skips the notebook's package-upgrade cell, and uses the installed Python environment. On macOS, it adds a read-only grant for `.venv` to the agent sandbox in the execution copy so Python can read its configuration and installed packages. It does not grant access to the repository's `.env` file. The original notebook remains unchanged.

Before rerunning, the launcher moves existing artifacts to the new run's `previous_artifacts/` folder because the notebook resets its artifact directory. Cell outputs are checkpointed to the executed notebook, including on failure. The default timeout is 3600 seconds per cell; use `--cell-timeout SECONDS` to change it.

## Local verification

The initial setup was verified with:

- Python 3.12.11 in `openai-eval-test-suite/.venv`.
- `openai==2.32.0`, `openai-agents==0.14.7`, and `halo-engine==0.3.5`, plus notebook execution tools. HALO requires these SDK versions; the full environment is recorded in [requirements-experiment.lock.txt](requirements-experiment.lock.txt).
- Node.js 24.13.0 and the pinned Promptfoo CLI, cached under `.local/npm-cache/`.
- Dependency consistency (`pip check`), notebook schema and code compilation, exact SDK/HALO imports, HALO configuration construction, local sandbox file operations and Python execution.
- An offline notebook execution using the dedicated kernel, including output checkpointing.
- An offline Promptfoo evaluation using a local Python provider: 1 passed, 0 failed, 0 errors.

No live model calls or experiment results were generated during setup. The API key is intentionally left for you to add later.

Run the commands from a normal terminal. Inside Codex's restricted sandbox, the local sandbox and Jupyter loopback sockets require an escalated command; the setup was verified that way.
