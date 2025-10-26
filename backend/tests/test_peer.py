from backend.blockchain.blockchain import Blockchain
from backend.peer import parse_peer_urls, sync_chain_from_peers


def test_parse_peer_urls_handles_commas_and_whitespace():
    peers = " http://localhost:5000 ,http://localhost:5001,, "
    assert parse_peer_urls(peers) == ["http://localhost:5000", "http://localhost:5001"]


def test_sync_chain_adopts_longer_valid_chain():
    local_chain = Blockchain()
    remote_chain = Blockchain()
    remote_chain.add_block("one", timestamp_provider=lambda: 1.0)

    def fake_fetch(url):
        assert url == "http://peer"
        return [block.to_dict() for block in remote_chain.chain]

    replaced = sync_chain_from_peers(
        local_chain,
        ["http://peer"],
        fetch_chain_fn=fake_fetch,
    )

    assert replaced is True
    assert local_chain.chain == remote_chain.chain


def test_sync_chain_skips_invalid_data():
    local_chain = Blockchain()

    def fake_fetch(_):
        return [{"foo": "bar"}]

    replaced = sync_chain_from_peers(local_chain, ["http://peer"], fetch_chain_fn=fake_fetch)

    assert replaced is False
    assert len(local_chain.chain) == 1
