# mining/multi_threaded_miner.py
import threading
import time
import hashlib
import json
import queue
from typing import List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.block import Block
from core.transaction import Transaction


class MultiThreadedMiner:
    """High-performance multi-threaded cryptocurrency miner"""
    
    def __init__(self, num_threads: int = 4, batch_size: int = 1000):
        self.num_threads = num_threads
        self.batch_size = batch_size
        self.mining = False
        self.found_block = None
        self.mining_lock = threading.Lock()
        self.stats_lock = threading.Lock()
        
        # Performance metrics
        self.hashes_per_second = 0
        self.total_hashes = 0
        self.start_time = 0
        self.blocks_found = 0
        
        # Thread pool
        self.executor = ThreadPoolExecutor(max_workers=num_threads)
        self.result_queue = queue.Queue()
        
        print(f"⛏️ Multi-threaded miner initialized with {num_threads} threads")
    
    def mine_block(self, block: Block, callback: Optional[Callable] = None) -> Optional[Block]:
        """
        Mine a block using multiple threads
        Returns the mined block or None if stopped
        """
        with self.mining_lock:
            if self.mining:
                print("⚠️ Mining already in progress")
                return None
            
            self.mining = True
            self.found_block = None
            self.start_time = time.time()
            self.total_hashes = 0
        
        print(f"🔨 Starting multi-threaded mining for block {block.index}")
        print(f"🎯 Target difficulty: {block.difficulty} leading zeros")
        
        try:
            # Start mining threads
            futures = []
            for thread_id in range(self.num_threads):
                start_nonce = thread_id * self.batch_size
                future = self.executor.submit(
                    self._mine_range, 
                    block, thread_id, start_nonce, callback
                )
                futures.append(future)
            
            # Wait for first thread to find solution
            for future in as_completed(futures):
                result = future.result()
                if result:
                    # Cancel remaining futures
                    for f in futures:
                        f.cancel()
                    
                    with self.mining_lock:
                        self.mining = False
                        self.blocks_found += 1
                    
                    return result
        
        except Exception as e:
            print(f"❌ Mining error: {e}")
        
        finally:
            with self.mining_lock:
                self.mining = False
        
        return None
    
    def _mine_range(self, block: Block, thread_id: int, start_nonce: int, callback: Optional[Callable]) -> Optional[Block]:
        """
        Mine a specific range of nonces
        """
        # Create a copy of the block for this thread
        thread_block = Block(
            index=block.index,
            prev_hash=block.prev_hash,
            transactions=block.transactions,
            timestamp=block.timestamp,
            difficulty=block.difficulty
        )
        
        target_prefix = "0" * block.difficulty
        nonce = start_nonce
        local_hashes = 0
        
        while self.mining and not self.found_block:
            thread_block.nonce = nonce
            block_hash = thread_block.calculate_hash()
            local_hashes += 1
            
            if block_hash.startswith(target_prefix):
                # Found solution!
                with self.mining_lock:
                    if not self.found_block:  # First thread wins
                        self.found_block = thread_block
                        thread_block.hash = block_hash
                        
                        # Update stats
                        elapsed = time.time() - self.start_time
                        self.hashes_per_second = self.total_hashes / elapsed if elapsed > 0 else 0
                        
                        print(f"🎉 Block {block.index} found by thread {thread_id}!")
                        print(f"🔢 Nonce: {nonce}")
                        print(f"⚡ Hash rate: {self.hashes_per_second:.0f} H/s")
                        
                        if callback:
                            callback(thread_block)
                
                return thread_block
            
            nonce += self.num_threads * self.batch_size
            
            # Update hash counter periodically
            if local_hashes % 1000 == 0:
                with self.stats_lock:
                    self.total_hashes += local_hashes
                local_hashes = 0
        
        return None
    
    def stop_mining(self):
        """Stop the mining process"""
        with self.mining_lock:
            self.mining = False
        print("⏹️ Mining stopped")
    
    def get_stats(self) -> dict:
        """Get mining performance statistics"""
        with self.stats_lock:
            elapsed = time.time() - self.start_time if self.start_time > 0 else 0
            current_hashrate = self.total_hashes / elapsed if elapsed > 0 else 0
            
            return {
                "mining": self.mining,
                "threads": self.num_threads,
                "total_hashes": self.total_hashes,
                "hash_rate": current_hashrate,
                "blocks_found": self.blocks_found,
                "elapsed_time": elapsed
            }
    
    def benchmark(self, difficulty: int = 3, duration: int = 10) -> dict:
        """
        Benchmark mining performance
        Returns performance metrics
        """
        print(f"🏃 Running {duration}s benchmark at difficulty {difficulty}...")
        
        # Create test block
        test_block = Block(
            index=0,
            prev_hash="0" * 64,
            transactions=[],
            timestamp=time.time(),
            difficulty=difficulty
        )
        
        self.start_time = time.time()
        self.total_hashes = 0
        self.mining = True
        
        # Start benchmark threads
        futures = []
        for thread_id in range(self.num_threads):
            start_nonce = thread_id * self.batch_size
            future = self.executor.submit(
                self._benchmark_range,
                test_block, thread_id, start_nonce, duration
            )
            futures.append(future)
        
        # Wait for completion
        for future in as_completed(futures):
            future.result()
        
        self.mining = False
        elapsed = time.time() - self.start_time
        hash_rate = self.total_hashes / elapsed if elapsed > 0 else 0
        
        results = {
            "duration": elapsed,
            "difficulty": difficulty,
            "threads": self.num_threads,
            "total_hashes": self.total_hashes,
            "hash_rate": hash_rate,
            "hashes_per_thread": self.total_hashes / self.num_threads
        }
        
        print(f"📊 Benchmark results:")
        print(f"   Duration: {elapsed:.1f}s")
        print(f"   Total hashes: {self.total_hashes:,}")
        print(f"   Hash rate: {hash_rate:.0f} H/s")
        print(f"   Hashes per thread: {results['hashes_per_thread']:,.0f}")
        
        return results
    
    def _benchmark_range(self, block: Block, thread_id: int, start_nonce: int, duration: int):
        """Benchmark mining for a specific duration"""
        end_time = time.time() + duration
        target_prefix = "0" * block.difficulty
        nonce = start_nonce
        local_hashes = 0
        
        thread_block = Block(
            index=block.index,
            prev_hash=block.prev_hash,
            transactions=block.transactions,
            timestamp=block.timestamp,
            difficulty=block.difficulty
        )
        
        while time.time() < end_time and self.mining:
            thread_block.nonce = nonce
            thread_block.calculate_hash()  # Calculate hash (we don't need to check for solution in benchmark)
            local_hashes += 1
            nonce += self.num_threads * self.batch_size
        
        with self.stats_lock:
            self.total_hashes += local_hashes
    
    def optimize_thread_count(self, test_duration: int = 5) -> int:
        """
        Find optimal thread count for this system
        Returns recommended thread count
        """
        print(f"🔍 Finding optimal thread count...")
        
        best_hashrate = 0
        best_threads = 1
        
        for threads in range(1, min(self.num_threads * 2, 9)):  # Test 1-8 threads
            # Temporarily adjust thread count
            old_threads = self.num_threads
            self.num_threads = threads
            
            # Run quick benchmark
            result = self.benchmark(difficulty=2, duration=test_duration)
            
            if result["hash_rate"] > best_hashrate:
                best_hashrate = result["hash_rate"]
                best_threads = threads
            
            print(f"   {threads} threads: {result['hash_rate']:.0f} H/s")
        
        # Restore original thread count
        self.num_threads = old_threads
        
        print(f"🎯 Optimal thread count: {best_threads} ({best_hashrate:.0f} H/s)")
        return best_threads


class MiningPool:
    """Simple mining pool implementation"""
    
    def __init__(self, pool_address: str, reward_split: float = 0.01):
        self.pool_address = pool_address
        self.reward_split = reward_split  # 1% pool fee
        self.miners = {}
        self.pool_stats = {
            "total_hashes": 0,
            "blocks_found": 0,
            "total_rewards": 0.0
        }
    
    def add_miner(self, miner_id: str, payout_address: str):
        """Add a miner to the pool"""
        self.miners[miner_id] = {
            "address": payout_address,
            "hashes_contributed": 0,
            "shares": 0,
            "rewards_earned": 0.0
        }
        print(f"➕ Miner {miner_id} joined pool")
    
    def remove_miner(self, miner_id: str):
        """Remove a miner from the pool"""
        if miner_id in self.miners:
            del self.miners[miner_id]
            print(f"➖ Miner {miner_id} left pool")
    
    def contribute_hashpower(self, miner_id: str, hashes: int):
        """Record hash contribution from miner"""
        if miner_id in self.miners:
            self.miners[miner_id]["hashes_contributed"] += hashes
            self.pool_stats["total_hashes"] += hashes
    
    def distribute_reward(self, block_reward: float):
        """Distribute block reward among miners"""
        self.pool_stats["blocks_found"] += 1
        self.pool_stats["total_rewards"] += block_reward
        
        pool_fee = block_reward * self.reward_split
        miner_reward = block_reward - pool_fee
        
        # Calculate shares based on hash contribution
        total_hashes = sum(m["hashes_contributed"] for m in self.miners.values())
        
        if total_hashes > 0:
            for miner_id, miner_data in self.miners.items():
                share_ratio = miner_data["hashes_contributed"] / total_hashes
                reward = miner_reward * share_ratio
                miner_data["rewards_earned"] += reward
                miner_data["shares"] += 1
                
                print(f"💰 Miner {miner_id} earned {reward:.8f} WWC")
        
        print(f"🏊 Pool fee: {pool_fee:.8f} WWC")
    
    def get_pool_stats(self) -> dict:
        """Get pool statistics"""
        return {
            "pool_address": self.pool_address,
            "active_miners": len(self.miners),
            "pool_stats": self.pool_stats,
            "miners": self.miners
        }
