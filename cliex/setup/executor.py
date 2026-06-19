from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, cast

from rich.console import Console

from cliex.runner.runner import run_command

console = Console()


def _resolve(value: str, project_path: Path, base_path: Path, *, from_base: bool = False) -> Path:
    """Resolve a step path: absolute as-is, else relative to project (or base)."""
    path = Path(value)
    if path.is_absolute():
        return path
    return (base_path if from_base else project_path) / path


def handle_run(step: dict[str, Any], project_path: Path, base_path: Path) -> None:
    cmd = step.get("cmd")
    if not cmd or not isinstance(cmd, str):
        raise ValueError("run step requires a command string in 'cmd'")
    name = step.get("name") or cmd.split()[0]
    console.print(f"[cyan]Running: {name}...[/cyan]")
    run_command(cmd, cwd=project_path)
    console.print(f"[green]✓ {name} completed[/green]")


def handle_copy(step: dict[str, Any], project_path: Path, base_path: Path) -> None:
    src = step.get("src")
    dest = step.get("dest")
    if not src or not dest:
        raise ValueError("copy step requires 'src' and 'dest'")

    # Prefer a path inside the project (runtime-generated files); fall back to
    # the profile directory (template files shipped alongside the profile).
    src_path = _resolve(src, project_path, base_path)
    if not src_path.exists():
        from_base = _resolve(src, project_path, base_path, from_base=True)
        if from_base.exists():
            src_path = from_base
    if not src_path.exists():
        raise FileNotFoundError(f"Source for copy not found: {src_path}")

    dest_path = _resolve(dest, project_path, base_path)

    if src_path.is_dir():
        shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
    else:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src_path, dest_path)
    console.print(f"[green]✓ Copied {src_path} to {dest_path}[/green]")


def handle_append(step: dict[str, Any], project_path: Path, base_path: Path) -> None:
    file_name = step.get("file")
    content = step.get("content")
    if not file_name or content is None:
        raise ValueError("append step requires 'file' and 'content'")

    target_path = _resolve(file_name, project_path, base_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("a", encoding="utf-8") as handle:
        handle.write(str(content))
    console.print(f"[green]✓ Appended content to {target_path}[/green]")


def handle_mkdir(step: dict[str, Any], project_path: Path, base_path: Path) -> None:
    path_value = step.get("path")
    if not path_value or not isinstance(path_value, str):
        raise ValueError("mkdir step requires 'path'")
    target = _resolve(path_value, project_path, base_path)
    target.mkdir(parents=True, exist_ok=True)
    console.print(f"[green]✓ Created directory {target}[/green]")


def handle_move(step: dict[str, Any], project_path: Path, base_path: Path) -> None:
    src = step.get("src")
    dest = step.get("dest")
    if not src or not dest:
        raise ValueError("move step requires 'src' and 'dest'")
    src_path = _resolve(src, project_path, base_path)
    if not src_path.exists():
        raise FileNotFoundError(f"Source for move not found: {src_path}")
    dest_path = _resolve(dest, project_path, base_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src_path), str(dest_path))
    console.print(f"[green]✓ Moved {src_path} to {dest_path}[/green]")


def handle_remove(step: dict[str, Any], project_path: Path, base_path: Path) -> None:
    path_value = step.get("path")
    if not path_value or not isinstance(path_value, str):
        raise ValueError("remove step requires 'path'")
    ignore_missing = step.get("ignore_missing", True)
    target = _resolve(path_value, project_path, base_path)
    if not target.exists():
        if ignore_missing:
            console.print(f"[yellow]⊘ Nothing to remove at {target}[/yellow]")
            return
        raise FileNotFoundError(f"Path to remove not found: {target}")
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()
    console.print(f"[green]✓ Removed {target}[/green]")


def handle_git(step: dict[str, Any], project_path: Path, base_path: Path) -> None:
    if "username" in step:
        run_command(f"git config --local user.name '{step['username']}'", cwd=project_path)
        console.print("[green]✓ Git username configured[/green]")

    if "email" in step:
        run_command(f"git config --local user.email '{step['email']}'", cwd=project_path)
        console.print("[green]✓ Git email configured[/green]")

    if "add" in step:
        run_command(f"git add {step['add']}", cwd=project_path)
        console.print("[green]✓ Git add completed[/green]")

    if "commit_message" in step:
        run_command(f"git commit -m \"{step['commit_message']}\"", cwd=project_path)
        console.print("[green]✓ Git commit completed[/green]")


STEP_HANDLER = Callable[[dict[str, Any], Path, Path], None]
STEP_HANDLERS: Dict[str, STEP_HANDLER] = {
    "run": handle_run,
    "copy": handle_copy,
    "append": handle_append,
    "mkdir": handle_mkdir,
    "move": handle_move,
    "remove": handle_remove,
    "git": handle_git,
}


def _platform_matches(when: str) -> bool:
    when = when.lower()
    is_windows = os.name == "nt"
    if when == "windows":
        return is_windows
    if when in ("unix", "linux"):
        return not is_windows and not sys.platform.startswith("darwin")
    if when in ("macos", "darwin"):
        return sys.platform.startswith("darwin")
    # Unknown value: don't skip (validator already warns).
    return True


def execute_setup(config: dict[str, Any], project_path: Path) -> None:
    steps_raw = config.get("steps")
    if not isinstance(steps_raw, list):
        raise ValueError("Setup config must contain a list of steps under 'steps'")

    steps_any = cast(List[Any], steps_raw)
    validated_steps: List[dict[str, Any]] = []
    for index, raw_step in enumerate(steps_any, start=1):
        if not isinstance(raw_step, dict):
            raise ValueError(f"Step {index} must be a mapping")
        validated_steps.append(cast(dict[str, Any], raw_step))

    steps = validated_steps
    base_path_value = config.get("_base_path")
    if isinstance(base_path_value, Path):
        base_path = base_path_value
    elif isinstance(base_path_value, str):
        base_path = Path(base_path_value)
    else:
        base_path = project_path

    for index, step in enumerate(steps, start=1):
        step_type = step.get("type")
        if not isinstance(step_type, str):
            raise ValueError(f"Step {index} is missing the required 'type' field")

        step_name = step.get("name")
        if step_name is not None and not isinstance(step_name, str):
            raise ValueError(f"Step {index} has invalid 'name' field")

        when = step.get("when")
        if isinstance(when, str) and not _platform_matches(when):
            console.print(
                f"[yellow]⊘ Step {index}/{len(steps)} skipped (when={when})[/yellow]"
            )
            continue

        handler = STEP_HANDLERS.get(step_type)
        if handler is None:
            raise ValueError(f"Unknown step type '{step_type}' at step {index}")

        console.print(f"[yellow]Step {index}/{len(steps)}: {step_type}: {step_name}[/yellow]")
        handler(step, project_path, base_path)
