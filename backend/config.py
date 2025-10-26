"""
Central configuration for the blockchain backend.

Only a handful of tuning constants are needed for the initial milestone, but
having them in a dedicated module makes it easy to iterate on difficulty and
timing logic later.
"""

from __future__ import annotations

import os

DEFAULT_DIFFICULTY = 3
DEFAULT_MINE_RATE_SECONDS = 8
GENESIS_INDEX = 0
GENESIS_TIMESTAMP = 0.0
GENESIS_PREVIOUS_HASH = "0" * 64
GENESIS_DATA = {"message": "Welcome to D8A Coin"}

PUBNUB_SUBSCRIBE_KEY = os.getenv("PUBNUB_SUBSCRIBE_KEY", "demo")
PUBNUB_PUBLISH_KEY = os.getenv("PUBNUB_PUBLISH_KEY", "demo")
PUBNUB_UUID = os.getenv("PUBNUB_UUID", "d8a-node")
PUBNUB_BLOCK_CHANNEL = os.getenv("PUBNUB_BLOCK_CHANNEL", "D8A_BLOCK")
PUBNUB_CHAIN_CHANNEL = os.getenv("PUBNUB_CHAIN_CHANNEL", "D8A_CHAIN")

PEER_SEEDS = os.getenv("PEER_SEEDS", "")
PEER_SYNC_TIMEOUT = float(os.getenv("PEER_SYNC_TIMEOUT", "5"))
