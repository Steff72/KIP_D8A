"""
Transaction pool for pending transactions awaiting inclusion in a block.

Each node maintains a pool so that locally created or network-broadcast
transactions can be tracked until they are mined.
"""

from __future__ import annotations

from typing import Dict, Optional

from backend.blockchain.blockchain import Blockchain
from backend.wallet.transaction import Transaction


class TransactionPool:
    """In-memory store for pending transactions."""

    def __init__(self) -> None:
        self.transaction_map: Dict[str, Transaction] = {}

    def set_transaction(self, transaction: Transaction) -> None:
        """Add or replace a transaction in the pool."""
        self.transaction_map[transaction.id] = transaction

    def existing_transaction(self, address: str) -> Optional[Transaction]:
        """
        Return the most recent transaction sent by the given address, if any.
        """
        return next(
            (tx for tx in self.transaction_map.values() if tx.input.get("address") == address),
            None,
        )

    def clear_blockchain_transactions(self, blockchain: Blockchain) -> None:
        """
        Remove transactions that were included in mined blocks.
        """
        for block in blockchain.chain:
            data = block.data
            if not isinstance(data, list):
                continue
            for item in data:
                if isinstance(item, dict):
                    tx_id = item.get("id")
                    if tx_id and tx_id in self.transaction_map:
                        del self.transaction_map[tx_id]

    def transactions(self) -> Iterable[Transaction]:
        """Return an iterable over all transactions in the pool."""
        return self.transaction_map.values()


__all__ = ["TransactionPool"]
