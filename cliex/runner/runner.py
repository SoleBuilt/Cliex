"""Command execution utilities."""

import subprocess
import shutil
from pathlib import Path
from typing import Optional

from rich.console import Console

console = Console()


def run_command(command: str, cwd: Optional[Path] = None) -> None:
    """
    Run an external command and stream output to terminal.
    
    Args:
        command: Command string to execute.
        cwd: Working directory for the command.
        
    Raises:
        RuntimeError: If command fails.
    """
    console.print(f"[cyan]Running: {command}[/cyan]")
    
    try:
        subprocess.run(
            command,
            cwd=cwd,
            check=True,
            shell=True,
        )
    except FileNotFoundError:
        # Try resolving executable via shutil.which and retry
        first_word = command.split()[0]
        exe = shutil.which(first_word)
        if exe:
            console.print(f"[yellow]Command {first_word} not found directly, trying {exe}[/yellow]")
            command2 = ' '.join([exe] + command.split()[1:])
            try:
                subprocess.run(command2, cwd=cwd, check=True, shell=True)
                return
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Command {exe} failed with exit code {e.returncode}")
        raise RuntimeError(f"Command {first_word} not found")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Command {command.split()[0]} failed with exit code {e.returncode}")
