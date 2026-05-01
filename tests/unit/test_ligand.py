"""Ligand identity and InChIKey computation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from sinanofactory.core import Ligand, Role
from sinanofactory.core.ligand import _deterministic_fallback_inchikey

pytestmark = pytest.mark.unit


def test_smiles_required() -> None:
    with pytest.raises(ValidationError):
        Ligand(smiles="", role=Role.STERIC_SHIELD)


def test_smiles_whitespace_stripped() -> None:
    lig = Ligand(smiles="  C[Si](C)(C)O  ", role=Role.STERIC_SHIELD)
    assert lig.smiles == "C[Si](C)(C)O"


def test_inchikey_shape_validated() -> None:
    """An explicit InChIKey of wrong shape must be rejected."""
    with pytest.raises(ValidationError, match="InChIKey"):
        Ligand(smiles="C", role=Role.STERIC_SHIELD, inchikey="too-short")


def test_with_inchikey_is_idempotent() -> None:
    lig = Ligand(smiles="C[Si](C)(C)O", role=Role.STERIC_SHIELD).with_inchikey()
    assert lig.inchikey is not None
    assert len(lig.inchikey) == 27
    again = lig.with_inchikey()
    assert again.inchikey == lig.inchikey


def test_with_inchikey_deterministic_for_same_smiles() -> None:
    a = Ligand(smiles="O[Si](O)(O)CCCOCC1CO1", role=Role.REACTIVE_ANCHOR).with_inchikey()
    b = Ligand(smiles="O[Si](O)(O)CCCOCC1CO1", role=Role.REACTIVE_ANCHOR).with_inchikey()
    assert a.inchikey == b.inchikey


def test_fallback_inchikey_shape() -> None:
    """Fallback (RDKit-free) must produce a structurally valid 27-char key."""
    key = _deterministic_fallback_inchikey("C[Si](C)(C)O")
    assert len(key) == 27
    assert key[14] == "-"
    assert key[25] == "-"


def test_ligand_is_frozen_immutable() -> None:
    lig = Ligand(smiles="C", role=Role.STERIC_SHIELD)
    with pytest.raises(ValidationError, match="frozen"):
        lig.smiles = "N"  # type: ignore[misc]
