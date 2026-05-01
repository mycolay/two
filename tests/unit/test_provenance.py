"""ProvenanceMixin coverage rules."""

from __future__ import annotations

from typing import ClassVar

import pytest
from pydantic import ConfigDict, ValidationError

from sinanofactory.core import (
    ProvenanceEntry,
    ProvenanceLabel,
    ProvenanceMixin,
    assumed,
    from_literature,
    measured,
    model_based,
)

pytestmark = pytest.mark.unit


class _Sample(ProvenanceMixin):
    provenance_required: ClassVar[frozenset[str]] = frozenset({"alpha", "beta"})
    alpha: float
    beta: float
    note: str = ""

    model_config = ConfigDict(frozen=True, extra="forbid")


def test_missing_provenance_raises() -> None:
    with pytest.raises(ValidationError, match="missing provenance"):
        _Sample(alpha=1.0, beta=2.0)


def test_partial_provenance_lists_missing() -> None:
    with pytest.raises(ValidationError, match=r"\['beta'\]"):
        _Sample(
            alpha=1.0,
            beta=2.0,
            provenance={"alpha": ProvenanceEntry(label=ProvenanceLabel.MEASURED)},
        )


def test_complete_provenance_passes() -> None:
    obj = _Sample(
        alpha=1.0,
        beta=2.0,
        provenance={
            "alpha": measured(run_id="run-001"),
            "beta": from_literature(citation="DOI:1234"),
        },
    )
    assert obj.alpha == 1.0
    assert obj.worst_provenance() == ProvenanceLabel.LITERATURE


def test_worst_provenance_with_assumed() -> None:
    obj = _Sample(
        alpha=1.0,
        beta=2.0,
        provenance={
            "alpha": measured(run_id="run-001"),
            "beta": assumed(),
        },
    )
    assert obj.worst_provenance() == ProvenanceLabel.ASSUMED


def test_worst_provenance_with_model_based() -> None:
    obj = _Sample(
        alpha=1.0,
        beta=2.0,
        provenance={
            "alpha": measured(run_id="run-001"),
            "beta": model_based(method="Cross-Ostwald"),
        },
    )
    assert obj.worst_provenance() == ProvenanceLabel.MODEL_BASED


def test_empty_provenance_yields_assumed_default() -> None:
    """A class with empty `_provenance_required` and empty `provenance` returns ASSUMED."""

    class _Free(ProvenanceMixin):
        x: int = 0
        model_config = ConfigDict(frozen=True)

    assert _Free().worst_provenance() == ProvenanceLabel.ASSUMED
