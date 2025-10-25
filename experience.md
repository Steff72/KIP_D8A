## 2025-02-14

Codex helped me bootstrap the environment today. After reviewing the concept and rules, we installed the core Python dependencies (Flask for the API, PubNub for networking, cryptography for wallet signatures, and pytest for TDD) inside the new virtual environment. Codex also generated an up-to-date `requirements.txt` from `pip freeze`, so future setups stay consistent.

### Standing up the blockchain core

I paired with Codex to create the initial `backend/` package structure and the first slice of real functionality. We used TDD to define the behavior for hashing utilities, blocks, and the blockchain (mining, validation, and safe chain replacement), then implemented the modules plus a lightweight `conftest.py` so pytest can import the new package cleanly. The existing backend tests were refreshed to reflect the new architecture, and wallet/transaction suites are temporarily skipped until those modules exist. All ledger-related tests are now green, giving me confidence to tackle networking and wallet milestones next.
