"""
Deterministic hashing helpers used throughout the backend.

The helper keeps the argument order stable by sorting the stringified payloads.
That property is handy both for tests and for comparing independent block data.
"""

from __future__ import annotations

import json
import hashlib
from typing import Any


def _stringify(data: Any) -> str:
    """Serialize arbitrary Python data into a deterministic string."""
    return json.dumps(
        data,
        sort_keys=True,
        default=str,
        separators=(",", ":"),
    )


def crypto_hash(*args: Any) -> str:
    """
    Produce a SHA-256 hash of the provided arguments.

    The values are stringified and sorted prior to hashing so that different
    permutations of equivalent data yield matching hashes.
    """

    serialized = "".join(sorted(_stringify(value) for value in args))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


__all__ = ["crypto_hash"]

