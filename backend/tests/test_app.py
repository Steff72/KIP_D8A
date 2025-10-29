import pytest

from backend import config
from backend.app import create_app
from backend.blockchain.blockchain import Blockchain
from backend.wallet.transaction import Transaction, create_transaction
from backend.wallet.transaction_pool import TransactionPool
from backend.wallet.wallet import Wallet


class StubPubSub:
    def __init__(self, blockchain, transaction_pool=None):
        self.blockchain = blockchain
        self.transaction_pool = transaction_pool
        self.blocks = []
        self.chain_broadcasts = 0
        self.transactions = []

    def broadcast_block(self, block):
        self.blocks.append(block)

    def broadcast_chain(self):
        self.chain_broadcasts += 1

    def broadcast_transaction(self, transaction):
        self.transactions.append(transaction)


@pytest.fixture
def api_client():
    """Provide a Flask test client paired with a dedicated blockchain instance."""
    blockchain = Blockchain()
    wallet = Wallet(balance=100)
    transaction_pool = TransactionPool()
    app = create_app(
        blockchain=blockchain,
        wallet=wallet,
        transaction_pool=transaction_pool,
        enable_pubsub=False,
        sync_on_startup=False,
    )
    app.config.update(TESTING=True)

    with app.test_client() as client:
        yield client, blockchain, wallet, transaction_pool


def test_get_chain_returns_serialized_blocks(api_client):
    client, blockchain, *_ = api_client
    blockchain.add_block("hello", timestamp_provider=lambda: 123.0)

    response = client.get("/api/chain")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["length"] == len(blockchain.chain)
    assert payload["chain"][-1]["data"] == "hello"


def test_post_blocks_mines_new_block(api_client):
    client, blockchain, *_ = api_client

    response = client.post("/api/blocks", json={"data": {"amount": 25}})

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["block"]["hash"] == blockchain.last_block.hash
    assert blockchain.last_block.data == {"amount": 25}


def test_post_blocks_broadcasts_via_pubsub():
    blockchain = Blockchain()
    wallet = Wallet(balance=100)
    transaction_pool = TransactionPool()
    app = create_app(
        blockchain=blockchain,
        wallet=wallet,
        transaction_pool=transaction_pool,
        enable_pubsub=True,
        pubsub_factory=lambda bc, transaction_pool, **_: StubPubSub(bc, transaction_pool),
        sync_on_startup=False,
    )
    app.config.update(TESTING=True)

    with app.test_client() as client:
        response = client.post("/api/blocks", json={"data": "hello"})

    assert response.status_code == 201
    pubsub = app.config["PUBSUB"]
    assert isinstance(pubsub, StubPubSub)
    assert len(pubsub.blocks) == 1
    assert pubsub.chain_broadcasts == 1


def test_post_block_defaults_to_transaction_pool(api_client):
    client, blockchain, wallet, transaction_pool = api_client
    recipient = Wallet().address
    transaction = create_transaction(wallet, recipient, 15)
    transaction_pool.set_transaction(transaction)

    response = client.post("/api/blocks", json={})

    assert response.status_code == 201
    last_block = blockchain.last_block
    assert any(item["id"] == transaction.id for item in last_block.data)
    assert transaction.id not in transaction_pool.transaction_map
    reward_entry = next(item for item in last_block.data if item["input"]["address"] == config.MINING_REWARD_ADDRESS)
    assert reward_entry["output"][wallet.address] == config.MINING_REWARD_AMOUNT


def test_create_transaction_via_api_broadcasts_and_stores():
    blockchain = Blockchain()
    wallet = Wallet(balance=100)
    transaction_pool = TransactionPool()
    recipient = Wallet().address
    app = create_app(
        blockchain=blockchain,
        wallet=wallet,
        transaction_pool=transaction_pool,
        enable_pubsub=True,
        pubsub_factory=lambda bc, transaction_pool, **_: StubPubSub(bc, transaction_pool),
        sync_on_startup=False,
    )
    app.config.update(TESTING=True)

    with app.test_client() as client:
        response = client.post("/api/transactions", json={"recipient": recipient, "amount": 25})

    assert response.status_code == 201
    payload = response.get_json()
    transaction = payload["transaction"]
    assert transaction_pool.transaction_map[transaction["id"]].output[recipient] == 25
    pubsub = app.config["PUBSUB"]
    assert pubsub.transactions[0].id == transaction["id"]


def test_transactions_endpoint_returns_pool(api_client):
    client, _, wallet, pool = api_client
    recipient = Wallet().address
    transaction = create_transaction(wallet, recipient, 20)
    pool.set_transaction(transaction)

    response = client.get("/api/transactions")

    assert response.status_code == 200
    body = response.get_json()
    assert body["transactions"][0]["id"] == transaction.id


def test_mining_without_pending_transactions_yields_reward_only(api_client):
    client, blockchain, wallet, _ = api_client

    response = client.post("/api/blocks")

    assert response.status_code == 201
    mined_block = blockchain.last_block
    assert isinstance(mined_block.data, list)
    assert len(mined_block.data) == 1
    reward_tx = mined_block.data[0]
    assert reward_tx["input"]["address"] == config.MINING_REWARD_ADDRESS
    assert reward_tx["output"][wallet.address] == config.MINING_REWARD_AMOUNT


def test_wallet_info_endpoint_reports_balance(api_client):
    client, blockchain, wallet, _ = api_client
    client.post("/api/blocks")

    response = client.get("/api/wallet/info")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["address"] == wallet.address
    assert payload["balance"] == wallet.calculate_balance(blockchain)


def test_transaction_update_endpoint_modifies_existing_transaction():
    wallet = Wallet(balance=100)
    transaction_pool = TransactionPool()
    blockchain = Blockchain()
    recipient = Wallet().address
    app = create_app(
        blockchain=blockchain,
        wallet=wallet,
        transaction_pool=transaction_pool,
        enable_pubsub=False,
        sync_on_startup=False,
    )
    app.config.update(TESTING=True)
    transaction = create_transaction(wallet, recipient, 20)
    transaction_pool.set_transaction(transaction)
    new_recipient = Wallet().address

    with app.test_client() as client:
        response = client.post(
            "/api/transactions/update",
            json={
                "transaction_id": transaction.id,
                "recipient": new_recipient,
                "amount": 5,
            },
        )

    assert response.status_code == 200
    updated = transaction_pool.transaction_map[transaction.id]
    assert updated.output[new_recipient] == 5
    assert updated.output[wallet.address] == wallet.balance - 25


def test_import_transaction_endpoint_accepts_external_payload():
    blockchain = Blockchain()
    wallet = Wallet(balance=100)
    transaction_pool = TransactionPool()
    sender = Wallet(balance=75)
    recipient = Wallet().address
    transaction = create_transaction(sender, recipient, 25)
    app = create_app(
        blockchain=blockchain,
        wallet=wallet,
        transaction_pool=transaction_pool,
        enable_pubsub=False,
        sync_on_startup=False,
    )
    app.config.update(TESTING=True)

    with app.test_client() as client:
        response = client.post("/api/transactions/import", json={"transaction": transaction.to_dict()})

    assert response.status_code == 200
    stored = transaction_pool.transaction_map[transaction.id]
    assert stored.output[recipient] == 25
