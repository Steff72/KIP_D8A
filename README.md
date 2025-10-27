# D8A Coin

D8A Coin is a miniature, educational blockchain that demonstrates the core pieces of a cryptocurrency implementation: proof-of-work mining, deterministic block/chain validation, and a Flask API that lets multiple nodes (or a frontend) inspect the ledger and submit new block data. The project is intentionally modular so future milestones (wallets, transactions, PubNub networking, React UI) can layer on top of the tested core.

## Prerequisites

- Python 3.9+
- `pip` (ships with Python 3.9)

## Environment Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running Tests

```bash
source .venv/bin/activate
pytest
```

## Wallets & Transactions

- Wallets are defined in `backend/wallet/wallet.py`; they generate SECP256k1 key pairs, derive deterministic addresses, and expose helper functions for signing/verification.
- Transactions live in `backend/wallet/transaction.py`, providing factories, update helpers, and validation routines that ensure outputs balance with the sender's input and signatures remain intact.

## Running the Flask API

```bash
source .venv/bin/activate
export FLASK_APP=backend.app:create_app
flask run --reload
```

The development server listens on `http://127.0.0.1:5000` by default with the following endpoints:

- `GET /api/chain` – returns the current blockchain (list of blocks plus chain length).
- `POST /api/blocks` – accepts JSON payloads containing a `data` field, mines, and returns the new block.

Use these routes locally or point other nodes/frontends at the server to share the chain state.

## Pub/Sub & Peer Synchronization

- PubNub is used to broadcast new blocks and full-chain snapshots. Provide your keys via:
  - `PUBNUB_SUBSCRIBE_KEY`
  - `PUBNUB_PUBLISH_KEY`
  - Optional overrides: `PUBNUB_UUID`, `PUBNUB_BLOCK_CHANNEL`, `PUBNUB_CHAIN_CHANNEL`
- Nodes can automatically sync from existing peers on startup by setting `PEER_SEEDS` to a comma-separated list of base URLs (e.g., `PEER_SEEDS=http://127.0.0.1:5000`).

## Running Multiple Nodes

Start one node on the default port:

```bash
source .venv/bin/activate
export FLASK_APP=backend.app:create_app
flask run --port 5000
```

Then start a second node that syncs from the first and broadcasts over PubNub:

```bash
source .venv/bin/activate
export FLASK_APP=backend.app:create_app
export FLASK_RUN_PORT=5001
export PEER_SEEDS=http://127.0.0.1:5000
flask run --port 5001
```

Each process maintains its own blockchain instance but converges on a shared ledger through the peer-sync bootstrap and the PubNub pub/sub channels.
