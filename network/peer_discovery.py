# network/peer_discovery.py
import socket
import threading
import time
import random
import json
from typing import List, Tuple, Set
from config import Config
from network.consensus import NetworkMessage


class PeerDiscovery:
    """Peer discovery and management system"""
    
    def __init__(self, local_port: int, config: Config = None):
        self.local_port = local_port
        self.config = config or Config()
        self.active_peers: Set[Tuple[str, int]] = set()
        self.known_peers: Set[Tuple[str, int]] = set()
        self.blacklisted_peers: Set[Tuple[str, int]] = set()
        self.discovery_running = False
        self.discovery_thread = None
        
        # Load initial peers from config
        self._load_initial_peers()
    
    def _load_initial_peers(self):
        """Load peers from configuration"""
        for peer in self.config.get_peers():
            peer_tuple = (peer["host"], peer["port"])
            if peer_tuple[1] != self.local_port:  # Don't add self
                self.known_peers.add(peer_tuple)
    
    def start_discovery(self):
        """Start peer discovery service"""
        if not self.discovery_running:
            self.discovery_running = True
            self.discovery_thread = threading.Thread(target=self._discovery_loop, daemon=True)
            self.discovery_thread.start()
            print("Peer discovery started")
    
    def stop_discovery(self):
        """Stop peer discovery service"""
        self.discovery_running = False
        if self.discovery_thread:
            self.discovery_thread.join(timeout=5)
        print("Peer discovery stopped")
    
    def _discovery_loop(self):
        """Main discovery loop"""
        while self.discovery_running:
            try:
                self._discover_peers()
                self._cleanup_inactive_peers()
                time.sleep(30)  # Discovery interval
            except Exception as e:
                print(f"Discovery error: {e}")
                time.sleep(10)
    
    def _discover_peers(self):
        """Discover new peers through various methods"""
        # Method 1: Try known peers
        self._probe_known_peers()
        
        # Method 2: Port scanning on localhost (for testing)
        self._scan_localhost_range()
        
        # Method 3: Request peer lists from active peers
        self._request_peer_lists()
    
    def _probe_known_peers(self):
        """Check if known peers are still active"""
        for peer in list(self.known_peers):
            if peer not in self.active_peers and peer not in self.blacklisted_peers:
                if self._ping_peer(peer):
                    self.active_peers.add(peer)
                    print(f"Connected to peer: {peer[0]}:{peer[1]}")
                else:
                    self.blacklisted_peers.add(peer)
                    self.known_peers.discard(peer)
    
    def _scan_localhost_range(self):
        """Scan common port range for local peers (development)"""
        if self.local_port >= 8330 and self.local_port <= 8340:
            # Scan other development ports
            for port in range(8330, 8341):
                if port != self.local_port:
                    peer = ("127.0.0.1", port)
                    if peer not in self.active_peers and peer not in self.blacklisted_peers:
                        if self._ping_peer(peer):
                            self.active_peers.add(peer)
                            self.known_peers.add(peer)
                            print(f"Discovered local peer: {peer[0]}:{peer[1]}")
    
    def _request_peer_lists(self):
        """Request peer lists from active connections"""
        for peer in list(self.active_peers):
            try:
                message = json.dumps(NetworkMessage.create("getpeers", {})).encode()
                
                sock = socket.socket()
                sock.settimeout(5)
                sock.connect(peer)
                sock.send(message)
                
                response_data = sock.recv(4096)
                sock.close()
                
                if response_data:
                    response = json.loads(response_data.decode())
                    if response.get("type") == "peers":
                        peer_list = response.get("data", [])
                        for peer_info in peer_list:
                            new_peer = (peer_info["host"], peer_info["port"])
                            if new_peer not in self.known_peers and new_peer[1] != self.local_port:
                                self.known_peers.add(new_peer)
                                print(f"Added discovered peer: {new_peer[0]}:{new_peer[1]}")
            except Exception as e:
                print(f"Failed to get peers from {peer}: {e}")
                self.active_peers.discard(peer)
    
    def _ping_peer(self, peer: Tuple[str, int]) -> bool:
        """Check if peer is responsive"""
        try:
            sock = socket.socket()
            sock.settimeout(3)
            sock.connect(peer)
            
            # Send ping message
            message = json.dumps(NetworkMessage.create("ping", {"timestamp": time.time()})).encode()
            
            sock.send(message)
            response_data = sock.recv(1024)
            sock.close()
            
            if response_data:
                response = json.loads(response_data.decode())
                return response.get("type") == "pong"
        except Exception:
            pass
        
        return False
    
    def _cleanup_inactive_peers(self):
        """Remove inactive peers from active list"""
        inactive_peers = []
        for peer in self.active_peers:
            if not self._ping_peer(peer):
                inactive_peers.append(peer)
        
        for peer in inactive_peers:
            self.active_peers.discard(peer)
            print(f"Peer went inactive: {peer[0]}:{peer[1]}")
    
    def add_peer(self, host: str, port: int):
        """Manually add a peer"""
        peer = (host, port)
        if port != self.local_port and peer not in self.blacklisted_peers:
            self.known_peers.add(peer)
            if self._ping_peer(peer):
                self.active_peers.add(peer)
                print(f"Added active peer: {host}:{port}")
            else:
                print(f"Added known peer: {host}:{port}")
    
    def remove_peer(self, host: str, port: int):
        """Remove a peer"""
        peer = (host, port)
        self.active_peers.discard(peer)
        self.known_peers.discard(peer)
        self.blacklisted_peers.add(peer)
        print(f"Removed peer: {host}:{port}")
    
    def get_active_peers(self) -> List[Tuple[str, int]]:
        """Get list of active peers"""
        return list(self.active_peers)
    
    def get_all_peers(self) -> List[Tuple[str, int]]:
        """Get list of all known peers"""
        return list(self.known_peers)
    
    def get_peer_stats(self) -> dict:
        """Get peer discovery statistics"""
        return {
            "active_peers": len(self.active_peers),
            "known_peers": len(self.known_peers),
            "blacklisted_peers": len(self.blacklisted_peers),
            "discovery_running": self.discovery_running
        }
