"""Domain enums — closed sets used across the schema.

Adding a new value to any enum here is an architectural change: the relevant
builders/filters in `sinanofactory.{core,screening,translation}` must learn to
handle it. Coordinate via ADR.
"""

from enum import StrEnum


class Material(StrEnum):
    """Bulk material of the nanoparticle core."""

    SIO2_AMORPHOUS = "sio2_amorphous"
    SIO2_CRYSTALLINE = "sio2_crystalline"
    FE3O4 = "fe3o4"
    AU = "au"
    TIO2 = "tio2"


class Morphology(StrEnum):
    """Geometric class of the core."""

    SPHERE = "sphere"
    ROD = "rod"
    PLATELET = "platelet"
    MESOPOROUS = "mesoporous"
    CORE_SHELL = "core_shell"
    JANUS = "janus"


class Role(StrEnum):
    """Functional role of a grafted ligand on the surface."""

    STERIC_SHIELD = "steric_shield"
    REACTIVE_ANCHOR = "reactive_anchor"
    CHELATOR = "chelator"
    HYDROPHOBIC_TAIL = "hydrophobic_tail"
    HYDROPHILIC_HEAD = "hydrophilic_head"
    STIMULUS_RESPONSIVE = "stimulus_responsive"


class DistributionKind(StrEnum):
    """How ligands are spatially distributed on the surface."""

    RANDOM = "random"
    JANUS = "janus"
    FIBONACCI = "fibonacci"
    PATCHY = "patchy"
    GRADIENT = "gradient"


class ProvenanceLabel(StrEnum):
    """Origin of a numerical value.

    Enforced on every float/array field via ProvenanceMixin (ADR-007).
    The HBM4 PoC suffered from model-based curves presented as measured;
    this enum makes that misrepresentation structurally impossible.
    """

    MEASURED = "measured"
    """Direct output of MD/DFT/AIMD trajectory analysis."""

    MODEL_BASED = "model_based"
    """Result of constitutive law / fit / mapping (e.g., Cross-Ostwald rheogram)."""

    LITERATURE = "literature"
    """Taken from a published source with citation in metadata."""

    ASSUMED = "assumed"
    """Educated guess / default value — flag for review."""
