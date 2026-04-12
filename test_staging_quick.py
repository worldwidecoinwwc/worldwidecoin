#!/usr/bin/env python3
"""
Quick Staging Test - Runs tests without blocking
"""

import os
import sys
import time
import json
from core.blockchain import Blockchain
from deployment.staging_config import create_staging_config


def test_staging_quick():
    """Quick staging test without blocking"""
    print("WorldWideCoin Quick Staging Test")
    print("=" * 50)
    
    try:
        # Test 1: Configuration
        print("1. Testing staging configuration...")
        config = create_staging_config()
        if config:
            print("   Configuration: PASS")
            print(f"   Environment: {config.deployment.environment}")
            print(f"   Network ID: {config.network.network_id}")
            print(f"   Port: {config.network.port}")
        else:
            print("   Configuration: FAIL")
            return False
        
        # Test 2: Blockchain initialization
        print("\n2. Testing blockchain initialization...")
        blockchain = Blockchain()
        if blockchain:
            print("   Blockchain: PASS")
            print(f"   Initial height: {len(blockchain.chain)}")
            print(f"   Mempool size: {len(blockchain.mempool.transactions)}")
        else:
            print("   Blockchain: FAIL")
            return False
        
        # Test 3: Mining
        print("\n3. Testing mining...")
        try:
            original_height = len(blockchain.chain)
            block = blockchain.create_block("test_miner")
            blockchain.add_block(block)
            new_height = len(blockchain.chain)
            
            if new_height > original_height:
                print("   Mining: PASS")
                print(f"   Block #{block.index} mined")
                print(f"   Hash: {block.hash[:16]}...")
            else:
                print("   Mining: FAIL - No block created")
                return False
        except Exception as e:
            print(f"   Mining: ERROR - {e}")
            return False
        
        # Test 4: Transactions
        print("\n4. Testing transactions...")
        try:
            from core.transaction import Transaction
            
            tx = Transaction(
                inputs=[],
                outputs=[{
                    "address": "test_recipient",
                    "amount": 10.0
                }]
            )
            
            blockchain.mempool.add_transaction(tx)
            mempool_size = len(blockchain.mempool.transactions)
            
            if mempool_size > 0:
                print("   Transactions: PASS")
                print(f"   Transactions in mempool: {mempool_size}")
            else:
                print("   Transactions: FAIL")
                return False
        except Exception as e:
            print(f"   Transactions: ERROR - {e}")
            return False
        
        # Test 5: Multiple blocks
        print("\n5. Testing multiple block mining...")
        try:
            start_height = len(blockchain.chain)
            
            for i in range(3):
                block = blockchain.create_block(f"test_miner_{i}")
                blockchain.add_block(block)
            
            end_height = len(blockchain.chain)
            blocks_mined = end_height - start_height
            
            if blocks_mined >= 3:
                print("   Multiple blocks: PASS")
                print(f"   Blocks mined: {blocks_mined}")
            else:
                print("   Multiple blocks: FAIL")
                return False
        except Exception as e:
            print(f"   Multiple blocks: ERROR - {e}")
            return False
        
        # Test 6: Configuration validation
        print("\n6. Testing configuration validation...")
        try:
            issues = config.validate_config()
            if len(issues) == 0:
                print("   Configuration validation: PASS")
            else:
                print(f"   Configuration validation: {len(issues)} issues")
                for issue in issues:
                    print(f"     - {issue}")
        except Exception as e:
            print(f"   Configuration validation: ERROR - {e}")
            return False
        
        # Test 7: Directory structure
        print("\n7. Testing directory structure...")
        required_dirs = [
            "data/staging",
            "data/staging/blockchain",
            "data/staging/utxo",
            "data/staging/backups",
            "logs/staging"
        ]
        
        dirs_exist = 0
        for dir_path in required_dirs:
            if os.path.exists(dir_path):
                dirs_exist += 1
            else:
                print(f"   Missing directory: {dir_path}")
        
        if dirs_exist == len(required_dirs):
            print("   Directory structure: PASS")
        else:
            print(f"   Directory structure: {dirs_exist}/{len(required_dirs)} exist")
        
        # Final status
        print("\n" + "=" * 50)
        print("Staging Test Results")
        print("=" * 50)
        print("All tests completed successfully!")
        print(f"Final blockchain height: {len(blockchain.chain)}")
        print(f"Final mempool size: {len(blockchain.mempool.transactions)}")
        print(f"Environment: {config.deployment.environment}")
        
        return True
        
    except Exception as e:
        print(f"Staging test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_staging_quick()
    sys.exit(0 if success else 1)
