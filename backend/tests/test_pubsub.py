import types

import pytest

from backend.blockchain.block import Block
from backend.blockchain.blockchain import Blockchain
from backend.pubsub import CHANNELS, BlockchainListener, PubSub
from backend.wallet.transaction import Transaction, create_transaction
from backend.wallet.transaction_pool import TransactionPool
from backend.wallet.wallet import Wallet


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


class InMemoryHub:
    def __init__(self):
        self.subscribers = {}

    def subscribe(self, client, channels):
        for channel in channels:
            self.subscribers.setdefault(channel, set()).add(client)

    def publish(self, channel, message, origin):
        event = types.SimpleNamespace(channel=channel, message=message)
        for client in list(self.subscribers.get(channel, [])):
            for listener in client.listeners:
                listener.message(origin, event)


class LoopbackPubNub(FakePubNub):
    class PublishBuilder(FakePubNub.PublishBuilder):
        def sync(self):
            super().sync()
            self.parent.hub.publish(self._channel, self._message, self.parent)
            return True

    class SubscribeBuilder(FakePubNub.SubscribeBuilder):
        def execute(self):
            super().execute()
            self.parent.hub.subscribe(self.parent, self._channels)
            return self

    def __init__(self, hub):
        super().__init__()
        self.hub = hub

    def publish(self):
        return LoopbackPubNub.PublishBuilder(self)

    def subscribe(self):
        return LoopbackPubNub.SubscribeBuilder(self)


def test_blockchain_listener_appends_valid_block():
    blockchain = Blockchain()
    pool = TransactionPool()
    listener = BlockchainListener(blockchain, pool)
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
    pool = TransactionPool()
    listener = BlockchainListener(blockchain, pool)

    remote_chain = Blockchain()
    remote_chain.add_block("one", timestamp_provider=lambda: 1.0)
    remote_chain.add_block("two", timestamp_provider=lambda: 2.0)

    message = types.SimpleNamespace(
        channel=CHANNELS["CHAIN"],
        message=[block.to_dict() for block in remote_chain.chain],
    )

    listener.message(None, message)

    assert blockchain.chain == remote_chain.chain


def test_blockchain_listener_adds_transaction_to_pool():
    blockchain = Blockchain()
    pool = TransactionPool()
    listener = BlockchainListener(blockchain, pool)
    sender = Wallet(balance=100)
    recipient = Wallet().address
    transaction = create_transaction(sender, recipient, 30)
    message = types.SimpleNamespace(
        channel=CHANNELS["TRANSACTION"],
        message=transaction.to_dict(),
    )

    listener.message(None, message)

    assert pool.transaction_map[transaction.id].output[recipient] == 30


def test_pubsub_broadcasts_with_custom_client():
    blockchain = Blockchain()
    pool = TransactionPool()
    fake_client = FakePubNub()
    pubsub = PubSub(blockchain, pool, pubnub_client=fake_client)
    block = blockchain.add_block("data", timestamp_provider=lambda: 1.0)
    transaction = create_transaction(Wallet(balance=100), Wallet().address, 20)
    pool.set_transaction(transaction)

    pubsub.broadcast_block(block)
    pubsub.broadcast_chain()
    pubsub.broadcast_transaction(transaction)

    assert fake_client.listeners  # listener registered
    assert CHANNELS["BLOCK"] in fake_client.subscribed_channels
    assert CHANNELS["TRANSACTION"] in fake_client.subscribed_channels
    assert len(fake_client.published) == 3
    assert fake_client.published[0][0] == CHANNELS["BLOCK"]
    assert fake_client.published[1][0] == CHANNELS["CHAIN"]
    assert fake_client.published[2][0] == CHANNELS["TRANSACTION"]


def test_block_broadcast_synchronizes_two_nodes():
    hub = InMemoryHub()

    blockchain_a = Blockchain()
    pool_a = TransactionPool()
    pubsub_a = PubSub(blockchain_a, pool_a, pubnub_client=LoopbackPubNub(hub))

    blockchain_b = Blockchain()
    pool_b = TransactionPool()
    pubsub_b = PubSub(blockchain_b, pool_b, pubnub_client=LoopbackPubNub(hub))

    block = blockchain_a.add_block("sync", timestamp_provider=lambda: 1.0)
    pubsub_a.broadcast_block(block)

    assert blockchain_b.last_block.hash == block.hash
