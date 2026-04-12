#!/usr/bin/env python3
"""
Clean WorldWideCoin Mining Script
Handles corrupted UTXO files and starts mining properly
"""

import os
import json
import time
import threading
from core.blockchain import Blockchain


def clean_utxo_file():
    """Clean corrupted UTXO file if it exists"""
    utxo_file = "core/utxo.json"
    
    if os.path.exists(utxo_file):
        try:
            with open(utxo_file, 'r') as f:
                json.load(f)
            print("UTXO file is valid")
            return True
        except json.JSONDecodeError:
            print(f"Removing corrupted UTXO file: {utxo_file}")
            os.remove(utxo_file)
            print("Corrupted UTXO file removed")
            return False
        except Exception as e:
            print(f"Error checking UTXO file: {e}")
            return False
    else:
        print("UTXO file does not exist")
        return False


class CleanMiner:
    """Clean miner that handles file corruption issues"""
    
    def __init__(self):
        self.running = False
        self.blocks_mined = 0
        self.start_time = None
        self.blockchain = None
    
    def start_mining(self, miner_address="clean_miner"):
        """Start mining with clean blockchain"""
        print("WorldWideCoin Clean Mining")
        print("=" * 40)
        
        try:
            # Clean corrupted files
            clean_utxo_file()
            
            # Create fresh blockchain
            print("Initializing blockchain...")
            self.blockchain = Blockchain()
            
            print(f"Blockchain ready: {len(self.blockchain.chain)} blocks")
            print(f"Current difficulty: {self.blockchain.get_difficulty()}")
            print(f"Current block reward: {self.blockchain.get_block_reward():.6f} WWC")
            
            # Start mining
            self.running = True
            self.start_time = time.time()
            
            print(f"\nStarting mining with address: {miner_address}")
            print("Press Ctrl+C to stop mining")
            print("-" * 40)
            
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
                    
                    # Small delay to prevent excessive CPU usage
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
            self.stop_mining()
    
    def stop_mining(self):
        """Stop mining and show statistics"""
        self.running = False
        
        if self.start_time:
            total_time = time.time() - self.start_time
            print(f"\n{'='*60}")
            print("MINING STOPPED")
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
                for block in self.blockchain.chain:
                    total_coins += self.blockchain.get_block_reward_at_height(block.index) if hasattr(self.blockchain, 'get_block_reward_at_height') else self.blockchain.get_block_reward()
                
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


def show_mining_info():
    """Show mining information"""
    print("\nWorldWideCoin Mining Information")
    print("=" * 40)
    print("Algorithm: SHA-256 (CPU-friendly)")
    print("Block Time: 60 seconds")
    print("Initial Reward: 1.0 WWC")
    print("Decay Rate: 2.5% per year")
    print("Treasury: 5% of rewards")
    print("Fee Burn: 20% of fees")
    print("Total Supply Target: ~21,024,000 WWC")
    print("Fair Launch: No premine, no ICO")
    print()


def main():
    """Main function"""
    show_mining_info()
    
    # Get miner address
    miner_address = input("Enter miner address (default: clean_miner): ").strip()
    miner_address = miner_address if miner_address else "clean_miner"
    
    # Create and start miner
    miner = CleanMiner()
    miner.start_mining(miner_address)


if __name__ == "__main__":
    main()
