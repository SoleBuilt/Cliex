"""Main CLI entry point."""

import sys
import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from cliex.cli.new import new_project


app = typer.Typer(
    help="CLI tool for project setup quickly with customizable YAML profiles."
)
console = Console()


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
        help="Setup profile key or YAML setup file path.",
    ),
) -> None:
    """Create a new project with setup."""
    try:
        if project_name is None:
            project_name = "."

        new_project(project_name, setup_name)
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
            table.add_row(
                key,
                profile.get("name", ""),
                profile.get("source", ""),
                "Yes" if profile.get("default") else "",
                profile.get("description", ""),
            )

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error listing profiles: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="registry")
def registry(
    setup_name: str = typer.Argument(
        ...,
        help="The name of the new setup profile to create/edit.",
    )
) -> None:
    """Create or edit a setup profile yaml file."""
    from cliex.setup.registry import get_writeable_setup_dir
    import yaml

    try:
        setup_dir = get_writeable_setup_dir()
        console.print(f"[cyan]Using setup directory: {setup_dir}[/cyan]")

        # Normalize the profile key (strip .yaml if user typed it)
        profile_key = setup_name.removesuffix(".yaml")
        filename = f"{profile_key}.yaml"
        filepath = setup_dir / filename

        # Create the setup YAML file if it doesn't exist
        if not filepath.exists():
            template = {
                "steps": [
                    {
                        "type": "run",
                        "name": "say-hello",
                        "cmd": 'echo "Hello from your new setup profile!"'
                    }
                ]
            }
            with filepath.open("w", encoding="utf-8") as handle:
                yaml.dump(template, handle, default_flow_style=False, sort_keys=False)
            console.print(f"[green]Created new setup profile: {filepath}[/green]")

            # Auto-update metadata.yaml to register the new profile
            metadata_path = setup_dir / "cliex-metadata.yaml"
            metadata: dict = {}
            if metadata_path.exists():
                with metadata_path.open("r", encoding="utf-8") as handle:
                    metadata = yaml.safe_load(handle) or {}

            if "profiles" not in metadata:
                metadata["profiles"] = {}

            if profile_key not in metadata["profiles"]:
                metadata["profiles"][profile_key] = {
                    "name": profile_key,
                    "description": f"Custom setup profile: {profile_key}",
                    "default": False,
                }
                with metadata_path.open("w", encoding="utf-8") as handle:
                    yaml.dump(metadata, handle, default_flow_style=False, sort_keys=False)
                console.print(f"[green]Registered '{profile_key}' in {metadata_path}[/green]")
        else:
            console.print(f"[cyan]Opening existing setup profile: {filepath}[/cyan]")

        open_file_in_editor(filepath)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="metadata")
def metadata_edit() -> None:
    """Open the cliex-metadata.yaml file for editing."""
    from cliex.setup.registry import get_writeable_setup_dir

    try:
        setup_dir = get_writeable_setup_dir()
        filepath = setup_dir / "cliex-metadata.yaml"

        if not filepath.exists():
            console.print(f"[yellow]cliex-metadata.yaml not found at: {filepath}[/yellow]")
            raise typer.Exit(1)

        console.print(f"[cyan]Opening cliex metadata: {filepath}[/cyan]")
        open_file_in_editor(filepath)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
