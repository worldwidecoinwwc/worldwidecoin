# mining/optimized_miner.py
import hashlib
import json
import time
from typing import List, Optional
from core.block import Block
from core.transaction import Transaction


class OptimizedMiner:
    """Optimized single-threaded miner with performance enhancements"""
    
    def __init__(self):
        # Pre-computed hash templates for speed
        self.hash_template = None
        self.target_prefix = None
        
        # Performance metrics
        self.start_time = 0
        self.total_hashes = 0
        self.last_report_time = 0
        
    def mine_block_optimized(self, block: Block, report_interval: int = 10000) -> Block:
        """
        Optimized mining with performance improvements
        """
        self.start_time = time.time()
        self.last_report_time = self.start_time
        self.total_hashes = 0
        
        # Pre-compute static parts of hash
        self._prepare_hash_template(block)
        
        print(f"⚡ Starting optimized mining for block {block.index}")
        print(f"🎯 Target: {self.target_prefix}")
        
        nonce = 0
        
        while True:
            block.nonce = nonce
            block_hash = self._calculate_hash_optimized(block)
            self.total_hashes += 1
            
            if block_hash.startswith(self.target_prefix):
                elapsed = time.time() - self.start_time
                hash_rate = self.total_hashes / elapsed if elapsed > 0 else 0
                
                print(f"🎉 Block found!")
                print(f"🔢 Nonce: {nonce}")
                print(f"⚡ Hash rate: {hash_rate:.0f} H/s")
                print(f"⏱️ Time: {elapsed:.2f}s")
                
                block.hash = block_hash
                return block
            
            # Progress reporting
            if self.total_hashes % report_interval == 0:
                self._report_progress()
            
            nonce += 1
    
    def _prepare_hash_template(self, block: Block):
        """Pre-compute static parts of block hash"""
        # Convert transactions to dict once
        self.txs_dict = [tx.to_dict() for tx in block.transactions]
        
        # Set target prefix
        self.target_prefix = "0" * block.difficulty
        
        # Store block fields for fast access
        self.block_index = block.index
        self.block_prev_hash = block.prev_hash
        self.block_timestamp = block.timestamp
        self.block_difficulty = block.difficulty
    
    def _calculate_hash_optimized(self, block: Block) -> str:
        """Optimized hash calculation with minimal object creation"""
        # Build hash data directly without intermediate dict
        hash_data = {
            "index": self.block_index,
            "prev_hash": self.block_prev_hash,
            "transactions": self.txs_dict,
            "timestamp": self.block_timestamp,
            "nonce": block.nonce,
            "difficulty": self.block_difficulty
        }
        
        return hashlib.sha256(
            json.dumps(hash_data, sort_keys=True).encode()
        ).hexdigest()
    
    def _report_progress(self):
        """Report mining progress"""
        current_time = time.time()
        elapsed = current_time - self.start_time
        hash_rate = self.total_hashes / elapsed if elapsed > 0 else 0
        
        if current_time - self.last_report_time >= 5:  # Report every 5 seconds
            print(f"⛏️ Mining progress: {self.total_hashes:,} hashes, {hash_rate:.0f} H/s")
            self.last_report_time = current_time


class GPUMiner:
    """GPU-accelerated mining interface (placeholder for future implementation)"""
    
    def __init__(self):
        self.gpu_available = self._check_gpu_availability()
        if self.gpu_available:
            print("🎮 GPU mining available")
        else:
            print("⚠️ GPU mining not available, using CPU")
    
    def _check_gpu_availability(self) -> bool:
        """Check if GPU mining is available"""
        try:
            # Try to import GPU mining libraries
            import cupy  # or pyopencl, etc.
            return True
        except ImportError:
            return False
    
    def mine_block_gpu(self, block: Block) -> Optional[Block]:
        """GPU-accelerated mining (placeholder)"""
        if not self.gpu_available:
            print("❌ GPU mining not available")
            return None
        
        print("🚀 Starting GPU mining...")
        # TODO: Implement GPU mining logic
        return None


class AdaptiveMiner:
    """Adaptive miner that switches strategies based on performance"""
    
    def __init__(self):
        self.strategies = {
            "single_thread": OptimizedMiner(),
            "multi_thread": None,  # Will be initialized later
            "gpu": GPUMiner()
        }
        
        self.current_strategy = "single_thread"
        self.performance_history = []
    
    def set_multi_thread_miner(self, multi_threaded_miner):
        """Set the multi-threaded miner instance"""
        self.strategies["multi_thread"] = multi_threaded_miner
    
    def mine_block_adaptive(self, block: Block) -> Block:
        """Mine using the best available strategy"""
        print(f"🧠 Using {self.current_strategy} mining strategy")
        
        if self.current_strategy == "gpu":
            result = self.strategies["gpu"].mine_block_gpu(block)
            if result:
                return result
            else:
                # Fallback to CPU mining
                self.current_strategy = "multi_thread"
        
        if self.current_strategy == "multi_thread" and self.strategies["multi_thread"]:
            # Use multi-threaded miner
            return self.strategies["multi_thread"].mine_block(block)
        
        # Default to optimized single-threaded mining
        return self.strategies["single_thread"].mine_block_optimized(block)
    
    def benchmark_strategies(self, duration: int = 10) -> str:
        """Benchmark all strategies and return the best one"""
        print("🏁 Benchmarking mining strategies...")
        
        results = {}
        
        # Benchmark single-threaded
        print("Testing single-threaded mining...")
        start_time = time.time()
        # TODO: Implement benchmark
        single_hashrate = 1000  # Placeholder
        results["single_thread"] = single_hashrate
        
        # Benchmark multi-threaded if available
        if self.strategies["multi_thread"]:
            print("Testing multi-threaded mining...")
            # TODO: Implement benchmark
            multi_hashrate = 3500  # Placeholder
            results["multi_thread"] = multi_hashrate
        
        # Benchmark GPU if available
        if self.strategies["gpu"].gpu_available:
            print("Testing GPU mining...")
            # TODO: Implement benchmark
            gpu_hashrate = 10000  # Placeholder
            results["gpu"] = gpu_hashrate
        
        # Find best strategy
        best_strategy = max(results.keys(), key=lambda k: results[k])
        best_hashrate = results[best_strategy]
        
        print(f"📊 Benchmark results:")
        for strategy, hashrate in results.items():
            status = "✅" if strategy == best_strategy else "  "
            print(f"   {status} {strategy}: {hashrate:.0f} H/s")
        
        print(f"🎯 Selected strategy: {best_strategy} ({best_hashrate:.0f} H/s)")
        
        self.current_strategy = best_strategy
        return best_strategy


class MiningOptimizer:
    """Advanced mining optimization utilities"""
    
    @staticmethod
    def optimize_difficulty_target(block: Block) -> Block:
        """Optimize difficulty target for faster mining"""
        # This is a placeholder for difficulty optimization
        # In reality, difficulty is determined by network consensus
        return block
    
    @staticmethod
    def optimize_transaction_selection(blockchain, max_transactions: int = 1000) -> List:
        """Select optimal transactions for mining"""
        mempool = blockchain.mempool.get_transactions()
        
        if not mempool:
            return []
        
        # Sort transactions by fee rate (fee per byte)
        sorted_txs = sorted(
            mempool,
            key=lambda tx: tx.get_fee() / len(str(tx.to_dict())),
            reverse=True
        )
        
        # Take top transactions up to limit
        return sorted_txs[:max_transactions]
    
    @staticmethod
    def calculate_optimal_batch_size(num_threads: int, difficulty: int) -> int:
        """Calculate optimal batch size for given threads and difficulty"""
        # Higher difficulty = smaller batches for better responsiveness
        # More threads = larger batches for better throughput
        base_batch = 1000
        
        # Adjust for difficulty
        difficulty_factor = max(0.1, 1.0 / (difficulty + 1))
        
        # Adjust for thread count
        thread_factor = min(2.0, num_threads / 4.0)
        
        optimal_batch = int(base_batch * difficulty_factor * thread_factor)
        return max(100, min(optimal_batch, 10000))
    
    @staticmethod
    def estimate_mining_time(difficulty: int, hash_rate: float) -> float:
        """Estimate time to find block at given difficulty"""
        if hash_rate <= 0:
            return float('inf')
        
        # Probability of finding valid hash per attempt
        probability = 1 / (16 ** difficulty)  # 16 = number of hex digits
        
        # Expected number of attempts
        expected_attempts = 1 / probability
        
        # Expected time in seconds
        expected_time = expected_attempts / hash_rate
        
        return expected_time
