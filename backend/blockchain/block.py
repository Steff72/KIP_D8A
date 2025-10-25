from __future__ import annotations

import time
from dataclasses import dataclass, asdict
from typing import Any, Callable, Mapping

from backend import config
from backend.util.crypto_hash import crypto_hash


TimestampProvider = Callable[[], float]


GENESIS_DATA: Mapping[str, Any] = {
    "index": config.GENESIS_INDEX,
    "timestamp": config.GENESIS_TIMESTAMP,
    "data": config.GENESIS_DATA,
    "last_hash": config.GENESIS_PREVIOUS_HASH,
    "nonce": 0,
    "difficulty": config.DEFAULT_DIFFICULTY,
}
GENESIS_HASH = crypto_hash(
    GENESIS_DATA["index"],
    GENESIS_DATA["timestamp"],
    GENESIS_DATA["data"],
    GENESIS_DATA["last_hash"],
    GENESIS_DATA["nonce"],
    GENESIS_DATA["difficulty"],
)
GENESIS_DATA = {**GENESIS_DATA, "hash": GENESIS_HASH}


@dataclass(frozen=True)
class Block:
    """
    A single block in the blockchain.

    Blocks are immutable data containers with a proof-of-work hash that links
    them to the previous block in the chain.
    """

    index: int
    timestamp: float
    data: Any
    last_hash: str
    nonce: int
    difficulty: int
    hash: str

    @staticmethod
    def calculate_hash(
        *,
        index: int,
        timestamp: float,
        data: Any,
        last_hash: str,
        nonce: int,
        difficulty: int,
    ) -> str:
        """Return the SHA-256 hash representing the block payload."""
        return crypto_hash(index, timestamp, data, last_hash, nonce, difficulty)

    @classmethod
    def create(
        cls,
        *,
        index: int,
        timestamp: float,
        data: Any,
        last_hash: str,
        nonce: int,
        difficulty: int,
    ) -> "Block":
        """Convenience constructor that computes the hash before instantiating."""
        block_hash = cls.calculate_hash(
            index=index,
            timestamp=timestamp,
            data=data,
            last_hash=last_hash,
            nonce=nonce,
            difficulty=difficulty,
        )
        return cls(index, timestamp, data, last_hash, nonce, difficulty, block_hash)

    @classmethod
    def genesis(cls) -> "Block":
        """Return the hard-coded genesis block."""
        return cls(**GENESIS_DATA)

    @classmethod
    def mine_block(
        cls,
        last_block: "Block",
        data: Any,
        *,
        timestamp_provider: TimestampProvider | None = None,
    ) -> "Block":
        """Perform a simple proof-of-work to mine the next block."""
        timestamp_provider = timestamp_provider or time.time
        nonce = 0
        index = last_block.index + 1

        while True:
            timestamp = timestamp_provider()
            difficulty = cls.adjust_difficulty(last_block, timestamp)
            block_hash = cls.calculate_hash(
                index=index,
                timestamp=timestamp,
                data=data,
                last_hash=last_block.hash,
                nonce=nonce,
                difficulty=difficulty,
            )
            if block_hash.startswith("0" * difficulty):
                return cls(index, timestamp, data, last_block.hash, nonce, difficulty, block_hash)
            nonce += 1

    @staticmethod
    def adjust_difficulty(last_block: "Block", new_timestamp: float) -> int:
        """Adjust difficulty relative to how quickly the block is mined."""
        difficulty = last_block.difficulty

        if (new_timestamp - last_block.timestamp) < config.DEFAULT_MINE_RATE_SECONDS:
            difficulty += 1
        else:
            difficulty = max(1, difficulty - 1)

        return difficulty

    @staticmethod
    def is_valid_block(last_block: "Block", block: "Block") -> None:
        """Validate a block relative to the previous block in the chain."""
        if block.last_hash != last_block.hash:
            raise ValueError("last_hash must reference the previous block")

        if block.index != last_block.index + 1:
            raise ValueError("block index must increment sequentially")

        if not block.hash.startswith("0" * block.difficulty):
            raise ValueError("proof-of-work requirement was not met")

        if abs(block.difficulty - last_block.difficulty) > 1:
            raise ValueError("difficulty must only adjust by 1 between blocks")

        reconstructed_hash = Block.calculate_hash(
            index=block.index,
            timestamp=block.timestamp,
            data=block.data,
            last_hash=block.last_hash,
            nonce=block.nonce,
            difficulty=block.difficulty,
        )

        if block.hash != reconstructed_hash:
            raise ValueError("block hash must be correct")

    def to_dict(self) -> dict:
        """Serialize the block for JSON responses."""
        return asdict(self)

__all__ = ["Block", "GENESIS_DATA"]
