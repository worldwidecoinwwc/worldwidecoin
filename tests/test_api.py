import json
import os
import time
import hashlib

from api.rest_api import WWCRestAPI
from core.block import Block
from core.transaction import Transaction


def setup_api(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    api = WWCRestAPI()
    return api, api.app.test_client()


def test_health_status_and_metrics(tmp_path, monkeypatch):
    api, client = setup_api(tmp_path, monkeypatch)

    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert 'timestamp' in data

    response = client.get('/status')
    assert response.status_code == 200
    status_data = response.get_json()
    assert status_data['chain_height'] == 1
    assert status_data['mempool_size'] == 0

    response = client.get('/metrics')
    assert response.status_code == 200
    metrics_data = response.get_json()
    assert metrics_data['chain_height'] == 1
    assert metrics_data['utxo_count'] == 0
    assert metrics_data['peer_count'] == 3


def test_utxo_and_history_endpoints(tmp_path, monkeypatch):
    api, client = setup_api(tmp_path, monkeypatch)
    address = api.wallet.address

    coinbase = Transaction(
        inputs=[],
        outputs=[
            {'address': address, 'amount': 9.5},
            {'address': api.blockchain.TREASURY_ADDRESS, 'amount': 0.5}
        ]
    )

    block = Block(
        index=api.blockchain.get_last_block().index + 1,
        prev_hash=api.blockchain.get_last_block().hash,
        transactions=[coinbase],
        timestamp=time.time(),
        difficulty=1
    )
    block.mine()
    api.blockchain.chain.append(block)
    api.blockchain.utxo.apply_transaction(coinbase, validate=False)

    response = client.get(f'/utxo/{address}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['address'] == address
    assert data['balance'] == 9.5
    assert len(data['utxos']) == 1

    response = client.get(f'/history/{address}')
    assert response.status_code == 200
    history_data = response.get_json()
    assert history_data['address'] == address
    assert len(history_data['transactions']) == 1
    assert history_data['transactions'][0]['type'] == 'received'


def test_tx_broadcast_invalid_payload(tmp_path, monkeypatch):
    _, client = setup_api(tmp_path, monkeypatch)

    response = client.post('/tx/broadcast', json={'inputs': []})
    assert response.status_code == 400
    error = response.get_json()
    assert 'Missing raw transaction fields' in error['error']


def test_tx_broadcast_accepts_valid_signed_transaction(tmp_path, monkeypatch):
    api, client = setup_api(tmp_path, monkeypatch)
    sender = api.wallet.address
    recipient = 'recipient-1234'

    api.blockchain.utxo.add_utxo('funding-tx', 0, sender, 10.0)

    tx = Transaction(
        inputs=[{"txid": 'funding-tx', 'index': 0, 'amount': 10.0}],
        outputs=[
            {'address': recipient, 'amount': 4.5},
            {'address': sender, 'amount': 5.5}
        ]
    )
    tx.signature = api.wallet.sign(tx.to_dict())
    tx.public_key = api.wallet.public_key.to_string().hex()

    response = client.post('/tx/broadcast', json={
        'inputs': tx.inputs,
        'outputs': tx.outputs,
        'signature': tx.signature,
        'public_key': tx.public_key
    })

    assert response.status_code == 200
    body = response.get_json()
    assert body['status'] == 'broadcasted'
    assert body['txid'] == tx.hash()
