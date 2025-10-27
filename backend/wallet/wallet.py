"""
Wallet and cryptographic helper utilities.

The wallet is responsible for generating an ECDSA key pair, exposing a public
address, signing payloads, and verifying signatures from other peers.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Tuple

from ecdsa import BadSignatureError, SECP256k1, SigningKey, VerifyingKey

from backend import config


def _serialize(data: Any) -> str:
    """Serialize the payload deterministically for signing/verification."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def generate_key_pair() -> Tuple[SigningKey, VerifyingKey]:
    """
    Generate a SECP256k1 key pair suitable for signing transactions.

    Returns
    -------
    (SigningKey, VerifyingKey)
        The private/public key pair.
    """

    private_key = SigningKey.generate(curve=SECP256k1)
    public_key = private_key.get_verifying_key()
    return private_key, public_key


def sign_message(private_key: SigningKey, data: Any) -> str:
    """
    Produce a hex-encoded signature for the provided payload.
    """

    serialized = _serialize(data).encode("utf-8")
    signature = private_key.sign(serialized)
    return signature.hex()


def _ensure_verifying_key(public_key: VerifyingKey | str) -> VerifyingKey:
    """Return a VerifyingKey instance from either a key object or hex string."""
    if isinstance(public_key, VerifyingKey):
        return public_key
    return public_key_from_hex(public_key)


def public_key_from_hex(hex_string: str) -> VerifyingKey:
    """Deserialize a verifying key that was encoded with ``public_key_hex``."""
    return VerifyingKey.from_string(bytes.fromhex(hex_string), curve=SECP256k1)


def verify_signature(public_key: VerifyingKey | str, data: Any, signature: str) -> bool:
    """
    Verify that `signature` matches `data` when signed by `public_key`.

    Parameters
    ----------
    public_key:
        Either a VerifyingKey instance or its hex string representation.
    data:
        The original payload that was signed.
    signature:
        Hex-encoded signature produced by :func:`sign_message`.
    """

    verifying_key = _ensure_verifying_key(public_key)
    serialized = _serialize(data).encode("utf-8")
    try:
        return verifying_key.verify(bytes.fromhex(signature), serialized)
    except BadSignatureError:
        return False


def derive_address(public_key: VerifyingKey) -> str:
    """
    Derive a wallet address by hashing the compressed public key.

    Keeping the address deterministic allows simple identity checks without
    exposing the full verifying key structure.
    """

    return hashlib.sha256(public_key.to_string()).hexdigest()


@dataclass
class Wallet:
    """
    Represents a participant in the blockchain network.

    The wallet holds a balance, an ECDSA key pair, and offers convenience
    methods for signing payloads and accessing serialized key data.
    """

    balance: int = config.STARTING_BALANCE

    def __post_init__(self) -> None:
        self._private_key, self._public_key = generate_key_pair()
        self.address = derive_address(self._public_key)

    @property
    def public_key(self) -> VerifyingKey:
        """Expose the verifying key object."""
        return self._public_key

    @property
    def public_key_hex(self) -> str:
        """Hex string representation for serialization."""
        return self._public_key.to_string().hex()

    def sign(self, data: Any) -> str:
        """
        Sign arbitrary data using the wallet's private key.
        """

        return sign_message(self._private_key, data)

    @staticmethod
    def verify(public_key: VerifyingKey | str, data: Any, signature: str) -> bool:
        """
        Convenience wrapper around :func:`verify_signature`.
        """

        return verify_signature(public_key, data, signature)


__all__ = [
    "Wallet",
    "derive_address",
    "generate_key_pair",
    "public_key_from_hex",
    "sign_message",
    "verify_signature",
]
