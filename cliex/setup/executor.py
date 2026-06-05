from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Callable, Dict, List, cast

from rich.console import Console

from cliex.runner.runner import run_command

console = Console()


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

    src_path = Path(src)
    if not src_path.is_absolute():
        src_path = Path(base_path) / src_path

    if not src_path.exists():
        raise FileNotFoundError(f"Source file for copy not found: {src_path}")

    dest_path = Path(dest)
    if not dest_path.is_absolute():
        dest_path = project_path / dest_path

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src_path, dest_path)
    console.print(f"[green]✓ Copied {src_path} to {dest_path}[/green]")


def handle_append(step: dict[str, Any], project_path: Path, base_path: Path) -> None:
    file_name = step.get("file")
    content = step.get("content")
    if not file_name or content is None:
        raise ValueError("append step requires 'file' and 'content'")

    target_path = Path(file_name)
    if not target_path.is_absolute():
        target_path = project_path / target_path

    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("a", encoding="utf-8") as handle:
        handle.write(str(content))
    console.print(f"[green]✓ Appended content to {target_path}[/green]")


def handle_git(step: dict[str, Any], project_path: Path, base_path: Path) -> None:
    if "username" in step:
        run_command(f"git config --global user.name '{step['username']}'", cwd=project_path)
        console.print("[green]✓ Git username configured[/green]")

    if "email" in step:
        run_command(f"git config --global user.email '{step['email']}'", cwd=project_path)
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
    "git": handle_git,
}


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

        handler = STEP_HANDLERS.get(step_type)
        if handler is None:
            raise ValueError(f"Unknown step type '{step_type}' at step {index}")

        console.print(f"[yellow]Step {index}/{len(steps)}: {step_type}: {step_name}[/yellow]")
        handler(step, project_path, base_path)
