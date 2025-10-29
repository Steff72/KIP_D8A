from __future__ import annotations

import logging
from typing import List, Sequence

from pubnub.callbacks import SubscribeCallback
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

from backend import config
from backend.blockchain.block import Block
from backend.blockchain.blockchain import Blockchain
from backend.wallet.transaction import Transaction, is_valid_transaction
from backend.wallet.transaction_pool import TransactionPool

logger = logging.getLogger(__name__)


CHANNELS = {
    "BLOCK": config.PUBNUB_BLOCK_CHANNEL,
    "CHAIN": config.PUBNUB_CHAIN_CHANNEL,
    "TRANSACTION": config.PUBNUB_TRANSACTION_CHANNEL,
}


class BlockchainListener(SubscribeCallback):
    """React to PubNub messages by validating and applying blockchain data."""

    def __init__(self, blockchain: Blockchain, transaction_pool: TransactionPool) -> None:
        self.blockchain = blockchain
        self.transaction_pool = transaction_pool

    def message(self, pubnub, message) -> None:  # pragma: no cover - invoked by PubNub
        channel = message.channel
        payload = message.message

        try:
            if channel == CHANNELS["BLOCK"]:
                self._handle_block(payload)
            elif channel == CHANNELS["CHAIN"]:
                self._handle_chain(payload)
            elif channel == CHANNELS["TRANSACTION"]:
                self._handle_transaction(payload)
        except ValueError as exc:
            logger.warning("Rejected payload from channel %s: %s", channel, exc)

    def _handle_block(self, payload: dict) -> None:
        block = Block.from_dict(payload)
        appended = self.blockchain.try_add_block(block)
        if appended:
            logger.info("Appended block %s from pubsub", block.hash)
            self.transaction_pool.clear_blockchain_transactions(self.blockchain)

    def _handle_chain(self, payload: Sequence[dict]) -> None:
        chain = [Block.from_dict(item) for item in payload]
        if self.blockchain.replace_chain(chain):
            logger.info("Replaced local chain via pubsub broadcast")
            self.transaction_pool.clear_blockchain_transactions(self.blockchain)

    def _handle_transaction(self, payload: dict) -> None:
        transaction = Transaction.from_dict(payload)
        is_valid_transaction(transaction)
        self.transaction_pool.set_transaction(transaction)
        logger.info("Recorded transaction %s from pubsub", transaction.id)


class PubSub:
    """Thin wrapper around PubNub to broadcast blockchain updates."""

    def __init__(
        self,
        blockchain: Blockchain,
        transaction_pool: TransactionPool,
        pubnub_client: PubNub | None = None,
    ) -> None:
        self.blockchain = blockchain
        self.transaction_pool = transaction_pool
        self.pubnub = pubnub_client or self._build_client()
        self.listener = BlockchainListener(blockchain, transaction_pool)

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

    def broadcast_transaction(self, transaction: Transaction) -> None:
        self._publish(CHANNELS["TRANSACTION"], transaction.to_dict())

    def _publish(self, channel: str, message: dict | List[dict]) -> None:
        if not self.pubnub:
            return
        try:
            self.pubnub.publish().channel(channel).message(message).sync()
        except Exception as exc:  # pragma: no cover - network errors
            logger.warning("Failed to publish to %s: %s", channel, exc)


__all__ = ["CHANNELS", "PubSub", "BlockchainListener"]

