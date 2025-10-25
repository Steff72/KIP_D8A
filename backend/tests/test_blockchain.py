import dataclasses

import pytest

from backend.blockchain.block import Block, GENESIS_DATA
from backend.blockchain.blockchain import Blockchain


def test_blockchain_starts_with_genesis():
    blockchain = Blockchain()
    assert blockchain.chain[0] == Block.genesis()
    assert blockchain.chain[0].hash == GENESIS_DATA["hash"]


def test_add_block_appends_mined_block():
    blockchain = Blockchain(difficulty=2)
    payload = {"amount": 5}
    new_block = blockchain.add_block(
        payload,
        timestamp_provider=lambda: 1_700_000_777.0,
    )

    assert new_block.data == payload
    assert new_block.previous_hash == blockchain.chain[-2].hash
    assert blockchain.last_block == new_block


def test_is_valid_chain_detects_tampering():
    blockchain = Blockchain(difficulty=1)
    blockchain.add_block("one", timestamp_provider=lambda: 1.0)
    blockchain.add_block("two", timestamp_provider=lambda: 2.0)

    assert Blockchain.is_valid_chain(blockchain.chain)

    tampered = list(blockchain.chain)
    tampered[1] = dataclasses.replace(tampered[1], data="evil")

    with pytest.raises(ValueError):
        Blockchain.is_valid_chain(tampered)


def test_replace_chain_prefers_longer_valid_chain():
    blockchain = Blockchain(difficulty=1)
    blockchain.add_block("a", timestamp_provider=lambda: 1.0)

    challenger = Blockchain(difficulty=1)
    challenger.add_block("a", timestamp_provider=lambda: 1.0)
    challenger.add_block("b", timestamp_provider=lambda: 2.0)

    assert blockchain.replace_chain(challenger.chain)
    assert blockchain.chain == challenger.chain


def test_replace_chain_rejects_shorter_or_invalid_chain():
    blockchain = Blockchain(difficulty=1)
    blockchain.add_block("a", timestamp_provider=lambda: 1.0)

    shorter = Blockchain(difficulty=1)

    assert not blockchain.replace_chain(shorter.chain)

    invalid = list(blockchain.chain)
    invalid[1] = dataclasses.replace(invalid[1], previous_hash="corrupt")

    assert not blockchain.replace_chain(invalid)
