# network/enhanced_node.py
import socket
import threading
import json
import time
from typing import Dict, List, Tuple, Optional

from core.blockchain import Blockchain
from core.transaction import Transaction
from core.block import Block
from network.peer_discovery import PeerDiscovery
from network.consensus import ConsensusManager, NetworkMessage
from network import p2p
from config import Config


class EnhancedNode:
    """Enhanced blockchain node with P2P networking and consensus"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8333, config_file: str = "config.json"):
        self.host = host
        self.port = port
        self.config = Config(config_file)
        
        # Core components
        self.blockchain = Blockchain()
        self.peer_discovery = PeerDiscovery(port, self.config)
        self.consensus = ConsensusManager(self.blockchain)
        
        # Node state
        self.running = False
        self.server_socket = None
        self.connected_peers: Dict[str, socket.socket] = {}
        
        # Message handlers
        self.message_handlers = {
            "ping": self._handle_ping,
            "pong": self._handle_pong,
            "getinfo": self._handle_getinfo,
            "info": self._handle_info,
            "getblocks": self._handle_getblocks,
            "blocks": self._handle_blocks,
            "getpeers": self._handle_getpeers,
            "peers": self._handle_peers,
            "transaction": self._handle_transaction,
            "block": self._handle_block,
            "inv": self._handle_inv,
            "getdata": self._handle_getdata,
            "version": self._handle_version,
            "verack": self._handle_verack
        }
    
    def start(self):
        """Start the enhanced node"""
        if self.running:
            print("Node is already running")
            return
        
        self.running = True
        
        # Start peer discovery
        self.peer_discovery.start_discovery()
        
        # Start P2P server
        self._start_server()
        
        # Start periodic sync
        threading.Thread(target=self._periodic_sync, daemon=True).start()
        
        print(f"Enhanced node started on {self.host}:{self.port}")
    
    def stop(self):
        """Stop the enhanced node"""
        self.running = False
        self.peer_discovery.stop_discovery()
        
        if self.server_socket:
            self.server_socket.close()
        
        # Close all peer connections
        for peer_socket in self.connected_peers.values():
            try:
                peer_socket.close()
            except:
                pass
        
        print("Enhanced node stopped")
    
    def _start_server(self):
        """Start the P2P server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        
        threading.Thread(target=self._server_loop, daemon=True).start()
    
    def _server_loop(self):
        """Main server loop"""
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
                threading.Thread(target=self._handle_connection, args=(conn, addr), daemon=True).start()
            except Exception as e:
                if self.running:
                    print(f"Server error: {e}")
    
    def _handle_connection(self, conn: socket.socket, addr: Tuple[str, int]):
        """Handle incoming connection"""
        try:
            while self.running:
                data = conn.recv(4096)
                if not data:
                    break
                
                try:
                    message = json.loads(data.decode())
                    if NetworkMessage.validate(message):
                        self._process_message(message, conn, addr)
                    else:
                        print(f"Invalid message format from {addr}: {message}")
                except json.JSONDecodeError:
                    print(f"Invalid JSON from {addr}")
        
        except Exception as e:
            print(f"Connection error with {addr}: {e}")
        
        finally:
            conn.close()
            peer_id = f"{addr[0]}:{addr[1]}"
            if peer_id in self.connected_peers:
                del self.connected_peers[peer_id]
    
    def _process_message(self, message: dict, conn: socket.socket, addr: Tuple[str, int]):
        """Process incoming message"""
        msg_type = message.get("type")
        handler = self.message_handlers.get(msg_type)
        
        if handler:
            try:
                response = handler(message.get("data", {}), conn, addr)
                if response:
                    conn.send(json.dumps(response).encode())
            except Exception as e:
                print(f"Error handling {msg_type} from {addr}: {e}")
        else:
            print(f"Unknown message type: {msg_type}")
    
    def _handle_ping(self, data: dict, conn: socket.socket, addr: Tuple[str, int]) -> dict:
        """Handle ping message"""
        return NetworkMessage.create("pong", {"timestamp": time.time()})
    
    def _handle_pong(self, data: dict, conn: socket.socket, addr: Tuple[str, int]) -> Optional[dict]:
        """Handle pong message"""
        return None
    
    def _handle_getinfo(self, data: dict, conn: socket.socket, addr: Tuple[str, int]) -> dict:
        """Handle chain info request"""
        last_block = self.blockchain.get_last_block()
        return NetworkMessage.create("info", {
            "height": len(self.blockchain.chain),
            "tip_hash": last_block.hash if last_block else "",
            "difficulty": last_block.difficulty if last_block else 1
        })
    
    def _handle_info(self, data: dict, conn: socket.socket, addr: Tuple[str, int]) -> Optional[dict]:
        """Handle chain info response"""
        peer_height = data.get("height", 0)
        peer_tip = data.get("tip_hash", "")
        
        if self.consensus.should_sync(peer_height, peer_tip):
            threading.Thread(target=self._sync_with_peer, args=(addr,), daemon=True).start()
        
        return None
    
    def _handle_getblocks(self, data: dict, conn: socket.socket, addr: Tuple[str, int]) -> dict:
        """Handle block range request"""
        start = data.get("start_index", 0)
        end = data.get("end_index", len(self.blockchain.chain))
        
        blocks = []
        for i in range(start, min(end, len(self.blockchain.chain))):
            block = self.blockchain.chain[i]
            blocks.append({
                "index": block.index,
                "prev_hash": block.previous_hash,
                "transactions": [tx.to_dict() for tx in block.transactions],
                "timestamp": block.timestamp,
                "difficulty": block.difficulty,
                "nonce": block.nonce,
                "hash": block.hash
            })
        
        return NetworkMessage.create("blocks", blocks)
    
    def _handle_blocks(self, data: dict, conn: socket.socket, addr: Tuple[str, int]) -> Optional[dict]:
        """Handle received blocks"""
        blocks_data = data if isinstance(data, list) else []
        
        for block_dict in blocks_data:
            if self._validate_and_add_block(block_dict):
                print(f"Added synced block {block_dict.get('index')}")
            else:
                print(f"Rejected invalid block {block_dict.get('index')}")
                break
        
        return None
    
    def _handle_getpeers(self, data: dict, conn: socket.socket, addr: Tuple[str, int]) -> dict:
        """Handle peer list request"""
        active_peers = self.peer_discovery.get_active_peers()
        peer_list = [{"host": host, "port": port} for host, port in active_peers]
        return NetworkMessage.create("peers", peer_list)
    
    def _handle_peers(self, data: dict, conn: socket.socket, addr: Tuple[str, int]) -> Optional[dict]:
        """Handle peer list response"""
        for peer_info in data:
            self.peer_discovery.add_peer(peer_info["host"], peer_info["port"])
        return None
    
    def _handle_transaction(self, data: dict, conn: socket.socket, addr: Tuple[str, int]) -> Optional[dict]:
        """Handle new transaction"""
        try:
            tx = Transaction(
                inputs=data.get("inputs", []),
                outputs=data.get("outputs", [])
            )
            
            try:
                self.blockchain.mempool.add_transaction(tx)
                print(f"Added transaction from {addr}")
                # Broadcast to other peers
                self._broadcast_message(NetworkMessage.create("transaction", data), exclude=addr)
            except Exception as e:
                print(f"Rejected invalid transaction from {addr}: {e}")
        
        except Exception as e:
            print(f"Error processing transaction: {e}")
        
        return None
    
    def _handle_block(self, data: dict, conn: socket.socket, addr: Tuple[str, int]) -> Optional[dict]:
        """Handle new block"""
        if self._validate_and_add_block(data):
            print(f"Added block {data.get('index')} from {addr}")
            # Broadcast to other peers
            self._broadcast_message(NetworkMessage.create("block", data), exclude=addr)
        else:
            print(f"Rejected invalid block {data.get('index')} from {addr}")
        
        return None
    
    def _handle_inv(self, data: dict, conn: socket.socket, addr: Tuple[str, int]) -> Optional[dict]:
        """Handle inventory announcement"""
        # Request announced data
        for item in data.get("inventory", []):
            if item["type"] in ["block", "transaction"]:
                self._send_message_to_peer(addr, NetworkMessage.create("getdata", {"type": item["type"], "hash": item["hash"]}))
        
        return None
    
    def _handle_getdata(self, data: dict, conn: socket.socket, addr: Tuple[str, int]) -> Optional[dict]:
        """Handle data request"""
        data_type = data.get("type")
        data_hash = data.get("hash")
        
        if data_type == "block":
            for block in self.blockchain.chain:
                if block.hash == data_hash:
                    block_dict = {
                        "index": block.index,
                        "prev_hash": block.previous_hash,
                        "transactions": [tx.to_dict() for tx in block.transactions],
                        "timestamp": block.timestamp,
                        "difficulty": block.difficulty,
                        "nonce": block.nonce,
                        "hash": block.hash
                    }
                    return NetworkMessage.create("block", block_dict)
        
        elif data_type == "transaction":
            for tx in self.blockchain.mempool:
                if tx.calculate_hash() == data_hash:
                    return NetworkMessage.create("transaction", tx.to_dict())
        
        return None
    
    def _handle_version(self, data: dict, conn: socket.socket, addr: Tuple[str, int]) -> dict:
        """Handle version handshake"""
        return NetworkMessage.create("verack", {"version": "1.0"})
    
    def _handle_verack(self, data: dict, conn: socket.socket, addr: Tuple[str, int]) -> Optional[dict]:
        """Handle version acknowledgment"""
        peer_id = f"{addr[0]}:{addr[1]}"
        self.connected_peers[peer_id] = conn
        print(f"Handshake completed with {peer_id}")
        return None
    
    def _validate_and_add_block(self, block_dict: dict) -> bool:
        """Validate and add a block"""
        try:
            # Check required fields
            required_fields = ["index", "prev_hash", "transactions", "timestamp", "difficulty", "nonce", "hash"]
            for field in required_fields:
                if field not in block_dict:
                    return False
            
            # Create block object
            txs = [
                Transaction(tx["inputs"], tx["outputs"])
                for tx in block_dict.get("transactions", [])
            ]
            
            block = Block(
                index=block_dict["index"],
                prev_hash=block_dict["prev_hash"],
                transactions=txs,
                timestamp=block_dict["timestamp"],
                difficulty=block_dict["difficulty"]
            )
            
            block.nonce = block_dict["nonce"]
            block.hash = block_dict["hash"]
            
            # Add to blockchain
            return self.blockchain.add_block(block)
        
        except Exception as e:
            print(f"Block validation error: {e}")
            return False
    
    def _sync_with_peer(self, addr: Tuple[str, int]):
        """Sync blockchain with peer"""
        try:
            # Request chain info
            message = NetworkMessage.create("getinfo")
            self._send_message_to_peer(addr, message)
        
        except Exception as e:
            print(f"Sync error with {addr}: {e}")
    
    def _send_message_to_peer(self, addr: Tuple[str, int], message: dict):
        """Send message to specific peer"""
        try:
            sock = socket.socket()
            sock.connect(addr)
            sock.send(json.dumps(message).encode())
            sock.close()
        except Exception as e:
            print(f"Failed to send message to {addr}: {e}")
    
    def _broadcast_message(self, message: dict, exclude: Tuple[str, int] = None):
        """Broadcast message to all active peers"""
        for peer in self.peer_discovery.get_active_peers():
            if exclude and peer == exclude:
                continue
            
            threading.Thread(target=self._send_message_to_peer, args=(peer, message), daemon=True).start()
    
    def _periodic_sync(self):
        """Periodic blockchain synchronization"""
        while self.running:
            try:
                # Sync with random peer
                active_peers = self.peer_discovery.get_active_peers()
                if active_peers:
                    peer = random.choice(active_peers)
                    self._sync_with_peer(peer)
                
                time.sleep(60)  # Sync every minute
            
            except Exception as e:
                print(f"Periodic sync error: {e}")
                time.sleep(30)
    
    def connect_to_peer(self, host: str, port: int):
        """Connect to a new peer"""
        self.peer_discovery.add_peer(host, port)
        
        # Start handshake
        try:
            message = NetworkMessage.create("version", {"version": "1.0"})
            self._send_message_to_peer((host, port), message)
        except Exception as e:
            print(f"Failed to connect to peer {host}:{port}: {e}")
    
    def broadcast_transaction(self, tx: Transaction):
        """Broadcast transaction to network"""
        message = NetworkMessage.create("transaction", tx.to_dict())
        self._broadcast_message(message)
    
    def broadcast_block(self, block: Block):
        """Broadcast block to network"""
        block_dict = {
            "index": block.index,
            "prev_hash": block.previous_hash,
            "transactions": [tx.to_dict() for tx in block.transactions],
            "timestamp": block.timestamp,
            "difficulty": block.difficulty,
            "nonce": block.nonce,
            "hash": block.hash
        }
        message = NetworkMessage.create("block", block_dict)
        self._broadcast_message(message)
    
    def get_status(self) -> dict:
        """Get node status"""
        return {
            "running": self.running,
            "address": f"{self.host}:{self.port}",
            "blockchain": {
                "height": len(self.blockchain.chain),
                "mempool_size": len(self.blockchain.mempool.transactions),
                "tip_hash": self.blockchain.get_last_block().hash if self.blockchain.chain else ""
            },
            "peers": self.peer_discovery.get_peer_stats(),
            "consensus": self.consensus.get_consensus_info()
        }
