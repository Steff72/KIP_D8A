import pytest

from backend.app import create_app
from backend.blockchain.blockchain import Blockchain


class StubPubSub:
    def __init__(self, blockchain):
        self.blockchain = blockchain
        self.blocks = []
        self.chain_broadcasts = 0

    def broadcast_block(self, block):
        self.blocks.append(block)

    def broadcast_chain(self):
        self.chain_broadcasts += 1


@pytest.fixture
def api_client():
    """Provide a Flask test client paired with a dedicated blockchain instance."""
    blockchain = Blockchain()
    app = create_app(
        blockchain=blockchain,
        enable_pubsub=False,
        sync_on_startup=False,
    )
    app.config.update(TESTING=True)

    with app.test_client() as client:
        yield client, blockchain


def test_get_chain_returns_serialized_blocks(api_client):
    client, blockchain = api_client
    blockchain.add_block("hello", timestamp_provider=lambda: 123.0)

    response = client.get("/api/chain")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["length"] == len(blockchain.chain)
    assert payload["chain"][-1]["data"] == "hello"


def test_post_blocks_mines_new_block(api_client):
    client, blockchain = api_client

    response = client.post("/api/blocks", json={"data": {"amount": 25}})

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["block"]["hash"] == blockchain.last_block.hash
    assert blockchain.last_block.data == {"amount": 25}


def test_post_blocks_requires_payload(api_client):
    client, _ = api_client

    response = client.post("/api/blocks", json={})

    assert response.status_code == 400
    payload = response.get_json()
    assert "data" in payload["message"]


def test_post_blocks_broadcasts_via_pubsub():
    blockchain = Blockchain()
    app = create_app(
        blockchain=blockchain,
        enable_pubsub=True,
        pubsub_factory=lambda bc: StubPubSub(bc),
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
