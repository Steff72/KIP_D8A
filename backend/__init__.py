"""
Backend package for the D8A Coin project.

The package is structured so additional blockchain components (networking,
transactions, wallets, etc.) can be layered on top of the foundational
Block and Blockchain implementations provided in this commit.
"""

__all__ = ["app", "blockchain", "peer", "pubsub", "util"]
