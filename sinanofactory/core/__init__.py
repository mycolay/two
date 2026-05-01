"""Core domain — Pydantic models for the Two-Dimensional World.

Public API: import from `sinanofactory.core` rather than from submodules.
The Surface object is the centre of gravity here (ADR-001).
"""

from sinanofactory.core.core_spec import (
    CoreSpec,
    Fe3O4Core,
    SBA15Core,
    ShellSpec,
    StoberCore,
)
from sinanofactory.core.enums import (
    DistributionKind,
    Material,
    Morphology,
    ProvenanceLabel,
    Role,
)
from sinanofactory.core.environment import Environment, Solvent, Sorbate
from sinanofactory.core.hash import canonical_hash, canonical_json
from sinanofactory.core.ligand import Ligand
from sinanofactory.core.provenance import (
    ProvenanceEntry,
    ProvenanceMixin,
    assumed,
    from_literature,
    measured,
    model_based,
)
from sinanofactory.core.spec import NanoparticleSpec
from sinanofactory.core.surface import (
    Distribution,
    GraftedLigand,
    Surface,
    hmds_glymo_surface,
)

__all__ = [
    # Specs (top-down)
    "NanoparticleSpec",
    "CoreSpec",
    "StoberCore",
    "SBA15Core",
    "Fe3O4Core",
    "ShellSpec",
    # Surface (the two-dimensional world)
    "Surface",
    "GraftedLigand",
    "Distribution",
    "hmds_glymo_surface",
    # Ligand + chemistry
    "Ligand",
    # Environment
    "Environment",
    "Solvent",
    "Sorbate",
    # Enums
    "Material",
    "Morphology",
    "Role",
    "DistributionKind",
    "ProvenanceLabel",
    # Provenance
    "ProvenanceEntry",
    "ProvenanceMixin",
    "measured",
    "model_based",
    "from_literature",
    "assumed",
    # Hashing
    "canonical_hash",
    "canonical_json",
]
