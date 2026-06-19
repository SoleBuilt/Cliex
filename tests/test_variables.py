"""Tests for variable resolution and {{ }} substitution."""

from pathlib import Path

import pytest

from cliex.setup.variables import render_steps, resolve_context


def test_builtins_always_present():
    ctx = resolve_context({"steps": []}, "my-app", Path("/tmp/my-app"), {}, assume_yes=True)
    assert ctx["project_name"] == "my-app"
    assert ctx["project_path"] == str(Path("/tmp/my-app"))


def test_cli_var_overrides_default():
    cfg = {"variables": [{"name": "title", "default": "Default"}], "steps": []}
    ctx = resolve_context(cfg, "a", Path("/a"), {"title": "FromCLI"}, assume_yes=True)
    assert ctx["title"] == "FromCLI"


def test_assume_yes_uses_default():
    cfg = {"variables": [{"name": "title", "default": "Default"}], "steps": []}
    ctx = resolve_context(cfg, "a", Path("/a"), {}, assume_yes=True)
    assert ctx["title"] == "Default"


def test_assume_yes_missing_value_raises():
    cfg = {"variables": [{"name": "needed"}], "steps": []}
    with pytest.raises(RuntimeError, match="needed"):
        resolve_context(cfg, "a", Path("/a"), {}, assume_yes=True)


def test_adhoc_cli_var_added():
    ctx = resolve_context({"steps": []}, "a", Path("/a"), {"extra": "v"}, assume_yes=True)
    assert ctx["extra"] == "v"


def test_render_substitutes_string_fields():
    ctx = {"project_name": "app", "title": "Hello"}
    steps = [
        {"type": "append", "file": "{{ project_name }}.md", "content": "# {{ title }}"},
        {"type": "run", "cmd": "echo {{ title }}"},
    ]
    out = render_steps(steps, ctx)
    assert out[0]["file"] == "app.md"
    assert out[0]["content"] == "# Hello"
    assert out[1]["cmd"] == "echo Hello"


def test_render_does_not_mutate_input():
    ctx = {"x": "Y"}
    steps = [{"type": "run", "cmd": "{{ x }}"}]
    render_steps(steps, ctx)
    assert steps[0]["cmd"] == "{{ x }}"  # original untouched


def test_render_unknown_variable_raises():
    with pytest.raises(RuntimeError, match="Unknown variable"):
        render_steps([{"type": "run", "cmd": "{{ missing }}"}], {"x": "1"})
