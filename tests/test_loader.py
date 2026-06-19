"""Tests for the YAML setup config loader."""

from pathlib import Path

import pytest

from cliex.setup.loader import load_setup_config

VALID = "name: X\ndescription: Y\nsteps:\n  - type: run\n    cmd: echo hi\n"


def test_load_valid_injects_base_path(tmp_path: Path):
    f = tmp_path / "p.yaml"
    f.write_text(VALID, encoding="utf-8")
    config = load_setup_config(f)
    assert config["_base_path"] == tmp_path
    assert isinstance(config["steps"], list)


def test_load_missing_file_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_setup_config(tmp_path / "nope.yaml")


def test_load_non_mapping_raises(tmp_path: Path):
    f = tmp_path / "p.yaml"
    f.write_text("- just\n- a\n- list\n", encoding="utf-8")
    with pytest.raises(ValueError, match="mapping"):
        load_setup_config(f)


def test_load_missing_steps_raises(tmp_path: Path):
    f = tmp_path / "p.yaml"
    f.write_text("name: X\n", encoding="utf-8")
    with pytest.raises(ValueError, match="steps"):
        load_setup_config(f)


def test_load_steps_not_list_raises(tmp_path: Path):
    f = tmp_path / "p.yaml"
    f.write_text("steps: not-a-list\n", encoding="utf-8")
    with pytest.raises(ValueError, match="list"):
        load_setup_config(f)
