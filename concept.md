# D8A Coin - Technical Concept & Specification

## Project Overview and Objectives

**Project Name:** D8A Coin (pronounced “Data Coin”) – a miniature blockchain-powered cryptocurrency system developed for the KIP (AI-assisted Programming) module. The project’s primary objective is to design and implement a fully functional mini-blockchain network from scratch, leveraging an AI development assistant (**Antigravity**) to aid in writing and maintaining the codebase. D8A Coin serves as an educational exercise in blockchain and distributed systems, demonstrating how a cryptocurrency can function at a small scale.

**Objectives:**

*   **Educational Blockchain Prototype:** Build a simplified blockchain that imitates the core features of cryptocurrencies like Bitcoin (chain of blocks, proof-of-work mining, dynamic difficulty, transactions, wallets, and cryptographic signatures).
*   **AI-Assisted Development:** Utilize **Antigravity** (an AI coding assistant) throughout the development process to accelerate coding, enforce good practices (like TDD and clean code), and document the project. Antigravity is treated as a “pair programmer,” aiding in code generation, refactoring, and documentation updates.
*   **Full-Stack Integration:** Develop both a backend (Python + Flask) and a frontend (React + Vite) to create a complete application. The backend handles the blockchain logic and networking, while the frontend provides a user interface for interactions (viewing the chain, creating transactions, initiating mining, etc.).
*   **Peer-to-Peer Network:** Implement a decentralized communication layer using PubNub (a publish/subscribe messaging service) to allow multiple node instances to broadcast and synchronize blockchain data (new blocks and transactions) in real time without a central server.
*   **Test-Driven Development & Reliability:** Adopt a test-driven development (TDD) approach from the start. Write unit tests for each component (block, blockchain, transactions, wallet, etc.) before implementation to ensure correctness. This ensures the system is reliable and that critical blockchain invariants (like valid hashes, signature verification) are upheld.
*   **Documentation & Reflective Process:** Maintain thorough documentation, including this technical concept specification and an experience log capturing development insights.

## System Architecture

The D8A Coin system is designed with a modular architecture split into distinct layers and components that work together:

### Backend (Flask API)

The core of D8A Coin runs on a Python backend using the Flask framework. Each instance of the backend represents a blockchain node in the network.

*   **Blockchain Core:** Modules for hashing utilities (`backend/util/crypto_hash.py`, `backend/util/hex_to_binary.py`) and core domain objects (`backend/blockchain/block.py`, `backend/blockchain/blockchain.py`). Blocks encapsulate proof-of-work metadata and expose helpers for deterministic hashing, mining, and validation.
*   **Wallet & Transaction Layer:** Modules (`backend/wallet/wallet.py`, `backend/wallet/transaction.py`, `backend/wallet/transaction_pool.py`) implement SECP256k1 wallets with deterministic addresses, signing helpers, a transaction pool, and transaction objects.
*   **API Layer:** A Flask app factory (`backend/app.py`) exposes the chain via REST.
    *   `GET /api/chain`: Returns the serialized ledger.
    *   `GET /api/wallet/info`: Reports the node wallet’s address and balance.
    *   `POST /api/blocks`: Mines the next block.
    *   `POST /api/transact`: Creates a new transaction.
*   **Networking:** `backend/pubsub.py` wraps PubNub’s SDK to broadcast mined blocks and pending transactions. `backend/peer.py` allows new nodes to sync by querying known peers.

### Frontend (React Application)

The user interface is built in React using Vite, allowing users to interact with the blockchain in real-time.

*   **Features:**
    *   **Dashboard:** Displays wallet info, transaction pool, and the blockchain history.
    *   **Real-time Updates:** Uses polling to automatically refresh data when new blocks or transactions occur.
    *   **Interactivity:** Users can create transactions and mine blocks directly from the UI.
    *   **Aesthetics:** Features a custom "Tech Circuit" logo, a clean dark-themed design, and user-friendly elements like copyable addresses.
*   **Communication:** The frontend communicates with the Flask API via HTTP requests.

### Peer-to-Peer Network (PubNub)

To enable a decentralized network, D8A Coin uses PubNub. Each node subscribes to specific channels:
*   **BLOCK:** For broadcasting newly mined blocks.
*   **TRANSACTION:** For sharing pending transactions.
*   **CHAIN:** For synchronizing the full ledger.

## Data Flow and API Design

### 1. Creating a Transaction
1.  **User Action:** User initiates a transaction via the frontend.
2.  **Frontend -> Backend:** `POST /api/transact` with recipient and amount.
3.  **Backend Processing:**
    *   Verifies balance.
    *   Creates a `Transaction` object with a digital signature.
    *   Adds to local `TransactionPool`.
    *   Broadcasts via PubNub on `TRANSACTION` channel.
4.  **Network Propagation:** Peers receive the transaction and add it to their pools.

### 2. Mining a Block
1.  **Trigger:** User clicks "Mine Block" (or automated trigger).
2.  **Backend Mining:** `POST /api/blocks`.
    *   Gathers pending transactions from the pool.
    *   Adds a mining reward transaction.
    *   Mines a new block (Proof-of-Work).
    *   Appends to local chain and clears confirmed transactions from the pool.
    *   Broadcasts the new block on `BLOCK` channel.
3.  **Network Reception:** Peers validate the block and append it to their chains.

## OOP Class Structure

*   **Block:** Represents a single block. Attributes: `timestamp`, `last_hash`, `hash`, `data`, `difficulty`, `nonce`. Methods: `mine_block`, `is_valid_block`.
*   **Blockchain:** Manages the ledger. Attributes: `chain`. Methods: `add_block`, `replace_chain`, `is_valid_chain`.
*   **Transaction:** Represents a transfer of value. Attributes: `id`, `output`, `input`. Methods: `update`, `is_valid_transaction`.
*   **Wallet:** Manages keys and signing. Attributes: `balance`, `public_key`, `private_key`. Methods: `sign`, `verify`.
*   **TransactionPool:** Manages pending transactions. Methods: `set_transaction`, `clear_blockchain_transactions`.
*   **PubSub:** Handles network messaging.

## Testing Strategy

TDD was a core strategy. We maintain a comprehensive suite of Pytest unit tests covering:
*   **Utility Functions:** Hashing and binary conversion.
*   **Block & Blockchain:** Mining logic, validation, difficulty adjustment.
*   **Wallet & Transaction:** Signature verification, balance checks, transaction updates.
*   **TransactionPool:** Adding and clearing transactions.

## Milestones and Versioning

*   **Milestone 1: Blockchain Core (v0.1)** - Completed. Basic blockchain with mining.
*   **Milestone 2: Cryptocurrency Transactions (v0.2)** - Completed. Wallets and transactions.
*   **Milestone 3: Transaction Pool & Mining (v0.3)** - Completed. Pooling and mining rewards.
*   **Milestone 4: Networking (v0.4)** - Completed. PubNub integration.
*   **Milestone 5: Frontend UI (v0.5)** - Completed. React dashboard with auto-refresh and polished UI.
*   **Milestone 6: Polish & Refinement (v1.0)** - Current State. Final refinements, logo updates, and cleanup.

## Version Control

We use Git for version control with atomic commits. Antigravity's contributions are reviewed and integrated into the codebase.
