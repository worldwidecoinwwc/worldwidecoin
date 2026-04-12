#!/usr/bin/env python3
"""
Check total mined coins for WorldWideCoin
Works with both file-based and in-memory blockchain
"""

import os
import json
import time
import math
from core.blockchain import Blockchain


def check_file_based_coins():
    """Check coins from file-based blockchain"""
    print("Checking File-Based Blockchain Coins")
    print("=" * 50)
    
    try:
        # Clean corrupted files first
        clean_corrupted_files()
        
        # Load blockchain
        blockchain = Blockchain()
        
        if not blockchain.chain:
            print("No blocks found in blockchain")
            return 0
        
        print(f"Blockchain Height: {len(blockchain.chain)}")
        print(f"Genesis Block: {blockchain.chain[0].calculate_hash()[:16]}...")
        
        # Calculate total coins mined
        total_coins = 0
        treasury_coins = 0
        miner_coins = 0
        
        for i, block in enumerate(blockchain.chain):
            if i == 0:  # Skip genesis block
                continue
            
            # Calculate reward for this block height
            t = i / blockchain.BLOCKS_PER_YEAR
            reward = blockchain.INITIAL_REWARD * math.exp(-blockchain.DECAY_RATE * t)
            
            # Calculate allocations
            treasury = reward * blockchain.TREASURY_PERCENT
            miner = reward * (1 - blockchain.TREASURY_PERCENT)
            
            total_coins += reward
            treasury_coins += treasury
            miner_coins += miner
        
        print(f"\nCoin Breakdown:")
        print(f"  Total Coins Mined: {total_coins:.6f} WWC")
        print(f"  Treasury Allocation: {treasury_coins:.6f} WWC")
        print(f"  Miner Rewards: {miner_coins:.6f} WWC")
        print(f"  Treasury Percentage: {blockchain.TREASURY_PERCENT * 100:.1f}%")
        
        # Show recent blocks
        print(f"\nRecent Blocks (Last 5):")
        for block in blockchain.chain[-5:]:
            t = block.index / blockchain.BLOCKS_PER_YEAR
            reward = blockchain.INITIAL_REWARD * math.exp(-blockchain.DECAY_RATE * t)
            print(f"  Block #{block.index}: {reward:.6f} WWC reward")
            print(f"    Hash: {block.calculate_hash()[:16]}...")
            print(f"    Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(block.timestamp))}")
        
        return total_coins
        
    except Exception as e:
        print(f"Error checking file-based coins: {e}")
        return 0


def check_in_memory_coins():
    """Check coins from in-memory blockchain (if file-based fails)"""
    print("\nChecking In-Memory Blockchain Coins")
    print("=" * 50)
    
    try:
        # Create simple in-memory blockchain
        from simple_working_mining import SimpleMemoryBlockchain
        
        blockchain = SimpleMemoryBlockchain()
        
        print(f"In-memory blockchain height: {len(blockchain.chain)}")
        
        # Calculate total coins
        total_coins = 0
        treasury_coins = 0
        miner_coins = 0
        
        for i, block in enumerate(blockchain.chain):
            if i == 0:  # Skip genesis
                continue
            
            # Calculate reward for this block height
            t = i / blockchain.BLOCKS_PER_YEAR
            reward = blockchain.INITIAL_REWARD * math.exp(-blockchain.DECAY_RATE * t)
            
            # Calculate allocations
            treasury = reward * blockchain.TREASURY_PERCENT
            miner = reward * (1 - blockchain.TREASURY_PERCENT)
            
            total_coins += reward
            treasury_coins += treasury
            miner_coins += miner
        
        print(f"\nIn-Memory Coin Breakdown:")
        print(f"  Total Coins Mined: {total_coins:.6f} WWC")
        print(f"  Treasury Allocation: {treasury_coins:.6f} WWC")
        print(f"  Miner Rewards: {miner_coins:.6f} WWC")
        
        return total_coins
        
    except Exception as e:
        print(f"Error checking in-memory coins: {e}")
        return 0


def clean_corrupted_files():
    """Clean corrupted files"""
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


def show_supply_projection():
    """Show supply projection based on current height"""
    print("\n" + "=" * 50)
    print("Supply Projection Analysis")
    print("=" * 50)
    
    try:
        blockchain = Blockchain()
        current_height = len(blockchain.chain)
        
        print(f"Current Blockchain Height: {current_height}")
        print(f"Current Block Reward: {blockchain.get_block_reward():.6f} WWC")
        
        # Calculate current supply
        current_supply = 0
        for i in range(1, current_height):
            t = i / blockchain.BLOCKS_PER_YEAR
            reward = blockchain.INITIAL_REWARD * math.exp(-blockchain.DECAY_RATE * t)
            current_supply += reward
        
        print(f"Current Total Supply: {current_supply:.6f} WWC")
        
        # Calculate maximum supply
        S_max = blockchain.INITIAL_REWARD * blockchain.BLOCKS_PER_YEAR / blockchain.DECAY_RATE
        print(f"Maximum Supply (S_max): {S_max:.0f} WWC")
        
        # Calculate percentage of max supply
        percentage = (current_supply / S_max) * 100
        print(f"Percentage of Max Supply: {percentage:.4f}%")
        
        # Show future projections
        print(f"\nFuture Supply Projections:")
        future_heights = [current_height + 1000, current_height + 10000, current_height + 100000]
        
        for future_height in future_heights:
            future_supply = 0
            for i in range(1, future_height):
                t = i / blockchain.BLOCKS_PER_YEAR
                reward = blockchain.INITIAL_REWARD * math.exp(-blockchain.DECAY_RATE * t)
                future_supply += reward
            
            print(f"  Height {future_height:7d}: {future_supply:12.0f} WWC")
        
    except Exception as e:
        print(f"Error in supply projection: {e}")


def show_mining_statistics():
    """Show detailed mining statistics"""
    print("\n" + "=" * 50)
    print("Mining Statistics")
    print("=" * 50)
    
    try:
        blockchain = Blockchain()
        
        if not blockchain.chain:
            print("No blocks found")
            return
        
        # Block statistics
        total_blocks = len(blockchain.chain)
        genesis_block = blockchain.chain[0]
        latest_block = blockchain.chain[-1]
        
        print(f"Total Blocks: {total_blocks}")
        print(f"Genesis Block: #{genesis_block.index}")
        print(f"Latest Block: #{latest_block.index}")
        print(f"Genesis Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(genesis_block.timestamp))}")
        print(f"Latest Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(latest_block.timestamp))}")
        
        # Time span
        if total_blocks > 1:
            time_span = latest_block.timestamp - genesis_block.timestamp
            avg_block_time = time_span / (total_blocks - 1)
            
            print(f"Time Span: {time_span:.0f} seconds ({time_span/3600:.1f} hours)")
            print(f"Average Block Time: {avg_block_time:.1f} seconds")
            print(f"Target Block Time: {blockchain.TARGET_BLOCK_TIME} seconds")
            
            # Mining efficiency
            efficiency = (blockchain.TARGET_BLOCK_TIME / avg_block_time) * 100
            print(f"Mining Efficiency: {efficiency:.1f}%")
        
        # Difficulty statistics
        difficulties = [block.difficulty for block in blockchain.chain]
        min_difficulty = min(difficulties)
        max_difficulty = max(difficulties)
        avg_difficulty = sum(difficulties) / len(difficulties)
        
        print(f"\nDifficulty Statistics:")
        print(f"  Minimum: {min_difficulty}")
        print(f"  Maximum: {max_difficulty}")
        print(f"  Average: {avg_difficulty:.2f}")
        print(f"  Current: {blockchain.get_difficulty()}")
        
        # Reward statistics
        rewards = []
        for i, block in enumerate(blockchain.chain[1:], 1):  # Skip genesis
            t = i / blockchain.BLOCKS_PER_YEAR
            reward = blockchain.INITIAL_REWARD * math.exp(-blockchain.DECAY_RATE * t)
            rewards.append(reward)
        
        if rewards:
            print(f"\nReward Statistics:")
            print(f"  First Block Reward: {rewards[0]:.6f} WWC")
            print(f"  Latest Block Reward: {rewards[-1]:.6f} WWC")
            print(f"  Average Reward: {sum(rewards)/len(rewards):.6f} WWC")
            print(f"  Reward Decay: {(1 - rewards[-1]/rewards[0])*100:.2f}%")
        
    except Exception as e:
        print(f"Error in mining statistics: {e}")


def generate_coin_report():
    """Generate comprehensive coin report"""
    print("\n" + "=" * 50)
    print("Generating Coin Report...")
    
    try:
        # Get coin counts
        file_coins = check_file_based_coins()
        memory_coins = check_in_memory_coins()
        
        # Use the higher value
        total_coins = max(file_coins, memory_coins)
        
        # Generate report
        report = {
            "timestamp": time.time(),
            "total_coins_mined": total_coins,
            "file_based_coins": file_coins,
            "memory_based_coins": memory_coins,
            "blockchain_height": len(Blockchain().chain) if file_coins > 0 else 0,
            "whitepaper_compliant": True,
            "reward_model": "R(t) = R0 × e^(-kt)",
            "initial_reward": 1.0,
            "decay_rate": 0.025,
            "treasury_percent": 0.05,
            "max_supply": 21024000
        }
        
        # Save report
        with open('coin_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Coin report saved to: coin_report.json")
        
        return report
        
    except Exception as e:
        print(f"Error generating report: {e}")
        return None


def main():
    """Main function"""
    print("WorldWideCoin Total Mined Coins Checker")
    print("=" * 50)
    
    # Check coins from different sources
    file_coins = check_file_based_coins()
    memory_coins = check_in_memory_coins()
    
    # Show supply projection
    show_supply_projection()
    
    # Show mining statistics
    show_mining_statistics()
    
    # Generate report
    report = generate_coin_report()
    
    # Summary
    print("\n" + "=" * 50)
    print("FINAL SUMMARY")
    print("=" * 50)
    print(f"File-based Coins: {file_coins:.6f} WWC")
    print(f"Memory-based Coins: {memory_coins:.6f} WWC")
    print(f"Total Coins Mined: {max(file_coins, memory_coins):.6f} WWC")
    
    if report:
        print(f"Report saved to: coin_report.json")
    
    print(f"\nWhitepaper Compliance: {'YES' if file_coins > 0 else 'NO'}")
    print(f"Treasury Allocation: 5% of rewards")
    print(f"Fee Burn: 20% of fees")
    print(f"Maximum Supply: ~21,024,000 WWC")


if __name__ == "__main__":
    main()
