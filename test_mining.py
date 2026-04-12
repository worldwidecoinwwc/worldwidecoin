#!/usr/bin/env python3
"""
Phase 4 Mining Testing Suite
Tests multi-threaded mining, performance optimization, and difficulty adjustment
"""

import time
import threading
from core.blockchain import Blockchain
from mining.miner import Miner
from mining.multi_threaded_miner import MultiThreadedMiner
from mining.optimized_miner import OptimizedMiner
from mining.difficulty_adjustment import DifficultyAdjustment, AdaptiveDifficulty
from mining.performance_monitor import PerformanceMonitor


def test_basic_mining():
    """Test 1: Basic mining functionality"""
    print("=== TEST 1: Basic Mining ===")
    
    blockchain = Blockchain()
    miner = Miner(blockchain, "test_miner", mining_mode="optimized")
    
    # Mine single block
    print("Mining single block...")
    start_time = time.time()
    
    block = miner._mine_single_block()
    
    if block:
        elapsed = time.time() - start_time
        print(f"✅ Block mined in {elapsed:.2f}s")
        print(f"   Index: {block.index}")
        print(f"   Hash: {block.hash[:16]}...")
        print(f"   Nonce: {block.nonce}")
    else:
        print("❌ Failed to mine block")
    
    print()


def test_multi_threaded_mining():
    """Test 2: Multi-threaded mining"""
    print("=== TEST 2: Multi-Threaded Mining ===")
    
    blockchain = Blockchain()
    multi_miner = MultiThreadedMiner(num_threads=4)
    
    # Create test block
    block = blockchain.create_block("multi_miner")
    
    print("Mining with 4 threads...")
    start_time = time.time()
    
    mined_block = multi_miner.mine_block(block)
    
    if mined_block:
        elapsed = time.time() - start_time
        stats = multi_miner.get_stats()
        
        print(f"✅ Block mined in {elapsed:.2f}s")
        print(f"   Hash rate: {stats['hash_rate']:.0f} H/s")
        print(f"   Total hashes: {stats['total_hashes']:,}")
        print(f"   Nonce: {mined_block.nonce}")
    else:
        print("❌ Failed to mine block")
    
    multi_miner.stop_mining()
    print()


def test_performance_monitoring():
    """Test 3: Performance monitoring"""
    print("=== TEST 3: Performance Monitoring ===")
    
    monitor = PerformanceMonitor(update_interval=1.0)
    
    def test_alert(alert, metrics):
        print(f"🚨 Alert: {alert}")
    
    monitor.add_alert_callback(test_alert)
    monitor.start_monitoring()
    
    # Simulate mining stats
    print("Simulating mining performance...")
    for i in range(5):
        monitor.update_mining_stats(
            hash_rate=1000 + i * 200,
            blocks_found=i // 2,
            difficulty=3
        )
        time.sleep(1)
    
    # Get performance summary
    summary = monitor.get_performance_summary(duration_minutes=1)
    print(f"Performance Summary:")
    print(f"   Average hash rate: {summary.get('hash_rate', {}).get('average', 0):.0f} H/s")
    print(f"   CPU usage: {summary.get('cpu_usage', {}).get('average', 0):.1f}%")
    
    monitor.stop_monitoring()
    print()


def test_difficulty_adjustment():
    """Test 4: Difficulty adjustment"""
    print("=== TEST 4: Difficulty Adjustment ===")
    
    from core.block import Block
    from core.transaction import Transaction
    
    # Create fake blockchain history
    blocks = []
    current_time = time.time()
    
    for i in range(20):
        block = Block(
            index=i,
            prev_hash=blocks[-1].hash if blocks else "0" * 64,
            transactions=[],
            timestamp=current_time + i * 30,  # 30 second intervals
            difficulty=2
        )
        block.hash = block.calculate_hash()
        blocks.append(block)
    
    # Test difficulty adjustment
    adjuster = DifficultyAdjustment(target_block_time=10.0, window_size=10)
    
    print("Testing difficulty adjustment...")
    old_difficulty = blocks[-1].difficulty
    new_difficulty = adjuster.calculate_difficulty(blocks)
    
    print(f"   Old difficulty: {old_difficulty}")
    print(f"   New difficulty: {new_difficulty}")
    
    # Get mining stats
    stats = adjuster.get_mining_stats(blocks)
    print(f"   Average block time: {stats.get('avg_block_time', 0):.1f}s")
    print(f"   Estimated hash rate: {stats.get('estimated_hash_rate', 0):.0f} H/s")
    print(f"   Difficulty trend: {stats.get('difficulty_trend', 'unknown')}")
    
    print()


def test_mining_benchmark():
    """Test 5: Mining benchmark"""
    print("=== TEST 5: Mining Benchmark ===")
    
    blockchain = Blockchain()
    miner = Miner(blockchain, "benchmark_miner", mining_mode="multi_thread", num_threads=2)
    
    print("Running 15-second benchmark...")
    results = miner.benchmark_mining(duration=15)
    
    print(f"Benchmark Results:")
    print(f"   Duration: {results['duration']:.1f}s")
    print(f"   Blocks found: {results['blocks_found']}")
    print(f"   Blocks per hour: {results['blocks_per_hour']:.1f}")
    
    perf_summary = results.get('performance_summary', {})
    if 'hash_rate' in perf_summary:
        hr_stats = perf_summary['hash_rate']
        print(f"   Average hash rate: {hr_stats.get('average', 0):.0f} H/s")
        print(f"   Peak hash rate: {hr_stats.get('maximum', 0):.0f} H/s")
    
    print()


def test_mining_optimization():
    """Test 6: Mining optimization"""
    print("=== TEST 6: Mining Optimization ===")
    
    blockchain = Blockchain()
    miner = Miner(blockchain, "optimize_miner", mining_mode="multi_thread", num_threads=4)
    
    print("Running optimization test...")
    miner.optimize_mining()
    
    print()


def test_continuous_mining():
    """Test 7: Continuous mining"""
    print("=== TEST 7: Continuous Mining (20s) ===")
    
    blockchain = Blockchain()
    miner = Miner(blockchain, "continuous_miner", mining_mode="multi_thread", num_threads=2)
    
    # Start mining in background
    mining_thread = threading.Thread(target=miner.start_mining, args=(True,), daemon=True)
    mining_thread.start()
    
    # Mine for 20 seconds
    print("Mining for 20 seconds...")
    time.sleep(20)
    
    # Stop mining
    miner.stop_mining()
    
    # Get final stats
    stats = miner.get_mining_stats()
    print(f"Final Stats:")
    print(f"   Blocks mined: {stats.get('blocks_mined', 0)}")
    print(f"   Total earnings: {stats.get('total_earnings', 0):.8f} WWC")
    print(f"   Uptime: {stats.get('uptime', 0):.1f}s")
    
    if stats.get('blocks_mined', 0) > 0:
        uptime = stats.get('uptime', 0)
        blocks = stats.get('blocks_mined', 0)
        earnings_per_hour = (stats.get('total_earnings', 0) / uptime) * 3600
        print(f"   Earnings per hour: {earnings_per_hour:.8f} WWC/h")
    
    print()


def test_mining_strategies():
    """Test 8: Different mining strategies"""
    print("=== TEST 8: Mining Strategy Comparison ===")
    
    blockchain = Blockchain()
    
    strategies = ["optimized", "multi_thread"]
    results = {}
    
    for strategy in strategies:
        print(f"Testing {strategy} strategy...")
        
        miner = Miner(blockchain, f"{strategy}_miner", mining_mode=strategy, num_threads=2)
        
        # Run quick benchmark
        result = miner.benchmark_mining(duration=10)
        avg_hashrate = result.get('performance_summary', {}).get('hash_rate', {}).get('average', 0)
        
        results[strategy] = {
            'hashrate': avg_hashrate,
            'blocks_found': result.get('blocks_found', 0)
        }
        
        print(f"   Hash rate: {avg_hashrate:.0f} H/s")
        print(f"   Blocks found: {result.get('blocks_found', 0)}")
        print()
    
    # Find best strategy
    best_strategy = max(results.keys(), key=lambda k: results[k]['hashrate'])
    print(f"Best strategy: {best_strategy} ({results[best_strategy]['hashrate']:.0f} H/s)")
    
    print()


def main():
    """Run all Phase 4 mining tests"""
    print("WorldWideCoin Phase 4 - Mining Testing")
    print("=" * 50)
    
    tests = [
        test_basic_mining,
        test_multi_threaded_mining,
        test_performance_monitoring,
        test_difficulty_adjustment,
        test_mining_benchmark,
        test_mining_optimization,
        test_continuous_mining,
        test_mining_strategies
    ]
    
    for i, test in enumerate(tests, 1):
        try:
            test()
        except Exception as e:
            print(f"❌ Test {i} failed: {e}")
            print()
    
    print("=" * 50)
    print("Phase 4 Mining Testing Complete!")


if __name__ == "__main__":
    main()
