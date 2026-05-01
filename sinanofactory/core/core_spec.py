"""CoreSpec — the bulk core (boundary condition for the surface).

Per ADR-001, the core is a *peripheral* abstraction: it sets the geometry on
which a Surface lives. Specialised subclasses encode geometry-specific knobs
(Stöber sphere, SBA-15 mesopore, magnetite for core-shell).
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field

from sinanofactory.core.enums import Material, Morphology
from sinanofactory.core.provenance import ProvenanceMixin


class CoreSpec(ProvenanceMixin):
    """Base class for core specifications. Subclasses set Morphology specifics."""

    material: Material
    morphology: Morphology
    diameter_nm: float = Field(gt=0, description="Characteristic linear size (nm).")
    crystallinity: Literal["amorphous", "crystalline", "mixed"] = "amorphous"

    provenance_required: ClassVar[frozenset[str]] = frozenset({"diameter_nm"})

    model_config = ConfigDict(frozen=True, extra="forbid")


class StoberCore(CoreSpec):
    """Stöber-method amorphous silica sphere."""

    material: Material = Material.SIO2_AMORPHOUS
    morphology: Morphology = Morphology.SPHERE
    pdi: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Polydispersity index (target < 0.1 for monodisperse).",
    )
    silanol_density_per_nm2: float = Field(
        default=4.6,
        gt=0,
        description="Surface OH groups per nm² (Iler 1979 default).",
    )

    provenance_required: ClassVar[frozenset[str]] = frozenset(
        {
            "diameter_nm",
            "pdi",
            "silanol_density_per_nm2",
        }
    )


class SBA15Core(CoreSpec):
    """SBA-15 mesoporous silica."""

    material: Material = Material.SIO2_AMORPHOUS
    morphology: Morphology = Morphology.MESOPOROUS
    pore_diameter_nm: float = Field(gt=0)
    wall_thickness_nm: float = Field(gt=0)

    provenance_required: ClassVar[frozenset[str]] = frozenset(
        {
            "diameter_nm",
            "pore_diameter_nm",
            "wall_thickness_nm",
        }
    )


class Fe3O4Core(CoreSpec):
    """Magnetite core for core-shell magnetic nanoparticles."""

    material: Material = Material.FE3O4
    morphology: Morphology = Morphology.SPHERE
    magnetization_emu_g: float | None = Field(default=None, ge=0)

    provenance_required: ClassVar[frozenset[str]] = frozenset({"diameter_nm"})


class ShellSpec(BaseModel):
    """Optional shell around the core (e.g., SiO₂ on Fe₃O₄)."""

    material: Material
    thickness_nm: float = Field(gt=0)
    method: str | None = Field(
        default=None,
        description="Synthesis method tag, e.g., 'modified Stöber'.",
    )

    model_config = ConfigDict(frozen=True, extra="forbid")


__all__ = ["CoreSpec", "Fe3O4Core", "SBA15Core", "ShellSpec", "StoberCore"]
