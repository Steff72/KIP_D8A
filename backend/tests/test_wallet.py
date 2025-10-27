import pytest

from backend.wallet.wallet import Wallet, verify_signature


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
