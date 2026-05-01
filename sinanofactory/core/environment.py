"""Environment — the chemistry around the nanoparticle (solvent, sorbates, T, pH)."""

from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field

from sinanofactory.core.provenance import ProvenanceMixin


class Sorbate(BaseModel):
    """A species present in the surrounding solution that may interact with the surface.

    Examples: Cu²⁺ in heavy-metal screening (UC-3), methylene blue in dye
    capture, Dy³⁺ in REE recovery (UC-2), CO₂ in carbon capture (UC-5).
    """

    smiles: str = Field(
        min_length=1,
        description="SMILES; for ions use bracketed notation, e.g. '[Cu+2]'.",
    )
    inchikey: str | None = None
    name: str | None = None
    charge: int = Field(default=0, description="Net formal charge.")
    concentration_M: float = Field(
        default=0.0,
        ge=0.0,
        description="Molar concentration in the bulk solvent (mol/L).",
    )

    model_config = ConfigDict(frozen=True, extra="forbid")


class Solvent(BaseModel):
    """Bulk solvent of the simulation box."""

    name: str = Field(min_length=1, description="e.g., 'water', 'bisphenol-f', 'toluene'.")
    smiles: str = Field(min_length=1)
    density_g_cm3: float | None = Field(default=None, ge=0)

    model_config = ConfigDict(frozen=True, extra="forbid")


class Environment(ProvenanceMixin):
    """Conditions surrounding the nanoparticle.

    All numerical fields (T, P, pH, ionic strength) carry provenance; default
    factories use ProvenanceLabel.ASSUMED so users are nudged to refine.
    """

    solvent: Solvent
    sorbates: list[Sorbate] = Field(default_factory=list)
    temperature_K: float = Field(gt=0)
    pressure_bar: float = Field(default=1.0, gt=0)
    pH: float | None = Field(default=None, ge=-2, le=16)
    ionic_strength_M: float | None = Field(default=None, ge=0)

    provenance_required: ClassVar[frozenset[str]] = frozenset({"temperature_K", "pressure_bar"})

    model_config = ConfigDict(frozen=True, extra="forbid")


__all__ = ["Environment", "Solvent", "Sorbate"]
