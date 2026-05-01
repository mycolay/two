"""Surface validators — invariants that prevent chemically nonsense specs."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from sinanofactory.core import (
    Distribution,
    DistributionKind,
    GraftedLigand,
    Ligand,
    ProvenanceEntry,
    ProvenanceLabel,
    Role,
    Surface,
    hmds_glymo_surface,
)

pytestmark = pytest.mark.unit


def _entry(label: ProvenanceLabel = ProvenanceLabel.ASSUMED) -> ProvenanceEntry:
    return ProvenanceEntry(label=label, source="test")


def test_fractions_must_sum_to_one(hmds_ligand: Ligand, glymo_ligand: Ligand) -> None:
    with pytest.raises(ValidationError, match="must be 1.0"):
        Surface(
            ligands=[
                GraftedLigand(ligand=hmds_ligand, fraction=0.5),
                GraftedLigand(ligand=glymo_ligand, fraction=0.4),  # sums to 0.9
            ],
            distribution=Distribution(kind=DistributionKind.FIBONACCI),
            grafting_density=4.0,
            coverage_fraction=0.9,
            provenance={"grafting_density": _entry(), "coverage_fraction": _entry()},
        )


def test_duplicate_smiles_rejected(hmds_ligand: Ligand) -> None:
    with pytest.raises(ValidationError, match="Duplicate ligand"):
        Surface(
            ligands=[
                GraftedLigand(ligand=hmds_ligand, fraction=0.5),
                GraftedLigand(ligand=hmds_ligand, fraction=0.5),
            ],
            distribution=Distribution(kind=DistributionKind.FIBONACCI),
            grafting_density=4.0,
            coverage_fraction=0.9,
            provenance={"grafting_density": _entry(), "coverage_fraction": _entry()},
        )


def test_janus_requires_two_ligands(hmds_ligand: Ligand) -> None:
    with pytest.raises(ValidationError, match="at least 2"):
        Surface(
            ligands=[GraftedLigand(ligand=hmds_ligand, fraction=1.0)],
            distribution=Distribution(kind=DistributionKind.JANUS, params={"axis": "z"}),
            grafting_density=4.0,
            coverage_fraction=0.9,
            provenance={"grafting_density": _entry(), "coverage_fraction": _entry()},
        )


def test_janus_axis_must_be_xyz() -> None:
    with pytest.raises(ValidationError, match="Janus axis"):
        Distribution(kind=DistributionKind.JANUS, params={"axis": "diagonal"})


def test_patchy_requires_n_patches() -> None:
    with pytest.raises(ValidationError, match="n_patches"):
        Distribution(kind=DistributionKind.PATCHY)
    with pytest.raises(ValidationError, match="n_patches"):
        Distribution(kind=DistributionKind.PATCHY, params={"n_patches": 1})


def test_provenance_required_for_numeric_fields(hmds_ligand: Ligand, glymo_ligand: Ligand) -> None:
    """Surface must not accept missing provenance for grafting_density / coverage_fraction."""
    with pytest.raises(ValidationError, match="missing provenance"):
        Surface(
            ligands=[
                GraftedLigand(ligand=hmds_ligand, fraction=0.85),
                GraftedLigand(ligand=glymo_ligand, fraction=0.15),
            ],
            distribution=Distribution(kind=DistributionKind.FIBONACCI),
            grafting_density=4.0,
            coverage_fraction=0.9,
            # provenance left empty — validator should fire
        )


def test_hmds_glymo_factory_is_valid_by_default() -> None:
    s = hmds_glymo_surface()
    assert s.has_role(Role.STERIC_SHIELD)
    assert s.has_role(Role.REACTIVE_ANCHOR)
    assert s.fraction_of(Role.STERIC_SHIELD) == pytest.approx(0.85)
    assert s.fraction_of(Role.REACTIVE_ANCHOR) == pytest.approx(0.15)


def test_hmds_glymo_factory_validates_ratio() -> None:
    with pytest.raises(ValueError, match="must equal 1.0"):
        hmds_glymo_surface(hmds_fraction=0.7, glymo_fraction=0.2)


def test_worst_provenance_picks_least_trusted() -> None:
    s = Surface(
        ligands=[
            GraftedLigand(
                ligand=Ligand(smiles="C[Si](C)(C)O", role=Role.STERIC_SHIELD).with_inchikey(),
                fraction=1.0,
            )
        ],
        distribution=Distribution(kind=DistributionKind.FIBONACCI),
        grafting_density=4.0,
        coverage_fraction=0.9,
        provenance={
            "grafting_density": _entry(ProvenanceLabel.MEASURED),
            "coverage_fraction": _entry(ProvenanceLabel.ASSUMED),  # weakest
        },
    )
    assert s.worst_provenance() == ProvenanceLabel.ASSUMED


def test_surface_is_frozen_immutable(hbm4_surface: Surface) -> None:
    with pytest.raises(ValidationError, match="frozen"):
        hbm4_surface.grafting_density = 10.0  # type: ignore[misc]
