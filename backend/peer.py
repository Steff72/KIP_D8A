from __future__ import annotations

import logging
from typing import Callable, Iterable, List, Sequence

import requests

from backend.blockchain.block import Block
from backend.blockchain.blockchain import Blockchain
from backend import config

logger = logging.getLogger(__name__)


def _default_fetcher(url: str) -> Sequence[dict]:
    response = requests.get(f"{url.rstrip('/')}/api/chain", timeout=config.PEER_SYNC_TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    return payload["chain"]


def sync_chain_from_peers(
    blockchain: Blockchain,
    peer_urls: Iterable[str],
    *,
    fetch_chain_fn: Callable[[str], Sequence[dict]] | None = None,
) -> bool:
    """
    Attempt to replace the local chain with data fetched from peers.

    Returns True as soon as a peer provides a longer, valid chain.
    """

    fetcher = fetch_chain_fn or _default_fetcher
    for url in peer_urls:
        try:
            raw_chain = fetcher(url)
            remote_chain = [Block.from_dict(block) for block in raw_chain]

            if blockchain.replace_chain(remote_chain):
                logger.info("Adopted chain from peer %s", url)
                return True
        except (requests.RequestException, KeyError, ValueError) as exc:
            logger.warning("Failed to sync from %s: %s", url, exc)
            continue

    return False


def parse_peer_urls(peers: str | None) -> List[str]:
    """Turn a comma-separated PEER_SEEDS string into a list of URLs."""
    if not peers:
        return []
    return [peer.strip() for peer in peers.split(",") if peer.strip()]


__all__ = ["parse_peer_urls", "sync_chain_from_peers"]

