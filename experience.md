## 2025-02-14

Codex helped me bootstrap the environment today. After reviewing the concept and rules, we installed the core Python dependencies (Flask for the API, PubNub for networking, cryptography for wallet signatures, and pytest for TDD) inside the new virtual environment. Codex also generated an up-to-date `requirements.txt` from `pip freeze`, so future setups stay consistent.

### Standing up the blockchain core

I paired with Codex to create the initial `backend/` package structure and the first slice of real functionality. We used TDD to define the behavior for hashing utilities, blocks, and the blockchain (mining, validation, and safe chain replacement), then implemented the modules plus a lightweight `conftest.py` so pytest can import the new package cleanly. The existing backend tests were refreshed to reflect the new architecture, and wallet/transaction suites are temporarily skipped until those modules exist. All ledger-related tests are now green, giving me confidence to tackle networking and wallet milestones next.

### Wiring up the Flask API

With the ledger solid, Codex and I layered on the first Flask interface. We followed TDD again: authored `backend/tests/test_app.py` to lock in expected behavior for `GET /api/chain`, `POST /api/blocks`, and basic validation errors, then added `backend/app.py` plus a `Block.to_dict()` helper so responses serialize cleanly. The app factory accepts an injected `Blockchain`, which made the tests trivial and sets us up for future dependency injection (PubNub, persistence, etc.). All tests are passing after the addition, so the project now has a usable HTTP surface for the upcoming frontend/network milestones.

### Strengthening consensus logic

Today’s focus with Codex was on the consensus mechanics. We tightened `Block` so it now tracks `last_hash`, adjusts difficulty relative to `DEFAULT_MINE_RATE_SECONDS`, and exposes `adjust_difficulty`/`to_dict`. `Block.is_valid_block` once again enforces last-hash linkage, proof-of-work, correct hashes, and the “only adjust difficulty by 1” rule. On top of that, `Blockchain.is_valid_chain`/`replace_chain` gained richer tests, while the HTTP layer keeps working thanks to the new serialization. Running pytest now covers the Flask endpoints plus the expanded consensus scenarios, giving me confidence that nodes can validate and adopt longer valid chains when they appear.

### Documenting the setup

To make onboarding easier, Codex helped me write a concise `README.md` that explains the project at a high level and walks through the usual steps (create a venv, install `requirements.txt`, run `pytest`, and start the Flask API via `FLASK_APP=backend.app:create_app`). This should keep future me—and anyone else who clones the repo—productive without hunting through concept docs for basic commands.

### Networking and synchronization

Today we focused on treating every Flask process like a real network participant. Codex and I:
- Extended `Block`/`Blockchain` with richer serialization plus `try_add_block`, and beefed up the tests to cover difficulty adjustments and incoming block validation.
- Added `backend/pubsub.py`, a PubNub wrapper + listener that broadcasts mined blocks/chains and validates anything it receives before touching the ledger. Tests cover both the broadcast path and listener behavior.
- Created `backend/peer.py` so new nodes can hit `/api/chain` on any `PEER_SEEDS` URL, deserialize the response, and adopt the longest valid chain before joining the pub/sub streams.
- Updated `backend/app.py` to wire in these services, expose the REST endpoints, and optionally skip networking pieces for tests. The README now documents the environment variables (`PUBNUB_*`, `PEER_SEEDS`) and shows how to run multiple nodes on different ports.

The full test suite (including the new networking specs) is passing, so we have a solid base for distributed consensus experiments.
