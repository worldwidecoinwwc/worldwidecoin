#!/usr/bin/env python3
"""
Working WorldWideCoin Mining Script
Fixed version that handles all errors
"""

import time
import signal
import sys
from core.blockchain import Blockchain


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\nStopping mining...")
    sys.exit(0)


def main():
    print("WorldWideCoin Working Mining")
    print("=" * 40)
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Create blockchain
        print("Initializing blockchain...")
        blockchain = Blockchain()
        
        print(f"Blockchain ready: {len(blockchain.chain)} blocks")
        print(f"Current difficulty: {blockchain.get_difficulty()}")
        print(f"Current block reward: {blockchain.get_block_reward():.6f} WWC")
        
        miner_address = "working_miner"
        blocks_mined = 0
        start_time = time.time()
        
        print(f"\nStarting mining with address: {miner_address}")
        print("Press Ctrl+C to stop mining")
        print("-" * 40)
        
        # Mining loop
        while True:
            try:
                # Create and mine block
                block = blockchain.create_block(miner_address)
                
                # Add block to blockchain
                blockchain.add_block(block)
                blocks_mined += 1
                
                # Display info
                elapsed = time.time() - start_time
                hash_rate = blocks_mined / elapsed if elapsed > 0 else 0
                
                print(f"BLOCK MINED! #{block.index}")
                print(f"Hash: {block.calculate_hash()[:16]}...")
                print(f"Reward: {blockchain.get_block_reward():.6f} WWC")
                print(f"Total Blocks: {blocks_mined}")
                print(f"Hash Rate: {hash_rate:.2f} H/s")
                print(f"Blockchain Height: {len(blockchain.chain)}")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"Mining error: {e}")
                time.sleep(5)
    
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
