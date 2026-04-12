#!/usr/bin/env python3
"""
Test script for Phase 3 - Multi-node network functionality
Demonstrates P2P synchronization, peer discovery, and consensus
"""

import time
import threading
import signal
import sys
from network.enhanced_node import EnhancedNode
from core.transaction import Transaction
from core.block import Block


class NetworkTest:
    """Test suite for multi-node network"""
    
    def __init__(self):
        self.nodes = []
        self.running = True
    
    def signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        print("\nShutting down network test...")
        self.running = False
        for node in self.nodes:
            node.stop()
        sys.exit(0)
    
    def create_network(self, num_nodes: int = 3):
        """Create a network of nodes"""
        print(f"Creating {num_nodes} node network...")
        
        # Create nodes on different ports
        base_port = 8330
        for i in range(num_nodes):
            port = base_port + i
            node = EnhancedNode(port=port)
            self.nodes.append(node)
            print(f"Created node {i+1} on port {port}")
        
        # Connect nodes to each other
        for i, node in enumerate(self.nodes):
            for j, other_node in enumerate(self.nodes):
                if i != j:
                    other_port = base_port + j
                    node.connect_to_peer("127.0.0.1", other_port)
        
        # Start all nodes
        for i, node in enumerate(self.nodes):
            node.start()
            time.sleep(0.5)  # Stagger startup
        
        print("Network created and started!")
    
    def test_blockchain_sync(self):
        """Test blockchain synchronization"""
        print("\n=== Testing Blockchain Synchronization ===")
        
        # Mine a block on node 0
        print("Mining block on node 1...")
        node0 = self.nodes[0]
        node0.blockchain.mine_pending_transactions("miner1")
        
        # Wait for propagation
        time.sleep(3)
        
        # Check all nodes have the same chain
        heights = [len(node.blockchain.chain) for node in self.nodes]
        print(f"Chain heights: {heights}")
        
        if len(set(heights)) == 1:
            print("SUCCESS: All nodes synchronized!")
        else:
            print("FAILED: Nodes not synchronized")
    
    def test_transaction_propagation(self):
        """Test transaction propagation"""
        print("\n=== Testing Transaction Propagation ===")
        
        # Create transaction on node 0
        from core.transaction import TxOutput
        tx = Transaction(
            inputs=[],
            outputs=[TxOutput("bob", 10.0)]
        )
        
        print(f"Broadcasting transaction: {tx.calculate_hash()[:16]}...")
        self.nodes[0].broadcast_transaction(tx)
        
        # Wait for propagation
        time.sleep(2)
        
        # Check all nodes received the transaction
        mempool_sizes = [len(node.blockchain.mempool.transactions) for node in self.nodes]
        print(f"Mempool sizes: {mempool_sizes}")
        
        if all(size > 0 for size in mempool_sizes):
            print("SUCCESS: Transaction propagated to all nodes!")
        else:
            print("FAILED: Transaction not fully propagated")
    
    def test_peer_discovery(self):
        """Test peer discovery"""
        print("\n=== Testing Peer Discovery ===")
        
        for i, node in enumerate(self.nodes):
            status = node.get_status()
            print(f"Node {i+1}: {status['peers']['active_peers']} active peers")
            
            # Show connected peers
            peers = node.peer_discovery.get_active_peers()
            for peer in peers:
                print(f"  - Connected to: {peer[0]}:{peer[1]}")
    
    def test_consensus(self):
        """Test consensus mechanism"""
        print("\n=== Testing Consensus ===")
        
        # Create conflicting chains
        node0 = self.nodes[0]
        node1 = self.nodes[1]
        
        # Mine different blocks on different nodes
        print("Mining conflicting blocks...")
        
        # Node 0 mines block
        node0.blockchain.mine_pending_transactions("miner1")
        time.sleep(1)
        
        # Node 1 mines different block
        node1.blockchain.mine_pending_transactions("miner2")
        time.sleep(1)
        
        # Check consensus resolution
        time.sleep(3)
        
        heights = [len(node.blockchain.chain) for node in self.nodes]
        print(f"Final chain heights: {heights}")
        
        # All nodes should have the same height after consensus
        if len(set(heights)) == 1:
            print("SUCCESS: Consensus achieved!")
        else:
            print("FAILED: Consensus not reached")
    
    def test_network_status(self):
        """Test network status reporting"""
        print("\n=== Network Status ===")
        
        for i, node in enumerate(self.nodes):
            status = node.get_status()
            print(f"\nNode {i+1} Status:")
            print(f"  Address: {status['address']}")
            print(f"  Blockchain Height: {status['blockchain']['height']}")
            print(f"  Mempool Size: {status['blockchain']['mempool_size']}")
            print(f"  Active Peers: {status['peers']['active_peers']}")
            print(f"  Known Peers: {status['peers']['known_peers']}")
    
    def run_all_tests(self):
        """Run all network tests"""
        print("Starting Phase 3 Network Tests...")
        print("=" * 50)
        
        # Set up signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        
        try:
            # Create network
            self.create_network(3)
            time.sleep(2)
            
            # Run tests
            self.test_peer_discovery()
            self.test_transaction_propagation()
            self.test_blockchain_sync()
            self.test_consensus()
            self.test_network_status()
            
            print("\n" + "=" * 50)
            print("Phase 3 Testing Complete!")
            print("Press Ctrl+C to exit...")
            
            # Keep running for manual testing
            while self.running:
                time.sleep(1)
        
        except KeyboardInterrupt:
            pass
        
        finally:
            # Cleanup
            for node in self.nodes:
                node.stop()
            print("Network test shutdown complete")


def main():
    """Main test runner"""
    test = NetworkTest()
    test.run_all_tests()


if __name__ == "__main__":
    main()
