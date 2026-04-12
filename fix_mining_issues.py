#!/usr/bin/env python3
"""
Fix WorldWideCoin mining issues
Handles corrupted files and ensures clean startup
"""

import os
import json
import shutil


def fix_corrupted_files():
    """Fix all corrupted files that prevent mining"""
    print("WorldWideCoin Mining Issues Fix")
    print("=" * 40)
    
    files_to_check = [
        "utxo.json",
        "chain.json", 
        "core/utxo.json",
        "core/chain.json"
    ]
    
    fixed_files = []
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            try:
                # Try to read the file
                with open(file_path, 'r') as f:
                    json.load(f)
                print(f"  {file_path}: OK")
            except (json.JSONDecodeError, IOError, ValueError):
                print(f"  {file_path}: CORRUPTED - Removing...")
                try:
                    # Backup the corrupted file
                    backup_path = f"{file_path}.backup"
                    shutil.copy2(file_path, backup_path)
                    print(f"    Backup saved to: {backup_path}")
                    
                    # Remove corrupted file
                    os.remove(file_path)
                    fixed_files.append(file_path)
                    print(f"    Removed corrupted file")
                except Exception as e:
                    print(f"    Error removing file: {e}")
        else:
            print(f"  {file_path}: Not found")
    
    print(f"\nFixed {len(fixed_files)} corrupted files")
    return fixed_files


def create_clean_environment():
    """Create a clean mining environment"""
    print("\nCreating clean mining environment...")
    
    # Ensure directories exist
    directories = ["core", "storage", "mining", "wallet"]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"  Created directory: {directory}")
    
    # Create empty valid files if needed
    files_to_create = [
        ("core/utxo.json", "{}"),
        ("storage/chain.json", "[]")
    ]
    
    for file_path, content in files_to_create:
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"  Created clean file: {file_path}")


def test_blockchain_startup():
    """Test blockchain startup after fixes"""
    print("\nTesting blockchain startup...")
    
    try:
        from core.blockchain import Blockchain
        
        print("  Importing blockchain module...")
        blockchain = Blockchain()
        
        print(f"  Blockchain created successfully")
        print(f"  Chain length: {len(blockchain.chain)}")
        print(f"  UTXO set size: {len(blockchain.utxo.utxos)}")
        print(f"  Mempool size: {len(blockchain.mempool.transactions)}")
        print(f"  Current difficulty: {blockchain.get_difficulty()}")
        print(f"  Current block reward: {blockchain.get_block_reward():.6f} WWC")
        
        return True
        
    except Exception as e:
        print(f"  Blockchain startup failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mining_functionality():
    """Test basic mining functionality"""
    print("\nTesting mining functionality...")
    
    try:
        from core.blockchain import Blockchain
        
        blockchain = Blockchain()
        
        # Test block creation
        miner_address = "test_miner_fix"
        block = blockchain.create_block(miner_address)
        
        print(f"  Block created: #{block.index}")
        print(f"  Block hash: {block.calculate_hash()[:16]}...")
        print(f"  Block reward: {blockchain.get_block_reward():.6f} WWC")
        
        # Test block addition
        blockchain.add_block(block)
        
        print(f"  Block added successfully")
        print(f"  New chain length: {len(blockchain.chain)}")
        
        return True
        
    except Exception as e:
        print(f"  Mining test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def generate_mining_script():
    """Generate a working mining script"""
    mining_script = '''#!/usr/bin/env python3
"""
Fixed WorldWideCoin Mining Script
Use this script for mining after fixes
"""

import time
import signal
import sys
from core.blockchain import Blockchain


class FixedMiner:
    def __init__(self):
        self.running = False
        self.blocks_mined = 0
        self.start_time = None
        self.blockchain = None
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\\nStopping mining...")
        self.running = False
        self.show_stats()
        sys.exit(0)
    
    def start_mining(self, miner_address="fixed_miner"):
        """Start mining with fixed blockchain"""
        print("WorldWideCoin Fixed Mining")
        print("=" * 40)
        
        # Set up signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        
        try:
            # Create blockchain
            print("Initializing blockchain...")
            self.blockchain = Blockchain()
            
            print(f"Blockchain ready: {len(self.blockchain.chain)} blocks")
            print(f"Current difficulty: {self.blockchain.get_difficulty()}")
            print(f"Current block reward: {self.blockchain.get_block_reward():.6f} WWC")
            
            # Start mining
            self.running = True
            self.start_time = time.time()
            
            print(f"\\nStarting mining with address: {miner_address}")
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
                    
                    print(f"\\nBLOCK MINED! #{block.index}")
                    print(f"Hash: {block.calculate_hash()[:16]}...")
                    print(f"Reward: {self.blockchain.get_block_reward():.6f} WWC")
                    print(f"Total Blocks: {self.blocks_mined}")
                    print(f"Hash Rate: {hash_rate:.2f} H/s")
                    print(f"Blockchain Height: {len(self.blockchain.chain)}")
                    
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"Mining error: {e}")
                    time.sleep(5)
        
        except Exception as e:
            print(f"Initialization error: {e}")
            import traceback
            traceback.print_exc()
    
    def show_stats(self):
        """Show mining statistics"""
        if self.start_time:
            total_time = time.time() - self.start_time
            print(f"\\n{'='*40}")
            print("MINING STATISTICS")
            print(f"{'='*40}")
            print(f"Total Blocks Mined: {self.blocks_mined}")
            print(f"Total Mining Time: {self._format_time(total_time)}")
            
            if self.blockchain:
                print(f"Final Blockchain Height: {len(self.blockchain.chain)}")
                print(f"Current Difficulty: {self.blockchain.get_difficulty()}")
                print(f"Current Block Reward: {self.blockchain.get_block_reward():.6f} WWC")
            print(f"{'='*40}")
    
    def _format_time(self, seconds):
        """Format time in readable format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"


if __name__ == "__main__":
    miner = FixedMiner()
    miner.start_mining()
'''
    
    with open('fixed_mining.py', 'w') as f:
        f.write(mining_script)
    
    print("  Generated: fixed_mining.py")


def main():
    """Main fix function"""
    print("WorldWideCoin Mining Issues Fix Tool")
    print("=" * 50)
    
    # Step 1: Fix corrupted files
    fixed_files = fix_corrupted_files()
    
    # Step 2: Create clean environment
    create_clean_environment()
    
    # Step 3: Test blockchain startup
    blockchain_ok = test_blockchain_startup()
    
    # Step 4: Test mining functionality
    mining_ok = test_mining_functionality()
    
    # Step 5: Generate working mining script
    generate_mining_script()
    
    # Summary
    print("\n" + "=" * 50)
    print("FIX SUMMARY")
    print("=" * 50)
    print(f"Corrupted files fixed: {len(fixed_files)}")
    print(f"Blockchain startup: {'PASS' if blockchain_ok else 'FAIL'}")
    print(f"Mining functionality: {'PASS' if mining_ok else 'FAIL'}")
    
    if blockchain_ok and mining_ok:
        print("\nSUCCESS: All issues fixed!")
        print("\nYou can now start mining with:")
        print("  python fixed_mining.py")
        print("\nOr use your original mining scripts:")
        print("  python start_mining.py")
        print("  python clean_mining.py")
    else:
        print("\nSome issues remain. Check the error messages above.")
    
    print("=" * 50)


if __name__ == "__main__":
    main()
