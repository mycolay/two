"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from sinanofactory.core import (
    Distribution,
    DistributionKind,
    Environment,
    Ligand,
    NanoparticleSpec,
    ProvenanceEntry,
    ProvenanceLabel,
    Role,
    Solvent,
    StoberCore,
    Surface,
    hmds_glymo_surface,
)


@pytest.fixture
def hmds_ligand() -> Ligand:
    return Ligand(
        smiles="C[Si](C)(C)O",
        role=Role.STERIC_SHIELD,
        name="TMS-OH",
    ).with_inchikey()


@pytest.fixture
def glymo_ligand() -> Ligand:
    return Ligand(
        smiles="O[Si](O)(O)CCCOCC1CO1",
        role=Role.REACTIVE_ANCHOR,
        name="GLYMO",
    ).with_inchikey()


@pytest.fixture
def hbm4_surface() -> Surface:
    return hmds_glymo_surface()


@pytest.fixture
def stober_core() -> StoberCore:
    return StoberCore(
        diameter_nm=20.0,
        provenance={
            "diameter_nm": ProvenanceEntry(label=ProvenanceLabel.LITERATURE, source="HBM4 PoC"),
            "pdi": ProvenanceEntry(label=ProvenanceLabel.ASSUMED),
            "silanol_density_per_nm2": ProvenanceEntry(
                label=ProvenanceLabel.LITERATURE, source="Iler 1979"
            ),
        },
    )


@pytest.fixture
def bisphenol_f_environment() -> Environment:
    return Environment(
        solvent=Solvent(name="bisphenol-f", smiles="OC1=CC=C(CC2=CC=C(O)C=C2)C=C1"),
        sorbates=[],
        temperature_K=353.0,
        pressure_bar=1.0,
        provenance={
            "temperature_K": ProvenanceEntry(
                label=ProvenanceLabel.LITERATURE, source="HBM4 dispensing T"
            ),
            "pressure_bar": ProvenanceEntry(label=ProvenanceLabel.ASSUMED),
        },
    )


@pytest.fixture
def hbm4_spec(
    stober_core: StoberCore,
    hbm4_surface: Surface,
    bisphenol_f_environment: Environment,
) -> NanoparticleSpec:
    """Reference HBM4-PoC spec, used to anchor the regression contract."""
    return NanoparticleSpec(
        core=stober_core,
        shell=None,
        surface=hbm4_surface,
        environment=bisphenol_f_environment,
        name="HBM4 underfill reference",
    )


@pytest.fixture
def fibonacci_distribution() -> Distribution:
    return Distribution(kind=DistributionKind.FIBONACCI)
