#!/usr/bin/env python3
"""
Multi-threaded WorldWideCoin Mining Script
Uses 11 threads as requested
"""

import time
import threading
import concurrent.futures
from core.blockchain import Blockchain


class MultiThreadMiner:
    """Multi-threaded miner for WorldWideCoin"""
    
    def __init__(self, blockchain, num_threads=11):
        self.blockchain = blockchain
        self.num_threads = num_threads
        self.running = False
        self.blocks_mined = 0
        self.start_time = None
        self.lock = threading.Lock()
    
    def start_mining(self, miner_address="multi_thread_miner"):
        """Start multi-threaded mining"""
        print(f"WorldWideCoin Multi-Threaded Mining ({self.num_threads} threads)")
        print("=" * 60)
        
        try:
            # Clean corrupted files first
            self._clean_corrupted_files()
            
            # Create blockchain
            print("Initializing blockchain...")
            self.blockchain = Blockchain()
            
            print(f"Blockchain ready: {len(self.blockchain.chain)} blocks")
            print(f"Current difficulty: {self.blockchain.get_difficulty()}")
            print(f"Current block reward: {self.blockchain.get_block_reward():.6f} WWC")
            
            # Start mining
            self.running = True
            self.start_time = time.time()
            
            print(f"\nStarting mining with {self.num_threads} threads")
            print(f"Miner address: {miner_address}")
            print("Press Ctrl+C to stop mining")
            print("-" * 60)
            
            # Mining loop with multi-threading
            while self.running:
                try:
                    # Use thread pool for mining
                    with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_threads) as executor:
                        # Submit mining tasks
                        futures = []
                        for i in range(self.num_threads):
                            future = executor.submit(self._mine_block, miner_address, i)
                            futures.append(future)
                        
                        # Wait for first successful block
                        for future in concurrent.futures.as_completed(futures, timeout=30):
                            try:
                                block = future.result()
                                if block:
                                    # Add block to blockchain
                                    with self.lock:
                                        self.blockchain.add_block(block)
                                        self.blocks_mined += 1
                                    
                                    # Cancel remaining futures
                                    for f in futures:
                                        if not f.done():
                                            f.cancel()
                                    
                                    # Display block info
                                    self._display_block_info(block)
                                    break
                            except Exception as e:
                                print(f"Mining thread error: {e}")
                    
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
    
    def _mine_block(self, miner_address, thread_id):
        """Mine a block in a separate thread"""
        try:
            # Create block
            block = self.blockchain.create_block(miner_address)
            
            # Mine the block
            block.mine()
            
            return block
            
        except Exception as e:
            print(f"Thread {thread_id} mining error: {e}")
            return None
    
    def _display_block_info(self, block):
        """Display block information"""
        elapsed = time.time() - self.start_time
        hash_rate = self.blocks_mined / elapsed if elapsed > 0 else 0
        
        print(f"\n{'='*60}")
        print(f"BLOCK MINED! #{block.index} (Thread-based)")
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
        print(f"Active Threads: {self.num_threads}")
        print(f"{'='*60}\n")
    
    def _clean_corrupted_files(self):
        """Clean corrupted files"""
        import os
        import json
        
        files_to_check = ["utxo.json", "chain.json", "core/utxo.json", "core/chain.json"]
        
        for file_path in files_to_check:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        json.load(f)
                except (json.JSONDecodeError, IOError, ValueError):
                    print(f"Removing corrupted file: {file_path}")
                    try:
                        os.remove(file_path)
                    except:
                        pass
    
    def show_stats(self):
        """Show mining statistics"""
        if self.start_time:
            total_time = time.time() - self.start_time
            print(f"\n{'='*60}")
            print("MULTI-THREADED MINING STATISTICS")
            print(f"{'='*60}")
            print(f"Total Blocks Mined: {self.blocks_mined}")
            print(f"Total Mining Time: {self._format_time(total_time)}")
            print(f"Number of Threads: {self.num_threads}")
            
            if total_time > 0 and self.blocks_mined > 0:
                avg_time_per_block = total_time / self.blocks_mined
                hash_rate = self.blocks_mined / total_time
                thread_efficiency = hash_rate / self.num_threads
                
                print(f"Average Time per Block: {avg_time_per_block:.2f}s")
                print(f"Average Hash Rate: {hash_rate:.2f} H/s")
                print(f"Thread Efficiency: {thread_efficiency:.2f} H/s per thread")
            
            if self.blockchain:
                print(f"Final Blockchain Height: {len(self.blockchain.chain)}")
                print(f"Current Difficulty: {self.blockchain.get_difficulty()}")
                print(f"Current Block Reward: {self.blockchain.get_block_reward():.6f} WWC")
                
                # Calculate total coins mined
                total_coins = 0
                for i, block in enumerate(self.blockchain.chain[1:], 1):  # Skip genesis
                    t = i / self.blockchain.BLOCKS_PER_YEAR
                    reward = self.blockchain.INITIAL_REWARD * (2.718281828 ** (-self.blockchain.DECAY_RATE * t))
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
    print("WorldWideCoin Multi-Threaded Mining")
    print("=" * 40)
    
    # Use 11 threads as requested
    num_threads = 11
    
    # Get miner address
    miner_address = input("Enter miner address (default: multi_thread_miner): ").strip()
    miner_address = miner_address if miner_address else "multi_thread_miner"
    
    print(f"\nStarting mining with {num_threads} threads...")
    
    # Create blockchain and miner
    try:
        blockchain = Blockchain()
        miner = MultiThreadMiner(blockchain, num_threads)
        miner.start_mining(miner_address)
    except Exception as e:
        print(f"Error starting mining: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
