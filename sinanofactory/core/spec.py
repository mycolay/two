"""NanoparticleSpec — the top-level identity of a system in the Factory.

This is the object that flows through every Tier (S-Tier 0..2 and D-Tier 0..4),
gets cached by InChIKey + spec_hash, and ultimately renders into a
SynthesisRecipe. Two specs with identical `canonical_hash()` are interchangeable.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field

from sinanofactory.core.core_spec import CoreSpec, ShellSpec
from sinanofactory.core.environment import Environment
from sinanofactory.core.hash import canonical_hash, canonical_json
from sinanofactory.core.surface import Surface


class NanoparticleSpec(BaseModel):
    """Complete description of a nanoparticle + its environment.

    Identity is determined by `canonical_hash()`: the SHA-256 of the
    canonical JSON representation, with metadata (`created_at`,
    `created_by`) stripped. This means two specs created by different
    users at different times but describing the same physical system
    will share a hash and a cache entry.
    """

    core: CoreSpec
    shell: ShellSpec | None = None
    surface: Surface
    environment: Environment

    # --- Metadata (NOT part of identity) ------------------------------
    name: str | None = Field(
        default=None,
        description="Optional human-readable label, e.g., 'HBM4 underfill candidate v3'.",
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_by: str | None = None
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)

    model_config = ConfigDict(frozen=True, extra="forbid")

    # Fields excluded from canonical_hash — these are metadata, not identity.
    # See ADR-001 + tests/unit/test_hash.py::test_spec_hash_unchanged_by_metadata_only_change
    _METADATA_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {
            "name",
            "created_at",
            "created_by",
            "notes",
            "tags",
        }
    )

    # --- Identity --------------------------------------------------------
    def canonical_hash(self) -> str:
        """Return SHA-256 hex digest of the canonical representation.

        Metadata fields (`name`, `created_at`, `created_by`, `notes`, `tags`)
        are excluded — see `_METADATA_FIELDS` and ADR-001.
        """
        return canonical_hash(self._identity_dict())

    def canonical_json(self) -> str:
        """Return the exact JSON used as input to `canonical_hash`.

        Useful for diffing two specs that hash differently to find the
        offending field.
        """
        return canonical_json(self._identity_dict())

    def _identity_dict(self) -> dict[str, Any]:
        """Dump the spec excluding metadata fields."""
        return self.model_dump(mode="json", exclude=set(self._METADATA_FIELDS))

    @property
    def short_id(self) -> str:
        """First 12 chars of canonical_hash — for filenames and logs."""
        return self.canonical_hash()[:12]


__all__ = ["NanoparticleSpec"]
