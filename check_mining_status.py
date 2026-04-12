#!/usr/bin/env python3
"""
Check mining status and coin storage for WorldWideCoin
"""

import json
import time
from core.blockchain import Blockchain
from storage.utxo import UTXOSet


def check_mining_status():
    """Check mining status and coin storage"""
    print("WorldWideCoin Mining Status Report")
    print("=" * 50)
    
    try:
        # Load blockchain
        blockchain = Blockchain()
        
        print(f"Blockchain Status:")
        print(f"  Total Blocks: {len(blockchain.chain)}")
        print(f"  Blockchain Height: {len(blockchain.chain) - 1}")
        print(f"  Mempool Size: {len(blockchain.mempool.transactions)}")
        
        if not blockchain.chain:
            print("\nNo blocks found. Blockchain is empty.")
            return
        
        # Calculate total coins mined
        total_coins = 0
        coinbase_transactions = []
        
        print(f"\nMining Details:")
        for i, block in enumerate(blockchain.chain):
            # Each block has a coinbase transaction (first transaction)
            if block.transactions:
                coinbase_tx = block.transactions[0]
                coinbase_transactions.append({
                    'block_height': block.index,
                    'block_hash': block.calculate_hash(),
                    'miner_address': 'coinbase',  # Simplified
                    'reward': 50.0,  # Simplified reward
                    'timestamp': block.timestamp
                })
                total_coins += 50.0  # Simplified block reward
        
        print(f"  Total Coins Mined: {total_coins} WWC")
        print(f"  Coinbase Transactions: {len(coinbase_transactions)}")
        
        # Check UTXO set
        utxo_set = blockchain.utxo
        all_utxos = utxo_set.get_all_utxos()
        
        print(f"\nUTXO Storage:")
        print(f"  Total UTXOs: {len(all_utxos)}")
        
        if all_utxos:
            total_utxo_value = 0
            addresses = set()
            
            for utxo_key, utxo_data in all_utxos.items():
                if not utxo_data.get('spent', False):
                    total_utxo_value += utxo_data.get('amount', 0)
                    if 'address' in utxo_data:
                        addresses.add(utxo_data['address'])
            
            print(f"  Unspent UTXOs: {len([u for u in all_utxos.values() if not u.get('spent', False)])}")
            print(f"  Total Unspent Value: {total_utxo_value} WWC")
            print(f"  Unique Addresses: {len(addresses)}")
            
            if addresses:
                print(f"\nAddress Balances:")
                for address in sorted(addresses):
                    balance = utxo_set.get_balance(address)
                    if balance > 0:
                        print(f"  {address}: {balance} WWC")
        
        # Show recent blocks
        print(f"\nRecent Blocks (Last 5):")
        for block in blockchain.chain[-5:]:
            print(f"  Block #{block.index}: {block.calculate_hash()[:16]}...")
            print(f"    Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(block.timestamp))}")
            print(f"    Transactions: {len(block.transactions)}")
            print(f"    Difficulty: {block.difficulty}")
        
        # Check coin storage location
        print(f"\nCoin Storage Location:")
        print(f"  Coins are stored in the UTXO (Unspent Transaction Output) set")
        print(f"  UTXO Database: In-memory (storage.utxo.UTXOSet)")
        print(f"  Blockchain Data: In-memory (core.blockchain.Blockchain)")
        
        # Show where coins are physically stored
        print(f"\nPhysical Storage:")
        print(f"  Currently: In-memory only (not persisted to disk)")
        print(f"  To persist: Add database storage to UTXOSet and Blockchain")
        
        # Generate mining report
        mining_report = {
            'timestamp': time.time(),
            'total_blocks': len(blockchain.chain),
            'total_coins_mined': total_coins,
            'coinbase_transactions': len(coinbase_transactions),
            'total_utxos': len(all_utxos),
            'unspent_utxos': len([u for u in all_utxos.values() if not u.get('spent', False)]),
            'total_unspent_value': sum(u.get('amount', 0) for u in all_utxos.values() if not u.get('spent', False)),
            'storage_type': 'in-memory',
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
        
        # Save report to file
        with open('mining_status.json', 'w') as f:
            json.dump(mining_report, f, indent=2)
        
        print(f"\nDetailed report saved to: mining_status.json")
        
        return mining_report
        
    except Exception as e:
        print(f"Error checking mining status: {e}")
        import traceback
        traceback.print_exc()


def show_coin_distribution():
    """Show how coins are distributed"""
    print("\n" + "=" * 50)
    print("Coin Distribution Analysis")
    print("=" * 50)
    
    try:
        blockchain = Blockchain()
        utxo_set = blockchain.utxo
        
        if not blockchain.chain:
            print("No blocks found.")
            return
        
        # Analyze coin distribution
        total_supply = sum(50.0 for _ in blockchain.chain)  # Simplified
        unspent_value = 0
        spent_value = 0
        
        all_utxos = utxo_set.get_all_utxos()
        
        for utxo_data in all_utxos.values():
            amount = utxo_data.get('amount', 0)
            if utxo_data.get('spent', False):
                spent_value += amount
            else:
                unspent_value += amount
        
        print(f"Total Supply: {total_supply} WWC")
        print(f"Unspent Coins: {unspent_value} WWC")
        print(f"Spent Coins: {spent_value} WWC")
        print(f"Mining Rewards: {total_supply} WWC")
        
        # Calculate distribution percentage
        if total_supply > 0:
            unspent_pct = (unspent_value / total_supply) * 100
            spent_pct = (spent_value / total_supply) * 100
            
            print(f"\nDistribution:")
            print(f"  Unspent: {unspent_pct:.2f}%")
            print(f"  Spent: {spent_pct:.2f}%")
        
    except Exception as e:
        print(f"Error analyzing coin distribution: {e}")


if __name__ == "__main__":
    check_mining_status()
    show_coin_distribution()
