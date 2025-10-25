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

