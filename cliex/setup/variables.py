"""Variable resolution and substitution for setup profiles.

Profiles may declare a top-level ``variables:`` list and reference values
using mustache-style ``{{ name }}`` placeholders inside step string fields.
Only plain name substitution is supported (no expressions, filters, or loops)
to keep the dependency footprint minimal and avoid template injection.
"""

from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any, Dict, List

import typer
from rich.console import Console

console = Console()

# Matches {{ name }} with optional surrounding whitespace.
_PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")

# Step string fields that get substitution applied.
_STRING_FIELDS = (
    "cmd",
    "content",
    "file",
    "src",
    "dest",
    "path",
    "add",
    "commit_message",
    "username",
    "email",
)


def resolve_context(
    config: Dict[str, Any],
    project_name: str,
    project_path: Path,
    cli_vars: Dict[str, str],
    assume_yes: bool,
) -> Dict[str, str]:
    """Build the substitution context from builtins, declarations, and CLI."""
    context: Dict[str, str] = {
        "project_name": project_name,
        "project_path": str(project_path),
    }

    declarations = config.get("variables")
    if declarations and isinstance(declarations, list):
        for raw in declarations:
            if not isinstance(raw, dict):
                continue
            name = raw.get("name")
            if not isinstance(name, str) or not name:
                continue
            default = raw.get("default")
            prompt_text = raw.get("prompt") or f"Enter value for '{name}'"

            if name in cli_vars:
                context[name] = cli_vars[name]
            elif assume_yes:
                if default is not None:
                    context[name] = str(default)
                else:
                    raise RuntimeError(
                        f"Variable '{name}' has no value. Pass --var {name}=<value>."
                    )
            else:
                answer = typer.prompt(
                    prompt_text,
                    default=str(default) if default is not None else None,
                )
                context[name] = str(answer)

    # CLI vars that weren't declared are still usable (ad-hoc).
    for key, value in cli_vars.items():
        context.setdefault(key, value)

    return context


def _substitute(value: str, context: Dict[str, str]) -> str:
    def replace(match: "re.Match[str]") -> str:
        name = match.group(1)
        if name not in context:
            available = ", ".join(sorted(context)) or "(none)"
            raise RuntimeError(
                f"Unknown variable '{{{{ {name} }}}}'. Available variables: {available}"
            )
        return context[name]

    return _PLACEHOLDER.sub(replace, value)


def render_steps(steps: List[Any], context: Dict[str, str]) -> List[Any]:
    """Return a copy of steps with {{ var }} placeholders substituted."""
    rendered = copy.deepcopy(steps)
    for step in rendered:
        if not isinstance(step, dict):
            continue
        for field in _STRING_FIELDS:
            if field in step and isinstance(step[field], str):
                step[field] = _substitute(step[field], context)
    return rendered
