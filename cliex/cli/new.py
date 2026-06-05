"""New project creation logic."""

from pathlib import Path
from typing import Optional

from rich.console import Console

from cliex.checker.checker import check_required_commands
from cliex.setup import execute_setup, load_setup_config, resolve_setup_path

console = Console()


def new_project(project_name: str = ".", setup_name: Optional[str] = None) -> None:
    """
    Create a new Next.js project with shadcn/ui, Firebase, and agent skills.

    Args:
        project_name: Project name or "." for current directory.
        setup_name: Optional profile key or YAML setup file path.

    Raises:
        RuntimeError: If any critical step fails.
    """
    if not project_name:
        project_name = "."

    console.print(f"[bold blue]Creating project: {project_name}[/bold blue]")

    console.print("[yellow]Checking required commands...[/yellow]")
    check_required_commands(["node", "npm", "npx", "git"])
    console.print("[green]✓ All required commands found[/green]")

    cwd = Path.cwd()

    if project_name == ".":
        project_path = cwd
    else:
        project_path = cwd / project_name

    if project_name != ".":
        if project_path.exists():
            raise RuntimeError(f"Target folder {project_path} already exists")
    else:
        if (cwd / "package.json").exists():
            raise RuntimeError(
                "Current directory already has package.json. "
                "Please use a different directory or clean up first."
            )

    console.print(f"[cyan]Project path: {project_path}[/cyan]")

    project_path.mkdir(parents=True, exist_ok=True)

    setup_path = resolve_setup_path(setup_name)
    console.print(f"[cyan]Using setup: {setup_path.name}[/cyan]")
    config = load_setup_config(setup_path)
    execute_setup(config, project_path)

    console.print("[bold green]Project setup completed![/bold green]")
    console.print("[bold]Next steps:[/bold]")
    if project_name != ".":
        console.print(f"  cd {project_name}")
    console.print("  npm run dev")
    console.print("[yellow]---------------------------[/yellow]")
