# network/node.py
import socket
import threading
import json

from core.blockchain import Blockchain
from core.transaction import Transaction
from core.block import Block
from network import p2p


class Node:

    def __init__(self, host="0.0.0.0", port=8333):
        self.host = host
        self.port = port
        self.peers = []
        self.blockchain = Blockchain()

    def start(self):

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen()

        print(f"🌐 Node running on {self.port}")

        while True:
            try:
                conn, addr = server.accept()
                threading.Thread(target=self.handle_peer, args=(conn, addr), daemon=True).start()
            except Exception as e:
                print(f"Error accepting connection: {e}")

    def handle_peer(self, conn, addr):

        try:
            data = conn.recv(4096)

            if not data:
                return

            msg = json.loads(data.decode())
            msg_type = msg.get("type")
            msg_data = msg.get("data", {})

            if msg_type == "transaction":

                tx = Transaction(
                    inputs=msg_data.get("inputs", []),
                    outputs=msg_data.get("outputs", [])
                )

                self.blockchain.mempool.add_transaction(tx)
                print(f"💸 Transaction received from {addr} + added to mempool")

            elif msg_type == "block":

                txs = [
                    Transaction(tx["inputs"], tx["outputs"])
                    for tx in msg_data.get("transactions", [])
                ]

                block = Block(
                    index=msg_data["index"],
                    prev_hash=msg_data["prev_hash"],
                    transactions=txs,
                    timestamp=msg_data["timestamp"],
                    difficulty=msg_data["difficulty"]
                )

                block.nonce = msg_data["nonce"]
                block.hash = msg_data["hash"]

                self.blockchain.add_block(block)
                print(f"📦 Block received from {addr} + added to chain (height: {len(self.blockchain.chain)})")

            elif msg_type == "getinfo":
                # Respond with chain info
                chain_height = len(self.blockchain.chain)
                response = json.dumps({
                    "type": "info",
                    "data": {
                        "height": chain_height,
                        "tip_hash": self.blockchain.get_last_block().hash
                    }
                }).encode()
                conn.send(response)
                print(f"📊 Chain info sent to {addr} (height: {chain_height})")

            elif msg_type == "getblocks":
                # Send requested blocks
                start = msg_data.get("start_index", 0)
                end = msg_data.get("end_index", len(self.blockchain.chain))

                blocks = []
                for i in range(start, min(end, len(self.blockchain.chain))):
                    block = self.blockchain.chain[i]
                    blocks.append({
                        "index": block.index,
                        "prev_hash": block.prev_hash,
                        "transactions": [tx.to_dict() for tx in block.transactions],
                        "timestamp": block.timestamp,
                        "difficulty": block.difficulty,
                        "nonce": block.nonce,
                        "hash": block.hash
                    })

                response = json.dumps({
                    "type": "blocks",
                    "data": blocks
                }).encode()
                conn.send(response)
                print(f"📤 {len(blocks)} blocks sent to {addr} (blocks {start}-{end})")

            elif msg_type == "blocks":
                # Receive synced blocks
                blocks_data = msg_data if isinstance(msg_data, list) else []

                for block_dict in blocks_data:
                    try:
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

                        self.blockchain.add_block(block)
                    except Exception as e:
                        print(f"Error syncing block: {e}")

                print(f"🔗 Chain synced: received {len(blocks_data)} blocks from {addr}")

        except Exception as e:
            print(f"Error handling peer {addr}: {e}")

        finally:
            conn.close()

    def broadcast_block(self, block):
        """Broadcast block to all connected peers"""
        p2p.broadcast_block(self.peers, block)

    def broadcast_transaction(self, tx):
        """Broadcast transaction to all connected peers"""
        p2p.broadcast_transaction(self.peers, tx)

    def connect_peer(self, host, port):
        """Connect to a new peer and attempt initial sync"""
        peer = (host, port)
        if peer not in self.peers:
            self.peers.append(peer)
            print(f"✅ Peer registered: {host}:{port}")
            
            # Attempt initial sync
            threading.Thread(target=self.sync_with_peer, args=(peer,), daemon=True).start()
        else:
            print(f"⚠️ Peer already registered: {host}:{port}")
    
    def sync_with_all_peers(self):
        """Attempt to sync with all known peers"""
        print(f"🔄 Starting sync with {len(self.peers)} peers...")
        
        for peer in self.peers:
            try:
                if self.sync_with_peer(peer):
                    print(f"✅ Synced with {peer}")
                    break  # Stop after successful sync
            except Exception as e:
                print(f"❌ Failed to sync with {peer}: {e}")
    
    def get_network_status(self):
        """Get current network status"""
        return {
            "peers_count": len(self.peers),
            "chain_height": len(self.blockchain.chain),
            "mempool_size": len(self.blockchain.mempool),
            "tip_hash": self.blockchain.get_last_block().hash if self.blockchain.chain else "",
            "peers": [f"{host}:{port}" for host, port in self.peers]
        }

    def sync_with_peer(self, peer):
        """Enhanced block synchronization with validation"""
        try:
            # Get peer's chain info
            message = json.dumps({
                "type": "getinfo",
                "data": {}
            }).encode()

            sock = socket.socket()
            sock.connect(peer)
            sock.send(message)

            response_data = sock.recv(4096)
            sock.close()

            if response_data:
                response = json.loads(response_data.decode())
                peer_height = response.get("data", {}).get("height", 0)
                peer_tip = response.get("data", {}).get("tip_hash", "")
                our_height = len(self.blockchain.chain)
                our_tip = self.blockchain.get_last_block().hash if our_height > 0 else ""

                print(f"📍 Peer height: {peer_height}, Our height: {our_height}")
                print(f"🔗 Peer tip: {peer_tip[:16]}..., Our tip: {our_tip[:16]}...")

                # Check if we need to sync
                if peer_height > our_height or (peer_height == our_height and peer_tip != our_tip):
                    print(f"🔄 Syncing blocks from peer...")
                    
                    # Request blocks in batches
                    batch_size = 10
                    start_index = our_height
                    
                    while start_index < peer_height:
                        end_index = min(start_index + batch_size, peer_height)
                        block_list = p2p.request_blocks(peer, start_index, end_index)
                        
                        if not block_list:
                            print(f"⚠️ No blocks received for range {start_index}-{end_index}")
                            break
                        
                        # Validate and add blocks
                        for block_dict in block_list:
                            if not self._validate_synced_block(block_dict, start_index):
                                print(f"❌ Block validation failed at index {block_dict.get('index')}")
                                return False
                                
                            try:
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

                                self.blockchain.add_block(block)
                                start_index += 1
                            except Exception as e:
                                print(f"Error adding synced block: {e}")
                                return False

                    print(f"✅ Chain synced! New height: {len(self.blockchain.chain)}")
                    return True
                else:
                    print("📊 Chain is up to date")
                    return True

        except Exception as e:
            print(f"Failed to sync with {peer}: {e}")
            return False
    
    def _validate_synced_block(self, block_dict, expected_index):
        """Validate received block data"""
        try:
            # Check required fields
            required_fields = ["index", "prev_hash", "transactions", "timestamp", "difficulty", "nonce", "hash"]
            for field in required_fields:
                if field not in block_dict:
                    print(f"Missing required field: {field}")
                    return False
            
            # Check index
            if block_dict["index"] != expected_index:
                print(f"Block index mismatch: expected {expected_index}, got {block_dict['index']}")
                return False
            
            # Check hash integrity
            if not self._verify_block_hash(block_dict):
                print(f"Invalid block hash for block {block_dict['index']}")
                return False
                
            return True
        except Exception as e:
            print(f"Block validation error: {e}")
            return False
    
    def _verify_block_hash(self, block_dict):
        """Verify block hash matches computed hash"""
        try:
            # Recreate block and compute hash
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
            computed_hash = block.calculate_hash()
            
            return computed_hash == block_dict["hash"]
        except Exception as e:
            print(f"Hash verification error: {e}")
            return False