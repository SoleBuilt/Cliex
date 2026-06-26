"""Tests for the profile registry: scanning, resolution, default, validation."""

from pathlib import Path

import pytest

from cliex.setup import registry

BUILTINS = {"nextjs-setup", "tauri-setup"}

VALID_PROFILE = """\
name: My Profile
description: A test profile.
steps:
  - type: run
    name: hello
    cmd: echo hi
"""


# --- scanning / sources -----------------------------------------------------

def test_load_registry_lists_builtins(user_dir: Path):
    reg = registry.load_registry()
    assert BUILTINS.issubset(reg.keys())
    for key in BUILTINS:
        assert reg[key]["source"] == "built-in"
        assert reg[key]["valid"] is True


def test_builtin_default_is_nextjs(user_dir: Path):
    reg = registry.load_registry()
    assert reg["nextjs-setup"]["default"] is True
    assert registry.get_default_profile()["key"] == "nextjs-setup"


def test_user_custom_profile_appears(write_user_profile):
    write_user_profile("my-stack", VALID_PROFILE)
    reg = registry.load_registry()
    assert reg["my-stack"]["source"] == "user custom"
    assert reg["my-stack"]["name"] == "My Profile"


def test_user_override_marks_source(write_user_profile):
    write_user_profile("tauri-setup", VALID_PROFILE)
    reg = registry.load_registry()
    assert reg["tauri-setup"]["source"] == "user override"


# --- resolution -------------------------------------------------------------

def test_resolve_plain_uses_builtin(user_dir: Path):
    path = registry.resolve_setup_path("tauri-setup")
    assert path == registry.PACKAGE_SETUP_DIR / "tauri-setup.yaml"


def test_resolve_plain_prefers_user_override(write_user_profile):
    user_path = write_user_profile("tauri-setup", VALID_PROFILE)
    assert registry.resolve_setup_path("tauri-setup") == user_path


def test_resolve_b_prefix_forces_builtin(write_user_profile):
    write_user_profile("tauri-setup", VALID_PROFILE)
    assert registry.resolve_setup_path("b:tauri-setup") == registry.PACKAGE_SETUP_DIR / "tauri-setup.yaml"


def test_resolve_u_prefix_forces_user(write_user_profile):
    user_path = write_user_profile("tauri-setup", VALID_PROFILE)
    assert registry.resolve_setup_path("u:tauri-setup") == user_path


def test_resolve_u_prefix_missing_raises(user_dir: Path):
    with pytest.raises(RuntimeError, match="No user profile named"):
        registry.resolve_setup_path("u:tauri-setup")


def test_resolve_b_prefix_missing_raises(user_dir: Path):
    with pytest.raises(RuntimeError, match="No built-in profile named"):
        registry.resolve_setup_path("b:does-not-exist")


def test_resolve_explicit_file_path(write_user_profile, tmp_path: Path):
    f = tmp_path / "loose.yaml"
    f.write_text(VALID_PROFILE, encoding="utf-8")
    assert registry.resolve_setup_path(str(f)) == f


def test_resolve_unknown_raises(user_dir: Path):
    with pytest.raises(RuntimeError, match="not found"):
        registry.resolve_setup_path("nope-nope")


# --- default read/write/clear ----------------------------------------------

def test_default_write_read_clear(write_user_profile):
    write_user_profile("my-stack", VALID_PROFILE)
    assert registry.read_user_default() is None  # falls back to builtin only

    registry.write_user_default("my-stack")
    assert registry.read_user_default() == "my-stack"
    assert registry.get_default_profile()["key"] == "my-stack"
    assert registry.load_registry()["my-stack"]["default"] is True

    registry.clear_user_default()
    assert registry.read_user_default() is None
    assert registry.get_default_profile()["key"] == "nextjs-setup"


# --- fork / delete ----------------------------------------------------------

def test_fork_builtin_creates_override(user_dir: Path):
    dest = registry.fork_builtin_to_user("tauri-setup")
    assert dest == user_dir / "tauri-setup.yaml"
    assert dest.exists()
    assert registry.load_registry()["tauri-setup"]["source"] == "user override"


def test_fork_unknown_raises(user_dir: Path):
    with pytest.raises(FileNotFoundError):
        registry.fork_builtin_to_user("nope")


def test_delete_user_override(write_user_profile, user_dir: Path):
    write_user_profile("tauri-setup", VALID_PROFILE)
    assert registry.delete_user_override("tauri-setup") is True
    assert registry.delete_user_override("tauri-setup") is False
    # back to built-in
    assert registry.load_registry()["tauri-setup"]["source"] == "built-in"


# --- validation / embedded metadata ----------------------------------------

def test_validate_good_profile(write_user_profile):
    path = write_user_profile("good", VALID_PROFILE)
    assert registry.validate_profile(path) == []


def test_validate_missing_steps(write_user_profile):
    path = write_user_profile("bad", "name: X\ndescription: Y\n")
    problems = registry.validate_profile(path)
    assert any("steps" in p for p in problems)


def test_validate_unknown_step_type(write_user_profile):
    path = write_user_profile(
        "bad", "name: X\ndescription: Y\nsteps:\n  - type: bogus\n"
    )
    problems = registry.validate_profile(path)
    assert any("unknown type 'bogus'" in p for p in problems)


def test_validate_bad_when_is_warning(write_user_profile):
    content = "name: X\ndescription: Y\nsteps:\n  - type: run\n    cmd: x\n    when: solaris\n"
    path = write_user_profile("bad", content)
    problems = registry.validate_profile(path)
    assert any(p.startswith("Warning:") and "when" in p for p in problems)


def test_invalid_yaml_profile_marked_invalid(write_user_profile):
    path = write_user_profile("broken", "name: X\n  bad: : indent\n")
    reg = registry.load_registry()
    assert reg["broken"]["valid"] is False
    assert reg["broken"]["error"]
