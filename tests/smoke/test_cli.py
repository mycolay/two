"""Smoke tests for the CLI surface — must always pass."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sinanofactory.cli import app
from sinanofactory.core import NanoparticleSpec
from sinanofactory.version import __version__

pytestmark = pytest.mark.smoke

runner = CliRunner()


def test_help_exits_zero() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Si nano Factory" in result.stdout


def test_version_prints_package_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_init_creates_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    result = runner.invoke(app, ["init", "--workspace", str(workspace)])
    assert result.exit_code == 0
    assert (workspace / "data" / "raw").is_dir()
    assert (workspace / "data" / "trajectories").is_dir()
    assert (workspace / "models").is_dir()
    assert (workspace / "specs").is_dir()


def test_init_force_on_existing_workspace_idempotent(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    runner.invoke(app, ["init", "--workspace", str(workspace)])
    result = runner.invoke(app, ["init", "--workspace", str(workspace), "--force"])
    assert result.exit_code == 0


def test_spec_validate_round_trip(tmp_path: Path, hbm4_spec: NanoparticleSpec) -> None:
    spec_path = tmp_path / "hbm4.json"
    spec_path.write_text(hbm4_spec.model_dump_json(indent=2), encoding="utf-8")

    result = runner.invoke(app, ["spec", "validate", str(spec_path)])
    assert result.exit_code == 0
    assert "VALID" in result.stdout


def test_spec_hash_command_returns_short_id(tmp_path: Path, hbm4_spec: NanoparticleSpec) -> None:
    spec_path = tmp_path / "hbm4.json"
    spec_path.write_text(hbm4_spec.model_dump_json(indent=2), encoding="utf-8")

    result = runner.invoke(app, ["spec", "hash", str(spec_path)])
    assert result.exit_code == 0
    assert hbm4_spec.short_id in result.stdout


def test_spec_validate_rejects_bad_json(tmp_path: Path) -> None:
    bad = tmp_path / "broken.json"
    bad.write_text('{"not": "a spec"}', encoding="utf-8")

    result = runner.invoke(app, ["spec", "validate", str(bad)])
    assert result.exit_code == 2
    assert "INVALID" in result.stdout


def test_unimplemented_command_exits_with_usage_code() -> None:
    result = runner.invoke(app, ["screen"])
    assert result.exit_code == 64  # EX_USAGE
    assert "not yet implemented" in result.stdout.lower()


def test_spec_validate_round_trip_via_canonical_json(
    tmp_path: Path, hbm4_spec: NanoparticleSpec
) -> None:
    """Reload a spec written via model_dump_json — hash must be preserved."""
    spec_path = tmp_path / "hbm4.json"
    spec_path.write_text(hbm4_spec.model_dump_json(), encoding="utf-8")
    reloaded = NanoparticleSpec.model_validate(json.loads(spec_path.read_text("utf-8")))
    assert reloaded.canonical_hash() == hbm4_spec.canonical_hash()
