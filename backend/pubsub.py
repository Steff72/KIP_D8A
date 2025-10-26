from __future__ import annotations

import logging
from typing import Iterable, List, Sequence

from pubnub.callbacks import SubscribeCallback
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

from backend.blockchain.block import Block
from backend.blockchain.blockchain import Blockchain
from backend import config

logger = logging.getLogger(__name__)


CHANNELS = {
    "BLOCK": config.PUBNUB_BLOCK_CHANNEL,
    "CHAIN": config.PUBNUB_CHAIN_CHANNEL,
}


class BlockchainListener(SubscribeCallback):
    """React to PubNub messages by validating and applying blockchain data."""

    def __init__(self, blockchain: Blockchain) -> None:
        self.blockchain = blockchain

    def message(self, pubnub, message) -> None:  # pragma: no cover - invoked by PubNub
        channel = message.channel
        payload = message.message

        try:
            if channel == CHANNELS["BLOCK"]:
                self._handle_block(payload)
            elif channel == CHANNELS["CHAIN"]:
                self._handle_chain(payload)
        except ValueError as exc:
            logger.warning("Rejected payload from channel %s: %s", channel, exc)

    def _handle_block(self, payload: dict) -> None:
        block = Block.from_dict(payload)
        appended = self.blockchain.try_add_block(block)
        if appended:
            logger.info("Appended block %s from pubsub", block.hash)

    def _handle_chain(self, payload: Sequence[dict]) -> None:
        chain = [Block.from_dict(item) for item in payload]
        if self.blockchain.replace_chain(chain):
            logger.info("Replaced local chain via pubsub broadcast")


class PubSub:
    """Thin wrapper around PubNub to broadcast blockchain updates."""

    def __init__(self, blockchain: Blockchain, pubnub_client: PubNub | None = None) -> None:
        self.blockchain = blockchain
        self.pubnub = pubnub_client or self._build_client()
        self.listener = BlockchainListener(blockchain)

        if self.pubnub:
            self.pubnub.add_listener(self.listener)
            self.pubnub.subscribe().channels(list(CHANNELS.values())).execute()

    def _build_client(self) -> PubNub:
        config_obj = PNConfiguration()
        config_obj.subscribe_key = config.PUBNUB_SUBSCRIBE_KEY
        config_obj.publish_key = config.PUBNUB_PUBLISH_KEY
        config_obj.uuid = config.PUBNUB_UUID
        return PubNub(config_obj)

    def broadcast_block(self, block: Block) -> None:
        self._publish(CHANNELS["BLOCK"], block.to_dict())

    def broadcast_chain(self) -> None:
        chain_payload = [block.to_dict() for block in self.blockchain.chain]
        self._publish(CHANNELS["CHAIN"], chain_payload)

    def _publish(self, channel: str, message: dict | List[dict]) -> None:
        if not self.pubnub:
            return
        try:
            self.pubnub.publish().channel(channel).message(message).sync()
        except Exception as exc:  # pragma: no cover - network errors
            logger.warning("Failed to publish to %s: %s", channel, exc)


__all__ = ["CHANNELS", "PubSub", "BlockchainListener"]

