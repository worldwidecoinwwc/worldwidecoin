# core/mempool_validator.py
import time
import heapq
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
from collections import defaultdict
from core.transaction import Transaction
from core.validation import TransactionValidator, ValidationError
from storage.utxo import UTXOSet


class MempoolValidationError(Exception):
    """Custom exception for mempool validation errors"""
    def __init__(self, message: str, error_code: str = "MEMPOOL_VALIDATION_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class MempoolEntry:
    """Represents a transaction entry in the mempool"""
    
    def __init__(self, tx: Transaction, fee: Decimal, size: int, timestamp: float):
        self.tx = tx
        self.fee = fee
        self.size = size
        self.timestamp = timestamp
        self.priority_score = self._calculate_priority()
    
    def _calculate_priority(self) -> float:
        """Calculate transaction priority score"""
        if self.size == 0:
            return 0.0
        
        # Priority = (fee * age) / size
        age = time.time() - self.timestamp
        return float(self.fee) * age / self.size
    
    def update_priority(self):
        """Update priority score based on current age"""
        self.priority_score = self._calculate_priority()
    
    def __lt__(self, other):
        """For priority queue (higher priority first)"""
        return self.priority_score > other.priority_score


class MempoolValidator:
    """Validates transactions for mempool inclusion"""
    
    def __init__(self, utxo_set: UTXOSet, max_mempool_size: int = 10000, max_mempool_bytes: int = 100000000):
        self.utxo_set = utxo_set
        self.max_mempool_size = max_mempool_size
        self.max_mempool_bytes = max_mempool_bytes
        self.min_relay_fee = Decimal('0.00001')
        self.max_tx_age = 86400 * 7  # 7 days
        
        # Mempool state
        self.entries: Dict[str, MempoolEntry] = {}
        self.priority_queue = []
        self.utxo_spent_by = {}  # UTXO -> tx_hash
        
        # Statistics
        self.total_size = 0
        self.total_bytes = 0
        self.total_fees = Decimal('0')
        
        # Transaction validator
        self.tx_validator = TransactionValidator(utxo_set)
    
    def validate_for_mempool(self, tx: Transaction) -> Tuple[bool, str]:
        """
        Validate transaction for mempool inclusion
        
        Returns:
            (is_valid, error_message)
        """
        try:
            # 1. Basic transaction validation
            is_valid, message = self.tx_validator.validate_transaction_for_mempool(tx)
            if not is_valid:
                return False, message
            
            # 2. Mempool-specific validation
            self._validate_mempool_rules(tx)
            
            # 3. Fee validation
            fee = self.tx_validator.utxo_validator.get_transaction_fee(tx)
            if not self._validate_fee(tx, fee):
                return False, "Transaction fee too low"
            
            # 4. Size validation
            size = self.tx_validator.utxo_validator.get_transaction_size(tx)
            if not self._validate_size(tx, size):
                return False, "Transaction too large"
            
            # 5. RBF validation (Replace-By-Fee)
            self._validate_rbf(tx, fee)
            
            return True, "Transaction is valid for mempool"
            
        except ValidationError as e:
            return False, e.message
        except Exception as e:
            return False, f"Mempool validation error: {str(e)}"
    
    def _validate_mempool_rules(self, tx: Transaction):
        """Validate mempool-specific rules"""
        tx_hash = self._get_tx_hash(tx)
        
        # Check for duplicate transaction
        if tx_hash in self.entries:
            raise MempoolValidationError("Transaction already in mempool", "DUPLICATE_TRANSACTION")
        
        # Check for conflicting transactions (double spends)
        for inp in tx.inputs:
            utxo_key = f"{inp['txid']}:{inp['vout']}"
            if utxo_key in self.utxo_spent_by:
                conflicting_tx = self.utxo_spent_by[utxo_key]
                raise MempoolValidationError(f"Double spend detected: UTXO {utxo_key} already spent by {conflicting_tx}", "DOUBLE_SPEND")
        
        # Check mempool capacity
        if len(self.entries) >= self.max_mempool_size:
            # Try to evict low-priority transactions
            if not self._evict_low_priority(tx):
                raise MempoolValidationError("Mempool is full", "MEMPOOL_FULL")
        
        # Check mempool byte capacity
        size = self.tx_validator.utxo_validator.get_transaction_size(tx)
        if self.total_bytes + size > self.max_mempool_bytes:
            if not self._evict_by_bytes(tx):
                raise MempoolValidationError("Mempool byte limit exceeded", "MEMPOOL_BYTES_FULL")
        
        # Check transaction age (for RBF)
        if hasattr(tx, 'locktime') and tx.locktime > time.time():
            raise MempoolValidationError("Transaction is time-locked", "TIME_LOCKED")
    
    def _validate_fee(self, tx: Transaction, fee: Decimal) -> bool:
        """Validate transaction fee"""
        # Minimum fee
        if fee < self.min_relay_fee:
            return False
        
        # Fee rate validation
        size = self.tx_validator.utxo_validator.get_transaction_size(tx)
        fee_rate = fee / size if size > 0 else Decimal('0')
        
        # Minimum fee rate (1000 satoshis per KB)
        min_fee_rate = Decimal('0.00001')
        if fee_rate < min_fee_rate:
            return False
        
        return True
    
    def _validate_size(self, tx: Transaction, size: int) -> bool:
        """Validate transaction size"""
        max_tx_size = 1000000  # 1MB
        return size <= max_tx_size
    
    def _validate_rbf(self, tx: Transaction, fee: Decimal):
        """Validate Replace-By-Fee rules"""
        tx_hash = self._get_tx_hash(tx)
        
        # Check if transaction replaces any existing transactions
        for inp in tx.inputs:
            utxo_key = f"{inp['txid']}:{inp['vout']}"
            if utxo_key in self.utxo_spent_by:
                existing_tx_hash = self.utxo_spent_by[utxo_key]
                existing_entry = self.entries.get(existing_tx_hash)
                
                if existing_entry:
                    # RBF rules: new transaction must pay higher fee
                    if fee <= existing_entry.fee:
                        raise MempoolValidationError(f"RBF fee too low: {fee} <= {existing_entry.fee}", "RBF_FEE_TOO_LOW")
                    
                    # RBF fee must be at least min_relay_fee higher
                    if fee - existing_entry.fee < self.min_relay_fee:
                        raise MempoolValidationError(f"RBF fee increase too small: {fee - existing_entry.fee} < {self.min_relay_fee}", "RBF_FEE_INCREASE_TOO_SMALL")
    
    def _get_tx_hash(self, tx: Transaction) -> str:
        """Get transaction hash"""
        if hasattr(tx, 'calculate_hash'):
            return tx.calculate_hash()
        
        # Fallback hash calculation
        tx_data = {
            'inputs': tx.inputs,
            'outputs': tx.outputs,
            'signature': getattr(tx, 'signature', ''),
            'public_key': getattr(tx, 'public_key', '')
        }
        
        import hashlib
        import json
        return hashlib.sha256(json.dumps(tx_data, sort_keys=True).encode()).hexdigest()
    
    def _evict_low_priority(self, new_tx: Transaction) -> bool:
        """Evict low priority transactions to make room"""
        if not self.entries:
            return False
        
        # Sort entries by priority (lowest first)
        sorted_entries = sorted(self.entries.values(), key=lambda x: x.priority_score)
        
        # Try to evict enough transactions
        evicted = 0
        for entry in sorted_entries:
            if len(self.entries) - evicted < self.max_mempool_size:
                break
            
            # Don't evict if new transaction has lower priority
            new_entry = MempoolEntry(
                new_tx, 
                self.tx_validator.utxo_validator.get_transaction_fee(new_tx),
                self.tx_validator.utxo_validator.get_transaction_size(new_tx),
                time.time()
            )
            
            if entry.priority_score >= new_entry.priority_score:
                break
            
            # Remove transaction
            self._remove_transaction(self._get_tx_hash(entry.tx))
            evicted += 1
        
        return evicted > 0
    
    def _evict_by_bytes(self, new_tx: Transaction) -> bool:
        """Evict transactions by byte size"""
        if not self.entries:
            return False
        
        new_size = self.tx_validator.utxo_validator.get_transaction_size(new_tx)
        
        # Sort entries by fee rate (lowest first)
        sorted_entries = sorted(
            self.entries.values(), 
            key=lambda x: x.fee / x.size if x.size > 0 else 0
        )
        
        evicted_bytes = 0
        for entry in sorted_entries:
            if self.total_bytes - evicted_bytes + new_size <= self.max_mempool_bytes:
                break
            
            # Remove transaction
            self._remove_transaction(self._get_tx_hash(entry.tx))
            evicted_bytes += entry.size
        
        return evicted_bytes > 0
    
    def _remove_transaction(self, tx_hash: str):
        """Remove transaction from mempool"""
        if tx_hash not in self.entries:
            return
        
        entry = self.entries[tx_hash]
        
        # Update statistics
        self.total_size -= 1
        self.total_bytes -= entry.size
        self.total_fees -= entry.fee
        
        # Remove UTXO spent references
        for inp in entry.tx.inputs:
            utxo_key = f"{inp['txid']}:{inp['vout']}"
            if utxo_key in self.utxo_spent_by:
                del self.utxo_spent_by[utxo_key]
        
        # Remove entry
        del self.entries[tx_hash]
    
    def add_transaction(self, tx: Transaction) -> Tuple[bool, str]:
        """Add transaction to mempool"""
        # Validate
        is_valid, message = self.validate_for_mempool(tx)
        if not is_valid:
            return False, message
        
        # Calculate fee and size
        fee = self.tx_validator.utxo_validator.get_transaction_fee(tx)
        size = self.tx_validator.utxo_validator.get_transaction_size(tx)
        
        # Create entry
        entry = MempoolEntry(tx, fee, size, time.time())
        tx_hash = self._get_tx_hash(tx)
        
        # Add to mempool
        self.entries[tx_hash] = entry
        heapq.heappush(self.priority_queue, entry)
        
        # Update UTXO spent references
        for inp in tx.inputs:
            utxo_key = f"{inp['txid']}:{inp['vout']}"
            self.utxo_spent_by[utxo_key] = tx_hash
        
        # Update statistics
        self.total_size += 1
        self.total_bytes += size
        self.total_fees += fee
        
        return True, "Transaction added to mempool"
    
    def remove_transaction(self, tx_hash: str) -> bool:
        """Remove transaction from mempool"""
        if tx_hash in self.entries:
            self._remove_transaction(tx_hash)
            return True
        return False
    
    def get_transactions_for_block(self, max_tx_count: int = 1000, max_block_size: int = 1000000) -> List[Transaction]:
        """Get transactions for block inclusion"""
        if not self.entries:
            return []
        
        # Update priorities
        for entry in self.entries.values():
            entry.update_priority()
        
        # Rebuild priority queue
        self.priority_queue = list(self.entries.values())
        heapq.heapify(self.priority_queue)
        
        # Select transactions
        selected_txs = []
        current_size = 0
        
        while (self.priority_queue and 
               len(selected_txs) < max_tx_count and 
               current_size < max_block_size):
            
            entry = heapq.heappop(self.priority_queue)
            tx_size = entry.size
            
            if current_size + tx_size > max_block_size:
                continue
            
            selected_txs.append(entry.tx)
            current_size += tx_size
        
        return selected_txs
    
    def get_mempool_info(self) -> Dict[str, Any]:
        """Get mempool information"""
        return {
            'size': self.total_size,
            'bytes': self.total_bytes,
            'total_fees': str(self.total_fees),
            'max_size': self.max_mempool_size,
            'max_bytes': self.max_mempool_bytes,
            'min_relay_fee': str(self.min_relay_fee),
            'oldest_tx_time': min((e.timestamp for e in self.entries.values()), default=0),
            'newest_tx_time': max((e.timestamp for e in self.entries.values()), default=0),
            'average_fee_rate': str(self.total_fees / self.total_bytes if self.total_bytes > 0 else 0),
            'utxo_spent_count': len(self.utxo_spent_by)
        }
    
    def get_transaction_fee_rate(self, tx_hash: str) -> Optional[Decimal]:
        """Get transaction fee rate"""
        entry = self.entries.get(tx_hash)
        if entry and entry.size > 0:
            return entry.fee / entry.size
        return None
    
    def estimate_fee(self, target_blocks: int = 6) -> Decimal:
        """Estimate fee rate for target confirmation"""
        if not self.entries:
            return self.min_relay_fee
        
        # Get fee rates from mempool
        fee_rates = []
        for entry in self.entries.values():
            if entry.size > 0:
                fee_rates.append(entry.fee / entry.size)
        
        if not fee_rates:
            return self.min_relay_fee
        
        # Sort fee rates
        fee_rates.sort()
        
        # Estimate based on target
        if target_blocks <= 1:
            # High priority - use top 25% fee rates
            index = int(len(fee_rates) * 0.75)
        elif target_blocks <= 6:
            # Medium priority - use median fee rate
            index = len(fee_rates) // 2
        else:
            # Low priority - use bottom 25% fee rates
            index = int(len(fee_rates) * 0.25)
        
        index = min(index, len(fee_rates) - 1)
        return max(fee_rates[index], self.min_relay_fee)
    
    def cleanup_expired_transactions(self) -> int:
        """Remove expired transactions from mempool"""
        current_time = time.time()
        expired_txs = []
        
        for tx_hash, entry in self.entries.items():
            if current_time - entry.timestamp > self.max_tx_age:
                expired_txs.append(tx_hash)
        
        for tx_hash in expired_txs:
            self.remove_transaction(tx_hash)
        
        return len(expired_txs)
    
    def get_conflicts(self, tx: Transaction) -> List[str]:
        """Get transactions that conflict with given transaction"""
        conflicts = []
        
        for inp in tx.inputs:
            utxo_key = f"{inp['txid']}:{inp['vout']}"
            if utxo_key in self.utxo_spent_by:
                conflicts.append(self.utxo_spent_by[utxo_key])
        
        return list(set(conflicts))  # Remove duplicates
    
    def get_transaction_info(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Get detailed transaction information"""
        entry = self.entries.get(tx_hash)
        if not entry:
            return None
        
        return {
            'tx_hash': tx_hash,
            'fee': str(entry.fee),
            'size': entry.size,
            'timestamp': entry.timestamp,
            'priority_score': entry.priority_score,
            'fee_rate': str(entry.fee / entry.size if entry.size > 0 else 0),
            'age': time.time() - entry.timestamp,
            'inputs_count': len(entry.tx.inputs),
            'outputs_count': len(entry.tx.outputs)
        }


# Utility functions
def create_mempool_validator(utxo_set: UTXOSet, max_size: int = 10000, max_bytes: int = 100000000) -> MempoolValidator:
    """Create a mempool validator instance"""
    return MempoolValidator(utxo_set, max_size, max_bytes)


def calculate_optimal_fee_rate(mempool_entries: List[MempoolEntry], target_blocks: int = 6) -> Decimal:
    """Calculate optimal fee rate from mempool entries"""
    if not mempool_entries:
        return Decimal('0.00001')
    
    # Sort by priority
    sorted_entries = sorted(mempool_entries, key=lambda x: x.priority_score, reverse=True)
    
    # Get fee rates
    fee_rates = []
    for entry in sorted_entries:
        if entry.size > 0:
            fee_rates.append(entry.fee / entry.size)
    
    if not fee_rates:
        return Decimal('0.00001')
    
    # Select fee rate based on target
    if target_blocks <= 1:
        # Top 10%
        index = max(0, int(len(fee_rates) * 0.1) - 1)
    elif target_blocks <= 3:
        # Top 25%
        index = max(0, int(len(fee_rates) * 0.25) - 1)
    elif target_blocks <= 6:
        # Median
        index = len(fee_rates) // 2
    else:
        # Bottom 25%
        index = min(len(fee_rates) - 1, int(len(fee_rates) * 0.75))
    
    return fee_rates[index]


def validate_rbf_rules(old_tx: Transaction, new_tx: Transaction, old_fee: Decimal, new_fee: Decimal) -> bool:
    """Validate Replace-By-Fee rules"""
    # New fee must be higher
    if new_fee <= old_fee:
        return False
    
    # Fee increase must be at least min_relay_fee
    min_fee_increase = Decimal('0.00001')
    if new_fee - old_fee < min_fee_increase:
        return False
    
    return True
