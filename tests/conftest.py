"""Shared pytest fixtures."""

from pathlib import Path

import pytest

from cliex.setup import registry


@pytest.fixture
def user_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolate the user config/setup directory to a temp path.

    Patching ``get_user_config_dir`` redirects every derived path
    (setups dir, config.yaml) without touching the real user profile.
    Returns the user *setups* directory.
    """
    config_dir = tmp_path / "cliex-config"

    monkeypatch.setattr(registry, "get_user_config_dir", lambda: config_dir)

    setups = config_dir / "setups"
    setups.mkdir(parents=True, exist_ok=True)
    return setups


@pytest.fixture
def write_user_profile(user_dir: Path):
    """Return a helper that writes a user profile YAML and returns its path."""

    def _write(key: str, content: str) -> Path:
        path = user_dir / f"{key}.yaml"
        path.write_text(content, encoding="utf-8")
        return path

    return _write
