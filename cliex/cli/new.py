"""New project creation logic."""

from pathlib import Path
from typing import Dict, Optional

from rich.console import Console

from cliex.checker.checker import check_required_commands
from cliex.setup import execute_setup, load_setup_config, resolve_setup_path
from cliex.setup.variables import render_steps, resolve_context

console = Console()


def new_project(
    project_name: str = ".",
    setup_name: Optional[str] = None,
    cli_vars: Optional[Dict[str, str]] = None,
    assume_yes: bool = False,
    git_username: Optional[str] = None,
    git_email: Optional[str] = None,
) -> None:
    """
    Create a new project from a setup profile.

    Args:
        project_name: Project name or "." for current directory.
        setup_name: Optional profile key (or 'b:'/'u:' prefix) or YAML file path.
        cli_vars: Variable overrides from the command line.
        assume_yes: Skip variable prompts and use declared defaults.
        git_username: Override git user.name for this run (else the stored default).
        git_email: Override git user.email for this run (else the stored default).

    Raises:
        RuntimeError: If any critical step fails.
    """
    if not project_name:
        project_name = "."
    cli_vars = cli_vars or {}

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

    context = resolve_context(config, project_name, project_path, cli_vars, assume_yes)

    # Git identity available to profiles as {{ git_username }} / {{ git_email }}.
    # Precedence: CLI flag > stored default (cliex config) > "" (git uses global).
    from cliex.setup.registry import read_user_git

    default_username, default_email = read_user_git()
    context["git_username"] = git_username or default_username or ""
    context["git_email"] = git_email or default_email or ""

    config["steps"] = render_steps(config["steps"], context)

    execute_setup(config, project_path)

    console.print("[bold green]Project setup completed![/bold green]")
    console.print("[bold]Next steps:[/bold]")
    if project_name != ".":
        console.print(f"  cd {project_name}")
    console.print("  npm run dev")
    console.print("[yellow]---------------------------[/yellow]")
