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
- `backend/wallet/transaction_pool.py` keeps a node's pending transactions in sync across the network until they are mined into a block.

## Running the Flask API

```bash
source .venv/bin/activate
export FLASK_APP=backend.app:create_app
flask run --reload
```

The development server listens on `http://127.0.0.1:5000` by default with the following endpoints:

- `GET /api/chain` – returns the current blockchain (list of blocks plus chain length).
- `POST /api/blocks` – accepts JSON payloads containing a `data` field, mines, and returns the new block.
- `GET /api/transactions` – returns the current transaction pool.
- `POST /api/transactions` – creates a new signed transaction for the node wallet and broadcasts it to peers.
- `POST /api/transactions/update` – allows the node wallet to append additional recipients to an existing pending transaction.
- `POST /api/transactions/import` – accepts a fully signed transaction (JSON) from an external wallet and validates/broadcasts it.

Use these routes locally or point other nodes/frontends at the server to share the chain state. When a production build of the React UI exists in `frontend/dist`, the Flask app also serves that bundle at `/`, so you can visit the root URL without running `npm run dev`.

## Pub/Sub & Peer Synchronization

- PubNub is used to broadcast new blocks, full-chain snapshots, and pool transactions.
- **Important**: You must provide your own PubNub keys in a `.env` file in the root directory.
  ```bash
  PUBNUB_PUBLISH_KEY=your_publish_key
  PUBNUB_SUBSCRIBE_KEY=your_subscribe_key
  ```
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

## Frontend UI

The `frontend/` directory contains a Vite-powered React dashboard that mirrors the design from the concept document. It surfaces wallet details, pending transactions, known addresses derived from the chain, and quick actions for submitting transactions or mining the next block.

Prerequisites:

- Node.js 18+ (tested with v22.18.0)
- npm 8+

Run the UI against a locally running Flask node:

```bash
cd frontend
npm install
npm run dev
```

By default, the dev server proxies `/api/*` requests to `http://localhost:5000`. Point the UI at a different backend by setting `VITE_API_BASE_URL` before starting the dev server or build:

```bash
VITE_API_BASE_URL=http://127.0.0.1:5001 npm run dev
```

For a production build, run `npm run build`—the artifacts will be written to `frontend/dist/`.

## Running Frontend Tests

The frontend includes a Vitest test suite. Run it via:

```bash
cd frontend
npm test
```

## Network Verification

To verify that multiple nodes are syncing correctly (using your `.env` keys), run the included script:

```bash
python3 verify_network.py
```

