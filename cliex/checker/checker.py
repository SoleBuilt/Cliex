"""System requirement checker."""

import shutil
from typing import List


def check_required_commands(commands: List[str]) -> None:
    """
    Check if required commands are available in PATH.
    
    Args:
        commands: List of command names to check.
        
    Raises:
        RuntimeError: If any required command is not found.
    """
    missing = []
    for cmd in commands:
        if shutil.which(cmd) is None:
            missing.append(cmd)
    
    if missing:
        raise RuntimeError(f"Missing required commands: {', '.join(missing)}")
