#!/usr/bin/env python3
"""
Simple WorldWideCoin Mining Script
Basic mining without complex dependencies
"""

import time
import threading
from core.blockchain import Blockchain


class SimpleMiner:
    """Simple miner for WorldWideCoin"""
    
    def __init__(self, blockchain):
        self.blockchain = blockchain
        self.running = False
        self.blocks_mined = 0
        self.start_time = None
    
    def start_mining(self, miner_address="simple_miner"):
        """Start mining blocks"""
        print(f"Starting mining with miner: {miner_address}")
        self.running = True
        self.start_time = time.time()
        
        while self.running:
            try:
                # Create a new block
                block = self.blockchain.create_block(miner_address)
                
                # Add block to blockchain
                self.blockchain.add_block(block)
                self.blocks_mined += 1
                
                # Display block info
                print(f"\n{'='*50}")
                print(f"BLOCK MINED! #{block.index}")
                print(f"Hash: {block.calculate_hash()[:16]}...")
                print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(block.timestamp))}")
                print(f"Difficulty: {block.difficulty}")
                print(f"Nonce: {block.nonce}")
                print(f"Transactions: {len(block.transactions)}")
                print(f"Total Blocks: {self.blocks_mined}")
                print(f"{'='*50}\n")
                
                # Small delay
                time.sleep(2)
                
            except KeyboardInterrupt:
                print("\nStopping mining...")
                self.running = False
                break
            except Exception as e:
                print(f"Mining error: {e}")
                time.sleep(5)
    
    def stop_mining(self):
        """Stop mining"""
        self.running = False
        
        if self.start_time:
            total_time = time.time() - self.start_time
            print(f"\n{'='*50}")
            print("MINING STOPPED")
            print(f"{'='*50}")
            print(f"Total Blocks Mined: {self.blocks_mined}")
            print(f"Total Mining Time: {self._format_time(total_time)}")
            print(f"Average Time per Block: {total_time/self.blocks_mined:.2f}s" if self.blocks_mined > 0 else "N/A")
            print(f"Final Blockchain Height: {len(self.blockchain.chain)}")
            print(f"{'='*50}")
    
    def _format_time(self, seconds):
        """Format time in readable format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def main():
    """Main function"""
    print("WorldWideCoin Simple Mining")
    print("=" * 40)
    
    try:
        # Create blockchain
        print("Initializing blockchain...")
        blockchain = Blockchain()
        
        # Create miner
        miner = SimpleMiner(blockchain)
        
        # Get miner address
        miner_address = input("Enter miner address (default: simple_miner): ").strip()
        miner_address = miner_address if miner_address else "simple_miner"
        
        print(f"\nStarting mining with address: {miner_address}")
        print("Press Ctrl+C to stop mining")
        print("-" * 40)
        
        # Start mining
        miner.start_mining(miner_address)
        
    except KeyboardInterrupt:
        print("\nMining stopped by user")
    except Exception as e:
        print(f"Mining error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
