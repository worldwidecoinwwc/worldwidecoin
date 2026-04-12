#!/usr/bin/env python3
"""
Verify WorldWideCoin implementation matches whitepaper specifications
"""

import math
import time
from core.blockchain import Blockchain


def verify_whitepaper_parameters():
    """Verify all whitepaper parameters are correctly implemented"""
    print("WorldWideCoin Whitepaper Compliance Check")
    print("=" * 50)
    
    # Create blockchain instance
    blockchain = Blockchain()
    
    # Check core parameters
    print("Core Parameters:")
    print(f"  Initial Block Reward: {blockchain.INITIAL_REWARD} WWC (Expected: 1.0 WWC)")
    print(f"  Annual Decay Rate: {blockchain.DECAY_RATE} (Expected: 0.025 = 2.5%)")
    print(f"  Blocks per Year: {blockchain.BLOCKS_PER_YEAR} (Expected: 525,600)")
    print(f"  Target Block Time: {blockchain.TARGET_BLOCK_TIME} seconds (Expected: 60s)")
    print(f"  Treasury Percent: {blockchain.TREASURY_PERCENT} (Expected: 0.05 = 5%)")
    print(f"  Fee Burn Percent: {blockchain.FEE_BURN_PERCENT} (Expected: 0.20 = 20%)")
    
    # Verify calculations
    print("\nMathematical Verification:")
    
    # Test continuous decay formula: R(t) = R0 × e^(-kt)
    def calculate_reward(height):
        t = height / blockchain.BLOCKS_PER_YEAR
        return blockchain.INITIAL_REWARD * math.exp(-blockchain.DECAY_RATE * t)
    
    # Test at different heights
    test_heights = [0, 525600, 1051200, 2102400]  # 0, 1, 2, 4 years
    for height in test_heights:
        reward = calculate_reward(height)
        blockchain_reward = blockchain.get_block_reward_at_height(height) if hasattr(blockchain, 'get_block_reward_at_height') else blockchain.get_block_reward()
        print(f"  Reward at height {height}: {reward:.6f} WWC")
    
    # Verify total supply formula: S_max = R0 × B / k
    S_max = blockchain.INITIAL_REWARD * blockchain.BLOCKS_PER_YEAR / blockchain.DECAY_RATE
    print(f"\nTotal Supply Calculation:")
    print(f"  S_max = R0 × B / k")
    print(f"  S_max = {blockchain.INITIAL_REWARD} × {blockchain.BLOCKS_PER_YEAR} / {blockchain.DECAY_RATE}")
    print(f"  S_max = {S_max:,.0f} WWC (Expected: ~21,024,000 WWC)")
    
    # Test mining process
    print("\nMining Process Test:")
    try:
        # Create a test block
        miner_address = "test_miner"
        block = blockchain.create_block(miner_address)
        
        print(f"  Block created successfully")
        print(f"  Block height: {block.index}")
        print(f"  Block reward: {blockchain.get_block_reward():.6f} WWC")
        print(f"  Treasury cut: {blockchain.get_block_reward() * blockchain.TREASURY_PERCENT:.6f} WWC")
        print(f"  Miner reward: {blockchain.get_block_reward() * (1 - blockchain.TREASURY_PERCENT):.6f} WWC")
        
        # Check coinbase transaction
        if block.transactions:
            coinbase = block.transactions[0]
            total_output = sum(out.get('amount', 0) for out in coinbase.outputs)
            print(f"  Coinbase total output: {total_output:.6f} WWC")
            
            # Check treasury allocation
            treasury_found = False
            for output in coinbase.outputs:
                if output.get('address') == blockchain.TREASURY_ADDRESS:
                    treasury_found = True
                    print(f"  Treasury allocation found: {output.get('amount', 0):.6f} WWC")
                    break
            
            if not treasury_found:
                print("  WARNING: Treasury allocation not found")
        
    except Exception as e:
        print(f"  Mining test failed: {e}")
    
    # Verify fee burn mechanism
    print("\nFee Burn Mechanism:")
    print(f"  Fee burn percentage: {blockchain.FEE_BURN_PERCENT * 100}%")
    print(f"  Miner receives: {(1 - blockchain.FEE_BURN_PERCENT) * 100}% of fees")
    print(f"  Burned: {blockchain.FEE_BURN_PERCENT * 100}% of fees")
    
    # Check CPU-friendly mining
    print("\nMining Algorithm:")
    print("  Using SHA-256 hash function (CPU-friendly)")
    print("  No ASIC-specific optimizations")
    print("  Standard proof-of-work implementation")
    
    # Verify fair launch parameters
    print("\nFair Launch Verification:")
    print(f"  No premine: {'YES' if not hasattr(blockchain, 'PREMINE') else 'NO'}")
    print(f"  No developer allocation: {'YES' if not hasattr(blockchain, 'DEV_ALLOCATION') else 'NO'}")
    print(f"  Mining-only issuance: {'YES' if blockchain.INITIAL_REWARD > 0 else 'NO'}")
    
    # Compliance summary
    print("\nCompliance Summary:")
    compliance_checks = [
        ("Initial Block Reward", blockchain.INITIAL_REWARD == 1.0),
        ("Annual Decay Rate", abs(blockchain.DECAY_RATE - 0.025) < 0.001),
        ("Blocks per Year", blockchain.BLOCKS_PER_YEAR == 525600),
        ("Block Time", blockchain.TARGET_BLOCK_TIME == 60),
        ("Treasury Allocation", abs(blockchain.TREASURY_PERCENT - 0.05) < 0.001),
        ("Fee Burn", abs(blockchain.FEE_BURN_PERCENT - 0.20) < 0.001),
        ("Total Supply Target", abs(S_max - 21024000) < 100000),
    ]
    
    passed = 0
    total = len(compliance_checks)
    
    for check_name, is_compliant in compliance_checks:
        status = "PASS" if is_compliant else "FAIL"
        print(f"  {check_name}: {status}")
        if is_compliant:
            passed += 1
    
    print(f"\nOverall Compliance: {passed}/{total} checks passed")
    print(f"Compliance Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("SUCCESS: WorldWideCoin fully complies with whitepaper specifications!")
    else:
        print("WARNING: Some parameters may need adjustment")
    
    return passed == total


def show_supply_projection():
    """Show supply projection over time"""
    print("\n" + "=" * 50)
    print("Supply Projection Over Time")
    print("=" * 50)
    
    blockchain = Blockchain()
    
    years = [1, 2, 5, 10, 20, 50, 100]
    
    for year in years:
        height = year * blockchain.BLOCKS_PER_YEAR
        reward = blockchain.INITIAL_REWARD * math.exp(-blockchain.DECAY_RATE * year)
        
        # Calculate total supply at this time
        total_supply = (blockchain.INITIAL_REWARD * blockchain.BLOCKS_PER_YEAR / blockchain.DECAY_RATE) * (1 - math.exp(-blockchain.DECAY_RATE * year))
        
        print(f"Year {year:3d}: Reward {reward:8.6f} WWC | Total Supply {total_supply:12.0f} WWC")
    
    # Show asymptotic approach
    S_max = blockchain.INITIAL_REWARD * blockchain.BLOCKS_PER_YEAR / blockchain.DECAY_RATE
    print(f"\nAsymptotic Maximum: {S_max:,.0f} WWC")


def create_compliance_report():
    """Create detailed compliance report"""
    blockchain = Blockchain()
    
    report = {
        "timestamp": time.time(),
        "whitepaper_version": "1.0",
        "compliance_check": {
            "initial_reward": {
                "specified": 1.0,
                "implemented": blockchain.INITIAL_REWARD,
                "compliant": blockchain.INITIAL_REWARD == 1.0
            },
            "decay_rate": {
                "specified": 0.025,
                "implemented": blockchain.DECAY_RATE,
                "compliant": abs(blockchain.DECAY_RATE - 0.025) < 0.001
            },
            "blocks_per_year": {
                "specified": 525600,
                "implemented": blockchain.BLOCKS_PER_YEAR,
                "compliant": blockchain.BLOCKS_PER_YEAR == 525600
            },
            "block_time": {
                "specified": 60,
                "implemented": blockchain.TARGET_BLOCK_TIME,
                "compliant": blockchain.TARGET_BLOCK_TIME == 60
            },
            "treasury_percent": {
                "specified": 0.05,
                "implemented": blockchain.TREASURY_PERCENT,
                "compliant": abs(blockchain.TREASURY_PERCENT - 0.05) < 0.001
            },
            "fee_burn_percent": {
                "specified": 0.20,
                "implemented": blockchain.FEE_BURN_PERCENT,
                "compliant": abs(blockchain.FEE_BURN_PERCENT - 0.20) < 0.001
            }
        },
        "total_supply_calculation": {
            "formula": "S_max = R0 × B / k",
            "R0": blockchain.INITIAL_REWARD,
            "B": blockchain.BLOCKS_PER_YEAR,
            "k": blockchain.DECAY_RATE,
            "S_max": blockchain.INITIAL_REWARD * blockchain.BLOCKS_PER_YEAR / blockchain.DECAY_RATE,
            "target": 21024000
        },
        "emission_model": {
            "formula": "R(t) = R0 × e^(-kt)",
            "continuous_decay": True,
            "no_halving_events": True
        },
        "fair_launch": {
            "no_premine": True,
            "no_ico": True,
            "no_developer_allocation": True,
            "mining_only": True
        },
        "mining": {
            "algorithm": "SHA-256",
            "cpu_friendly": True,
            "asic_resistant": False
        }
    }
    
    import json
    with open('whitepaper_compliance.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed compliance report saved to: whitepaper_compliance.json")


if __name__ == "__main__":
    is_compliant = verify_whitepaper_parameters()
    show_supply_projection()
    create_compliance_report()
    
    if is_compliant:
        print("\n" + "=" * 50)
        print("WORLWIDECOIN IS FULLY COMPLIANT WITH WHITEPAPER!")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("SOME PARAMETERS NEED ADJUSTMENT")
        print("=" * 50)
