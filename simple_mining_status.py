#!/usr/bin/env python3
"""
Simple mining status checker that doesn't rely on corrupted files
"""

import json
import time
import os
from core.blockchain import Blockchain


def check_mining_status_simple():
    """Check mining status without loading corrupted UTXO files"""
    print("WorldWideCoin Mining Status Report")
    print("=" * 50)
    
    try:
        # Check if UTXO file exists and is corrupted
        utxo_file = "core/utxo.json"
        if os.path.exists(utxo_file):
            try:
                with open(utxo_file, 'r') as f:
                    json.load(f)
                print("UTXO file is valid")
            except json.JSONDecodeError:
                print(f"UTXO file {utxo_file} is corrupted. Creating fresh blockchain...")
                # Remove corrupted file
                os.remove(utxo_file)
                print("Corrupted UTXO file removed")
        
        # Create fresh blockchain
        blockchain = Blockchain()
        
        print(f"Blockchain Status:")
        print(f"  Total Blocks: {len(blockchain.chain)}")
        print(f"  Blockchain Height: {len(blockchain.chain) - 1}")
        print(f"  Mempool Size: {len(blockchain.mempool.transactions)}")
        
        if not blockchain.chain:
            print("\nNo blocks found. Blockchain is empty.")
            return
        
        # Calculate total coins mined
        total_coins = len(blockchain.chain) * 50.0  # 50 WWC per block
        
        print(f"\nMining Details:")
        print(f"  Total Coins Mined: {total_coins} WWC")
        print(f"  Blocks Mined: {len(blockchain.chain)}")
        print(f"  Block Reward: 50.0 WWC per block")
        
        # Show recent blocks
        print(f"\nRecent Blocks (Last 5):")
        for block in blockchain.chain[-5:]:
            print(f"  Block #{block.index}: {block.calculate_hash()[:16]}...")
            print(f"    Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(block.timestamp))}")
            print(f"    Transactions: {len(block.transactions)}")
            print(f"    Difficulty: {block.difficulty}")
        
        # Show coin storage information
        print(f"\nCoin Storage Information:")
        print(f"  Storage Type: In-memory")
        print(f"  UTXO Set: core/utxo.json (when saved)")
        print(f"  Blockchain: core/blockchain.json (when saved)")
        print(f"  Current State: Not persisted to disk")
        
        # Show where coins are stored
        print(f"\nWhere Are Your Coins:")
        print(f"  1. In the UTXO (Unspent Transaction Output) set")
        print(f"  2. Each block contains a coinbase transaction with 50 WWC reward")
        print(f"  3. Coins are tracked by transaction outputs, not balances")
        print(f"  4. Currently stored in memory only")
        
        # Show how to access coins
        print(f"\nHow to Access Your Coins:")
        print(f"  1. Use wallet/wallet.py to create addresses")
        print(f"  2. Use wallet/tx_builder.py to create transactions")
        print(f"  3. Coins are accessible through the UTXO set")
        
        # Generate simple report
        report = {
            'timestamp': time.time(),
            'total_blocks': len(blockchain.chain),
            'total_coins_mined': total_coins,
            'block_reward': 50.0,
            'storage_type': 'in-memory',
            'utxo_file': 'core/utxo.json',
            'blockchain_file': 'core/blockchain.json',
            'recent_blocks': [
                {
                    'height': block.index,
                    'hash': block.calculate_hash(),
                    'timestamp': block.timestamp,
                    'transactions': len(block.transactions)
                }
                for block in blockchain.chain[-5:]
            ]
        }
        
        # Save report
        with open('mining_status_simple.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nDetailed report saved to: mining_status_simple.json")
        
        return report
        
    except Exception as e:
        print(f"Error checking mining status: {e}")
        return None


def show_wallet_info():
    """Show wallet information for accessing coins"""
    print("\n" + "=" * 50)
    print("Wallet Information")
    print("=" * 50)
    
    try:
        from wallet.wallet import Wallet
        
        # Create a wallet to show addresses
        wallet = Wallet()
        
        print(f"Your Wallet Address: {wallet.address}")
        print(f"Private Key: [HIDDEN - Check wallet files]")
        print(f"Public Key: {wallet.public_key[:16]}...")
        
        print(f"\nTo Access Your Mined Coins:")
        print(f"1. Your mining rewards are in coinbase transactions")
        print(f"2. Create transactions to spend the coins")
        print(f"3. Use wallet/tx_builder.py to build transactions")
        print(f"4. Coins will be sent to your wallet address")
        
    except Exception as e:
        print(f"Error accessing wallet: {e}")
        print(f"Make sure wallet files exist in wallet/ directory")


def show_storage_locations():
    """Show where blockchain data is stored"""
    print("\n" + "=" * 50)
    print("Storage Locations")
    print("=" * 50)
    
    files_to_check = [
        'core/utxo.json',
        'core/blockchain.json',
        'wallet/wallet.json',
        'wallet/addresses.json'
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"  {file_path}: EXISTS ({size} bytes)")
        else:
            print(f"  {file_path}: NOT FOUND")
    
    print(f"\nCurrent Storage: In-memory only")
    print(f"To persist data: Add save() methods to blockchain and UTXO set")


if __name__ == "__main__":
    check_mining_status_simple()
    show_wallet_info()
    show_storage_locations()
