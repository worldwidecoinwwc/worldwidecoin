# network/consensus.py
import time
from typing import List, Dict, Optional
from core.blockchain import Blockchain
from core.block import Block


class ConsensusManager:
    """Network consensus and conflict resolution"""
    
    def __init__(self, blockchain: Blockchain):
        self.blockchain = blockchain
        self.peer_chains: Dict[str, List[Block]] = {}
        self.last_consensus_time = 0
        self.consensus_interval = 60  # seconds
    
    def resolve_conflicts(self, peer_chains: Dict[str, List[Block]]) -> bool:
        """Resolve conflicts between multiple peer chains"""
        if not peer_chains:
            return False
        
        # Find the longest valid chain
        best_chain = None
        best_peer = None
        best_length = 0
        
        for peer_id, chain in peer_chains.items():
            if self._validate_chain(chain):
                if len(chain) > best_length:
                    best_chain = chain
                    best_peer = peer_id
                    best_length = len(chain)
                elif len(chain) == best_length and best_chain:
                    # If same length, choose chain with more work (lower difficulty target)
                    if self._calculate_chain_work(chain) > self._calculate_chain_work(best_chain):
                        best_chain = chain
                        best_peer = peer_id
        
        if best_chain and len(best_chain) > len(self.blockchain.chain):
            print(f"Adopting longer chain from peer {best_peer} (length: {len(best_chain)})")
            self.blockchain.chain = best_chain
            return True
        
        return False
    
    def _validate_chain(self, chain: List[Block]) -> bool:
        """Validate a complete chain"""
        if not chain:
            return False
        
        # Check genesis block
        if chain[0].index != 0 or chain[0].previous_hash != "0":
            return False
        
        # Validate each block
        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i-1]
            
            # Check block index
            if current_block.index != i:
                return False
            
            # Check previous hash link
            if current_block.previous_hash != previous_block.hash:
                return False
            
            # Check block hash
            if current_block.hash != current_block.calculate_hash():
                return False
            
            # Check proof of work
            if not self._is_valid_proof(current_block):
                return False
        
        return True
    
    def _is_valid_proof(self, block: Block) -> bool:
        """Check if block proof of work is valid"""
        # Simple hash difficulty check
        target = "0" * block.difficulty
        return block.hash.startswith(target)
    
    def _calculate_chain_work(self, chain: List[Block]) -> int:
        """Calculate total work done in chain (simplified)"""
        total_work = 0
        for block in chain:
            # More work = higher difficulty
            total_work += 2 ** block.difficulty
        return total_work
    
    def should_sync(self, peer_height: int, peer_tip: str) -> bool:
        """Determine if we should sync with peer"""
        our_height = len(self.blockchain.chain)
        our_tip = self.blockchain.get_last_block().hash if our_height > 0 else ""
        
        # Sync if peer has longer chain
        if peer_height > our_height:
            return True
        
        # Sync if same height but different tip (conflict)
        if peer_height == our_height and peer_tip != our_tip:
            return True
        
        return False
    
    def register_peer_chain(self, peer_id: str, chain: List[Block]):
        """Register a peer's chain for consensus"""
        self.peer_chains[peer_id] = chain
    
    def get_consensus_info(self) -> Dict:
        """Get current consensus information"""
        return {
            "our_height": len(self.blockchain.chain),
            "our_tip": self.blockchain.get_last_block().hash if self.blockchain.chain else "",
            "peer_chains": len(self.peer_chains),
            "last_consensus": self.last_consensus_time
        }


class NetworkMessage:
    """Standardized network message format"""
    
    MESSAGE_TYPES = {
        "ping": "Node connectivity check",
        "pong": "Ping response",
        "getinfo": "Request chain information",
        "info": "Chain information response",
        "getblocks": "Request block range",
        "blocks": "Block data response",
        "getpeers": "Request peer list",
        "peers": "Peer list response",
        "transaction": "New transaction",
        "block": "New block",
        "inv": "Inventory announcement",
        "getdata": "Request specific data",
        "version": "Protocol version handshake",
        "verack": "Version acknowledgment"
    }
    
    @staticmethod
    def create(msg_type: str, data: dict = None) -> dict:
        """Create a standardized message"""
        if msg_type not in NetworkMessage.MESSAGE_TYPES:
            raise ValueError(f"Unknown message type: {msg_type}")
        
        return {
            "type": msg_type,
            "timestamp": time.time(),
            "data": data or {}
        }
    
    @staticmethod
    def validate(message: dict) -> bool:
        """Validate message format"""
        required_fields = ["type", "timestamp", "data"]
        for field in required_fields:
            if field not in message:
                return False
        
        if message["type"] not in NetworkMessage.MESSAGE_TYPES:
            return False
        
        return True
