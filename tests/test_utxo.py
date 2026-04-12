from core.utxo import UTXOSet


def test_utxo_add_spend():

    utxo = UTXOSet(persistent=False)

    utxo.add_utxo("tx1", 0, "alice", 10)

    assert len(utxo.utxos) == 1

    utxo.spend_utxo("tx1", 0)

    assert len(utxo.utxos) == 0


def test_utxo_validate_transaction():

    from core.transaction import Transaction

    utxo = UTXOSet(persistent=False)
    utxo.add_utxo("tx1", 0, "alice", 10)

    tx = Transaction(
        inputs=[{"txid": "tx1", "index": 0, "amount": 10}],
        outputs=[{"address": "bob", "amount": 9}]
    )

    assert utxo.validate_transaction(tx)


def test_utxo_reject_missing_input():

    from core.transaction import Transaction

    utxo = UTXOSet(persistent=False)

    tx = Transaction(
        inputs=[{"txid": "tx1", "index": 0, "amount": 10}],
        outputs=[{"address": "bob", "amount": 10}]
    )

    assert not utxo.validate_transaction(tx)