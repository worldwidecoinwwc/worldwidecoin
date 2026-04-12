#!/usr/bin/env python3
"""
WorldWideCoin Mining Starter
Simple script to start mining WorldWideCoin
"""

import time
import threading
from core.blockchain import Blockchain
from mining.multi_threaded_miner import MultiThreadedMiner


class MiningDashboard:
    """Simple mining dashboard"""
    
    def __init__(self):
        self.running = False
        self.blocks_mined = 0
        self.start_time = None
        self.miner = None
        self.blockchain = None
    
    def start_mining(self, threads=4):
        """Start mining with specified number of threads"""
        print("WorldWideCoin Mining Dashboard")
        print("=" * 50)
        
        try:
            # Initialize blockchain
            print("Initializing blockchain...")
            self.blockchain = Blockchain()
            
            # Create miner
            print(f"Creating multi-threaded miner with {threads} threads...")
            self.miner = MultiThreadedMiner(num_threads=threads)
            
            # Start mining
            print("Starting mining...")
            self.running = True
            self.start_time = time.time()
            
            # Start mining in background thread
            mining_thread = threading.Thread(target=self._mine_loop, daemon=True)
            mining_thread.start()
            
            # Start dashboard
            self._run_dashboard()
            
        except KeyboardInterrupt:
            print("\nStopping mining...")
            self.stop_mining()
        except Exception as e:
            print(f"Mining error: {e}")
            self.stop_mining()
    
    def _mine_loop(self):
        """Mining loop"""
        while self.running:
            try:
                # Mine a block using blockchain's mining method
                block = self.blockchain.create_block("dashboard_miner")
                
                if block:
                    # Add block to blockchain
                    self.blockchain.add_block(block)
                    self.blocks_mined += 1
                    
                    print(f"\n{'='*50}")
                    print(f"BLOCK MINED! #{block.index}")
                    print(f"Hash: {block.calculate_hash()[:16]}...")
                    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(block.timestamp))}")
                    print(f"Difficulty: {block.difficulty}")
                    print(f"Nonce: {block.nonce}")
                    print(f"Transactions: {len(block.transactions)}")
                    print(f"{'='*50}\n")
                
                time.sleep(1)  # Small delay between mining attempts
                
            except Exception as e:
                print(f"Mining error: {e}")
                time.sleep(5)
    
    def _run_dashboard(self):
        """Run mining dashboard"""
        try:
            while self.running:
                # Clear screen
                print("\033[2J\033[H", end="")
                
                # Display dashboard
                self._display_dashboard()
                
                # Wait for update
                time.sleep(2)
                
        except KeyboardInterrupt:
            self.running = False
    
    def _display_dashboard(self):
        """Display mining dashboard"""
        elapsed_time = time.time() - self.start_time if self.start_time else 0
        
        print(f"""
{'='*60}
WORLDWIDECOIN MINING DASHBOARD
{'='*60}

Mining Status: {'ACTIVE' if self.running else 'STOPPED'}
Mining Threads: {self.miner.num_threads if self.miner else 'N/A'}
Blocks Mined: {self.blocks_mined}
Mining Time: {self._format_time(elapsed_time)}
Hash Rate: {self._calculate_hash_rate():.2f} H/s
Blockchain Height: {len(self.blockchain.chain)}
Current Difficulty: {self.blockchain.get_difficulty() if hasattr(self.blockchain, 'get_difficulty') else 'N/A'}
Mempool Size: {len(self.blockchain.mempool.transactions)}

Recent Blocks:
{self._get_recent_blocks()}

Controls:
- Press Ctrl+C to stop mining
- Check terminal for new block notifications
{'='*60}
        """)
    
    def _format_time(self, seconds):
        """Format time in readable format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def _calculate_hash_rate(self):
        """Calculate hash rate"""
        if not self.start_time or self.blocks_mined == 0:
            return 0.0
        
        elapsed_time = time.time() - self.start_time
        if elapsed_time > 0:
            # Simplified hash rate calculation
            return self.blocks_mined / elapsed_time
        return 0.0
    
    def _get_recent_blocks(self):
        """Get recent blocks information"""
        if not self.blockchain.chain:
            return "No blocks mined yet"
        
        recent_blocks = []
        for block in self.blockchain.chain[-3:]:  # Last 3 blocks
            recent_blocks.append(
                f"#{block.index}: {block.calculate_hash()[:12]}... "
                f"({time.strftime('%H:%M:%S', time.localtime(block.timestamp))})"
            )
        
        return "\n".join(recent_blocks) if recent_blocks else "No blocks available"
    
    def stop_mining(self):
        """Stop mining"""
        self.running = False
        if self.miner:
            self.miner.stop()
        
        # Final statistics
        if self.start_time:
            total_time = time.time() - self.start_time
            print(f"\n{'='*50}")
            print("MINING STOPPED")
            print(f"{'='*50}")
            print(f"Total Blocks Mined: {self.blocks_mined}")
            print(f"Total Mining Time: {self._format_time(total_time)}")
            print(f"Average Hash Rate: {self._calculate_hash_rate():.2f} H/s")
            print(f"Final Blockchain Height: {len(self.blockchain.chain)}")
            print(f"{'='*50}")


def main():
    """Main function"""
    print("WorldWideCoin Mining Starter")
    print("=" * 30)
    
    # Get user preferences
    try:
        threads = input("Enter number of mining threads (1-8, default=4): ").strip()
        threads = int(threads) if threads else 4
        threads = max(1, min(8, threads))  # Limit between 1-8
    except ValueError:
        threads = 4
    
    print(f"Starting mining with {threads} threads...")
    
    # Create and start mining dashboard
    dashboard = MiningDashboard()
    dashboard.start_mining(threads)


if __name__ == "__main__":
    main()
