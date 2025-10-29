import pytest

from backend import config
from backend.wallet.transaction import (
    Transaction,
    create_reward_transaction,
    create_transaction,
    is_valid_transaction,
)
from backend.wallet.wallet import Wallet


def test_create_transaction_generates_outputs_and_input():
    sender = Wallet(balance=100)
    recipient_address = Wallet().address

    transaction = create_transaction(sender, recipient_address, 25)

    assert transaction.output[recipient_address] == 25
    assert transaction.output[sender.address] == 75
    assert transaction.input["address"] == sender.address
    assert transaction.input["amount"] == 100
    assert "signature" in transaction.input


def test_transaction_update_adds_recipient_and_resigns():
    sender = Wallet(balance=100)
    recipient = Wallet().address
    transaction = create_transaction(sender, recipient, 40)

    new_recipient = Wallet().address
    transaction.update(sender, new_recipient, 10)

    assert transaction.output[new_recipient] == 10
    assert transaction.output[sender.address] == 50
    assert transaction.input["address"] == sender.address
    assert "signature" in transaction.input
    assert transaction.input["amount"] == sender.balance


def test_is_valid_transaction_accepts_legitimate_transaction():
    sender = Wallet(balance=100)
    recipient = Wallet().address
    transaction = create_transaction(sender, recipient, 30)

    assert is_valid_transaction(transaction) is True


def test_is_valid_transaction_rejects_excessive_amount():
    sender = Wallet(balance=30)
    recipient = Wallet().address
    transaction = create_transaction(sender, recipient, 25)

    transaction.output[recipient] = 40  # tamper recipient amount

    with pytest.raises(ValueError, match="outputs do not match input amount"):
        is_valid_transaction(transaction)


def test_is_valid_transaction_rejects_bad_signature():
    sender = Wallet(balance=60)
    recipient = Wallet().address
    transaction = create_transaction(sender, recipient, 20)

    forged_wallet = Wallet()
    transaction.input["signature"] = forged_wallet.sign(transaction.output)

    with pytest.raises(ValueError, match="Invalid signature"):
        is_valid_transaction(transaction)


def test_transaction_serialization_round_trip():
    sender = Wallet(balance=70)
    recipient = Wallet().address
    transaction = create_transaction(sender, recipient, 15)

    restored = Transaction.from_dict(transaction.to_dict())
    assert restored.output == transaction.output
    assert restored.input == transaction.input


def test_create_reward_transaction_targets_miner():
    miner = Wallet()

    reward = create_reward_transaction(miner)

    assert reward.output[miner.address] == config.MINING_REWARD_AMOUNT
    assert reward.input["address"] == config.MINING_REWARD_ADDRESS
    assert reward.input["amount"] == config.MINING_REWARD_AMOUNT
    assert is_valid_transaction(reward) is True


def test_invalid_reward_transaction_is_rejected():
    miner = Wallet()
    reward = create_reward_transaction(miner)

    reward.output[miner.address] = config.MINING_REWARD_AMOUNT + 1

    with pytest.raises(ValueError, match="Mining reward amount is invalid"):
        is_valid_transaction(reward)
