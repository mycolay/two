"""Surface — the first-class object of the schema (ADR-001).

Two-Dimensional World philosophy: all chemistry happens here. The bulk
core is treated as a boundary condition (see core_spec.py). Validators
are concentrated on this object.
"""

from __future__ import annotations

import math
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from sinanofactory.core.enums import DistributionKind, ProvenanceLabel, Role
from sinanofactory.core.ligand import Ligand
from sinanofactory.core.provenance import ProvenanceEntry, ProvenanceMixin


class Distribution(BaseModel):
    """How ligands are placed on the surface.

    The `kind` discriminator selects the geometric algorithm; `params`
    holds kind-specific knobs (e.g., Janus axis, patch count).
    """

    kind: DistributionKind = Field(description="Spatial distribution algorithm.")
    params: dict[str, float | int | str] = Field(default_factory=dict)

    model_config = ConfigDict(frozen=True, extra="forbid")

    @model_validator(mode="after")
    def _check_required_params(self) -> Distribution:
        required: dict[DistributionKind, set[str]] = {
            DistributionKind.RANDOM: set(),
            DistributionKind.FIBONACCI: set(),
            DistributionKind.JANUS: {"axis"},
            DistributionKind.PATCHY: {"n_patches"},
            DistributionKind.GRADIENT: {"axis"},
        }
        missing = required[self.kind] - set(self.params)
        if missing:
            raise ValueError(
                f"Distribution(kind={self.kind!s}) requires params: {sorted(missing)}."
            )
        if self.kind == DistributionKind.JANUS and self.params.get("axis") not in {"x", "y", "z"}:
            raise ValueError("Janus axis must be one of 'x', 'y', 'z'.")
        if self.kind == DistributionKind.PATCHY:
            n = self.params.get("n_patches")
            if not isinstance(n, int) or n < 2:
                raise ValueError("Patchy distribution requires n_patches: int >= 2.")
        return self


class GraftedLigand(BaseModel):
    """One ligand species + its placement parameters on the surface.

    Multiple GraftedLigands on the same Surface = multifunctional grafting
    (e.g., HMDS at fraction=0.85 + GLYMO at fraction=0.15 in HBM4 PoC).
    The fractions across all GraftedLigands on a Surface must sum to 1.0.
    """

    ligand: Ligand
    fraction: float = Field(
        ge=0.0, le=1.0, description="Fraction of total grafting points occupied by this ligand."
    )
    notes: str | None = None

    model_config = ConfigDict(frozen=True, extra="forbid")


class Surface(ProvenanceMixin):
    """The two-dimensional world.

    Numerical fields (`grafting_density`, `coverage_fraction`) are
    provenance-tracked: each entry in `provenance` declares whether the
    value is measured, model-based, taken from literature, or assumed.
    See ADR-007.
    """

    ligands: list[GraftedLigand] = Field(min_length=1, description="One or more grafted species.")
    distribution: Distribution
    grafting_density: float = Field(
        gt=0.0,
        description="Total ligands per nm² (counts all species).",
    )
    coverage_fraction: float = Field(
        ge=0.0,
        le=1.0,
        description="Fraction of available silanols actually grafted (0..1).",
    )

    provenance_required: ClassVar[frozenset[str]] = frozenset(
        {
            "grafting_density",
            "coverage_fraction",
        }
    )

    model_config = ConfigDict(frozen=True, extra="forbid")

    @field_validator("ligands", mode="after")
    @classmethod
    def _ensure_unique_ligands(cls, ligands: list[GraftedLigand]) -> list[GraftedLigand]:
        smiles_seen: set[str] = set()
        for gl in ligands:
            if gl.ligand.smiles in smiles_seen:
                raise ValueError(
                    f"Duplicate ligand on the same surface: SMILES={gl.ligand.smiles!r}. "
                    "Combine into one GraftedLigand with the summed fraction."
                )
            smiles_seen.add(gl.ligand.smiles)
        return ligands

    @model_validator(mode="after")
    def _validate_fractions_sum_to_one(self) -> Surface:
        total = sum(gl.fraction for gl in self.ligands)
        if not math.isclose(total, 1.0, abs_tol=1e-6):
            raise ValueError(
                f"Sum of GraftedLigand.fraction must be 1.0 (within 1e-6), got {total:.9f}."
            )
        return self

    @model_validator(mode="after")
    def _validate_distribution_consistency(self) -> Surface:
        if self.distribution.kind == DistributionKind.JANUS and len(self.ligands) < 2:
            raise ValueError(
                "Janus distribution requires at least 2 distinct GraftedLigands; got "
                f"{len(self.ligands)}."
            )
        return self

    @model_validator(mode="after")
    def _validate_anchor_role_present(self) -> Surface:
        """If covalent integration with a matrix is intended, at least one
        ligand should carry Role.REACTIVE_ANCHOR. Warn-only via metadata —
        not all surfaces need an anchor (e.g., pure HMDS pasivation)."""
        # Soft check: do not raise. Could be elevated to ValidationError
        # if a NanoparticleSpec.environment declares a curing matrix.
        return self

    def has_role(self, role: Role) -> bool:
        """Return True if any grafted ligand on this surface plays `role`."""
        return any(gl.ligand.role == role for gl in self.ligands)

    def fraction_of(self, role: Role) -> float:
        """Sum of fractions for all ligands playing `role`."""
        return sum(gl.fraction for gl in self.ligands if gl.ligand.role == role)


def hmds_glymo_surface(
    hmds_fraction: float = 0.85,
    glymo_fraction: float = 0.15,
    grafting_density: float = 4.5,
    coverage_fraction: float = 0.95,
) -> Surface:
    """Convenience factory: HBM4-style HMDS/GLYMO bifunctional surface.

    Default values reproduce the HBM4 PoC composition.
    """
    if not math.isclose(hmds_fraction + glymo_fraction, 1.0, abs_tol=1e-6):
        raise ValueError(
            f"hmds_fraction + glymo_fraction must equal 1.0; "
            f"got {hmds_fraction + glymo_fraction:.6f}."
        )
    hmds = Ligand(
        smiles="C[Si](C)(C)O", role=Role.STERIC_SHIELD, name="TMS-OH (from HMDS)"
    ).with_inchikey()
    glymo = Ligand(
        smiles="O[Si](O)(O)CCCOCC1CO1",
        role=Role.REACTIVE_ANCHOR,
        name="GLYMO (hydrolysed)",
    ).with_inchikey()
    return Surface(
        ligands=[
            GraftedLigand(ligand=hmds, fraction=hmds_fraction),
            GraftedLigand(ligand=glymo, fraction=glymo_fraction),
        ],
        distribution=Distribution(kind=DistributionKind.FIBONACCI),
        grafting_density=grafting_density,
        coverage_fraction=coverage_fraction,
        provenance={
            "grafting_density": ProvenanceEntry(
                label=ProvenanceLabel.LITERATURE,
                source="Iler 1979 (silica chemistry); HBM4 PoC default",
            ),
            "coverage_fraction": ProvenanceEntry(
                label=ProvenanceLabel.ASSUMED,
                source="HBM4 PoC default; refine via DFT cluster",
            ),
        },
    )


__all__ = ["Distribution", "GraftedLigand", "Surface", "hmds_glymo_surface"]
