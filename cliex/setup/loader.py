from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Union, cast

import yaml  # type: ignore[import]


def load_setup_config(config_path: Union[Path, str]) -> Dict[str, Any]:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Setup file not found: {path}")
    if not path.is_file():
        raise ValueError(f"Setup path is not a file: {path}")

    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    if not isinstance(config, dict):
        raise ValueError("Setup config must be a mapping")

    if "steps" not in config:
        raise ValueError("Setup config must contain a top-level 'steps' list")
    if not isinstance(config["steps"], list):
        raise ValueError("Setup config 'steps' must be a list")

    config = cast(Dict[str, Any], config)
    config["_base_path"] = path.parent
    return config
