from __future__ import annotations

from typing import Iterable, List, Sequence

from flask import Flask, abort, jsonify, request

from backend import config
from backend.blockchain.blockchain import Blockchain
from backend.peer import parse_peer_urls, sync_chain_from_peers
from backend.pubsub import PubSub


def _serialize_chain(chain: Sequence) -> List[dict]:
    return [block.to_dict() for block in chain]


def create_app(
    *,
    blockchain: Blockchain | None = None,
    enable_pubsub: bool = True,
    pubsub_factory=None,
    sync_on_startup: bool = True,
    peer_urls: list[str] | None = None,
) -> Flask:
    """
    Application factory wiring HTTP endpoints to the blockchain core.

    A blockchain instance can be injected (handy for tests); otherwise a new
    instance is created for the app process. Pub/Sub integration and peer
    synchronization can be toggled (or injected) for tests.
    """

    app = Flask(__name__)
    chain = blockchain or Blockchain()
    seeds = peer_urls

    if seeds is None:
        seeds = parse_peer_urls(config.PEER_SEEDS)

    if sync_on_startup and seeds:
        sync_chain_from_peers(chain, seeds)

    pubsub = None
    if enable_pubsub:
        factory = pubsub_factory or PubSub
        pubsub = factory(chain)

    app.config["BLOCKCHAIN"] = chain
    app.config["PUBSUB"] = pubsub

    @app.get("/api/chain")
    def get_chain():
        return jsonify(
            {
                "chain": _serialize_chain(chain.chain),
                "length": len(chain.chain),
            }
        )

    @app.post("/api/blocks")
    def post_block():
        payload = request.get_json(silent=True) or {}
        if "data" not in payload:
            abort(400, description="Request body must include 'data'.")

        new_block = chain.add_block(payload["data"])
        if pubsub:
            pubsub.broadcast_block(new_block)
            pubsub.broadcast_chain()
        return jsonify({"block": new_block.to_dict()}), 201

    @app.errorhandler(400)
    def handle_bad_request(err):  # pragma: no cover - Flask invokes automatically
        return (
            jsonify(
                {
                    "error": "Bad Request",
                    "message": err.description,
                }
            ),
            400,
        )

    return app


__all__ = ["create_app"]
