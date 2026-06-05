from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional, cast

import yaml  # type: ignore[import]

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SETUP_DIR = PACKAGE_ROOT / "templates" / "setups"
PACKAGE_METADATA_FILE = PACKAGE_SETUP_DIR / "cliex-metadata.yaml"


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
    os_name = os.name
    if os_name == "nt":
        return _get_windows_config_dir()
    return _get_unix_config_dir()


def get_user_setup_dir() -> Path:
    return get_user_config_dir() / "setups"


def get_writeable_setup_dir() -> Path:
    """Return the best writable directory for setup files.

    In development mode (editable install), the package templates directory
    is writable, so we use it directly. In production mode (installed package
    or compiled .exe), we fall back to the user config directory.
    """
    import tempfile # type: ignore

    # Test if the package setup directory is writable
    try:
        test_file = PACKAGE_SETUP_DIR / ".write_test"
        test_file.touch()
        test_file.unlink()
        return PACKAGE_SETUP_DIR
    except OSError:
        # Not writable, fall back to user config directory
        user_dir = get_user_setup_dir()
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir


def _load_metadata_file(path: Path) -> Dict[str, Dict[str, Any]]:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if not isinstance(data, dict):
        return {}

    if "profiles" not in data:
        return {}
    
    profiles_raw = data["profiles"]     # type: ignore[assignment]
    if not isinstance(profiles_raw, dict):
        return {}

    return cast(Dict[str, Dict[str, Any]], profiles_raw)


def _scan_setup_files(directory: Path) -> Dict[str, Path]:
    result: Dict[str, Path] = {}
    if not directory.exists():
        return result

    for path in directory.glob("*.yaml"):
        if path.name == "cliex-metadata.yaml":
            continue
        key = path.stem
        result[key] = path

    return result


def load_registry() -> Dict[str, Dict[str, Any]]:
    profiles: Dict[str, Dict[str, Any]] = {}

    package_metadata = _load_metadata_file(PACKAGE_METADATA_FILE)
    package_files = _scan_setup_files(PACKAGE_SETUP_DIR)

    for key, path in package_files.items():
        metadata = package_metadata.get(key, {})
        profiles[key] = {
            "key": key,
            "name": metadata.get("name", key),
            "description": metadata.get("description", ""),
            "default": bool(metadata.get("default", False)),
            "path": path,
            "source": "package",
        }

    user_dir = get_user_setup_dir()
    user_metadata = _load_metadata_file(user_dir / "cliex-metadata.yaml")
    user_files = _scan_setup_files(user_dir)

    for key, path in user_files.items():
        metadata = user_metadata.get(key, {})
        profiles[key] = {
            "key": key,
            "name": metadata.get("name", key),
            "description": metadata.get("description", ""),
            "default": bool(metadata.get("default", False)),
            "path": path,
            "source": "user",
        }

    return profiles


def get_default_profile() -> Optional[Dict[str, Any]]:
    registry = load_registry()

    user_defaults = [
        profile for profile in registry.values()
        if profile["source"] == "user" and profile["default"]
    ]
    if len(user_defaults) > 1:
        raise RuntimeError("More than one user setup profile is marked default.")
    if user_defaults:
        return user_defaults[0]

    package_defaults = [
        profile for profile in registry.values()
        if profile["source"] == "package" and profile["default"]
    ]
    if len(package_defaults) > 1:
        raise RuntimeError("More than one packaged setup profile is marked default.")
    if package_defaults:
        return package_defaults[0]

    return None


def resolve_setup_path(setup_arg: Optional[str]) -> Path:
    if setup_arg:
        candidate = Path(setup_arg)
        if candidate.exists() and candidate.is_file():
            return candidate

        registry = load_registry()
        profile = registry.get(setup_arg)
        if profile is not None:
            path = profile["path"]
            if not path.exists():
                raise FileNotFoundError(f"Profile '{setup_arg}' setup file not found: {path}")
            return path

        available = ", ".join(sorted(registry.keys()))
        raise RuntimeError(
            f"Setup profile '{setup_arg}' not found. Available profiles: {available}"
        )

    default_profile = get_default_profile()
    if default_profile is None:
        raise RuntimeError("No default setup profile found in registry.")
    path = default_profile["path"]
    if not path.exists():
        raise FileNotFoundError(f"Default setup file not found: {path}")
    return path
