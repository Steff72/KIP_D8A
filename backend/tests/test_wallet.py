import pytest

from backend import config
from backend.blockchain.blockchain import Blockchain
from backend.wallet.transaction import create_reward_transaction, create_transaction
from backend.wallet.wallet import Wallet, calculate_balance, verify_signature


def test_wallet_signs_and_verifies_messages():
    wallet = Wallet()
    message = {"amount": 10}
    signature = wallet.sign(message)

    assert verify_signature(wallet.public_key, message, signature) is True


def test_wallet_rejects_invalid_signature():
    wallet = Wallet()
    message = {"amount": 5}
    signature = wallet.sign(message)
    other_wallet = Wallet()

    assert verify_signature(other_wallet.public_key, message, signature) is False


def test_calculate_balance_accounts_for_transactions_and_rewards():
    blockchain = Blockchain()
    miner = Wallet(balance=100)
    recipient = Wallet()

    payment = create_transaction(miner, recipient.address, 30)
    reward = create_reward_transaction(miner)
    blockchain.add_block([payment.to_dict(), reward.to_dict()], timestamp_provider=lambda: 1.0)

    assert miner.calculate_balance(blockchain) == config.STARTING_BALANCE - 30 + config.MINING_REWARD_AMOUNT
    assert calculate_balance(blockchain, recipient.address) == config.STARTING_BALANCE + 30
