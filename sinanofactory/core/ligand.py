"""Ligand — a single chemical entity that can be grafted onto a surface."""

from __future__ import annotations

import hashlib

from pydantic import BaseModel, ConfigDict, Field, field_validator

from sinanofactory.core.enums import Role


class Ligand(BaseModel):
    """A single ligand species (independent of where/how it is grafted).

    Identity is determined by SMILES → InChIKey. The InChIKey is computed
    automatically by RDKit when available, with a deterministic fallback when
    RDKit is not installed (so the core schema can be exercised in CI without
    GPU/chem extras).

    GraftedLigand (in surface.py) wraps this with placement information.
    """

    smiles: str = Field(min_length=1, description="SMILES string for the ligand structure.")
    inchikey: str | None = Field(
        default=None,
        description="27-char hashed identifier; auto-computed from SMILES if omitted.",
    )
    role: Role = Field(description="Functional role on the surface.")
    name: str | None = Field(default=None, description="Human-readable name (e.g. 'GLYMO').")
    molecular_weight: float | None = Field(
        default=None,
        ge=0,
        description="Daltons; optional, computed during build if RDKit available.",
    )

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    @field_validator("smiles", mode="after")
    @classmethod
    def _strip_smiles(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("SMILES must be non-empty after stripping whitespace.")
        return v.strip()

    @field_validator("inchikey", mode="after")
    @classmethod
    def _check_inchikey_shape(cls, v: str | None) -> str | None:
        if v is None:
            return None
        # InChIKey: 14 chars + '-' + 10 chars + '-' + 1 char = 27 total
        if len(v) != 27 or v[14] != "-" or v[25] != "-":
            raise ValueError(f"InChIKey must match 'XXXXXXXXXXXXXX-XXXXXXXXXX-X' shape, got {v!r}.")
        return v

    def with_inchikey(self) -> Ligand:
        """Return a new Ligand with InChIKey computed (RDKit) or hashed-fallback."""
        if self.inchikey is not None:
            return self
        return self.model_copy(update={"inchikey": _smiles_to_inchikey(self.smiles)})


def _smiles_to_inchikey(smiles: str) -> str:
    """Compute InChIKey from SMILES.

    Uses RDKit if available; otherwise falls back to a deterministic SHA-256-
    derived 27-char string of the same shape. The fallback is NOT a real
    InChIKey — it is structurally compatible (same length, same separators)
    so cache lookups remain consistent across environments, but two different
    SMILES that map to the same InChI under RDKit will map to different
    fallbacks here. Document this in any RDKit-free pipeline.
    """
    try:
        from rdkit import Chem
        from rdkit.Chem import inchi
    except ImportError:
        return _deterministic_fallback_inchikey(smiles)

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"RDKit could not parse SMILES: {smiles!r}.")
    key: str = inchi.MolToInchiKey(mol)  # type: ignore[no-untyped-call]
    if not key:
        raise ValueError(f"RDKit produced empty InChIKey for SMILES: {smiles!r}.")
    return key


def _deterministic_fallback_inchikey(smiles: str) -> str:
    """RDKit-free fallback: SHA-256 → base36 → reshape into InChIKey form."""
    digest = hashlib.sha256(smiles.encode("utf-8")).hexdigest().upper()
    # Use only A-Z and 0-9 (real InChIKey alphabet)
    pool = "".join(c for c in digest if c.isalnum())
    if len(pool) < 25:
        # Extremely unlikely; pad deterministically.
        pool = (pool + "A" * 25)[:25]
    return f"{pool[:14]}-{pool[14:24]}-{pool[24]}"


__all__ = ["Ligand"]
