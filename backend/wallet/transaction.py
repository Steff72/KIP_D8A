"""
Transaction data structures and validation helpers.

Transactions capture the intent to move value from one wallet to another.
The outputs map recipients to the amount they will receive, while the input
records the sender's metadata (address, balance, and signature).
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional
from uuid import uuid4

from backend import config
from backend.wallet.wallet import Wallet, derive_address, public_key_from_hex, verify_signature


def _current_timestamp() -> float:
    """Provide a high-resolution timestamp for transaction inputs."""
    return time.time_ns() / 1_000_000_000


class Transaction:
    """Represent a collection of outputs signed by the sender."""

    def __init__(
        self,
        *,
        id: Optional[str] = None,
        output: Optional[Dict[str, int]] = None,
        input: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.id = id or uuid4().hex
        self.output: Dict[str, int] = output or {}
        self.input: Dict[str, Any] = input or {}

    def update(self, sender_wallet: Wallet, recipient: str, amount: int) -> None:
        """
        Append an additional recipient to the transaction.

        The sender must have sufficient remaining balance in the transaction, and
        the transaction is re-signed to keep the input signature in sync with the
        outputs.
        """

        if amount <= 0:
            raise ValueError("amount must be greater than zero")

        sender_change = self.output.get(sender_wallet.address)
        if sender_change is None:
            raise ValueError("transaction does not belong to the sender")

        if amount > sender_change:
            raise ValueError("amount exceeds available transaction balance")

        self.output[sender_wallet.address] = sender_change - amount
        self.output[recipient] = self.output.get(recipient, 0) + amount
        self.input = self._build_input(sender_wallet)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the transaction."""
        return {
            "id": self.id,
            "output": dict(self.output),
            "input": dict(self.input),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "Transaction":
        """Deserialize a transaction from a dictionary representation."""
        return cls(
            id=payload["id"],
            output=dict(payload["output"]),
            input=dict(payload["input"]),
        )

    def _build_output(self, sender_wallet: Wallet, recipient: str, amount: int) -> Dict[str, int]:
        """Create the output map (recipient amount plus change back to sender)."""
        if amount > sender_wallet.balance:
            raise ValueError("amount exceeds wallet balance")

        output = {
            recipient: amount,
            sender_wallet.address: sender_wallet.balance - amount,
        }
        return output

    def _build_input(self, sender_wallet: Wallet) -> Dict[str, Any]:
        """Generate the metadata payload that records sender details."""
        return {
            "timestamp": _current_timestamp(),
            "amount": sender_wallet.balance,
            "address": sender_wallet.address,
            "public_key": sender_wallet.public_key_hex,
            "signature": sender_wallet.sign(self.output),
        }


def create_transaction(sender_wallet: Wallet, recipient: str, amount: int) -> Transaction:
    """
    Factory helper to produce a signed transaction.
    """

    if amount <= 0:
        raise ValueError("amount must be greater than zero")

    transaction = Transaction()
    transaction.output = transaction._build_output(sender_wallet, recipient, amount)
    transaction.input = transaction._build_input(sender_wallet)
    return transaction


def create_reward_transaction(miner_wallet: Wallet) -> Transaction:
    """
    Create the special mining reward transaction awarded to block miners.
    """

    transaction = Transaction()
    transaction.output = {miner_wallet.address: config.MINING_REWARD_AMOUNT}
    transaction.input = {
        "timestamp": _current_timestamp(),
        "amount": config.MINING_REWARD_AMOUNT,
        "address": config.MINING_REWARD_ADDRESS,
    }
    return transaction


def is_valid_transaction(transaction: Transaction) -> bool:
    """
    Validate that a transaction's outputs and signature are consistent.

    Raises
    ------
    ValueError
        If the transaction is malformed or the signature fails verification.
    """

    input_payload = transaction.input
    output_total = sum(transaction.output.values())
    input_address = input_payload.get("address")

    if input_address == config.MINING_REWARD_ADDRESS:
        if len(transaction.output) != 1:
            raise ValueError("Mining reward must target a single address.")
        if output_total != config.MINING_REWARD_AMOUNT:
            raise ValueError("Mining reward amount is invalid.")
        if input_payload.get("amount") != config.MINING_REWARD_AMOUNT:
            raise ValueError("Mining reward input amount is invalid.")
        return True

    if output_total != input_payload["amount"]:
        raise ValueError("Transaction outputs do not match input amount.")

    public_key_hex = input_payload["public_key"]
    signature = input_payload["signature"]

    if not verify_signature(public_key_hex, transaction.output, signature):
        raise ValueError("Invalid signature for transaction.")

    reconstructed_address = derive_address(public_key_from_hex(public_key_hex))
    if reconstructed_address != input_payload["address"]:
        raise ValueError("Address does not match public key.")

    return True


__all__ = [
    "Transaction",
    "create_transaction",
    "create_reward_transaction",
    "is_valid_transaction",
]
