import dataclasses

import pytest

from backend.blockchain.block import Block, GENESIS_DATA


def test_genesis_block_matches_definition():
    genesis = Block.genesis()

    for key, value in GENESIS_DATA.items():
        assert getattr(genesis, key) == value


def test_mined_block_meets_difficulty_and_links_previous():
    last_block = Block.genesis()
    mined_block = Block.mine_block(
        last_block,
        data={"amount": 99},
        difficulty=2,
        timestamp_provider=lambda: 1_700_000_321.0,
    )

    assert mined_block.previous_hash == last_block.hash
    assert mined_block.hash.startswith("0" * mined_block.difficulty)


@pytest.fixture
def valid_block_pair():
    first = Block.genesis()
    second = Block.mine_block(
        first,
        data="payload",
        difficulty=3,
        timestamp_provider=lambda: 1_700_000_444.0,
    )
    return first, second


def test_is_valid_block(valid_block_pair):
    last_block, block = valid_block_pair
    Block.is_valid_block(last_block, block)


def test_is_valid_block_detects_wrong_previous_hash(valid_block_pair):
    last_block, block = valid_block_pair
    tampered = dataclasses.replace(block, previous_hash="abc")

    with pytest.raises(ValueError, match="previous_hash"):
        Block.is_valid_block(last_block, tampered)


def test_is_valid_block_detects_weak_pow(valid_block_pair):
    last_block, block = valid_block_pair
    tampered = dataclasses.replace(block, hash="f" * len(block.hash))

    with pytest.raises(ValueError, match="proof-of-work"):
        Block.is_valid_block(last_block, tampered)


def test_is_valid_block_detects_invalid_hash(valid_block_pair):
    last_block, block = valid_block_pair
    tampered = dataclasses.replace(block, hash="0" * block.difficulty + "abc")

    with pytest.raises(ValueError, match="block hash"):
        Block.is_valid_block(last_block, tampered)
