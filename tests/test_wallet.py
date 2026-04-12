from wallet.wallet import Wallet


def test_wallet_creation():

    wallet = Wallet()

    assert wallet.address is not None
    assert wallet.private_key is not None
    assert wallet.public_key is not None