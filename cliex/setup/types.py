"""Shared typed structures for the setup package."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional, TypedDict

# Where a profile lives / how it relates to the built-in set.
Source = Literal["built-in", "user custom", "user override"]

# Platform selector for a step's optional `when` field.
When = Literal["windows", "unix", "linux", "macos", "darwin"]


class ProfileMetadata(TypedDict):
    """Metadata read from inside a profile file (never raises on bad input)."""

    name: str
    description: str
    valid: bool
    error: Optional[str]


class ProfileInfo(TypedDict):
    """A registry entry describing one available setup profile."""

    key: str
    name: str
    description: str
    path: Path
    source: Source
    valid: bool
    error: Optional[str]
    default: bool
