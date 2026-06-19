from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml  # type: ignore[import]

from cliex.setup.types import ProfileInfo, ProfileMetadata, Source

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SETUP_DIR = PACKAGE_ROOT / "templates" / "setups"

# The bundled default profile. Changes only when the maintainer edits source.
BUILTIN_DEFAULT_KEY = "nextjs-setup"

# Legacy file that older versions stored central metadata in. We no longer use
# it (metadata is now embedded in each profile), but keep skipping it so a
# leftover copy in a user directory is never treated as a profile.
_LEGACY_METADATA_NAME = "cliex-metadata.yaml"
_CONFIG_NAME = "config.yaml"


def _get_windows_config_dir() -> Path:
    appdata = os.getenv("APPDATA")
    if appdata:
        return Path(appdata) / "cliex"
    return Path.home() / "AppData" / "Roaming" / "cliex"


def _get_unix_config_dir() -> Path:
    xdg_config = os.getenv("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "cliex"
    return Path.home() / ".config" / "cliex"


def get_user_config_dir() -> Path:
    if os.name == "nt":
        return _get_windows_config_dir()
    return _get_unix_config_dir()


def get_user_setup_dir() -> Path:
    return get_user_config_dir() / "setups"


def _user_config_file() -> Path:
    """Path to the small user config holding the default profile key."""
    return get_user_config_dir() / _CONFIG_NAME


# ---------------------------------------------------------------------------
# User default (stored separately from profiles so shared files never carry it)
# ---------------------------------------------------------------------------

def read_user_default() -> Optional[str]:
    path = _user_config_file()
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(data, dict):
        return None
    default = data.get("default") # type: ignore
    return default if isinstance(default, str) else None


def write_user_default(key: str) -> None:
    path = _user_config_file()
    data: Dict[str, Any] = {}
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as handle:
                loaded = yaml.safe_load(handle)
            if isinstance(loaded, dict):
                data = loaded # type: ignore
        except (OSError, yaml.YAMLError):
            data = {}
    data["default"] = key
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.dump(data, handle, default_flow_style=False, sort_keys=False)


def clear_user_default() -> None:
    path = _user_config_file()
    if not path.exists():
        return
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError):
        return
    if not isinstance(data, dict) or "default" not in data:
        return
    data.pop("default", None) # type: ignore
    with path.open("w", encoding="utf-8") as handle:
        yaml.dump(data, handle, default_flow_style=False, sort_keys=False)


# ---------------------------------------------------------------------------
# Embedded metadata + file scanning
# ---------------------------------------------------------------------------

def _read_embedded_metadata(path: Path) -> ProfileMetadata:
    """Read name/description embedded in a profile file. Never raises."""
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as exc:
        return ProfileMetadata(
            name=path.stem, description="", valid=False, error=f"Invalid YAML: {exc}"
        )

    if not isinstance(data, dict):
        return ProfileMetadata(
            name=path.stem, description="", valid=False, error="Profile must be a mapping"
        )

    name = data.get("name") # type: ignore
    description = data.get("description") # type: ignore
    steps = data.get("steps") # type: ignore

    valid = isinstance(steps, list)
    return ProfileMetadata(
        name=name if isinstance(name, str) and name else path.stem,
        description=description if isinstance(description, str) else "",
        valid=valid,
        error=None if valid else "Missing or invalid 'steps' list",
    )


def _scan_dir(directory: Path) -> Dict[str, Path]:
    result: Dict[str, Path] = {}
    if not directory.exists():
        return result
    for path in directory.glob("*.yaml"):
        if path.name == _LEGACY_METADATA_NAME:
            continue
        result[path.stem] = path
    return result


def _package_files() -> Dict[str, Path]:
    return _scan_dir(PACKAGE_SETUP_DIR)


def _user_files() -> Dict[str, Path]:
    return _scan_dir(get_user_setup_dir())


def get_user_setup_path(key: str) -> Path:
    return get_user_setup_dir() / f"{key}.yaml"


def get_builtin_setup_path(key: str) -> Optional[Path]:
    return _package_files().get(key)


def fork_builtin_to_user(key: str) -> Path:
    """Copy a built-in profile into the user setup dir (creates an override)."""
    src = get_builtin_setup_path(key)
    if src is None:
        raise FileNotFoundError(f"No built-in profile named '{key}' to fork.")
    user_dir = get_user_setup_dir()
    user_dir.mkdir(parents=True, exist_ok=True)
    dest = get_user_setup_path(key)
    shutil.copy(src, dest)
    return dest


def delete_user_override(key: str) -> bool:
    """Delete a user profile file. Returns True if a file was removed."""
    path = get_user_setup_path(key)
    if path.exists():
        path.unlink()
        return True
    return False


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

def _effective_default_key() -> Optional[str]:
    user_default = read_user_default()
    if user_default:
        return user_default
    return BUILTIN_DEFAULT_KEY


def _make_entry(key: str, path: Path, source: Source) -> ProfileInfo:
    meta = _read_embedded_metadata(path)
    return ProfileInfo(
        key=key,
        name=meta["name"],
        description=meta["description"],
        path=path,
        source=source,
        valid=meta["valid"],
        error=meta["error"],
        default=False,
    )


def load_registry() -> Dict[str, ProfileInfo]:
    """Build the merged registry of profiles (built-in + user, user wins)."""
    profiles: Dict[str, ProfileInfo] = {}

    package_files = _package_files()
    user_files = _user_files()
    default_key = _effective_default_key()

    for key, path in package_files.items():
        profiles[key] = _make_entry(key, path, "built-in")

    for key, path in user_files.items():
        source: Source = "user override" if key in package_files else "user custom"
        profiles[key] = _make_entry(key, path, source)

    if default_key and default_key in profiles:
        profiles[default_key]["default"] = True

    return profiles


def get_default_profile() -> Optional[ProfileInfo]:
    registry = load_registry()
    key = _effective_default_key()
    if key and key in registry:
        return registry[key]
    return None


def resolve_setup_path(setup_arg: Optional[str]) -> Path:
    if not setup_arg:
        default_profile = get_default_profile()
        if default_profile is None:
            raise RuntimeError("No default setup profile found.")
        path = default_profile["path"]
        if not path.exists():
            raise FileNotFoundError(f"Default setup file not found: {path}")
        return path

    # Forced scope: built-in only
    if setup_arg.startswith("b:"):
        key = setup_arg[2:]
        path = _package_files().get(key)
        if path is None:
            raise RuntimeError(f"No built-in profile named '{key}'.")
        return path

    # Forced scope: user custom only
    if setup_arg.startswith("u:"):
        key = setup_arg[2:]
        path = _user_files().get(key)
        if path is None:
            raise RuntimeError(f"No user profile named '{key}'.")
        return path

    # Explicit file path wins
    candidate = Path(setup_arg)
    if candidate.exists() and candidate.is_file():
        return candidate

    # Merged registry lookup (user overrides built-in)
    registry = load_registry()
    profile = registry.get(setup_arg)
    if profile is not None:
        path = profile["path"]
        if not path.exists():
            raise FileNotFoundError(f"Profile '{setup_arg}' setup file not found: {path}")
        return path

    available = ", ".join(sorted(registry.keys())) or "(none)"
    raise RuntimeError(
        f"Setup profile '{setup_arg}' not found. Available profiles: {available}"
    )


# ---------------------------------------------------------------------------
# Validation (shared by `cliex validate` and lazy checks)
# ---------------------------------------------------------------------------

_VALID_WHEN = {"windows", "unix", "linux", "macos", "darwin"}


def validate_profile(path: Path) -> List[str]:
    """Return a list of problem messages for a profile. Empty list = OK.

    Messages prefixed with 'Warning:' are non-fatal.
    """
    # Imported lazily to avoid a circular import at module load.
    from cliex.setup.executor import STEP_HANDLERS

    problems: List[str] = []

    if not path.exists():
        return [f"File not found: {path}"]

    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as exc:
        return [f"Invalid YAML: {exc}"]

    if not isinstance(data, dict):
        return ["Profile must be a mapping (top-level keys)"]

    name = data.get("name") # type: ignore
    if not isinstance(name, str) or not name:
        problems.append("Warning: missing 'name'")
    description = data.get("description") # type: ignore
    if not isinstance(description, str) or not description:
        problems.append("Warning: missing 'description'")

    variables = data.get("variables") # type: ignore
    if variables is not None:
        if not isinstance(variables, list):
            problems.append("'variables' must be a list")
        else:
            for i, var in enumerate(variables, start=1): # type: ignore
                if not isinstance(var, dict) or not isinstance(var.get("name"), str): # type: ignore
                    problems.append(f"variable {i} must be a mapping with a 'name'")

    steps = data.get("steps") # type: ignore
    if not isinstance(steps, list):
        problems.append("Missing or invalid 'steps' list")
        return problems

    for i, step in enumerate(steps, start=1): # type: ignore
        if not isinstance(step, dict):
            problems.append(f"step {i} must be a mapping")
            continue
        step_type = step.get("type") # type: ignore
        if not isinstance(step_type, str):
            problems.append(f"step {i} missing 'type'")
        elif step_type not in STEP_HANDLERS:
            known = ", ".join(sorted(STEP_HANDLERS))
            problems.append(f"step {i} unknown type '{step_type}' (known: {known})")
        step_name = step.get("name") # type: ignore
        if step_name is not None and not isinstance(step_name, str):
            problems.append(f"step {i} has invalid 'name'")
        when = step.get("when") # type: ignore
        if when is not None and (not isinstance(when, str) or when.lower() not in _VALID_WHEN):
            problems.append(
                f"Warning: step {i} has unknown 'when' value '{when}' "
                f"(expected one of: {', '.join(sorted(_VALID_WHEN))})"
            )

    return problems
