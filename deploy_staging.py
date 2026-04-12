#!/usr/bin/env python3
"""
Simplified Staging Deployment Script
Deploys WorldWideCoin to staging environment for testing
"""

import os
import sys
import time
import json
import threading
from core.blockchain import Blockchain
from network.enhanced_node import EnhancedNode
from deployment.staging_config import create_staging_config


class StagingEnvironment:
    """Simple staging environment for testing"""
    
    def __init__(self):
        self.nodes = []
        self.blockchain = None
        self.config = None
        self.running = False
        
        print("Staging environment initialized")
    
    def setup(self):
        """Setup staging environment"""
        print("Setting up staging environment...")
        
        # Create staging configuration
        self.config = create_staging_config()
        if not self.config:
            print("Failed to create staging configuration")
            return False
        
        # Initialize blockchain
        self.blockchain = Blockchain()
        
        # Create staging nodes
        for i in range(2):  # 2 nodes for staging
            port = 18330 + i
            node = EnhancedNode(port=port)
            self.nodes.append(node)
            print(f"Created staging node on port {port}")
        
        print("Staging environment setup complete")
        return True
    
    def start(self):
        """Start staging environment"""
        if self.running:
            print("Staging environment already running")
            return
        
        print("Starting staging environment...")
        
        # Start nodes
        for node in self.nodes:
            node.start()
        
        # Connect nodes
        if len(self.nodes) > 1:
            for i in range(1, len(self.nodes)):
                self.nodes[i].connect_to_peer("127.0.0.1", self.nodes[0].port)
        
        self.running = True
        print("Staging environment started")
        
        # Wait for startup
        time.sleep(2)
        
        # Run initial tests
        self.run_health_checks()
    
    def stop(self):
        """Stop staging environment"""
        if not self.running:
            return
        
        print("Stopping staging environment...")
        
        # Stop nodes
        for node in self.nodes:
            node.stop()
        
        self.running = False
        print("Staging environment stopped")
    
    def run_health_checks(self):
        """Run health checks on staging environment"""
        print("Running health checks...")
        
        all_healthy = True
        
        # Check nodes
        for i, node in enumerate(self.nodes):
            try:
                status = node.get_status()
                print(f"Node {i}: {'HEALTHY' if status['running'] else 'UNHEALTHY'}")
                print(f"  Address: {status['address']}")
                print(f"  Chain height: {status['blockchain']['height']}")
                print(f"  Active peers: {status['peers']['active_peers']}")
                
                if not status['running']:
                    all_healthy = False
                    
            except Exception as e:
                print(f"Node {i}: ERROR - {e}")
                all_healthy = False
        
        # Check blockchain
        try:
            height = len(self.blockchain.chain)
            print(f"Blockchain: {'HEALTHY' if height > 0 else 'EMPTY'}")
            print(f"  Height: {height}")
            print(f"  Mempool size: {len(self.blockchain.mempool.transactions)}")
            
            if height == 0:
                all_healthy = False
                
        except Exception as e:
            print(f"Blockchain: ERROR - {e}")
            all_healthy = False
        
        print(f"Overall health: {'HEALTHY' if all_healthy else 'UNHEALTHY'}")
        return all_healthy
    
    def test_mining(self):
        """Test mining functionality"""
        print("Testing mining functionality...")
        
        try:
            # Mine a block on first node
            if self.nodes:
                original_height = len(self.blockchain.chain)
                
                # Create and mine block
                block = self.blockchain.create_block("staging_miner")
                self.blockchain.add_block(block)
                
                new_height = len(self.blockchain.chain)
                
                if new_height > original_height:
                    print(f"Mining test: PASS")
                    print(f"  Block mined: #{block.index}")
                    print(f"  Hash: {block.hash[:16]}...")
                    print(f"  Nonce: {block.nonce}")
                    return True
                else:
                    print(f"Mining test: FAIL - No block created")
                    return False
                    
        except Exception as e:
            print(f"Mining test: ERROR - {e}")
            return False
    
    def test_transactions(self):
        """Test transaction functionality"""
        print("Testing transaction functionality...")
        
        try:
            # Create test transaction
            from core.transaction import Transaction
            from core.transaction import TxOutput
            
            tx = Transaction(
                inputs=[],
                outputs=[TxOutput("test_recipient", 10.0)]
            )
            
            # Add to mempool
            self.blockchain.mempool.add_transaction(tx)
            
            mempool_size = len(self.blockchain.mempool.transactions)
            
            if mempool_size > 0:
                print(f"Transaction test: PASS")
                print(f"  Transactions in mempool: {mempool_size}")
                return True
            else:
                print(f"Transaction test: FAIL - No transactions in mempool")
                return False
                
        except Exception as e:
            print(f"Transaction test: ERROR - {e}")
            return False
    
    def test_network_sync(self):
        """Test network synchronization"""
        print("Testing network synchronization...")
        
        if len(self.nodes) < 2:
            print("Network sync test: SKIP - Need at least 2 nodes")
            return True
        
        try:
            # Mine a block on first node
            original_height = len(self.blockchain.chain)
            block = self.blockchain.create_block("sync_test_miner")
            self.blockchain.add_block(block)
            
            # Wait for sync
            time.sleep(3)
            
            # Check if second node has the block
            node2_status = self.nodes[1].get_status()
            node2_height = node2_status['blockchain']['height']
            
            if node2_height > original_height:
                print(f"Network sync test: PASS")
                print(f"  Node 2 height: {node2_height}")
                return True
            else:
                print(f"Network sync test: FAIL - Node 2 height: {node2_height}")
                return False
                
        except Exception as e:
            print(f"Network sync test: ERROR - {e}")
            return False
    
    def run_stress_test(self, duration_minutes: int = 2):
        """Run stress test on staging environment"""
        print(f"Running stress test for {duration_minutes} minutes...")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        metrics = {
            "blocks_mined": 0,
            "transactions_created": 0,
            "errors": []
        }
        
        try:
            while time.time() < end_time:
                # Mine blocks
                try:
                    block = self.blockchain.create_block("stress_test_miner")
                    self.blockchain.add_block(block)
                    metrics["blocks_mined"] += 1
                except Exception as e:
                    metrics["errors"].append(f"Mining error: {e}")
                
                # Create transactions
                try:
                    from core.transaction import Transaction
                    from core.transaction import TxOutput
                    
                    tx = Transaction(
                        inputs=[],
                        outputs=[TxOutput(f"stress_addr_{metrics['transactions_created']}", 1.0)]
                    )
                    self.blockchain.mempool.add_transaction(tx)
                    metrics["transactions_created"] += 1
                except Exception as e:
                    metrics["errors"].append(f"Transaction error: {e}")
                
                # Check health
                if not self.run_health_checks():
                    metrics["errors"].append("Health check failed")
                
                time.sleep(10)  # Every 10 seconds
            
            actual_duration = time.time() - start_time
            
            print(f"Stress test completed:")
            print(f"  Duration: {actual_duration:.1f}s")
            print(f"  Blocks mined: {metrics['blocks_mined']}")
            print(f"  Transactions created: {metrics['transactions_created']}")
            print(f"  Errors: {len(metrics['errors'])}")
            
            return len(metrics["errors"]) == 0
            
        except Exception as e:
            print(f"Stress test failed: {e}")
            return False
    
    def get_status(self):
        """Get staging environment status"""
        status = {
            "running": self.running,
            "nodes": len(self.nodes),
            "blockchain_height": len(self.blockchain.chain) if self.blockchain else 0,
            "mempool_size": len(self.blockchain.mempool.transactions) if self.blockchain else 0,
            "config": {
                "environment": self.config.deployment.environment if self.config else "unknown",
                "network_id": self.config.network.network_id if self.config else 0,
                "port": self.config.network.port if self.config else 0
            }
        }
        
        return status


def main():
    """Main staging deployment function"""
    print("WorldWideCoin Staging Deployment")
    print("=" * 50)
    
    # Create staging environment
    staging = StagingEnvironment()
    
    try:
        # Setup staging
        if not staging.setup():
            print("Staging setup failed")
            return 1
        
        # Start staging
        staging.start()
        
        # Run tests
        print("\n" + "=" * 50)
        print("Running Staging Tests")
        print("=" * 50)
        
        tests = [
            ("Health Checks", staging.run_health_checks),
            ("Mining", staging.test_mining),
            ("Transactions", staging.test_transactions),
            ("Network Sync", staging.test_network_sync)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            print(f"\n--- {test_name} ---")
            try:
                if test_func():
                    passed += 1
                    print(f"Result: PASS")
                else:
                    failed += 1
                    print(f"Result: FAIL")
            except Exception as e:
                failed += 1
                print(f"Result: ERROR - {e}")
        
        # Run stress test
        print(f"\n--- Stress Test ---")
        try:
            if staging.run_stress_test(1):  # 1 minute stress test
                passed += 1
                print("Result: PASS")
            else:
                failed += 1
                print("Result: FAIL")
        except Exception as e:
            failed += 1
            print(f"Result: ERROR - {e}")
        
        # Final status
        print("\n" + "=" * 50)
        print("Staging Test Results")
        print("=" * 50)
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/(passed+failed))*100:.1f}%")
        
        # Get final status
        status = staging.get_status()
        print(f"\nFinal Status:")
        print(f"  Running: {status['running']}")
        print(f"  Nodes: {status['nodes']}")
        print(f"  Blockchain Height: {status['blockchain_height']}")
        print(f"  Mempool Size: {status['mempool_size']}")
        print(f"  Environment: {status['config']['environment']}")
        
        print("\nStaging environment is running. Press Ctrl+C to stop.")
        
        # Keep running
        try:
            while True:
                time.sleep(30)
                health = staging.run_health_checks()
                print(f"Health check: {'OK' if health else 'FAILED'}")
        except KeyboardInterrupt:
            print("\nStopping staging environment...")
        
    finally:
        staging.stop()
        print("Staging environment stopped")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
