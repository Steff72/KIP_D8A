import types

import pytest

from backend.blockchain.block import Block
from backend.blockchain.blockchain import Blockchain
from backend.pubsub import CHANNELS, BlockchainListener, PubSub


class FakePubNub:
    def __init__(self):
        self.published = []
        self.listeners = []
        self.subscribed_channels = []

    class PublishBuilder:
        def __init__(self, parent):
            self.parent = parent
            self._channel = None
            self._message = None

        def channel(self, name):
            self._channel = name
            return self

        def message(self, payload):
            self._message = payload
            return self

        def sync(self):
            self.parent.published.append((self._channel, self._message))
            return True

    class SubscribeBuilder:
        def __init__(self, parent):
            self.parent = parent
            self._channels = []

        def channels(self, channels):
            self._channels = channels
            return self

        def execute(self):
            self.parent.subscribed_channels = self._channels
            return self

    def publish(self):
        return FakePubNub.PublishBuilder(self)

    def subscribe(self):
        return FakePubNub.SubscribeBuilder(self)

    def add_listener(self, listener):
        self.listeners.append(listener)


def test_blockchain_listener_appends_valid_block():
    blockchain = Blockchain()
    listener = BlockchainListener(blockchain)
    new_block = Block.mine_block(
        blockchain.last_block,
        data="network",
        timestamp_provider=lambda: blockchain.last_block.timestamp + 10.0,
    )
    message = types.SimpleNamespace(
        channel=CHANNELS["BLOCK"],
        message=new_block.to_dict(),
    )

    listener.message(None, message)

    assert blockchain.last_block == new_block


def test_blockchain_listener_replaces_chain():
    blockchain = Blockchain()
    listener = BlockchainListener(blockchain)

    remote_chain = Blockchain()
    remote_chain.add_block("one", timestamp_provider=lambda: 1.0)
    remote_chain.add_block("two", timestamp_provider=lambda: 2.0)

    message = types.SimpleNamespace(
        channel=CHANNELS["CHAIN"],
        message=[block.to_dict() for block in remote_chain.chain],
    )

    listener.message(None, message)

    assert blockchain.chain == remote_chain.chain


def test_pubsub_broadcasts_with_custom_client():
    blockchain = Blockchain()
    fake_client = FakePubNub()
    pubsub = PubSub(blockchain, pubnub_client=fake_client)
    block = blockchain.add_block("data", timestamp_provider=lambda: 1.0)

    pubsub.broadcast_block(block)
    pubsub.broadcast_chain()

    assert fake_client.listeners  # listener registered
    assert CHANNELS["BLOCK"] in fake_client.subscribed_channels
    assert len(fake_client.published) == 2
    assert fake_client.published[0][0] == CHANNELS["BLOCK"]
    assert fake_client.published[1][0] == CHANNELS["CHAIN"]
