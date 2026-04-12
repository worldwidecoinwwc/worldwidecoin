#!/usr/bin/env python3
"""
Manual Network Testing Guide for Phase 3
Step-by-step verification of P2P network functionality
"""

import time
import threading
from network.enhanced_node import EnhancedNode


def test_single_node():
    """Test 1: Single node startup and status"""
    print("=== TEST 1: Single Node ===")
    
    # Create and start node
    node = EnhancedNode(port=8330)
    node.start()
    
    print("✅ Node started on port 8330")
    
    # Wait for startup
    time.sleep(2)
    
    # Check status
    status = node.get_status()
    print(f"Status: Running={status['running']}")
    print(f"Address: {status['address']}")
    print(f"Chain Height: {status['blockchain']['height']}")
    print(f"Mempool Size: {status['blockchain']['mempool_size']}")
    print(f"Active Peers: {status['peers']['active_peers']}")
    
    # Stop node
    node.stop()
    print("✅ Node stopped\n")


def test_peer_discovery():
    """Test 2: Peer discovery functionality"""
    print("=== TEST 2: Peer Discovery ===")
    
    # Create node
    node = EnhancedNode(port=8330)
    node.start()
    
    time.sleep(1)
    
    # Check initial peer stats
    stats = node.peer_discovery.get_peer_stats()
    print(f"Initial peers: {stats}")
    
    # Add manual peer
    node.peer_discovery.add_peer("127.0.0.1", 8331)
    print("Added peer 127.0.0.1:8331")
    
    # Check updated stats
    stats_after = node.peer_discovery.get_peer_stats()
    print(f"After adding peer: {stats_after}")
    
    # Test peer ping (will fail since no node on 8331)
    print("Testing peer ping...")
    result = node.peer_discovery._ping_peer(("127.0.0.1", 8331))
    print(f"Ping result: {result}")
    
    node.stop()
    print("✅ Peer discovery test completed\n")


def test_two_nodes():
    """Test 3: Two-node network"""
    print("=== TEST 3: Two-Node Network ===")
    
    # Create two nodes
    node1 = EnhancedNode(port=8330)
    node2 = EnhancedNode(port=8331)
    
    node1.start()
    node2.start()
    
    time.sleep(2)
    
    print("✅ Both nodes started")
    
    # Connect node1 to node2
    print("Connecting node1 to node2...")
    node1.connect_to_peer("127.0.0.1", 8331)
    
    time.sleep(3)
    
    # Check peer connections
    status1 = node1.get_status()
    status2 = node2.get_status()
    
    print(f"Node1 peers: {status1['peers']['active_peers']}")
    print(f"Node2 peers: {status2['peers']['active_peers']}")
    
    # Test message exchange
    print("Testing message exchange...")
    node1._send_message_to_peer(("127.0.0.1", 8331), {"type": "ping", "data": {}})
    
    time.sleep(1)
    
    node1.stop()
    node2.stop()
    print("✅ Two-node test completed\n")


def test_blockchain_sync():
    """Test 4: Blockchain synchronization"""
    print("=== TEST 4: Blockchain Sync ===")
    
    # Create nodes
    node1 = EnhancedNode(port=8330)
    node2 = EnhancedNode(port=8331)
    
    node1.start()
    node2.start()
    
    time.sleep(1)
    
    # Connect nodes
    node1.connect_to_peer("127.0.0.1", 8331)
    time.sleep(2)
    
    # Mine block on node1
    print("Mining block on node1...")
    node1.blockchain.mine_pending_transactions("miner1")
    
    print(f"Node1 height: {len(node1.blockchain.chain)}")
    print(f"Node2 height: {len(node2.blockchain.chain)}")
    
    time.sleep(3)
    
    # Check if sync worked
    height1 = len(node1.blockchain.chain)
    height2 = len(node2.blockchain.chain)
    
    print(f"After sync - Node1: {height1}, Node2: {height2}")
    
    if height1 == height2:
        print("✅ Blockchain sync working!")
    else:
        print("❌ Blockchain sync needs attention")
    
    node1.stop()
    node2.stop()
    print("✅ Sync test completed\n")


def test_consensus():
    """Test 5: Consensus mechanisms"""
    print("=== TEST 5: Consensus ===")
    
    from network.consensus import ConsensusManager, NetworkMessage
    from core.blockchain import Blockchain
    
    # Create consensus manager
    blockchain = Blockchain()
    consensus = ConsensusManager(blockchain)
    
    print("✅ Consensus manager created")
    
    # Test message creation
    message = NetworkMessage.create("ping", {"test": "data"})
    print(f"Created message: {message}")
    
    # Test message validation
    is_valid = NetworkMessage.validate(message)
    print(f"Message validation: {is_valid}")
    
    # Test consensus info
    info = consensus.get_consensus_info()
    print(f"Consensus info: {info}")
    
    print("✅ Consensus test completed\n")


def interactive_test():
    """Interactive testing mode"""
    print("=== INTERACTIVE MODE ===")
    print("Commands: status, peers, connect <host> <port>, mine, quit")
    
    node = EnhancedNode(port=8330)
    node.start()
    
    time.sleep(1)
    
    while True:
        try:
            cmd = input("WWC> ").strip().split()
            if not cmd:
                continue
                
            if cmd[0] == "quit":
                break
            elif cmd[0] == "status":
                status = node.get_status()
                print(f"Status: {status}")
            elif cmd[0] == "peers":
                stats = node.peer_discovery.get_peer_stats()
                active = node.peer_discovery.get_active_peers()
                print(f"Stats: {stats}")
                print(f"Active: {active}")
            elif cmd[0] == "connect" and len(cmd) == 3:
                node.connect_to_peer(cmd[1], int(cmd[2]))
            elif cmd[0] == "mine":
                node.blockchain.mine_pending_transactions("miner")
                print(f"Mined block. Height: {len(node.blockchain.chain)}")
            else:
                print("Unknown command")
                
        except KeyboardInterrupt:
            break
    
    node.stop()
    print("✅ Interactive mode ended")


def main():
    """Main testing menu"""
    print("WorldWideCoin Phase 3 - Manual Network Testing")
    print("=" * 50)
    
    tests = [
        ("1", "Single Node", test_single_node),
        ("2", "Peer Discovery", test_peer_discovery),
        ("3", "Two-Node Network", test_two_nodes),
        ("4", "Blockchain Sync", test_blockchain_sync),
        ("5", "Consensus", test_consensus),
        ("6", "Interactive Mode", interactive_test),
        ("a", "Run All Tests", lambda: [t() for t in [test_single_node, test_peer_discovery, test_two_nodes, test_blockchain_sync, test_consensus]])
    ]
    
    print("Available tests:")
    for code, name, _ in tests:
        print(f"  {code}. {name}")
    
    choice = input("\nSelect test (1-6, a): ").strip()
    
    for code, name, func in tests:
        if choice == code:
            print(f"\nRunning {name} test...")
            func()
            return
    
    print("Invalid choice")


if __name__ == "__main__":
    main()
