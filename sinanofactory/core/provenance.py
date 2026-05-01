"""Provenance tracking — every numerical value declares its origin.

See ADR-007 in docs/ARCHITECTURE.md for the rationale (HBM4 PoC lesson).
"""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sinanofactory.core.enums import ProvenanceLabel


class ProvenanceEntry(BaseModel):
    """One provenance record: who said this value, when, and how confident."""

    label: ProvenanceLabel
    source: str | None = Field(
        default=None,
        description="DOI, internal run-id, lab notebook, or 'default' for assumed values.",
    )
    notes: str | None = None

    model_config = ConfigDict(frozen=True, extra="forbid")


class ProvenanceMixin(BaseModel):
    """Mixin requiring `provenance` dict to cover declared numeric fields.

    Subclasses MUST set `provenance_required: ClassVar[frozenset[str]]` to the
    field names that need provenance. (We use `frozenset` to make it hashable
    and to avoid Pydantic v2's private-attribute treatment of underscore-
    prefixed names — `ClassVar` alone is not enough when the name starts with
    an underscore.) The validator runs after all other field validation and
    raises if any required field is missing a record.

    Example:
        class MyModel(ProvenanceMixin):
            provenance_required: ClassVar[frozenset[str]] = frozenset({"density", "T"})
            density: float
            T: float
    """

    provenance: dict[str, ProvenanceEntry] = Field(
        default_factory=dict,
        description="Per-field origin records; key = field name, value = ProvenanceEntry.",
    )

    # Subclasses override. Empty frozenset = no required fields.
    provenance_required: ClassVar[frozenset[str]] = frozenset()

    @model_validator(mode="after")
    def _check_provenance_coverage(self) -> ProvenanceMixin:
        required = self.__class__.provenance_required
        if not required:
            return self
        missing = required - set(self.provenance)
        if missing:
            raise ValueError(
                f"{type(self).__name__}: missing provenance for fields: "
                f"{sorted(missing)}. Every numeric field must declare origin "
                "(measured / model_based / literature / assumed)."
            )
        return self

    def worst_provenance(self) -> ProvenanceLabel:
        """Return the 'least trustworthy' label across all entries.

        Order (best → worst): measured, literature, model_based, assumed.
        Used by the dashboard / PDF renderer to colour-flag results.
        """
        order = [
            ProvenanceLabel.MEASURED,
            ProvenanceLabel.LITERATURE,
            ProvenanceLabel.MODEL_BASED,
            ProvenanceLabel.ASSUMED,
        ]
        if not self.provenance:
            return ProvenanceLabel.ASSUMED
        labels = {entry.label for entry in self.provenance.values()}
        for label in reversed(order):
            if label in labels:
                return label
        return ProvenanceLabel.ASSUMED


def assumed(source: str = "default") -> ProvenanceEntry:
    """Convenience constructor for assumed values."""
    return ProvenanceEntry(label=ProvenanceLabel.ASSUMED, source=source)


def measured(run_id: str, notes: str | None = None) -> ProvenanceEntry:
    """Convenience constructor for measured values from a specific run."""
    return ProvenanceEntry(label=ProvenanceLabel.MEASURED, source=run_id, notes=notes)


def from_literature(citation: str, notes: str | None = None) -> ProvenanceEntry:
    """Convenience constructor for literature values (DOI or full citation)."""
    return ProvenanceEntry(label=ProvenanceLabel.LITERATURE, source=citation, notes=notes)


def model_based(method: str, notes: str | None = None) -> ProvenanceEntry:
    """Convenience constructor for values derived from a constitutive model."""
    return ProvenanceEntry(label=ProvenanceLabel.MODEL_BASED, source=method, notes=notes)


__all__ = [
    "ProvenanceEntry",
    "ProvenanceMixin",
    "assumed",
    "from_literature",
    "measured",
    "model_based",
]


# Suppress unused import warning - re-exported for convenience.
_ = Any
