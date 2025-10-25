"""
Central configuration for the blockchain backend.

Only a handful of tuning constants are needed for the initial milestone, but
having them in a dedicated module makes it easy to iterate on difficulty and
timing logic later.
"""

DEFAULT_DIFFICULTY = 3
DEFAULT_MINE_RATE_SECONDS = 8
GENESIS_INDEX = 0
GENESIS_TIMESTAMP = 0.0
GENESIS_PREVIOUS_HASH = "0" * 64
GENESIS_DATA = {"message": "Welcome to D8A Coin"}

