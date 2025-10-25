"""
Utility to convert hexadecimal strings to zero-padded binary strings.
"""

from __future__ import annotations


def hex_to_binary(hex_string: str) -> str:
    """Return the binary representation of a hex string (with leading zeros)."""
    scale = 16
    # Each hex digit encodes four bits, so pad the binary output accordingly.
    return bin(int(hex_string, scale))[2:].zfill(len(hex_string) * 4)


__all__ = ["hex_to_binary"]

