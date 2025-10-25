from __future__ import annotations

from typing import Iterable, List

from flask import Flask, abort, jsonify, request

from backend.blockchain.blockchain import Blockchain


def _serialize_chain(chain: Iterable) -> List[dict]:
    return [block.to_dict() for block in chain]


def create_app(*, blockchain: Blockchain | None = None) -> Flask:
    """
    Application factory wiring HTTP endpoints to the blockchain core.

    A blockchain instance can be injected (handy for tests); otherwise a new
    instance is created for the app process.
    """

    app = Flask(__name__)
    chain = blockchain or Blockchain()

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
