from __future__ import annotations

from typing import Iterable, List, Sequence

from backend.blockchain.block import Block


class Blockchain:
    """
    Minimal blockchain implementation with validation helpers.

    Additional networking, transaction pools, and wallet logic can build on top
    of this class without needing to modify its proof-of-work guarantees.
    """

    def __init__(self) -> None:
        self.chain: List[Block] = [Block.genesis()]

    @property
    def last_block(self) -> Block:
        return self.chain[-1]

    def add_block(self, data, *, timestamp_provider=None) -> Block:
        """Mine and append a new block to the chain."""
        block = Block.mine_block(
            self.last_block,
            data,
            timestamp_provider=timestamp_provider,
        )
        self.chain.append(block)
        return block

    def try_add_block(self, block: Block) -> bool:
        """Attempt to append a peer-provided block after validation."""
        try:
            Block.is_valid_block(self.last_block, block)
        except ValueError:
            return False

        self.chain.append(block)
        return True

    @staticmethod
    def is_valid_chain(chain: Sequence[Block]) -> bool:
        """Return True if the provided chain is valid."""
        if not chain:
            raise ValueError("chain must contain at least the genesis block")

        if chain[0] != Block.genesis():
            raise ValueError("chain must start with the genesis block")

        for last_block, block in zip(chain, chain[1:]):
            Block.is_valid_block(last_block, block)

        return True

    def replace_chain(self, new_chain: Iterable[Block]) -> bool:
        """
        Replace the current chain if the new one is both longer and valid.

        Returns True when the replacement occurs.
        """
        new_chain_list = list(new_chain)

        if len(new_chain_list) <= len(self.chain):
            return False

        try:
            self.is_valid_chain(new_chain_list)
        except ValueError:
            return False

        self.chain = new_chain_list
        return True


__all__ = ["Blockchain"]
