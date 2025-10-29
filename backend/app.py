from __future__ import annotations

from pathlib import Path
from typing import List, Sequence
import sys

from flask import Flask, abort, jsonify, request, send_from_directory

# Allow running this module directly (e.g., ``python backend/app.py``) by
# ensuring the project root is on the import path before importing ``backend``.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"

from backend import config
from backend.blockchain.blockchain import Blockchain
from backend.peer import parse_peer_urls, sync_chain_from_peers
from backend.pubsub import PubSub
from backend.wallet.transaction import (
    Transaction,
    create_reward_transaction,
    create_transaction,
    is_valid_transaction,
)
from backend.wallet.transaction_pool import TransactionPool
from backend.wallet.wallet import Wallet


def _serialize_chain(chain: Sequence) -> List[dict]:
    return [block.to_dict() for block in chain]


def create_app(
    *,
    blockchain: Blockchain | None = None,
    wallet: Wallet | None = None,
    transaction_pool: TransactionPool | None = None,
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
    if FRONTEND_DIST.exists():
        app = Flask(__name__, static_folder=str(FRONTEND_DIST), static_url_path="/")
    else:
        app = Flask(__name__)
    chain = blockchain or Blockchain()
    wallet = wallet or Wallet()
    transaction_pool = transaction_pool or TransactionPool()
    seeds = peer_urls

    if seeds is None:
        seeds = parse_peer_urls(config.PEER_SEEDS)

    if sync_on_startup and seeds:
        sync_chain_from_peers(chain, seeds)

    pubsub = None
    if enable_pubsub:
        factory = pubsub_factory or PubSub
        pubsub = factory(chain, transaction_pool)

    app.config["BLOCKCHAIN"] = chain
    app.config["WALLET"] = wallet
    app.config["TRANSACTION_POOL"] = transaction_pool
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
        data = payload.get("data")

        # Default to packaging the current transaction pool when no explicit data is supplied.
        if data is None:
            pool_payload = [tx.to_dict() for tx in transaction_pool.transactions()]
            reward_transaction = create_reward_transaction(wallet)
            pool_payload.append(reward_transaction.to_dict())
            data = pool_payload

        new_block = chain.add_block(data)
        transaction_pool.clear_blockchain_transactions(chain)
        if pubsub:
            pubsub.broadcast_block(new_block)
            pubsub.broadcast_chain()
        return jsonify({"block": new_block.to_dict()}), 201

    @app.get("/api/transactions")
    def get_transactions():
        transactions = [tx.to_dict() for tx in transaction_pool.transactions()]
        return jsonify({"transactions": transactions})

    @app.get("/api/wallet/info")
    def get_wallet_info():
        balance = wallet.calculate_balance(chain)
        return jsonify(
            {
                "address": wallet.address,
                "balance": balance,
            }
        )

    @app.post("/api/transactions")
    def post_transaction():
        payload = request.get_json(silent=True) or {}
        if not payload:
            abort(400, description="Transaction payload required.")

        recipient = payload.get("recipient")
        amount = payload.get("amount")

        if not recipient or amount is None:
            abort(400, description="Both 'recipient' and 'amount' are required.")

        try:
            amount = int(amount)
        except (TypeError, ValueError):
            abort(400, description="'amount' must be an integer.")

        try:
            transaction = create_transaction(wallet, recipient, amount)
        except ValueError as exc:
            abort(400, description=str(exc))

        transaction_pool.set_transaction(transaction)
        if pubsub:
            pubsub.broadcast_transaction(transaction)
        return jsonify({"transaction": transaction.to_dict()}), 201

    @app.post("/api/transactions/import")
    def import_transaction():
        payload = request.get_json(silent=True) or {}
        if not payload:
            abort(400, description="Transaction payload required.")

        transaction_data = payload.get("transaction") or payload

        try:
            transaction = Transaction.from_dict(transaction_data)
            is_valid_transaction(transaction)
        except (KeyError, ValueError) as exc:
            abort(400, description=str(exc))

        transaction_pool.set_transaction(transaction)
        if pubsub:
            pubsub.broadcast_transaction(transaction)
        return jsonify({"transaction": transaction.to_dict()}), 200

    @app.post("/api/transactions/update")
    def update_transaction():
        payload = request.get_json(silent=True) or {}
        if not payload:
            abort(400, description="Transaction payload required.")

        transaction_id = payload.get("transaction_id")
        recipient = payload.get("recipient")
        amount = payload.get("amount")

        if not transaction_id:
            abort(400, description="'transaction_id' is required.")
        if not recipient or amount is None:
            abort(400, description="Both 'recipient' and 'amount' are required.")

        try:
            amount = int(amount)
        except (TypeError, ValueError):
            abort(400, description="'amount' must be an integer.")

        transaction = transaction_pool.transaction_map.get(transaction_id)
        if not transaction:
            abort(404, description="Transaction not found.")

        try:
            transaction.update(wallet, recipient, amount)
        except ValueError as exc:
            abort(400, description=str(exc))

        transaction_pool.set_transaction(transaction)
        if pubsub:
            pubsub.broadcast_transaction(transaction)
        return jsonify({"transaction": transaction.to_dict()})

    if app.static_folder and Path(app.static_folder).exists():
        static_dir = Path(app.static_folder)

        @app.get("/", defaults={"path": ""})
        @app.get("/<path:path>")
        def serve_frontend(path):  # pragma: no cover - integration behaviour
            if path.startswith("api/"):
                abort(404)

            candidate = static_dir / path
            if path and candidate.exists() and candidate.is_file():
                return send_from_directory(static_dir, path)
            return send_from_directory(static_dir, "index.html")

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
