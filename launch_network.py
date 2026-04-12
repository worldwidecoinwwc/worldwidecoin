#!/usr/bin/env python3
"""
Simple network launcher for WorldWideCoin Phase 3
Starts multiple nodes for testing P2P functionality
"""

import sys
import time
import threading
from network.enhanced_node import EnhancedNode


def launch_node(port: int, connect_to: list = None):
    """Launch a single node"""
    print(f"Starting node on port {port}...")
    
    node = EnhancedNode(port=port)
    node.start()
    
    # Connect to other nodes if specified
    if connect_to:
        for peer_port in connect_to:
            node.connect_to_peer("127.0.0.1", peer_port)
    
    return node


def main():
    """Main launcher"""
    if len(sys.argv) < 2:
        print("Usage: python launch_network.py <num_nodes> [base_port]")
        print("Example: python launch_network.py 3 8330")
        sys.exit(1)
    
    num_nodes = int(sys.argv[1])
    base_port = int(sys.argv[2]) if len(sys.argv) > 2 else 8330
    
    print(f"Launching {num_nodes} nodes starting from port {base_port}")
    print("=" * 50)
    
    nodes = []
    
    try:
        # Launch nodes
        for i in range(num_nodes):
            port = base_port + i
            
            # Connect to previous nodes
            connect_to = list(range(base_port, port))
            
            node = launch_node(port, connect_to)
            nodes.append(node)
            
            time.sleep(0.5)  # Stagger startup
        
        print(f"\n{num_nodes} nodes launched successfully!")
        print("Press Ctrl+C to stop all nodes...")
        
        # Show network status
        time.sleep(2)
        print("\nNetwork Status:")
        print("-" * 30)
        
        for i, node in enumerate(nodes):
            status = node.get_status()
            print(f"Node {i+1} (port {base_port + i}):")
            print(f"  Height: {status['blockchain']['height']}")
            print(f"  Peers: {status['peers']['active_peers']}")
            print(f"  Mempool: {status['blockchain']['mempool_size']} txs")
        
        # Keep running
        while True:
            time.sleep(10)
            
            # Periodic status update
            print(f"\n[{time.strftime('%H:%M:%S')}] Network Status:")
            for i, node in enumerate(nodes):
                status = node.get_status()
                print(f"  Node {i+1}: height={status['blockchain']['height']}, peers={status['peers']['active_peers']}")
    
    except KeyboardInterrupt:
        print("\nShutting down nodes...")
        
        for node in nodes:
            node.stop()
        
        print("All nodes stopped")
    
    except Exception as e:
        print(f"Error: {e}")
        
        for node in nodes:
            try:
                node.stop()
            except:
                pass


if __name__ == "__main__":
    main()
