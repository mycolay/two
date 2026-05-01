"""Property-based tests for canonical hashing.

The hash is the *identity* function for NanoparticleSpec — every cache entry,
every replay, every dedup depends on it. Bugs here corrupt everything
downstream silently. We therefore exercise it with Hypothesis.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from sinanofactory.core import NanoparticleSpec, canonical_hash, canonical_json

pytestmark = pytest.mark.unit


# ============================================================================
# Pure-function tests on canonical_hash / canonical_json
# ============================================================================


def test_dict_key_order_does_not_affect_hash() -> None:
    a = {"x": 1, "y": 2, "z": 3}
    b = {"z": 3, "y": 2, "x": 1}
    assert canonical_hash(a) == canonical_hash(b)


def test_list_order_does_affect_hash() -> None:
    """Lists are ordered — [a, b] != [b, a]. This is intentional."""
    a = [1, 2, 3]
    b = [3, 2, 1]
    assert canonical_hash(a) != canonical_hash(b)


def test_float_precision_normalised() -> None:
    """0.1 + 0.2 should hash same as 0.3 (within 10-decimal tolerance)."""
    assert canonical_hash(0.1 + 0.2) == canonical_hash(0.3)


def test_datetime_is_stripped_from_identity() -> None:
    """Datetimes are metadata, not identity. Same dict + different dt → same hash."""
    base = {"value": 42}
    a = {**base, "ts": datetime.now(UTC)}
    b = {**base, "ts": datetime.now(UTC) + timedelta(days=365)}
    assert canonical_hash(a) == canonical_hash(b)


def test_canonical_json_is_deterministic() -> None:
    a = {"a": 1, "b": [1, 2, {"x": 0.1, "y": 0.2}]}
    json_repr = canonical_json(a)
    parsed = json.loads(json_repr)
    assert parsed["a"] == 1
    # Re-canonicalising the parsed result must produce the same string.
    assert canonical_json(parsed) == json_repr


# ============================================================================
# Property-based tests on canonical_hash
# ============================================================================


@given(
    st.dictionaries(
        keys=st.text(min_size=1, max_size=20).filter(lambda s: not s.startswith("_")),
        values=st.one_of(
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False, width=32),
            st.booleans(),
            st.text(max_size=50),
        ),
        max_size=10,
    )
)
@settings(max_examples=200, deadline=2000)
def test_hash_is_deterministic(d: dict[str, object]) -> None:
    """canonical_hash(x) == canonical_hash(x) for any x."""
    assert canonical_hash(d) == canonical_hash(d)


@given(
    st.dictionaries(
        keys=st.text(min_size=1, max_size=10).filter(lambda s: not s.startswith("_")),
        values=st.integers(),
        min_size=2,
        max_size=10,
    )
)
@settings(max_examples=100, deadline=2000)
def test_hash_invariant_under_key_permutation(d: dict[str, int]) -> None:
    """Reshuffling the key insertion order must not change the hash."""
    reordered = {k: d[k] for k in sorted(d, reverse=True)}
    assert canonical_hash(d) == canonical_hash(reordered)


# ============================================================================
# Integration with NanoparticleSpec
# ============================================================================


def test_spec_hash_is_stable_across_reload(hbm4_spec: NanoparticleSpec) -> None:
    """Round-trip via JSON must preserve the canonical_hash."""
    blob = hbm4_spec.model_dump_json()
    reloaded = NanoparticleSpec.model_validate_json(blob)
    assert reloaded.canonical_hash() == hbm4_spec.canonical_hash()


def test_spec_hash_changes_with_meaningful_field(hbm4_spec: NanoparticleSpec) -> None:
    """Changing a chemically meaningful field MUST change the hash."""
    bigger = hbm4_spec.model_copy(
        update={"core": hbm4_spec.core.model_copy(update={"diameter_nm": 200.0})}
    )
    assert bigger.canonical_hash() != hbm4_spec.canonical_hash()


def test_spec_hash_unchanged_by_metadata_only_change(hbm4_spec: NanoparticleSpec) -> None:
    """Metadata fields (name, created_by, notes, tags) MUST NOT affect hash."""
    relabelled = hbm4_spec.model_copy(
        update={"name": "totally different label", "notes": "scribbles", "tags": ["foo", "bar"]}
    )
    assert relabelled.canonical_hash() == hbm4_spec.canonical_hash()


def test_short_id_is_first_12_chars(hbm4_spec: NanoparticleSpec) -> None:
    assert hbm4_spec.short_id == hbm4_spec.canonical_hash()[:12]
    assert len(hbm4_spec.short_id) == 12
