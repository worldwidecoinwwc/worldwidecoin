#!/usr/bin/env python3
"""
Simple Working Mining Script
Bypasses file corruption issues with in-memory blockchain
"""

import time
import json
import os
from core.block import Block
from core.transaction import Transaction


class SimpleMemoryBlockchain:
    """Simple in-memory blockchain that doesn't use files"""
    
    INITIAL_REWARD = 1.0
    DECAY_RATE = 0.025
    BLOCKS_PER_YEAR = 525600
    TREASURY_PERCENT = 0.05
    TARGET_BLOCK_TIME = 60
    
    def __init__(self):
        self.chain = []
        self.mempool = []
        self.create_genesis_block()
    
    def create_genesis_block(self):
        """Create genesis block"""
        genesis = Block(
            index=0,
            prev_hash="0",
            transactions=[],
            timestamp=time.time(),
            difficulty=1
        )
        genesis.mine()
        self.chain.append(genesis)
    
    def get_last_block(self):
        """Get last block"""
        return self.chain[-1] if self.chain else None
    
    def get_block_reward(self):
        """Calculate block reward with continuous decay"""
        height = len(self.chain)
        t = height / self.BLOCKS_PER_YEAR
        return self.INITIAL_REWARD * (2.718281828 ** (-self.DECAY_RATE * t))
    
    def get_difficulty(self):
        """Simple difficulty adjustment"""
        if len(self.chain) < 2:
            return 1
        
        last_block = self.chain[-1]
        prev_block = self.chain[-2]
        
        # Adjust difficulty based on block time
        time_diff = last_block.timestamp - prev_block.timestamp
        
        if time_diff < self.TARGET_BLOCK_TIME * 0.8:
            return min(last_block.difficulty + 1, 8)
        elif time_diff > self.TARGET_BLOCK_TIME * 1.2:
            return max(last_block.difficulty - 1, 1)
        else:
            return last_block.difficulty
    
    def create_block(self, miner_address):
        """Create a new block"""
        # Get transactions from mempool (simplified)
        txs = self.mempool[:10]  # Limit to 10 transactions
        self.mempool = self.mempool[10:]  # Remove from mempool
        
        # Calculate rewards
        base_reward = self.get_block_reward()
        treasury_cut = base_reward * self.TREASURY_PERCENT
        miner_reward = base_reward * (1 - self.TREASURY_PERCENT)
        
        # Create coinbase transaction
        coinbase = Transaction(
            inputs=[],
            outputs=[
                {"address": miner_address, "amount": miner_reward},
                {"address": "WWC_TREASURY", "amount": treasury_cut}
            ]
        )
        
        # Insert coinbase at beginning
        txs.insert(0, coinbase)
        
        # Create block
        block = Block(
            index=len(self.chain),
            prev_hash=self.get_last_block().hash,
            transactions=txs,
            timestamp=time.time(),
            difficulty=self.get_difficulty()
        )
        
        # Mine the block
        block.mine()
        
        return block
    
    def add_block(self, block):
        """Add block to chain"""
        self.chain.append(block)
    
    def add_transaction(self, tx):
        """Add transaction to mempool"""
        self.mempool.append(tx)


class SimpleMiner:
    """Simple miner that works with in-memory blockchain"""
    
    def __init__(self):
        self.running = False
        self.blocks_mined = 0
        self.start_time = None
        self.blockchain = None
    
    def start_mining(self, miner_address="simple_miner"):
        """Start mining"""
        print("WorldWideCoin Simple Working Mining")
        print("=" * 50)
        
        try:
            # Create in-memory blockchain
            print("Creating in-memory blockchain...")
            self.blockchain = SimpleMemoryBlockchain()
            
            print(f"Blockchain ready: {len(self.blockchain.chain)} blocks")
            print(f"Current difficulty: {self.blockchain.get_difficulty()}")
            print(f"Current block reward: {self.blockchain.get_block_reward():.6f} WWC")
            
            # Start mining
            self.running = True
            self.start_time = time.time()
            
            print(f"\nStarting mining with address: {miner_address}")
            print("Press Ctrl+C to stop mining")
            print("-" * 50)
            
            # Mining loop
            while self.running:
                try:
                    # Create and mine block
                    block = self.blockchain.create_block(miner_address)
                    
                    # Add block to blockchain
                    self.blockchain.add_block(block)
                    self.blocks_mined += 1
                    
                    # Display block info
                    elapsed = time.time() - self.start_time
                    hash_rate = self.blocks_mined / elapsed if elapsed > 0 else 0
                    
                    print(f"\n{'='*60}")
                    print(f"BLOCK MINED! #{block.index}")
                    print(f"Hash: {block.calculate_hash()[:16]}...")
                    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(block.timestamp))}")
                    print(f"Difficulty: {block.difficulty}")
                    print(f"Nonce: {block.nonce}")
                    print(f"Transactions: {len(block.transactions)}")
                    print(f"Block Reward: {self.blockchain.get_block_reward():.6f} WWC")
                    print(f"Treasury Cut: {self.blockchain.get_block_reward() * self.blockchain.TREASURY_PERCENT:.6f} WWC")
                    print(f"Miner Reward: {self.blockchain.get_block_reward() * (1 - self.blockchain.TREASURY_PERCENT):.6f} WWC")
                    print(f"Total Blocks: {self.blocks_mined}")
                    print(f"Mining Time: {self._format_time(elapsed)}")
                    print(f"Hash Rate: {hash_rate:.2f} H/s")
                    print(f"Blockchain Height: {len(self.blockchain.chain)}")
                    print(f"{'='*60}\n")
                    
                    # Small delay
                    time.sleep(1)
                    
                except KeyboardInterrupt:
                    print("\nStopping mining...")
                    self.running = False
                    break
                except Exception as e:
                    print(f"Mining error: {e}")
                    time.sleep(5)
        
        except KeyboardInterrupt:
            print("\nMining stopped by user")
        except Exception as e:
            print(f"Initialization error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.show_stats()
    
    def show_stats(self):
        """Show mining statistics"""
        if self.start_time:
            total_time = time.time() - self.start_time
            print(f"\n{'='*60}")
            print("MINING STATISTICS")
            print(f"{'='*60}")
            print(f"Total Blocks Mined: {self.blocks_mined}")
            print(f"Total Mining Time: {self._format_time(total_time)}")
            
            if total_time > 0 and self.blocks_mined > 0:
                avg_time_per_block = total_time / self.blocks_mined
                hash_rate = self.blocks_mined / total_time
                print(f"Average Time per Block: {avg_time_per_block:.2f}s")
                print(f"Average Hash Rate: {hash_rate:.2f} H/s")
            
            if self.blockchain:
                print(f"Final Blockchain Height: {len(self.blockchain.chain)}")
                print(f"Current Difficulty: {self.blockchain.get_difficulty()}")
                print(f"Current Block Reward: {self.blockchain.get_block_reward():.6f} WWC")
                
                # Calculate total coins mined
                total_coins = 0
                for i, block in enumerate(self.blockchain.chain[1:], 1):  # Skip genesis
                    reward = self.blockchain.INITIAL_REWARD * (2.718281828 ** (-self.blockchain.DECAY_RATE * (i / self.blockchain.BLOCKS_PER_YEAR)))
                    total_coins += reward
                
                print(f"Total Coins Mined: {total_coins:.6f} WWC")
                
                # Show treasury allocation
                treasury_coins = total_coins * self.blockchain.TREASURY_PERCENT
                miner_coins = total_coins * (1 - self.blockchain.TREASURY_PERCENT)
                print(f"Treasury Allocation: {treasury_coins:.6f} WWC")
                print(f"Miner Rewards: {miner_coins:.6f} WWC")
            
            print(f"{'='*60}")
    
    def _format_time(self, seconds):
        """Format time in readable format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def main():
    """Main function"""
    print("WorldWideCoin Simple Working Mining")
    print("=" * 40)
    print("This script uses in-memory blockchain to avoid file corruption issues")
    print()
    
    # Get miner address
    miner_address = input("Enter miner address (default: simple_miner): ").strip()
    miner_address = miner_address if miner_address else "simple_miner"
    
    # Create and start miner
    miner = SimpleMiner()
    miner.start_mining(miner_address)


if __name__ == "__main__":
    main()
