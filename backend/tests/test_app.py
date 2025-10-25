import pytest

from backend.app import create_app
from backend.blockchain.blockchain import Blockchain


@pytest.fixture
def api_client():
    """Provide a Flask test client paired with a dedicated blockchain instance."""
    blockchain = Blockchain(difficulty=1)
    app = create_app(blockchain=blockchain)
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

