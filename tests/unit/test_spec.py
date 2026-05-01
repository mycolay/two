"""NanoparticleSpec construction + JSON round-trip + identity invariants."""

from __future__ import annotations

import json

import pytest

from sinanofactory.core import NanoparticleSpec

pytestmark = pytest.mark.unit


def test_hbm4_spec_constructs(hbm4_spec: NanoparticleSpec) -> None:
    assert hbm4_spec.core.diameter_nm == 20.0
    assert len(hbm4_spec.surface.ligands) == 2
    assert hbm4_spec.environment.solvent.name == "bisphenol-f"
    assert hbm4_spec.environment.temperature_K == 353.0


def test_short_id_is_12_hex_chars(hbm4_spec: NanoparticleSpec) -> None:
    sid = hbm4_spec.short_id
    assert len(sid) == 12
    int(sid, 16)  # raises if not hex


def test_json_round_trip_preserves_hash(hbm4_spec: NanoparticleSpec) -> None:
    blob = hbm4_spec.model_dump_json()
    reloaded = NanoparticleSpec.model_validate_json(blob)
    assert reloaded.canonical_hash() == hbm4_spec.canonical_hash()


def test_canonical_json_is_actually_json(hbm4_spec: NanoparticleSpec) -> None:
    """canonical_json output must round-trip through stdlib json."""
    parsed = json.loads(hbm4_spec.canonical_json())
    assert "core" in parsed
    assert "surface" in parsed
    assert "environment" in parsed
    # Metadata fields are stripped from canonical repr (they're ts-derived).
    # 'created_at' becomes None and falls out of the canonical dict.


def test_spec_is_frozen(hbm4_spec: NanoparticleSpec) -> None:
    from pydantic import ValidationError

    with pytest.raises((ValidationError, AttributeError)):
        hbm4_spec.name = "mutated"  # type: ignore[misc]


def test_two_specs_with_same_chemistry_share_hash(hbm4_spec: NanoparticleSpec) -> None:
    """Building twice with different metadata must yield same hash."""
    twin = hbm4_spec.model_copy(
        update={"name": "different label", "notes": "different note", "tags": ["a"]}
    )
    assert twin.canonical_hash() == hbm4_spec.canonical_hash()


def test_changing_temperature_changes_hash(hbm4_spec: NanoparticleSpec) -> None:
    hotter = hbm4_spec.model_copy(
        update={"environment": hbm4_spec.environment.model_copy(update={"temperature_K": 400.0})}
    )
    assert hotter.canonical_hash() != hbm4_spec.canonical_hash()
