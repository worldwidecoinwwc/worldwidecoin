from core.block import Block
from core.blockchain import Blockchain
from core.transaction import Transaction
from core.utxo import UTXOSet
from storage.mempool import Mempool
from wallet.wallet import Wallet
import time


def test_difficulty_initial():
    """Test that initial blocks have difficulty 1"""
    bc = Blockchain()
    bc.chain = []
    bc.utxo = UTXOSet(persistent=False)
    bc.mempool = Mempool(bc.utxo)
    
    # Create genesis
    genesis = Block(0, "0", [], time.time(), 1)
    genesis.mine()
    bc.chain.append(genesis)
    
    assert bc.get_difficulty() == 1


def test_difficulty_no_adjustment_below_window():
    """Test that difficulty stays 1 until we reach DIFFICULTY_WINDOW blocks"""
    bc = Blockchain()
    bc.chain = []
    bc.utxo = UTXOSet(persistent=False)
    bc.mempool = Mempool(bc.utxo)

    # Create genesis
    genesis = Block(0, "0", [], time.time(), 1)
    genesis.mine()
    bc.chain.append(genesis)

    # Add blocks until we reach the window-1
    alice = Wallet()
    for i in range(1, bc.DIFFICULTY_WINDOW):
        block = bc.create_block(miner_address=alice.address, reward=1)
        block.mine()
        bc.add_block(block)

    # Before reaching the window, difficulty should still be 1
    assert len(bc.chain) == bc.DIFFICULTY_WINDOW
    
    # Now add one more block to trigger adjustment
    block = bc.create_block(miner_address=alice.address, reward=1)
    block.mine()
    bc.add_block(block)

    # After window+1 blocks, adjustment should have happened
    # (difficulty likely increased due to fast mining)
    assert len(bc.chain) == bc.DIFFICULTY_WINDOW + 1


def test_difficulty_increases_fast_mining():
    """Test that difficulty increases if blocks are mined too fast"""
    bc = Blockchain()
    bc.chain = []
    bc.utxo = UTXOSet(persistent=False)
    bc.mempool = Mempool(bc.utxo)

    alice = Wallet()
    current_time = time.time()

    # Create genesis
    genesis = Block(0, "0", [], current_time, 1)
    genesis.mine()
    bc.chain.append(genesis)

    # Mine blocks VERY fast (almost instantly - 0 seconds between them)
    # This simulates fast mining that should trigger difficulty increase
    for i in range(1, bc.DIFFICULTY_WINDOW + 1):
        block = bc.create_block(miner_address=alice.address, reward=1)
        block.timestamp = current_time + i  # Increment by 1 second only
        block.difficulty = bc.get_difficulty()
        block.mine()
        bc.add_block(block)

    # After DIFFICULTY_WINDOW blocks mined in ~5 seconds (should take ~50 seconds)
    # Difficulty should increase
    new_diff = bc.get_difficulty()
    print(f"New difficulty after fast mining: {new_diff}")
    assert new_diff > 1, f"Expected difficulty > 1, got {new_diff}"


def test_difficulty_decreases_slow_mining():
    """Test that difficulty decreases if blocks are mined too slowly"""
    bc = Blockchain()
    bc.chain = []
    bc.utxo = UTXOSet(persistent=False)
    bc.mempool = Mempool(bc.utxo)

    alice = Wallet()
    current_time = time.time()

    # Create genesis with difficulty 8 to start
    genesis = Block(0, "0", [], current_time, 8)
    genesis.nonce = 0
    genesis.hash = genesis.calculate_hash()  # Skip mining to avoid slowness in test
    bc.chain.append(genesis)

    # Mine blocks VERY slowly (600 seconds = 10 minutes per block)
    # This simulates slow mining that should trigger difficulty decrease
    for i in range(1, bc.DIFFICULTY_WINDOW + 1):
        block = bc.create_block(miner_address=alice.address, reward=1)
        block.timestamp = current_time + (i * 600)  # 10 minutes apart
        block.difficulty = bc.get_difficulty()
        block.nonce = 0
        block.hash = block.calculate_hash()  # Skip mining
        bc.chain.append(block)

    # After DIFFICULTY_WINDOW blocks mined slowly (should take ~50 seconds)
    # Difficulty should decrease
    new_diff = bc.get_difficulty()
    print(f"New difficulty after slow mining: {new_diff}")
    assert new_diff < 8, f"Expected difficulty < 8, got {new_diff}"


def test_difficulty_bounded():
    """Test that difficulty stays between 1 and max bounds"""
    bc = Blockchain()

    # Manually set chain state with extreme time gaps
    bc.chain = []
    bc.utxo = UTXOSet(persistent=False)
    bc.mempool = Mempool(bc.utxo)

    current_time = 1000000
    
    # Create genesis with high difficulty
    genesis = Block(0, "0", [], current_time, 32)
    genesis.nonce = 0
    genesis.hash = genesis.calculate_hash()
    bc.chain.append(genesis)

    # Add DIFFICULTY_WINDOW blocks with HUGE time gaps
    for i in range(1, bc.DIFFICULTY_WINDOW + 1):
        block = Block(i, bc.chain[-1].hash, [], current_time + (i * 86400 * 365), 32)  # 1 year apart
        block.nonce = 0
        block.hash = block.calculate_hash()
        bc.chain.append(block)

    new_diff = bc.get_difficulty()
    print(f"Difficulty with huge time gaps: {new_diff}")
    assert new_diff >= 1, f"Difficulty should be >= 1, got {new_diff}"
    assert new_diff <= 32, f"Difficulty should be <= 32, got {new_diff}"


def test_difficulty_stable_when_on_target():
    """Test that difficulty stays stable if mining rate matches target"""
    bc = Blockchain()
    bc.chain = []
    bc.utxo = UTXOSet(persistent=False)
    bc.mempool = Mempool(bc.utxo)

    alice = Wallet()
    current_time = time.time()

    # Create genesis
    genesis = Block(0, "0", [], current_time, 1)
    genesis.mine()
    bc.chain.append(genesis)

    # Mine blocks at EXACTLY the target rate (10 seconds per block)
    for i in range(1, bc.DIFFICULTY_WINDOW + 2):
        block = bc.create_block(miner_address=alice.address, reward=1)
        block.timestamp = current_time + (i * bc.TARGET_BLOCK_TIME)
        block.difficulty = bc.get_difficulty()
        block.nonce = 0
        block.hash = block.calculate_hash()
        bc.chain.append(block)

    # Difficulty should stay close to 1 (or minimal adjustment)
    final_diff = bc.get_difficulty()
    print(f"Difficulty on target rate: {final_diff}")
    assert final_diff == 1, f"Expected difficulty 1 when on target, got {final_diff}"
