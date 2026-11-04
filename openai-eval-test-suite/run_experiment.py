"""Run the agent improvement notebook with a dedicated Python kernel."""

from __future__ import annotations

import argparse
import ast
import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NOTEBOOK = ROOT / "agent_improvement_loop.ipynb"
ARTIFACTS = ROOT / "agent_improvement_loop_artifacts"
RUNS = ROOT / "runs"
MODELS = {
    "agent": "OPENAI_AGENT_MODEL",
    "analysis": "OPENAI_ANALYSIS_MODEL",
    "eval_generation": "OPENAI_EVAL_GENERATION_MODEL",
    "judge": "OPENAI_JUDGE_MODEL",
    "halo": "OPENAI_HALO_MODEL",
}


def load_environment() -> None:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env", override=False)
    os.environ["PATH"] = str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", "")
    os.environ.setdefault("PROMPTFOO_VERSION", "0.121.9")
    os.environ.setdefault("PROMPTFOO_DISABLE_TELEMETRY", "1")
    os.environ.setdefault("npm_config_cache", str(ROOT / ".local/npm-cache"))
    os.environ.setdefault("IPYTHONDIR", str(ROOT / ".local/ipython"))
    os.environ.setdefault("JUPYTER_RUNTIME_DIR", str(ROOT / ".local/jupyter"))
    os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".local/matplotlib"))
    for name in ("IPYTHONDIR", "JUPYTER_RUNTIME_DIR", "MPLCONFIGDIR"):
        Path(os.environ[name]).mkdir(parents=True, exist_ok=True)


def prepare_notebook():
    import nbformat

    notebook = nbformat.read(NOTEBOOK, as_version=4)
    for cell in notebook.cells:
        if cell.cell_type == "code":
            cell.outputs = []
            cell.execution_count = None
            cell.metadata.pop("execution", None)
            if cell.source.startswith("%%capture") and "%pip install" in cell.source:
                cell.metadata["tags"] = list(set(cell.metadata.get("tags", [])) | {"skip-execution"})
            if sys.platform == "darwin" and "async def run_sdk_agent(" in cell.source:
                # The macOS backend allows PATH/bin but Python also needs its
                # parent venv's config and site-packages. Grant only read access.
                original = "from agents.sandbox import Manifest, SandboxAgent, SandboxRunConfig"
                manifest = "default_manifest=Manifest(\n"
                if original not in cell.source or manifest not in cell.source:
                    raise RuntimeError("Upstream sandbox setup changed; review the macOS venv adaptation.")
                cell.source = cell.source.replace(original, original + ", SandboxPathGrant", 1)
                cell.source = cell.source.replace(
                    manifest,
                    manifest + "                extra_path_grants=(SandboxPathGrant(path=sys.prefix, read_only=True),),\n",
                    1,
                )
    nbformat.validate(notebook)
    return notebook


async def sandbox_check() -> None:
    from agents.sandbox import Manifest, SandboxPathGrant
    from agents.sandbox.entries import Dir, LocalDir
    from agents.sandbox.sandboxes.unix_local import UnixLocalSandboxClient

    with tempfile.TemporaryDirectory(prefix="agent-loop-check-") as directory:
        source = Path(directory).resolve() / "data"
        source.mkdir()
        (source / "check.txt").write_text("agent-loop setup verified\n", encoding="utf-8")
        client = UnixLocalSandboxClient()
        grants = (SandboxPathGrant(path=sys.prefix, read_only=True),) if sys.platform == "darwin" else ()
        session = await client.create(manifest=Manifest(
            entries={"data": LocalDir(src=source), "outputs": Dir()},
            extra_path_grants=grants,
        ))
        try:
            async with session:
                with await session.read(Path("data/check.txt")) as handle:
                    assert handle.read() == b"agent-loop setup verified\n"
                result = await session.exec(
                    "python", "-c",
                    "import csv, json, openai; from pathlib import Path; print(Path('data/check.txt').read_text().strip())",
                    shell=False, timeout=30,
                )
                if not result.ok() or result.stdout.strip() != b"agent-loop setup verified":
                    raise RuntimeError(f"Local sandbox command failed: {result.stderr.decode(errors='replace')}")
        finally:
            await client.delete(session)


def check_setup() -> dict:
    from IPython.core.inputtransformer2 import TransformerManager
    from agents.sandbox import SandboxAgent, SandboxRunConfig  # noqa: F401
    from engine.agents.agent_config import AgentConfig
    from engine.engine_config import EngineConfig
    from engine.main import stream_engine_async  # noqa: F401
    from engine.model_config import ModelConfig
    from engine.models.engine_output import AgentOutputItem, AgentTextDelta  # noqa: F401
    from engine.models.messages import AgentMessage  # noqa: F401
    from engine.sandbox.sandbox import Sandbox  # noqa: F401

    if shutil.which("npx") is None:
        raise RuntimeError("Node.js with npx is required.")
    notebook = prepare_notebook()
    transformer = TransformerManager()
    for index, cell in enumerate(notebook.cells):
        if cell.cell_type == "code":
            compile(transformer.transform_cell(cell.source), f"notebook-cell-{index}", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    agent = AgentConfig(name="root", model=ModelConfig(name="gpt-5.5"), maximum_turns=20)
    EngineConfig(
        root_agent=agent,
        subagent=agent.model_copy(update={"name": "sub"}),
        synthesis_model=ModelConfig(name="gpt-5.5"),
        compaction_model=ModelConfig(name="gpt-5.5", temperature=1.0),
        maximum_depth=1,
        maximum_parallel_subagents=2,
    )
    asyncio.run(sandbox_check())
    analysis_model = os.getenv("OPENAI_ANALYSIS_MODEL", "gpt-5.5")
    model_values = {stage: os.getenv(name, "gpt-5.5" if stage == "agent" else analysis_model) for stage, name in MODELS.items()}
    return {
        "python": sys.version.split()[0],
        "packages": {name: version(name) for name in ("openai", "openai-agents", "halo-engine", "nbclient", "ipykernel")},
        "models": model_values,
        "promptfoo": os.environ["PROMPTFOO_VERSION"],
        "api_key_present": bool(os.getenv("OPENAI_API_KEY")),
        "notebook_valid": True,
        "local_sandbox_checked": True,
        "live_api_calls_made": False,
    }


def execute_notebook(run_dir: Path, timeout: int) -> None:
    import nbformat
    from jupyter_client import KernelManager
    from jupyter_client.kernelspec import KernelSpecManager
    from nbclient import NotebookClient

    notebook = prepare_notebook()
    output = run_dir / "agent_improvement_loop.executed.ipynb"

    class ProgressClient(NotebookClient):
        def process_message(self, msg, cell, cell_index):
            result = super().process_message(msg, cell, cell_index)
            if msg["msg_type"] == "stream":
                print(msg["content"]["text"], end="", flush=True)
            return result

    def checkpoint(**kwargs) -> None:
        nbformat.write(notebook, output)

    def cell_started(cell, cell_index, **kwargs) -> None:
        if cell.cell_type == "code" and "skip-execution" not in cell.metadata.get("tags", []):
            print(f"\n[{datetime.now().astimezone().strftime('%H:%M:%S')}] Notebook cell {cell_index}", flush=True)

    # A temporary kernelspec guarantees use of this venv without registering
    # anything in the user's global Jupyter installation.
    with tempfile.TemporaryDirectory(prefix="agent-loop-kernel-") as directory:
        kernel_dir = Path(directory) / "agent-loop"
        kernel_dir.mkdir()
        (kernel_dir / "kernel.json").write_text(json.dumps({
            "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
            "display_name": "Agent improvement experiment",
            "language": "python",
        }), encoding="utf-8")
        specs = KernelSpecManager(kernel_dirs=[directory], ensure_native_kernel=False)
        manager = KernelManager(kernel_name="agent-loop", kernel_spec_manager=specs)
        client = ProgressClient(
            notebook,
            km=manager,
            timeout=timeout,
            allow_errors=False,
            on_cell_start=cell_started,
            on_cell_executed=checkpoint,
            resources={"metadata": {"path": str(ROOT)}},
        )
        try:
            client.execute(cwd=str(ROOT), cleanup_kc=True)
        finally:
            nbformat.write(notebook, output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate dependencies, notebook and local sandbox without API calls.")
    parser.add_argument("--cell-timeout", type=int, default=3600, help="Timeout for each notebook cell in seconds (default: 3600).")
    args = parser.parse_args()
    load_environment()
    report = check_setup()
    print(json.dumps(report, indent=2), flush=True)
    if args.check:
        print("Setup checks passed. Set OPENAI_API_KEY in the example folder's .env before a live run.")
        return 0
    if not report["api_key_present"]:
        print("Live run has not started: set OPENAI_API_KEY in the example folder's .env, then rerun its run_experiment.sh.", file=sys.stderr)
        return 2

    run_dir = RUNS / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    run_dir.mkdir(parents=True)
    if ARTIFACTS.exists():
        archived = run_dir / "previous_artifacts"
        shutil.move(str(ARTIFACTS), archived)
        print(f"Previous artifacts archived at {archived}")
    report["source_commit"] = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    report["upstream_cookbook_commit"] = "0f38c4a3c6cff6ae72da564a153e4bb7fd5b7636"
    report.pop("live_api_calls_made", None)
    report["live_execution_started"] = True
    report["status"] = "running"
    status_path = run_dir / "run.json"
    status_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Running five live traces and the feedback/eval/HALO stages. Results: {run_dir}", flush=True)
    try:
        execute_notebook(run_dir, args.cell_timeout)
        handoff = ARTIFACTS / "codex_handoff.md"
        if not handoff.is_file():
            raise RuntimeError("Notebook ended without the expected codex_handoff.md.")
        report["status"] = "completed"
        print(f"\nExperiment completed. Handoff: {handoff}")
        return 0
    except BaseException as exc:
        report["status"] = "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed"
        report["error_type"] = type(exc).__name__
        print(f"\nRun {report['status']}; saved notebook: {run_dir}", file=sys.stderr)
        raise
    finally:
        status_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
