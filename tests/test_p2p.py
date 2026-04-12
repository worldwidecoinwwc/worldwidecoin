from network.node import Node
from network.p2p import broadcast_block, broadcast_transaction, encode_message, request_blocks
from core.transaction import Transaction
from core.block import Block
from wallet.wallet import Wallet


def test_encode_message():
    msg = encode_message("test", {"data": "value"})
    assert b'"type": "test"' in msg or b'"type":"test"' in msg


def test_broadcast_block_empty_peers():
    """Test broadcast to empty peer list (should not crash)"""
    block = Block(
        index=1,
        prev_hash="0",
        transactions=[],
        timestamp=1234567890,
        difficulty=1
    )

    broadcast_block([], block)


def test_broadcast_transaction_empty_peers():
    """Test broadcast to empty peer list (should not crash)"""
    tx = Transaction(
        inputs=[],
        outputs=[{"address": "alice", "amount": 1}]
    )

    broadcast_transaction([], tx)


def test_node_broadcast_callback():
    """Test that blockchain calls broadcast callback after add_block"""
    from core.blockchain import Blockchain
    from core.utxo import UTXOSet
    from storage.mempool import Mempool
    from storage.chain_store import ChainStore
    import time

    alice = Wallet()

    # Create a fresh blockchain in memory (no persistence)
    bc = Blockchain()
    
    # Clear chain and UTXO to start fresh
    bc.chain = []
    bc.utxo = UTXOSet(persistent=False)
    bc.mempool = Mempool(bc.utxo)
    
    # Create genesis
    from core.block import Block
    genesis = Block(0, "0", [], time.time(), 1)
    genesis.mine()
    bc.chain.append(genesis)

    broadcast_called = []

    def mock_broadcast(block):
        broadcast_called.append(block)

    bc.broadcast_callback = mock_broadcast

    # Create and mine a block
    block = bc.create_block(miner_address=alice.address, reward=1)
    block.mine()

    # Add block should trigger broadcast callback
    bc.add_block(block)

    assert len(broadcast_called) == 1
    assert broadcast_called[0].index == 1


def test_node_connect_peer():
    """Test registering peer addresses"""
    node = Node(port=9999)

    node.connect_peer("127.0.0.1", 8333)
    node.connect_peer("127.0.0.1", 8334)

    assert len(node.peers) == 2
    assert ("127.0.0.1", 8333) in node.peers


def test_node_chain_sync_scenario():
    """Test chain sync: two nodes exchange blocks"""
    from core.blockchain import Blockchain
    from core.utxo import UTXOSet
    from storage.mempool import Mempool
    import time

    alice = Wallet()

    # Node 1: has 3 blocks
    bc1 = Blockchain()
    bc1.chain = []
    bc1.utxo = UTXOSet(persistent=False)
    bc1.mempool = Mempool(bc1.utxo)

    genesis = Block(0, "0", [], time.time(), 1)
    genesis.mine()
    bc1.chain.append(genesis)

    for i in range(1, 3):
        block = bc1.create_block(miner_address=alice.address, reward=1)
        block.mine()
        bc1.add_block(block)

    # Node 2: only has genesis (same genesis as Node 1)
    bc2 = Blockchain()
    bc2.chain = []
    bc2.utxo = UTXOSet(persistent=False)
    bc2.mempool = Mempool(bc2.utxo)

    # Use same genesis block from bc1
    bc2.chain.append(genesis)

    assert len(bc1.chain) == 3
    assert len(bc2.chain) == 1

    # Simulate block sync: copy blocks from bc1 to bc2
    for i in range(1, len(bc1.chain)):
        block = bc1.chain[i]
        bc2.add_block(block)

    assert len(bc2.chain) == 3
    assert bc1.chain[-1].hash == bc2.chain[-1].hash


def test_encode_chain_info():
    """Test encoding chain info message"""
    msg = encode_message("info", {
        "height": 5,
        "tip_hash": "abc123"
    })

    assert b"info" in msg
    assert b"height" in msg
    assert b"5" in msg

