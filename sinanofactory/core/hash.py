"""Canonical hashing for NanoparticleSpec.

Two specs with the same `canonical_hash()` describe the same physical system,
regardless of construction order, JSON-key order, or floating-point repr.
Used as the primary key for caching, deduplication, and reproducibility.

See ADR-001 + tests/unit/test_hash.py (Hypothesis property: idempotence).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

# Float resolution for canonical representation.
# 10 decimals = sub-pico-{nm,K,...} precision — safely beyond physical noise.
_FLOAT_REPR_DIGITS = 10


def _canonicalise(value: Any) -> Any:
    """Recursively transform `value` into a JSON-stable, canonical representation.

    Rules:
    - dicts → sorted by key
    - lists/tuples preserved in order (order is meaningful for our schema)
    - floats → fixed-precision string repr (avoids 0.1 + 0.2 != 0.3)
    - enums → their .value
    - datetimes → stripped (they're metadata, not identity; see ADR-001)
    - nested BaseModel → its `.model_dump()`
    """
    # Avoid circular import — Pydantic v2 BaseModel only needed at runtime.
    from pydantic import BaseModel

    if isinstance(value, BaseModel):
        return _canonicalise(value.model_dump(mode="json"))
    if isinstance(value, datetime):
        return None  # excluded from identity hash
    if isinstance(value, dict):
        return {k: _canonicalise(value[k]) for k in sorted(value)}
    if isinstance(value, list | tuple):
        return [_canonicalise(item) for item in value]
    if isinstance(value, float):
        return f"{value:.{_FLOAT_REPR_DIGITS}f}"
    # str, int, bool, None — already canonical
    return value


def canonical_hash(value: Any) -> str:
    """Return SHA-256 hex digest of the canonical JSON repr of `value`.

    This is *the* identity function for spec-like objects. Two inputs that
    describe the same physical system MUST produce the same hash; two inputs
    differing in any chemically meaningful way MUST produce different hashes.
    """
    canonical = _canonicalise(value)
    blob = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def canonical_json(value: Any) -> str:
    """Return the canonical JSON string used as input to `canonical_hash`.

    Useful for debugging hash mismatches: diff the two canonical strings.
    """
    canonical = _canonicalise(value)
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


__all__ = ["canonical_hash", "canonical_json"]
