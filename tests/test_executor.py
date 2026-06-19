"""Tests for the step executor: handlers, dispatch, and `when`."""

import os
from pathlib import Path

import pytest

from cliex.setup.executor import execute_setup


def _run(steps, project: Path):
    execute_setup({"_base_path": project, "steps": steps}, project)


def test_mkdir_copy_move_remove(tmp_path: Path):
    steps = [
        {"type": "mkdir", "name": "md", "path": "src/sub"},
        {"type": "copy", "name": "cp", "src": "src", "dest": "src_copy"},
        {"type": "move", "name": "mv", "src": "src_copy", "dest": "moved"},
        {"type": "remove", "name": "rm", "path": "moved"},
    ]
    _run(steps, tmp_path)
    assert (tmp_path / "src" / "sub").is_dir()
    assert not (tmp_path / "src_copy").exists()
    assert not (tmp_path / "moved").exists()


def test_append_creates_and_appends(tmp_path: Path):
    steps = [
        {"type": "append", "name": "a", "file": "notes.txt", "content": "one\n"},
        {"type": "append", "name": "b", "file": "notes.txt", "content": "two\n"},
    ]
    _run(steps, tmp_path)
    assert (tmp_path / "notes.txt").read_text(encoding="utf-8") == "one\ntwo\n"


def test_remove_missing_ignored_by_default(tmp_path: Path):
    _run([{"type": "remove", "name": "rm", "path": "ghost"}], tmp_path)  # no raise


def test_remove_missing_strict_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        _run(
            [{"type": "remove", "name": "rm", "path": "ghost", "ignore_missing": False}],
            tmp_path,
        )


def test_unknown_step_type_raises(tmp_path: Path):
    with pytest.raises(ValueError, match="Unknown step type"):
        _run([{"type": "frobnicate", "name": "x"}], tmp_path)


def test_when_skips_non_matching_platform(tmp_path: Path):
    other = "macos" if os.name == "nt" else "windows"
    _run([{"type": "mkdir", "name": "md", "path": "should_skip", "when": other}], tmp_path)
    assert not (tmp_path / "should_skip").exists()


def test_when_runs_matching_platform(tmp_path: Path):
    current = "windows" if os.name == "nt" else "unix"
    _run([{"type": "mkdir", "name": "md", "path": "made", "when": current}], tmp_path)
    assert (tmp_path / "made").is_dir()


def test_copy_directory_tree(tmp_path: Path):
    src = tmp_path / "tree"
    (src / "deep").mkdir(parents=True)
    (src / "deep" / "f.txt").write_text("x", encoding="utf-8")
    _run([{"type": "copy", "name": "cp", "src": "tree", "dest": "tree_copy"}], tmp_path)
    assert (tmp_path / "tree_copy" / "deep" / "f.txt").read_text(encoding="utf-8") == "x"


def test_missing_steps_raises(tmp_path: Path):
    with pytest.raises(ValueError, match="list of steps"):
        execute_setup({"steps": "nope"}, tmp_path)
