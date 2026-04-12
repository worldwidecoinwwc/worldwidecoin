from wallet.wallet import Wallet
from core.transaction import Transaction


def test_transaction_signing():

    alice = Wallet()
    bob = Wallet()

    tx = Transaction(
        inputs=[],
        outputs=[{"address": bob.address, "amount": 5}]
    )

    signature = alice.sign(tx.to_dict())

    tx.signature = signature
    tx.public_key = alice.public_key.to_string().hex()

    assert signature is not None