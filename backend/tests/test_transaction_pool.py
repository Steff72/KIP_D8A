from backend.blockchain.blockchain import Blockchain
from backend.wallet.transaction import Transaction, create_transaction
from backend.wallet.transaction_pool import TransactionPool
from backend.wallet.wallet import Wallet


def test_set_transaction_stores_reference():
    pool = TransactionPool()
    transaction = create_transaction(Wallet(balance=100), Wallet().address, 20)

    pool.set_transaction(transaction)

    assert pool.transaction_map[transaction.id] == transaction


def test_existing_transaction_returns_latest_for_sender():
    pool = TransactionPool()
    sender = Wallet(balance=100)
    recipient = Wallet().address
    transaction = create_transaction(sender, recipient, 30)

    pool.set_transaction(transaction)
    existing = pool.existing_transaction(sender.address)

    assert existing == transaction


def test_clear_blockchain_transactions_removes_included_ids():
    pool = TransactionPool()
    blockchain = Blockchain()
    sender = Wallet(balance=100)
    recipient = Wallet().address
    transaction = create_transaction(sender, recipient, 40)

    pool.set_transaction(transaction)
    blockchain.add_block([transaction.to_dict()], timestamp_provider=lambda: 1.0)

    pool.clear_blockchain_transactions(blockchain)

    assert transaction.id not in pool.transaction_map
