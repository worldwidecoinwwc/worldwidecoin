from core.transaction import Transaction
from wallet.wallet import Wallet
from storage.mempool import Mempool
from core.utxo import UTXOSet


def test_mempool_add_coinbase():
    utxo = UTXOSet(persistent=False)
    mempool = Mempool(utxo)

    tx = Transaction(
        inputs=[],
        outputs=[{"address": "miner", "amount": 1}]
    )

    mempool.add_transaction(tx)
    assert len(mempool.transactions) == 1


def test_mempool_reject_invalid_signature():
    utxo = UTXOSet(persistent=False)
    mempool = Mempool(utxo)

    tx = Transaction(
        inputs=[{"txid": "fake", "index": 0, "amount": 1}],
        outputs=[{"address": "bob", "amount": 1}]
    )

    # No signature
    try:
        mempool.add_transaction(tx)
        assert False, "Should reject unsigned tx"
    except Exception as e:
        assert "signature" in str(e).lower()


def test_mempool_reject_invalid_utxo():
    utxo = UTXOSet(persistent=False)
    mempool = Mempool(utxo)

    alice = Wallet()

    tx = Transaction(
        inputs=[{"txid": "nonexistent", "index": 0, "amount": 10}],
        outputs=[{"address": "bob", "amount": 10}]
    )

    tx.signature = alice.sign(tx.to_dict())
    tx.public_key = alice.public_key.to_string().hex()

    try:
        mempool.add_transaction(tx)
        assert False, "Should reject tx with missing UTXO"
    except Exception as e:
        assert "utxo" in str(e).lower()


def test_mempool_add_valid_transaction():
    utxo = UTXOSet(persistent=False)
    mempool = Mempool(utxo)

    alice = Wallet()

    # Add a UTXO owned by alice
    utxo.add_utxo("tx1", 0, alice.address, 10)

    tx = Transaction(
        inputs=[{"txid": "tx1", "index": 0, "amount": 10}],
        outputs=[{"address": "bob", "amount": 9}]
    )

    tx.signature = alice.sign(tx.to_dict())
    tx.public_key = alice.public_key.to_string().hex()

    mempool.add_transaction(tx)
    assert len(mempool.transactions) == 1