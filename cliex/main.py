"""Main CLI entry point."""

import sys
import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
from rich.console import Console

from cliex.cli.new import new_project


app = typer.Typer(
    help="CLI tool for project setup quickly with customizable YAML profiles."
)
console = Console()


def _parse_vars(pairs: Optional[List[str]]) -> Dict[str, str]:
    """Parse repeated --var key=value options into a dict."""
    result: Dict[str, str] = {}
    if not pairs:
        return result
    for pair in pairs:
        if "=" not in pair:
            raise typer.BadParameter(f"--var must be key=value, got '{pair}'")
        key, value = pair.split("=", 1)
        key = key.strip()
        if not key:
            raise typer.BadParameter(f"--var key cannot be empty in '{pair}'")
        result[key] = value
    return result


@app.command()
def new(
    project_name: Optional[str] = typer.Argument(
        None,
        help="Project name or '.' for current directory. Defaults to '.' if not provided.",
    ),
    setup_name: Optional[str] = typer.Option(
        None,
        "--setup",
        "-s",
        help="Setup profile key, 'b:key' (built-in), 'u:key' (user), or YAML file path.",
    ),
    var: Optional[List[str]] = typer.Option(
        None,
        "--var",
        "-v",
        help="Set a profile variable, e.g. --var git_user=Duc. Repeatable.",
    ),
    assume_yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Don't prompt for variables; use declared defaults.",
    ),
) -> None:
    """Create a new project with setup."""
    try:
        if project_name is None:
            project_name = "."

        cli_vars = _parse_vars(var)
        new_project(project_name, setup_name, cli_vars, assume_yes)
    except RuntimeError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("[yellow]Setup cancelled by user[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


def open_file_in_editor(path: Path) -> None:
    """Open a file in the system's default text editor."""
    import platform
    import os
    import subprocess

    system = platform.system()
    try:
        if system == "Windows":
            try:
                os.startfile(path)
            except OSError:
                # Fallback to notepad
                subprocess.run(["notepad.exe", str(path)])
        elif system == "Darwin":  # macOS
            subprocess.run(["open", str(path)], check=True)
        else:  # Linux
            subprocess.run(["xdg-open", str(path)], check=True)
    except Exception as e:
        raise RuntimeError(f"Failed to open editor: {e}")


@app.command(name="list")
def list_profiles() -> None:
    """List all registered setup profiles."""
    from cliex.setup.registry import load_registry
    from rich.table import Table

    try:
        registry = load_registry()
        if not registry:
            console.print("[yellow]No setup profiles found.[/yellow]")
            return

        table = Table(title="Available Setup Profiles")
        table.add_column("Key", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Source", style="magenta")
        table.add_column("Default", style="yellow", justify="center")
        table.add_column("Description", style="white")

        for key, profile in sorted(registry.items()):
            if profile.get("valid", True):
                description = profile.get("description", "")
                key_cell = key
            else:
                description = f"[red]⚠ {profile.get('error', 'invalid profile')}[/red]"
                key_cell = f"[red]{key}[/red]"
            table.add_row(
                key_cell,
                profile.get("name", ""),
                profile.get("source", ""),
                "Yes" if profile.get("default") else "",
                description,
            )

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error listing profiles: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="registry")
def registry(
    setup_name: str = typer.Argument(
        ...,
        help="The name of the setup profile to create/fork/edit.",
    )
) -> None:
    """Create, fork, or edit a setup profile yaml file (always in the user directory)."""
    from cliex.setup.registry import (
        get_builtin_setup_path,
        get_user_setup_dir,
        get_user_setup_path,
        fork_builtin_to_user,
    )
    import yaml

    try:
        profile_key = setup_name.removesuffix(".yaml")
        user_dir = get_user_setup_dir()
        user_dir.mkdir(parents=True, exist_ok=True)
        user_path = get_user_setup_path(profile_key)

        if user_path.exists():
            console.print(f"[cyan]Opening existing user profile: {user_path}[/cyan]")
        elif get_builtin_setup_path(profile_key) is not None:
            user_path = fork_builtin_to_user(profile_key)
            console.print(
                f"[green]Forked built-in '{profile_key}' to a local override: {user_path}[/green]"
            )
            console.print(
                "[yellow]This local copy overrides the built-in; future updates won't touch it.[/yellow]"
            )
        else:
            template: Dict[str, Any] = {
                "name": profile_key,
                "description": f"Custom setup profile: {profile_key}",
                "steps": [
                    {
                        "type": "run",
                        "name": "say-hello",
                        "cmd": 'echo "Hello from your new setup profile!"',
                    }
                ],
            }
            with user_path.open("w", encoding="utf-8") as handle:
                yaml.dump(template, handle, default_flow_style=False, sort_keys=False)
            console.print(f"[green]Created new setup profile: {user_path}[/green]")

        open_file_in_editor(user_path)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="set-default")
def set_default(
    setup_name: str = typer.Argument(..., help="Profile key to set as default.")
) -> None:
    """Set the default setup profile (used when 'new' has no --setup)."""
    from cliex.setup.registry import load_registry, write_user_default

    try:
        key = setup_name.removesuffix(".yaml")
        registry = load_registry()
        if key not in registry:
            available = ", ".join(sorted(registry.keys())) or "(none)"
            console.print(
                f"[red]Profile '{key}' not found. Available: {available}[/red]"
            )
            raise typer.Exit(1)
        write_user_default(key)
        console.print(f"[green]✓ Default profile set to '{key}'[/green]")
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="reset")
def reset(
    setup_name: str = typer.Argument(
        ..., help="Profile key whose user override should be removed."
    )
) -> None:
    """Remove a user override and revert to the built-in profile."""
    from cliex.setup.registry import (
        clear_user_default,
        delete_user_override,
        get_builtin_setup_path,
        read_user_default,
    )

    try:
        key = setup_name.removesuffix(".yaml")
        if get_builtin_setup_path(key) is None:
            console.print(
                f"[red]No built-in profile named '{key}' to revert to.[/red]"
            )
            raise typer.Exit(1)
        if not delete_user_override(key):
            console.print(
                f"[yellow]No user override for '{key}'; already using the built-in.[/yellow]"
            )
            return
        if read_user_default() == key:
            clear_user_default()
        console.print(f"[green]✓ Reverted '{key}' to the built-in profile.[/green]")
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="validate")
def validate(
    setup_name: Optional[str] = typer.Argument(
        None, help="Profile key to validate. Omit to validate all profiles."
    )
) -> None:
    """Validate one or all setup profiles."""
    from cliex.setup.registry import load_registry, validate_profile

    try:
        registry = load_registry()
        if setup_name:
            key = setup_name.removesuffix(".yaml")
            if key not in registry:
                available = ", ".join(sorted(registry.keys())) or "(none)"
                console.print(f"[red]Profile '{key}' not found. Available: {available}[/red]")
                raise typer.Exit(1)
            targets = {key: registry[key]}
        else:
            targets = registry

        if not targets:
            console.print("[yellow]No setup profiles found.[/yellow]")
            return

        had_error = False
        for key, profile in sorted(targets.items()):
            problems = validate_profile(profile["path"])
            errors = [p for p in problems if not p.startswith("Warning:")]
            warnings = [p for p in problems if p.startswith("Warning:")]
            if errors:
                had_error = True
                console.print(f"[red]✗ {key}[/red]")
                for p in errors:
                    console.print(f"    [red]{p}[/red]")
            else:
                console.print(f"[green]✓ {key}[/green]")
            for w in warnings:
                console.print(f"    [yellow]{w}[/yellow]")

        if had_error:
            raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
