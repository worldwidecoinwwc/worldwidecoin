# core/block_validation.py
import time
import hashlib
import json
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
from core.block import Block
from core.transaction import Transaction
from core.validation import TransactionValidator, ValidationError
from core.script import verify_script
from storage.utxo import UTXOSet


class BlockValidationError(Exception):
    """Custom exception for block validation errors"""
    def __init__(self, message: str, error_code: str = "BLOCK_VALIDATION_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class BlockValidator:
    """Validates blocks according to consensus rules"""
    
    def __init__(self, blockchain, utxo_set: UTXOSet):
        self.blockchain = blockchain
        self.utxo_set = utxo_set
        self.transaction_validator = TransactionValidator(utxo_set)
        
        # Consensus parameters
        self.max_block_size = 4000000  # 4MB
        self.max_block_weight = 4000000
        self.max_coinbase_script_size = 100
        self.min_block_time = 60  # Minimum time between blocks
        self.max_future_block_time = 7200  # 2 hours future
        
        # Block rewards
        self.block_reward = Decimal('50.0')
        self.halving_interval = 210000
        self.treasury_percent = Decimal('0.05')
        self.fee_burn_percent = Decimal('0.5')
    
    def validate_block(self, block: Block, check_transactions: bool = True) -> bool:
        """
        Validate a block according to consensus rules
        
        Args:
            block: Block to validate
            check_transactions: Whether to validate all transactions
            
        Returns:
            True if valid, raises BlockValidationError if invalid
        """
        try:
            # 1. Basic block structure validation
            self._validate_block_structure(block)
            
            # 2. Block header validation
            self._validate_block_header(block)
            
            # 3. Block size validation
            self._validate_block_size(block)
            
            # 4. Transaction validation
            if check_transactions:
                self._validate_block_transactions(block)
            
            # 5. Merkle tree validation
            self._validate_merkle_tree(block)
            
            # 6. Proof-of-Work validation
            self._validate_proof_of_work(block)
            
            # 7. Block reward validation
            self._validate_block_reward(block)
            
            return True
            
        except BlockValidationError:
            raise
        except Exception as e:
            raise BlockValidationError(f"Unexpected validation error: {str(e)}", "UNKNOWN_ERROR")
    
    def _validate_block_structure(self, block: Block):
        """Validate basic block structure"""
        if not isinstance(block, Block):
            raise BlockValidationError("Invalid block object", "INVALID_BLOCK_TYPE")
        
        # Required fields
        required_fields = ['index', 'prev_hash', 'transactions', 'timestamp', 'difficulty', 'nonce']
        for field in required_fields:
            if not hasattr(block, field):
                raise BlockValidationError(f"Block missing required field: {field}", "MISSING_BLOCK_FIELD")
        
        # Basic field validation
        if block.index < 0:
            raise BlockValidationError("Invalid block index", "INVALID_BLOCK_INDEX")
        
        if not isinstance(block.prev_hash, str) or len(block.prev_hash) != 64:
            raise BlockValidationError("Invalid previous hash", "INVALID_PREV_HASH")
        
        if not isinstance(block.transactions, list):
            raise BlockValidationError("Invalid transactions type", "INVALID_TRANSACTIONS_TYPE")
        
        if not isinstance(block.timestamp, (int, float)) or block.timestamp <= 0:
            raise BlockValidationError("Invalid timestamp", "INVALID_TIMESTAMP")
        
        if not isinstance(block.difficulty, int) or block.difficulty < 1 or block.difficulty > 32:
            raise BlockValidationError("Invalid difficulty", "INVALID_DIFFICULTY")
        
        if not isinstance(block.nonce, int) or block.nonce < 0:
            raise BlockValidationError("Invalid nonce", "INVALID_NONCE")
    
    def _validate_block_header(self, block: Block):
        """Validate block header"""
        # Check if block connects to previous block
        if block.index > 0:
            if len(self.blockchain.chain) == 0:
                raise BlockValidationError("Previous block not found", "PREV_BLOCK_NOT_FOUND")
            
            prev_block = self.blockchain.chain[-1]
            
            if block.index != prev_block.index + 1:
                raise BlockValidationError(f"Invalid block index: expected {prev_block.index + 1}, got {block.index}", "INVALID_BLOCK_INDEX")
            
            if block.prev_hash != prev_block.hash:
                raise BlockValidationError(f"Invalid previous hash: expected {prev_block.hash}, got {block.prev_hash}", "INVALID_PREV_HASH")
        
        # Check timestamp
        current_time = time.time()
        
        if block.timestamp > current_time + self.max_future_block_time:
            raise BlockValidationError("Block timestamp too far in future", "FUTURE_TIMESTAMP")
        
        if block.index > 0:
            prev_block = self.blockchain.chain[-1]
            if block.timestamp < prev_block.timestamp - self.min_block_time:
                raise BlockValidationError("Block timestamp too old", "OLD_TIMESTAMP")
        
        # Check difficulty
        expected_difficulty = self._get_expected_difficulty()
        if block.difficulty != expected_difficulty:
            raise BlockValidationError(f"Invalid difficulty: expected {expected_difficulty}, got {block.difficulty}", "INVALID_DIFFICULTY")
    
    def _validate_block_size(self, block: Block):
        """Validate block size"""
        # Calculate block size
        block_data = json.dumps({
            'index': block.index,
            'prev_hash': block.prev_hash,
            'transactions': [tx.to_dict() if hasattr(tx, 'to_dict') else str(tx) for tx in block.transactions],
            'timestamp': block.timestamp,
            'difficulty': block.difficulty,
            'nonce': block.nonce
        }, sort_keys=True)
        
        block_size = len(block_data.encode('utf-8'))
        
        if block_size > self.max_block_size:
            raise BlockValidationError(f"Block too large: {block_size} > {self.max_block_size}", "BLOCK_TOO_LARGE")
        
        # Calculate block weight (simplified)
        block_weight = block_size
        if block_weight > self.max_block_weight:
            raise BlockValidationError(f"Block weight too high: {block_weight} > {self.max_block_weight}", "BLOCK_WEIGHT_TOO_HIGH")
    
    def _validate_block_transactions(self, block: Block):
        """Validate all transactions in block"""
        if not block.transactions:
            raise BlockValidationError("Block has no transactions", "NO_TRANSACTIONS")
        
        # First transaction must be coinbase
        if not self._is_coinbase_transaction(block.transactions[0]):
            raise BlockValidationError("First transaction is not coinbase", "INVALID_COINBASE")
        
        # Validate coinbase transaction
        self._validate_coinbase_transaction(block.transactions[0], block.index)
        
        # Validate remaining transactions
        for i, tx in enumerate(block.transactions[1:], 1):
            try:
                # Validate transaction structure
                if not isinstance(tx, Transaction):
                    raise BlockValidationError(f"Transaction {i} is not a Transaction object", "INVALID_TX_TYPE")
                
                # Validate transaction using transaction validator
                is_valid, message = self.transaction_validator.validate_transaction_for_block(tx)
                if not is_valid:
                    raise BlockValidationError(f"Transaction {i} validation failed: {message}", "TX_VALIDATION_FAILED")
                
            except ValidationError as e:
                raise BlockValidationError(f"Transaction {i} validation failed: {e.message}", "TX_VALIDATION_FAILED")
        
        # Check for duplicate transactions
        tx_hashes = []
        for tx in block.transactions:
            tx_hash = tx.calculate_hash() if hasattr(tx, 'calculate_hash') else str(hash(tx))
            if tx_hash in tx_hashes:
                raise BlockValidationError("Duplicate transaction found in block", "DUPLICATE_TRANSACTION")
            tx_hashes.append(tx_hash)
        
        # Check for double spends within block
        self._check_double_spends(block.transactions[1:])
    
    def _validate_merkle_tree(self, block: Block):
        """Validate Merkle tree"""
        if not block.transactions:
            return
        
        # Calculate Merkle root
        tx_hashes = []
        for tx in block.transactions:
            if hasattr(tx, 'calculate_hash'):
                tx_hash = tx.calculate_hash()
            else:
                # Fallback hash calculation
                tx_data = json.dumps(tx.to_dict() if hasattr(tx, 'to_dict') else str(tx), sort_keys=True)
                tx_hash = hashlib.sha256(tx_data.encode()).hexdigest()
            tx_hashes.append(tx_hash)
        
        merkle_root = self._calculate_merkle_root(tx_hashes)
        
        # Compare with block's Merkle root (if available)
        if hasattr(block, 'merkle_root') and block.merkle_root:
            if merkle_root != block.merkle_root:
                raise BlockValidationError(f"Invalid Merkle root: expected {block.merkle_root}, got {merkle_root}", "INVALID_MERKLE_ROOT")
    
    def _validate_proof_of_work(self, block: Block):
        """Validate Proof-of-Work"""
        # Calculate block hash
        block_hash = block.calculate_hash()
        
        # Check if hash meets difficulty target
        target = self._get_difficulty_target(block.difficulty)
        
        # Convert hash to integer
        hash_int = int(block_hash, 16)
        target_int = int(target, 16)
        
        if hash_int > target_int:
            raise BlockValidationError(f"Invalid Proof-of-Work: {block_hash} > {target}", "INVALID_POW")
    
    def _validate_block_reward(self, block: Block):
        """Validate block reward and fees"""
        if not block.transactions:
            return
        
        coinbase_tx = block.transactions[0]
        
        # Calculate expected block reward
        block_reward = self._calculate_block_reward(block.index)
        
        # Calculate total fees from transactions
        total_fees = Decimal('0')
        for tx in block.transactions[1:]:
            fee = self.transaction_validator.utxo_validator.get_transaction_fee(tx)
            total_fees += fee
        
        # Calculate expected coinbase output
        expected_coinbase_output = block_reward + total_fees
        
        # Get actual coinbase output
        actual_coinbase_output = Decimal('0')
        for output in coinbase_tx.outputs:
            actual_coinbase_output += Decimal(str(output.get('amount', 0)))
        
        # Check if coinbase output is correct
        if actual_coinbase_output != expected_coinbase_output:
            raise BlockValidationError(f"Invalid coinbase reward: expected {expected_coinbase_output}, got {actual_coinbase_output}", "INVALID_COINBASE_REWARD")
    
    def _is_coinbase_transaction(self, tx: Transaction) -> bool:
        """Check if transaction is coinbase"""
        # Coinbase transactions have no inputs
        return len(tx.inputs) == 0
    
    def _validate_coinbase_transaction(self, tx: Transaction, block_index: int):
        """Validate coinbase transaction"""
        # Coinbase should have exactly one output
        if len(tx.outputs) != 1:
            raise BlockValidationError("Coinbase transaction must have exactly one output", "INVALID_COINBASE_OUTPUTS")
        
        # Check coinbase script size
        if hasattr(tx, 'coinbase_script') and len(tx.coinbase_script) > self.max_coinbase_script_size:
            raise BlockValidationError("Coinbase script too large", "COINBASE_SCRIPT_TOO_LARGE")
        
        # Validate coinbase output
        output = tx.outputs[0]
        if not isinstance(output, dict):
            raise BlockValidationError("Invalid coinbase output type", "INVALID_COINBASE_OUTPUT_TYPE")
        
        if 'address' not in output or 'amount' not in output:
            raise BlockValidationError("Coinbase output missing required fields", "MISSING_COINBASE_FIELDS")
        
        amount = Decimal(str(output['amount']))
        if amount <= 0:
            raise BlockValidationError("Coinbase output amount must be positive", "INVALID_COINBASE_AMOUNT")
    
    def _check_double_spends(self, transactions: List[Transaction]):
        """Check for double spends within block"""
        spent_utxos = set()
        
        for tx in transactions:
            for inp in tx.inputs:
                utxo_key = f"{inp['txid']}:{inp['vout']}"
                if utxo_key in spent_utxos:
                    raise BlockValidationError(f"Double spend detected: {utxo_key}", "DOUBLE_SPEND")
                spent_utxos.add(utxo_key)
    
    def _get_expected_difficulty(self) -> int:
        """Get expected difficulty for next block"""
        if hasattr(self.blockchain, 'get_difficulty'):
            return self.blockchain.get_difficulty()
        return 4  # Default difficulty
    
    def _get_difficulty_target(self, difficulty: int) -> str:
        """Get difficulty target for given difficulty"""
        # Create target with required leading zeros
        target = "0" * difficulty + "f" * (64 - difficulty)
        return target
    
    def _calculate_merkle_root(self, tx_hashes: List[str]) -> str:
        """Calculate Merkle root from transaction hashes"""
        if not tx_hashes:
            return "0" * 64
        
        # Make even number of hashes
        if len(tx_hashes) % 2 == 1:
            tx_hashes.append(tx_hashes[-1])
        
        # Build Merkle tree
        current_level = tx_hashes
        
        while len(current_level) > 1:
            next_level = []
            
            for i in range(0, len(current_level), 2):
                # Combine two hashes
                combined = current_level[i] + current_level[i + 1]
                # Hash the combination
                combined_hash = hashlib.sha256(combined.encode()).hexdigest()
                next_level.append(combined_hash)
            
            current_level = next_level
        
        return current_level[0]
    
    def _calculate_block_reward(self, block_index: int) -> Decimal:
        """Calculate block reward for given block index"""
        # Calculate number of halvings
        halvings = block_index // self.halving_interval
        
        # Apply halving
        reward = self.block_reward
        for _ in range(halvings):
            reward = reward / 2
        
        return reward
    
    def validate_block_sequence(self, blocks: List[Block]) -> Tuple[bool, List[str]]:
        """
        Validate a sequence of blocks
        
        Returns:
            (is_valid, error_messages)
        """
        errors = []
        
        try:
            # Validate each block
            for i, block in enumerate(blocks):
                try:
                    self.validate_block(block, check_transactions=True)
                except BlockValidationError as e:
                    errors.append(f"Block {i}: {e.message}")
                    return False, errors
            
            # Validate sequence consistency
            for i in range(1, len(blocks)):
                if blocks[i].index != blocks[i-1].index + 1:
                    errors.append(f"Block sequence gap at index {i}")
                    return False, errors
                
                if blocks[i].prev_hash != blocks[i-1].hash:
                    errors.append(f"Block sequence break at index {i}")
                    return False, errors
            
            return True, errors
            
        except Exception as e:
            errors.append(f"Sequence validation error: {str(e)}")
            return False, errors
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        return {
            'max_block_size': self.max_block_size,
            'max_block_weight': self.max_block_weight,
            'min_block_time': self.min_block_time,
            'max_future_block_time': self.max_future_block_time,
            'block_reward': str(self.block_reward),
            'halving_interval': self.halving_interval,
            'treasury_percent': str(self.treasury_percent),
            'fee_burn_percent': str(self.fee_burn_percent),
            'total_validations': getattr(self, '_total_validations', 0),
            'total_errors': getattr(self, '_total_errors', 0)
        }


class BlockOrphanChecker:
    """Checks for orphan blocks and chain forks"""
    
    def __init__(self, blockchain):
        self.blockchain = blockchain
    
    def check_orphans(self, new_block: Block) -> List[Block]:
        """Check for orphan blocks when adding new block"""
        orphans = []
        
        # Check if new block creates orphan
        if new_block.index > 0:
            expected_prev_hash = self.blockchain.chain[-1].hash if self.blockchain.chain else None
            
            if expected_prev_hash and new_block.prev_hash != expected_prev_hash:
                # Find blocks that reference this block's prev_hash
                for block in self.blockchain.chain:
                    if block.prev_hash == new_block.prev_hash and block.index == new_block.index:
                        orphans.append(block)
        
        return orphans
    
    def resolve_fork(self, fork_blocks: List[Block]) -> Block:
        """Resolve chain fork by selecting longest chain"""
        if not fork_blocks:
            return None
        
        # Select block with highest cumulative difficulty
        best_block = fork_blocks[0]
        best_score = self._calculate_chain_score(best_block)
        
        for block in fork_blocks[1:]:
            score = self._calculate_chain_score(block)
            if score > best_score:
                best_block = block
                best_score = score
        
        return best_block
    
    def _calculate_chain_score(self, block: Block) -> int:
        """Calculate chain score (cumulative difficulty)"""
        score = 0
        current_block = block
        
        while current_block:
            score += current_block.difficulty
            if current_block.index > 0:
                # Find previous block
                for prev_block in self.blockchain.chain:
                    if prev_block.hash == current_block.prev_hash:
                        current_block = prev_block
                        break
                else:
                    break
            else:
                break
        
        return score


# Utility functions
def create_block_validator(blockchain, utxo_set: UTXOSet) -> BlockValidator:
    """Create a block validator instance"""
    return BlockValidator(blockchain, utxo_set)


def validate_block_serialized(serialized_block: str, blockchain, utxo_set: UTXOSet) -> Tuple[bool, str]:
    """Validate a serialized block"""
    try:
        # Deserialize block
        block_data = json.loads(serialized_block)
        block = Block(
            index=block_data.get('index'),
            prev_hash=block_data.get('prev_hash'),
            transactions=block_data.get('transactions', []),
            timestamp=block_data.get('timestamp'),
            difficulty=block_data.get('difficulty'),
            nonce=block_data.get('nonce')
        )
        
        # Validate
        validator = BlockValidator(blockchain, utxo_set)
        validator.validate_block(block)
        
        return True, "Block is valid"
        
    except Exception as e:
        return False, f"Block validation error: {str(e)}"


def calculate_block_work(difficulty: int) -> int:
    """Calculate work done for a block with given difficulty"""
    return 2 ** (256 - difficulty)


def calculate_chain_difficulty(blocks: List[Block]) -> float:
    """Calculate average difficulty of a chain"""
    if not blocks:
        return 0.0
    
    total_difficulty = sum(block.difficulty for block in blocks)
    return total_difficulty / len(blocks)
