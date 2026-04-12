#!/usr/bin/env python3
"""
Phase 2 Transaction Validation Testing Suite
Tests UTXO validation, block validation, mempool filtering, script validation, and fee calculation
"""

import time
import json
import hashlib
from decimal import Decimal
from core.validation import TransactionValidator, ValidationError, create_transaction_validator
from core.block_validation import BlockValidator, BlockValidationError, create_block_validator
from core.mempool_validator import MempoolValidator, create_mempool_validator
from core.script import Script, ScriptBuilder, create_p2pkh_script, verify_script
from core.fees import FeeCalculator, FeeEstimator, FeeManager, create_fee_manager
from core.transaction import Transaction
from core.blockchain import Blockchain
from storage.utxo import UTXOSet
from ecdsa import SigningKey, SECP256k1


def test_utxo_validation():
    """Test 1: UTXO transaction validation"""
    print("=== TEST 1: UTXO Transaction Validation ===")
    
    # Create blockchain and UTXO set
    blockchain = Blockchain()
    utxo_set = blockchain.utxo
    
    # Create validator
    validator = TransactionValidator(utxo_set)
    
    # Create test transaction
    tx = Transaction(
        inputs=[],
        outputs=[{
            "address": "test_recipient",
            "amount": 10.0
        }]
    )
    
    # Add signature and public key for validation
    key = SigningKey.generate(curve=SECP256k1)
    tx_data = json.dumps(tx.to_dict(), sort_keys=True).encode()
    tx.signature = key.sign_digest(hashlib.sha256(tx_data).digest()).hex()
    tx.public_key = key.get_verifying_key().to_string().hex()
    
    # Test validation (should fail - no inputs)
    try:
        is_valid, message = validator.validate_transaction_for_mempool(tx)
        print(f"Empty transaction validation: {'PASS' if not is_valid else 'FAIL'}")
        print(f"  Message: {message}")
    except Exception as e:
        print(f"Empty transaction validation: ERROR - {e}")
    
    # Create a valid transaction with inputs
    # First, create a UTXO by mining a block
    block = blockchain.create_block("test_miner")
    blockchain.add_block(block)
    
    # Get the coinbase UTXO
    coinbase_tx = block.transactions[0]
    utxo_key = f"{coinbase_tx.calculate_hash()}:0"
    
    # Create transaction that spends the coinbase
    spend_tx = Transaction(
        inputs=[{
            "txid": coinbase_tx.calculate_hash(),
            "vout": 0
        }],
        outputs=[{
            "address": "test_recipient",
            "amount": 5.0
        }]
    )
    
    # Add signature
    spend_tx_data = json.dumps(spend_tx.to_dict(), sort_keys=True).encode()
    spend_tx.signature = key.sign_digest(hashlib.sha256(spend_tx_data).digest()).hex()
    spend_tx.public_key = key.get_verifying_key().to_string().hex()
    
    # Test validation (should pass)
    try:
        is_valid, message = validator.validate_transaction_for_mempool(spend_tx)
        print(f"Valid transaction validation: {'PASS' if is_valid else 'FAIL'}")
        print(f"  Message: {message}")
    except Exception as e:
        print(f"Valid transaction validation: ERROR - {e}")
    
    # Test fee calculation
    fee = validator.utxo_validator.get_transaction_fee(spend_tx)
    print(f"Transaction fee: {fee}")
    
    # Test transaction size estimation
    size = validator.utxo_validator.get_transaction_size(spend_tx)
    print(f"Transaction size: {size} bytes")
    
    print("UTXO validation test completed")
    print()


def test_script_validation():
    """Test 2: Script validation system"""
    print("=== TEST 2: Script Validation System ===")
    
    # Create script interpreter
    script = Script()
    
    # Test basic stack operations
    print("Testing stack operations...")
    
    # Test OP_DUP
    script.stack.push(b"test")
    original_size = script.stack.size()
    script._execute_opcode(0x76, b'', 0)  # OP_DUP
    print(f"OP_DUP: {'PASS' if script.stack.size() == original_size + 1 else 'FAIL'}")
    
    # Test OP_DROP
    script._execute_opcode(0x75, b'', 0)  # OP_DROP
    print(f"OP_DROP: {'PASS' if script.stack.size() == original_size else 'FAIL'}")
    
    # Test arithmetic operations
    print("Testing arithmetic operations...")
    
    script.stack.push(script._int_to_bytes(5))
    script.stack.push(script._int_to_bytes(3))
    script._execute_opcode(0x93, b'', 0)  # OP_ADD
    result = script.stack.pop()
    expected = script._int_to_bytes(8)
    print(f"OP_ADD: {'PASS' if result == expected else 'FAIL'}")
    
    # Test crypto operations
    print("Testing crypto operations...")
    
    # Test OP_SHA256
    test_data = b"Hello World"
    script.stack.push(test_data)
    script._execute_opcode(0xa8, b'', 0)  # OP_SHA256
    hash_result = script.stack.pop()
    expected_hash = hashlib.sha256(test_data).digest()
    print(f"OP_SHA256: {'PASS' if hash_result == expected_hash else 'FAIL'}")
    
    # Test script building
    print("Testing script building...")
    
    # Create P2PKH script
    pubkey = "02a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"
    p2pkh_script = create_p2pkh_script(pubkey)
    print(f"P2PKH script created: {len(p2pkh_script)} bytes")
    
    # Test script execution with signature verification
    print("Testing signature verification...")
    
    key = SigningKey.generate(curve=SECP256k1)
    message = b"test message"
    signature = key.sign_digest(message).hex()
    pubkey_hex = key.get_verifying_key().to_string().hex()
    
    # Create simple script: <signature> <pubkey> OP_CHECKSIG
    script_sig = bytes.fromhex(signature + pubkey_hex)
    script_pubkey = ScriptBuilder.p2pk(key.get_verifying_key().to_string())
    
    # Verify script
    tx_data = {"message": message.hex()}
    is_valid = script.execute(script_sig, script_pubkey, tx_data)
    print(f"Signature verification: {'PASS' if is_valid else 'FAIL'}")
    
    print("Script validation test completed")
    print()


def test_block_validation():
    """Test 3: Block validation rules"""
    print("=== TEST 3: Block Validation Rules ===")
    
    # Create blockchain and validator
    blockchain = Blockchain()
    utxo_set = blockchain.utxo
    validator = BlockValidator(blockchain, utxo_set)
    
    # Test genesis block validation
    print("Testing genesis block validation...")
    
    genesis_block = blockchain.chain[0] if blockchain.chain else blockchain.create_block("genesis")
    
    try:
        validator.validate_block(genesis_block)
        print("Genesis block validation: PASS")
    except BlockValidationError as e:
        print(f"Genesis block validation: FAIL - {e.message}")
    except Exception as e:
        print(f"Genesis block validation: ERROR - {e}")
    
    # Test regular block validation
    print("Testing regular block validation...")
    
    # Mine a new block
    new_block = blockchain.create_block("test_miner")
    blockchain.add_block(new_block)
    
    try:
        validator.validate_block(new_block)
        print("Regular block validation: PASS")
    except BlockValidationError as e:
        print(f"Regular block validation: FAIL - {e.message}")
    except Exception as e:
        print(f"Regular block validation: ERROR - {e}")
    
    # Test invalid block (wrong previous hash)
    print("Testing invalid block validation...")
    
    invalid_block = blockchain.create_block("test_miner")
    invalid_block.prev_hash = "0" * 64  # Invalid previous hash
    
    try:
        validator.validate_block(invalid_block)
        print("Invalid block validation: FAIL - Should have failed")
    except BlockValidationError as e:
        print(f"Invalid block validation: PASS - {e.message}")
    except Exception as e:
        print(f"Invalid block validation: ERROR - {e}")
    
    # Test Merkle tree validation
    print("Testing Merkle tree validation...")
    
    tx_hashes = [tx.calculate_hash() for tx in new_block.transactions]
    merkle_root = validator._calculate_merkle_root(tx_hashes)
    
    if hasattr(new_block, 'merkle_root') and new_block.merkle_root:
        print(f"Merkle tree validation: {'PASS' if merkle_root == new_block.merkle_root else 'FAIL'}")
    else:
        print("Merkle tree validation: SKIPPED - No merkle_root in block")
    
    print("Block validation test completed")
    print()


def test_mempool_filtering():
    """Test 4: Mempool filtering system"""
    print("=== TEST 4: Mempool Filtering System ===")
    
    # Create blockchain and mempool validator
    blockchain = Blockchain()
    utxo_set = blockchain.utxo
    mempool_validator = create_mempool_validator(utxo_set, max_size=100, max_bytes=1000000)
    
    # Mine a block to create UTXOs
    block = blockchain.create_block("test_miner")
    blockchain.add_block(block)
    
    # Create test transaction
    coinbase_tx = block.transactions[0]
    key = SigningKey.generate(curve=SECP256k1)
    
    tx = Transaction(
        inputs=[{
            "txid": coinbase_tx.calculate_hash(),
            "vout": 0
        }],
        outputs=[{
            "address": "test_recipient",
            "amount": 5.0
        }]
    )
    
    tx_data = json.dumps(tx.to_dict(), sort_keys=True).encode()
    tx.signature = key.sign_digest(hashlib.sha256(tx_data).digest()).hex()
    tx.public_key = key.get_verifying_key().to_string().hex()
    
    # Test mempool validation
    print("Testing mempool validation...")
    
    is_valid, message = mempool_validator.validate_for_mempool(tx)
    print(f"Mempool validation: {'PASS' if is_valid else 'FAIL'}")
    print(f"  Message: {message}")
    
    # Test adding to mempool
    print("Testing mempool addition...")
    
    added, message = mempool_validator.add_transaction(tx)
    print(f"Mempool addition: {'PASS' if added else 'FAIL'}")
    print(f"  Message: {message}")
    
    # Test mempool info
    mempool_info = mempool_validator.get_mempool_info()
    print(f"Mempool size: {mempool_info['size']}")
    print(f"Mempool bytes: {mempool_info['bytes']}")
    print(f"Total fees: {mempool_info['total_fees']}")
    
    # Test double spend detection
    print("Testing double spend detection...")
    
    # Create another transaction spending the same UTXO
    double_spend_tx = Transaction(
        inputs=[{
            "txid": coinbase_tx.calculate_hash(),
            "vout": 0
        }],
        outputs=[{
            "address": "another_recipient",
            "amount": 3.0
        }]
    )
    
    double_spend_tx_data = json.dumps(double_spend_tx.to_dict(), sort_keys=True).encode()
    double_spend_tx.signature = key.sign_digest(hashlib.sha256(double_spend_tx_data).digest()).hex()
    double_spend_tx.public_key = key.get_verifying_key().to_string().hex()
    
    is_valid, message = mempool_validator.validate_for_mempool(double_spend_tx)
    print(f"Double spend detection: {'PASS' if not is_valid else 'FAIL'}")
    print(f"  Message: {message}")
    
    # Test transaction selection for block
    print("Testing transaction selection for block...")
    
    block_txs = mempool_validator.get_transactions_for_block(max_tx_count=10, max_block_size=1000000)
    print(f"Selected transactions: {len(block_txs)}")
    
    print("Mempool filtering test completed")
    print()


def test_fee_calculation():
    """Test 5: Transaction fee calculation"""
    print("=== TEST 5: Transaction Fee Calculation ===")
    
    # Create fee manager
    fee_manager = create_fee_manager()
    
    # Test basic fee calculation
    print("Testing basic fee calculation...")
    
    tx_size = 250
    inputs_count = 2
    outputs_count = 2
    
    low_fee = fee_manager.calculate_transaction_fee(tx_size, inputs_count, outputs_count, 'low')
    medium_fee = fee_manager.calculate_transaction_fee(tx_size, inputs_count, outputs_count, 'medium')
    high_fee = fee_manager.calculate_transaction_fee(tx_size, inputs_count, outputs_count, 'high')
    
    print(f"Low priority fee: {low_fee}")
    print(f"Medium priority fee: {medium_fee}")
    print(f"High priority fee: {high_fee}")
    
    # Test fee rate calculation
    print("Testing fee rate calculation...")
    
    fee_rate = fee_manager.calculator.calculate_fee_rate(tx_size, medium_fee)
    print(f"Fee rate: {fee_rate} WWC per byte")
    
    # Test fee estimation
    print("Testing fee estimation...")
    
    # Add some fee samples
    fee_manager.add_fee_confirmation(Decimal('0.0001'), 100, 6)
    fee_manager.add_fee_confirmation(Decimal('0.00005'), 101, 12)
    fee_manager.add_fee_confirmation(Decimal('0.0002'), 102, 3)
    
    # Get fee estimates
    estimates = fee_manager.get_fee_recommendations(tx_size)
    print(f"Low priority recommendation: {estimates['low']['total_fee']} WWC")
    print(f"Medium priority recommendation: {estimates['medium']['total_fee']} WWC")
    print(f"High priority recommendation: {estimates['high']['total_fee']} WWC")
    
    # Test network condition updates
    print("Testing network condition updates...")
    
    fee_manager.update_network_conditions(mempool_size=500, max_mempool_size=1000, average_block_time=300)
    print(f"Updated mempool pressure factor: {fee_manager.calculator.mempool_pressure_factor}")
    print(f"Updated network congestion factor: {fee_manager.calculator.network_congestion_factor}")
    
    # Test fee statistics
    stats = fee_manager.get_statistics()
    print(f"Total fees collected: {stats['manager_stats']['total_fees_collected']}")
    print(f"Average fee rate: {stats['manager_stats']['average_fee_rate']}")
    
    print("Fee calculation test completed")
    print()


def test_integration():
    """Test 6: Integration tests"""
    print("=== TEST 6: Integration Tests ===")
    
    # Create complete system
    blockchain = Blockchain()
    utxo_set = blockchain.utxo
    tx_validator = create_transaction_validator(utxo_set)
    block_validator = create_block_validator(blockchain, utxo_set)
    mempool_validator = create_mempool_validator(utxo_set)
    fee_manager = create_fee_manager()
    
    # Mine initial block for UTXOs
    print("Mining initial block...")
    block = blockchain.create_block("test_miner")
    blockchain.add_block(block)
    
    # Create multiple transactions
    print("Creating multiple transactions...")
    
    key = SigningKey.generate(curve=SECP256k1)
    transactions = []
    
    for i in range(3):
        tx = Transaction(
            inputs=[{
                "txid": block.transactions[0].calculate_hash(),
                "vout": 0
            }],
            outputs=[{
                "address": f"recipient_{i}",
                "amount": Decimal(str(10.0 - i * 2))
            }]
        )
        
        tx_data = json.dumps(tx.to_dict(), sort_keys=True).encode()
        tx.signature = key.sign_digest(hashlib.sha256(tx_data).digest()).hex()
        tx.public_key = key.get_verifying_key().to_string().hex()
        
        transactions.append(tx)
    
    # Test transaction validation and mempool addition
    print("Testing transaction validation and mempool addition...")
    
    for i, tx in enumerate(transactions):
        # Validate transaction
        is_valid, message = tx_validator.validate_transaction_for_mempool(tx)
        print(f"  Transaction {i} validation: {'PASS' if is_valid else 'FAIL'}")
        
        # Add to mempool
        if is_valid:
            added, message = mempool_validator.add_transaction(tx)
            print(f"  Transaction {i} mempool addition: {'PASS' if added else 'FAIL'}")
    
    # Create block with mempool transactions
    print("Creating block with mempool transactions...")
    
    # Get transactions from mempool
    mempool_txs = mempool_validator.get_transactions_for_block()
    print(f"Selected {len(mempool_txs)} transactions from mempool")
    
    # Create new block
    new_block = blockchain.create_block("integration_test")
    
    # Replace coinbase transaction with mempool transactions
    new_block.transactions = [new_block.transactions[0]] + mempool_txs
    
    # Validate block
    try:
        block_validator.validate_block(new_block, check_transactions=True)
        print("Block validation: PASS")
        
        # Add block to blockchain
        blockchain.add_block(new_block)
        print("Block added to blockchain: PASS")
        
    except BlockValidationError as e:
        print(f"Block validation: FAIL - {e.message}")
    except Exception as e:
        print(f"Block validation: ERROR - {e}")
    
    # Test fee calculation integration
    print("Testing fee calculation integration...")
    
    for tx in mempool_txs:
        fee = fee_manager.calculate_transaction_fee(
            fee_manager.calculator.get_transaction_size(tx),
            len(tx.inputs),
            len(tx.outputs),
            'medium'
        )
        print(f"  Transaction fee: {fee}")
    
    # Test statistics
    print("Testing system statistics...")
    
    print(f"Blockchain height: {len(blockchain.chain)}")
    print(f"Mempool size: {len(mempool_validator.entries)}")
    print(f"Total fees collected: {fee_manager.total_fees_collected}")
    
    print("Integration test completed")
    print()


def main():
    """Run all Phase 2 validation tests"""
    print("WorldWideCoin Phase 2 - Transaction Validation Testing")
    print("=" * 60)
    
    tests = [
        test_utxo_validation,
        test_script_validation,
        test_block_validation,
        test_mempool_filtering,
        test_fee_calculation,
        test_integration
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(tests, 1):
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"Test {i} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        print()
    
    print("=" * 60)
    print(f"Phase 2 Validation Testing Complete!")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/(passed+failed))*100:.1f}%")
    
    if failed == 0:
        print("All tests passed! Phase 2 is ready for integration.")
    else:
        print(f"{failed} tests failed. Review and fix issues before proceeding.")


if __name__ == "__main__":
    main()
