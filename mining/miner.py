# mining/miner.py
import time
import threading
from typing import Optional, Callable
from core.blockchain import Blockchain
from core.block import Block
from core.transaction import Transaction
from mining.multi_threaded_miner import MultiThreadedMiner
from mining.optimized_miner import OptimizedMiner, AdaptiveMiner
from mining.performance_monitor import PerformanceMonitor


class Miner:
    """Enhanced cryptocurrency miner with multiple strategies"""
    
    def __init__(self, blockchain: Blockchain, miner_address: str, 
                 mining_mode: str = "adaptive", num_threads: int = 4):
        self.blockchain = blockchain
        self.miner_address = miner_address
        self.mining_mode = mining_mode
        self.num_threads = num_threads
        
        # Initialize mining components
        self.multi_threaded_miner = MultiThreadedMiner(num_threads)
        self.optimized_miner = OptimizedMiner()
        self.adaptive_miner = AdaptiveMiner()
        
        # Set up adaptive miner
        self.adaptive_miner.set_multi_thread_miner(self.multi_threaded_miner)
        
        # Performance monitoring
        self.monitor = PerformanceMonitor(update_interval=2.0)
        self.monitor.add_alert_callback(self._performance_alert)
        
        # Mining state
        self.mining = False
        self.blocks_mined = 0
        self.start_time = 0
        self.last_block_time = 0
        
        # Mining statistics
        self.total_earnings = 0.0
        self.mining_stats = {
            "total_hashes": 0,
            "blocks_found": 0,
            "uptime": 0.0,
            "average_hashrate": 0.0
        }
        
        print(f"⛏️ Miner initialized for {miner_address}")
        print(f"🔧 Mining mode: {mining_mode}")
        print(f"🧵 Threads: {num_threads}")
    
    def start_mining(self, continuous: bool = True):
        """Start mining process"""
        if self.mining:
            print("⚠️ Mining already in progress")
            return
        
        self.mining = True
        self.start_time = time.time()
        self.last_block_time = time.time()
        
        # Start performance monitoring
        self.monitor.start_monitoring()
        
        print(f"🚀 Started mining in {self.mining_mode} mode")
        
        try:
            if continuous:
                self._continuous_mining()
            else:
                return self._mine_single_block()
        
        except KeyboardInterrupt:
            print("\n⏹️ Mining interrupted by user")
        
        finally:
            self.stop_mining()
    
    def stop_mining(self):
        """Stop mining process"""
        self.mining = False
        self.multi_threaded_miner.stop_mining()
        self.monitor.stop_monitoring()
        
        # Update final statistics
        if self.start_time > 0:
            self.mining_stats["uptime"] = time.time() - self.start_time
        
        print("⛏️ Mining stopped")
        self._print_mining_summary()
    
    def _continuous_mining(self):
        """Continuous mining loop"""
        while self.mining:
            try:
                # Create and mine block
                block = self.blockchain.create_block(self.miner_address)
                
                # Mine using selected strategy
                if self.mining_mode == "multi_thread":
                    mined_block = self.multi_threaded_miner.mine_block(
                        block, callback=self._on_block_found
                    )
                elif self.mining_mode == "optimized":
                    mined_block = self.optimized_miner.mine_block_optimized(block)
                elif self.mining_mode == "adaptive":
                    mined_block = self.adaptive_miner.mine_block_adaptive(block)
                else:
                    mined_block = self.multi_threaded_miner.mine_block(
                        block, callback=self._on_block_found
                    )
                
                if mined_block and self.mining:
                    # Add block to blockchain
                    self.blockchain.add_block(mined_block)
                    self._on_block_found(mined_block)
                
                # Brief pause to prevent excessive CPU usage
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Mining error: {e}")
                time.sleep(1)
    
    def _mine_single_block(self) -> Optional[Block]:
        """Mine a single block"""
        try:
            block = self.blockchain.create_block(self.miner_address)
            
            if self.mining_mode == "multi_thread":
                return self.multi_threaded_miner.mine_block(
                    block, callback=self._on_block_found
                )
            elif self.mining_mode == "optimized":
                return self.optimized_miner.mine_block_optimized(block)
            elif self.mining_mode == "adaptive":
                return self.adaptive_miner.mine_block_adaptive(block)
            else:
                return self.multi_threaded_miner.mine_block(
                    block, callback=self._on_block_found
                )
        
        except Exception as e:
            print(f"❌ Single block mining error: {e}")
            return None
    
    def _on_block_found(self, block: Block):
        """Callback when block is found"""
        current_time = time.time()
        block_time = current_time - self.last_block_time
        
        # Update statistics
        self.blocks_mined += 1
        self.mining_stats["blocks_found"] += 1
        
        # Calculate earnings
        block_reward = self.blockchain.get_block_reward()
        self.total_earnings += block_reward
        
        # Update performance monitor
        stats = self.multi_threaded_miner.get_stats()
        self.monitor.update_mining_stats(
            hash_rate=stats.get("hash_rate", 0),
            blocks_found=self.blocks_mined,
            difficulty=block.difficulty
        )
        
        # Print block information
        print(f"\n🎉 BLOCK FOUND! #{block.index}")
        print(f"⛏️ Miner: {self.miner_address}")
        print(f"💰 Reward: {block_reward:.8f} WWC")
        print(f"⏱️ Time: {block_time:.2f}s")
        print(f"🔢 Nonce: {block.nonce}")
        print(f"🔗 Hash: {block.hash[:16]}...")
        
        self.last_block_time = current_time
    
    def _performance_alert(self, alert: str, metrics):
        """Handle performance alerts"""
        if "High CPU usage" in alert:
            print(f"\n⚠️ Performance Alert: {alert}")
            print("💡 Consider reducing thread count")
        elif "High temperature" in alert:
            print(f"\n🔥 Performance Alert: {alert}")
            print("💡 Check cooling system")
        elif "Mining hash rate is zero" in alert:
            print(f"\n❌ Performance Alert: {alert}")
            print("💡 Check mining configuration")
    
    def _print_mining_summary(self):
        """Print mining summary"""
        if self.start_time > 0:
            uptime = time.time() - self.start_time
            
            print(f"\n📊 Mining Summary:")
            print(f"⏱️ Uptime: {uptime:.1f}s ({uptime/3600:.1f}h)")
            print(f"🔢 Blocks mined: {self.blocks_mined}")
            print(f"💰 Total earnings: {self.total_earnings:.8f} WWC")
            
            if self.blocks_mined > 0:
                avg_time = uptime / self.blocks_mined
                print(f"⚡ Average block time: {avg_time:.1f}s")
                print(f"🏆 Earnings per hour: {(self.total_earnings/uptime*3600):.8f} WWC/h")
            
            # Get performance summary
            perf_summary = self.monitor.get_performance_summary(duration_minutes=int(uptime/60)+1)
            if perf_summary:
                hash_stats = perf_summary.get("hash_rate", {})
                print(f"⛏️ Average hash rate: {hash_stats.get('average', 0):.0f} H/s")
                print(f"🚀 Peak hash rate: {hash_stats.get('maximum', 0):.0f} H/s")
    
    def get_mining_stats(self) -> dict:
        """Get current mining statistics"""
        # Update uptime
        if self.start_time > 0 and self.mining:
            self.mining_stats["uptime"] = time.time() - self.start_time
        
        # Get current performance
        current_metrics = self.monitor.get_current_metrics()
        if current_metrics:
            self.mining_stats["current_hashrate"] = current_metrics.hash_rate
            self.mining_stats["cpu_usage"] = current_metrics.cpu_usage
            self.mining_stats["efficiency"] = current_metrics.efficiency
        
        # Add mining-specific stats
        self.mining_stats.update({
            "blocks_mined": self.blocks_mined,
            "total_earnings": self.total_earnings,
            "miner_address": self.miner_address,
            "mining_mode": self.mining_mode,
            "threads": self.num_threads
        })
        
        return self.mining_stats
    
    def benchmark_mining(self, duration: int = 30) -> dict:
        """Benchmark mining performance"""
        print(f"🏃 Running {duration}s mining benchmark...")
        
        # Start monitoring
        self.monitor.start_monitoring()
        start_time = time.time()
        
        # Mine for specified duration
        self.mining = True
        blocks_found = 0
        
        while time.time() - start_time < duration and self.mining:
            block = self._mine_single_block()
            if block:
                blocks_found += 1
                self._on_block_found(block)
            time.sleep(0.1)
        
        self.mining = False
        
        # Get performance summary
        summary = self.monitor.get_performance_summary(duration_minutes=duration/60)
        self.monitor.stop_monitoring()
        
        # Calculate benchmark results
        elapsed = time.time() - start_time
        results = {
            "duration": elapsed,
            "blocks_found": blocks_found,
            "blocks_per_hour": (blocks_found / elapsed) * 3600 if elapsed > 0 else 0,
            "performance_summary": summary
        }
        
        print(f"\n📊 Benchmark Results:")
        print(f"⏱️ Duration: {elapsed:.1f}s")
        print(f"🔢 Blocks found: {blocks_found}")
        print(f"📈 Blocks per hour: {results['blocks_per_hour']:.1f}")
        
        if summary and "hash_rate" in summary:
            hr_stats = summary["hash_rate"]
            print(f"⛏️ Average hash rate: {hr_stats.get('average', 0):.0f} H/s")
            print(f"🚀 Peak hash rate: {hr_stats.get('maximum', 0):.0f} H/s")
        
        return results
    
    def optimize_mining(self):
        """Optimize mining parameters"""
        print("🔧 Optimizing mining parameters...")
        
        # Benchmark different thread counts
        optimal_threads = self.multi_threaded_miner.optimize_thread_count(test_duration=5)
        
        # Benchmark different mining modes
        print("🏁 Testing mining strategies...")
        
        modes = ["multi_thread", "optimized"]
        best_mode = self.mining_mode
        best_hashrate = 0
        
        for mode in modes:
            old_mode = self.mining_mode
            self.mining_mode = mode
            
            result = self.benchmark_mining(duration=10)
            avg_hashrate = result["performance_summary"].get("hash_rate", {}).get("average", 0)
            
            if avg_hashrate > best_hashrate:
                best_hashrate = avg_hashrate
                best_mode = mode
            
            print(f"   {mode}: {avg_hashrate:.0f} H/s")
            
            self.mining_mode = old_mode
        
        # Apply optimizations
        self.mining_mode = best_mode
        self.num_threads = optimal_threads
        
        print(f"\n🎯 Optimizations applied:")
        print(f"   Best mode: {best_mode}")
        print(f"   Optimal threads: {optimal_threads}")
        print(f"   Expected hashrate: {best_hashrate:.0f} H/s")


# Convenience function for quick mining
def quick_miner(miner_address: str, num_threads: int = 4, duration: int = 60):
    """Quick start mining with default settings"""
    from core.blockchain import Blockchain
    
    blockchain = Blockchain()
    miner = Miner(blockchain, miner_address, mining_mode="multi_thread", num_threads=num_threads)
    
    try:
        if duration > 0:
            print(f"⏰ Mining for {duration} seconds...")
            time.sleep(duration)
        else:
            print("⏰ Mining indefinitely (Ctrl+C to stop)...")
            while True:
                time.sleep(1)
    
    except KeyboardInterrupt:
        pass
    
    finally:
        miner.stop_mining()


if __name__ == "__main__":
    # Quick test
    quick_miner("test_miner", num_threads=2, duration=10)