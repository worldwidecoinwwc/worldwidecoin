# core/validation.py
import hashlib
import json
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
from core.transaction import Transaction
from storage.utxo import UTXOSet


class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class UTXOValidator:
    """Validates UTXO transactions"""
    
    def __init__(self, utxo_set: UTXOSet):
        self.utxo_set = utxo_set
        self.min_fee = Decimal('0.0001')  # Minimum transaction fee
        self.max_tx_size = 1000000  # 1MB max transaction size
        self.max_inputs = 100  # Maximum inputs per transaction
        self.max_outputs = 100  # Maximum outputs per transaction
    
    def validate_transaction(self, tx: Transaction, check_utxo_spent: bool = True) -> bool:
        """
        Validate a transaction against UTXO set and rules
        
        Args:
            tx: Transaction to validate
            check_utxo_spent: Whether to check if UTXOs are already spent
            
        Returns:
            True if valid, raises ValidationError if invalid
        """
        try:
            # 1. Basic transaction structure validation
            self._validate_transaction_structure(tx)
            
            # 2. Input validation
            input_sum = self._validate_inputs(tx, check_utxo_spent)
            
            # 3. Output validation
            output_sum = self._validate_outputs(tx)
            
            # 4. Fee validation
            self._validate_fees(input_sum, output_sum)
            
            # 5. Script validation (basic for now)
            self._validate_scripts(tx)
            
            return True
            
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Unexpected validation error: {str(e)}", "UNKNOWN_ERROR")
    
    def _validate_transaction_structure(self, tx: Transaction):
        """Validate basic transaction structure"""
        if not isinstance(tx, Transaction):
            raise ValidationError("Invalid transaction object", "INVALID_TX_TYPE")
        
        if not tx.inputs:
            raise ValidationError("Transaction has no inputs", "NO_INPUTS")
        
        if not tx.outputs:
            raise ValidationError("Transaction has no outputs", "NO_OUTPUTS")
        
        if len(tx.inputs) > self.max_inputs:
            raise ValidationError(f"Too many inputs: {len(tx.inputs)} > {self.max_inputs}", "TOO_MANY_INPUTS")
        
        if len(tx.outputs) > self.max_outputs:
            raise ValidationError(f"Too many outputs: {len(tx.outputs)} > {self.max_outputs}", "TOO_MANY_OUTPUTS")
        
        # Check for duplicate inputs
        input_refs = [(inp.get('txid'), inp.get('vout')) for inp in tx.inputs]
        if len(input_refs) != len(set(input_refs)):
            raise ValidationError("Duplicate inputs found", "DUPLICATE_INPUTS")
        
        # Check for duplicate outputs (same address)
        output_addresses = [out.get('address') for out in tx.outputs]
        if len(output_addresses) != len(set(output_addresses)):
            raise ValidationError("Duplicate output addresses found", "DUPLICATE_OUTPUTS")
    
    def _validate_inputs(self, tx: Transaction, check_utxo_spent: bool) -> Decimal:
        """Validate transaction inputs and return total input amount"""
        input_sum = Decimal('0')
        
        for i, inp in enumerate(tx.inputs):
            # Validate input structure
            if not isinstance(inp, dict):
                raise ValidationError(f"Input {i} is not a dictionary", "INVALID_INPUT_TYPE")
            
            required_fields = ['txid', 'vout']
            for field in required_fields:
                if field not in inp:
                    raise ValidationError(f"Input {i} missing required field: {field}", "MISSING_INPUT_FIELD")
            
            txid = inp['txid']
            vout = inp['vout']
            
            # Validate txid format
            if not isinstance(txid, str) or len(txid) != 64:
                raise ValidationError(f"Input {i} has invalid txid format", "INVALID_TXID")
            
            # Validate vout
            if not isinstance(vout, int) or vout < 0:
                raise ValidationError(f"Input {i} has invalid vout", "INVALID_VOUT")
            
            # Check if UTXO exists
            utxo_key = f"{txid}:{vout}"
            utxo = self.utxo_set.get_utxo(utxo_key)
            
            if not utxo:
                raise ValidationError(f"Input {i} references non-existent UTXO: {utxo_key}", "UTXO_NOT_FOUND")
            
            # Check if UTXO is already spent (only if checking)
            if check_utxo_spent and utxo.get('spent', False):
                raise ValidationError(f"Input {i} references already spent UTXO: {utxo_key}", "UTXO_ALREADY_SPENT")
            
            # Validate script signature if present
            if 'script_sig' in inp:
                self._validate_script_signature(inp['script_sig'], utxo.get('script_pubkey'))
            
            # Add to input sum
            amount = Decimal(str(utxo.get('amount', 0)))
            if amount <= 0:
                raise ValidationError(f"Input {i} has invalid amount: {amount}", "INVALID_INPUT_AMOUNT")
            
            input_sum += amount
        
        return input_sum
    
    def _validate_outputs(self, tx: Transaction) -> Decimal:
        """Validate transaction outputs and return total output amount"""
        output_sum = Decimal('0')
        
        for i, out in enumerate(tx.outputs):
            # Validate output structure
            if not isinstance(out, dict):
                raise ValidationError(f"Output {i} is not a dictionary", "INVALID_OUTPUT_TYPE")
            
            required_fields = ['address', 'amount']
            for field in required_fields:
                if field not in out:
                    raise ValidationError(f"Output {i} missing required field: {field}", "MISSING_OUTPUT_FIELD")
            
            address = out['address']
            amount = Decimal(str(out.get('amount', 0)))
            
            # Validate address format
            if not isinstance(address, str) or len(address) < 26 or len(address) > 35:
                raise ValidationError(f"Output {i} has invalid address format", "INVALID_ADDRESS")
            
            # Validate amount
            if amount <= 0:
                raise ValidationError(f"Output {i} has invalid amount: {amount}", "INVALID_OUTPUT_AMOUNT")
            
            # Check for dust outputs
            if amount < self.min_fee:
                raise ValidationError(f"Output {i} is below dust threshold: {amount}", "DUST_OUTPUT")
            
            # Validate script pubkey if present
            if 'script_pubkey' in out:
                self._validate_script_pubkey(out['script_pubkey'])
            
            output_sum += amount
        
        return output_sum
    
    def _validate_fees(self, input_sum: Decimal, output_sum: Decimal):
        """Validate transaction fees"""
        fee = input_sum - output_sum
        
        if fee < 0:
            raise ValidationError("Transaction outputs exceed inputs", "OUTPUTS_EXCEED_INPUTS")
        
        if fee < self.min_fee:
            raise ValidationError(f"Transaction fee too low: {fee} < {self.min_fee}", "FEE_TOO_LOW")
    
    def _validate_scripts(self, tx: Transaction):
        """Validate transaction scripts"""
        # For now, basic script validation
        # Full script validation will be implemented in Phase 2.4
        
        # Check if transaction has signature
        if not hasattr(tx, 'signature') or not tx.signature:
            raise ValidationError("Transaction missing signature", "MISSING_SIGNATURE")
        
        if not hasattr(tx, 'public_key') or not tx.public_key:
            raise ValidationError("Transaction missing public key", "MISSING_PUBLIC_KEY")
        
        # Validate signature format
        if not isinstance(tx.signature, str) or len(tx.signature) != 128:
            raise ValidationError("Invalid signature format", "INVALID_SIGNATURE")
        
        # Validate public key format
        if not isinstance(tx.public_key, str) or len(tx.public_key) != 130:
            raise ValidationError("Invalid public key format", "INVALID_PUBLIC_KEY")
    
    def _validate_script_signature(self, script_sig: str, script_pubkey: str):
        """Validate script signature against script pubkey"""
        # Basic validation for now
        if not isinstance(script_sig, str):
            raise ValidationError("Invalid script signature type", "INVALID_SCRIPT_SIG")
        
        if not isinstance(script_pubkey, str):
            raise ValidationError("Invalid script pubkey type", "INVALID_SCRIPT_PUBKEY")
    
    def _validate_script_pubkey(self, script_pubkey: str):
        """Validate script pubkey format"""
        if not isinstance(script_pubkey, str):
            raise ValidationError("Invalid script pubkey type", "INVALID_SCRIPT_PUBKEY")
        
        # Basic length check
        if len(script_pubkey) < 10 or len(script_pubkey) > 1000:
            raise ValidationError("Script pubkey length invalid", "INVALID_SCRIPT_PUBKEY_LENGTH")
    
    def get_transaction_fee(self, tx: Transaction) -> Decimal:
        """Calculate transaction fee"""
        input_sum = Decimal('0')
        
        for inp in tx.inputs:
            txid = inp['txid']
            vout = inp['vout']
            utxo_key = f"{txid}:{vout}"
            utxo = self.utxo_set.get_utxo(utxo_key)
            
            if utxo:
                input_sum += Decimal(str(utxo.get('amount', 0)))
        
        output_sum = Decimal('0')
        for out in tx.outputs:
            output_sum += Decimal(str(out.get('amount', 0)))
        
        return input_sum - output_sum
    
    def estimate_fee(self, tx_size: int, fee_rate: Decimal = Decimal('0.0001')) -> Decimal:
        """Estimate transaction fee based on size and fee rate"""
        return Decimal(tx_size) * fee_rate
    
    def get_transaction_size(self, tx: Transaction) -> int:
        """Get transaction size in bytes"""
        # Serialize transaction to estimate size
        tx_dict = {
            'inputs': tx.inputs,
            'outputs': tx.outputs,
            'signature': getattr(tx, 'signature', ''),
            'public_key': getattr(tx, 'public_key', '')
        }
        
        serialized = json.dumps(tx_dict, sort_keys=True).encode('utf-8')
        return len(serialized)


class TransactionValidator:
    """Main transaction validation coordinator"""
    
    def __init__(self, utxo_set: UTXOSet):
        self.utxo_validator = UTXOValidator(utxo_set)
        self.mempool_validator = None  # Will be set later
        self.block_validator = None   # Will be set later
    
    def validate_transaction_for_mempool(self, tx: Transaction) -> Tuple[bool, str]:
        """
        Validate transaction for mempool inclusion
        
        Returns:
            (is_valid, error_message)
        """
        try:
            # Basic UTXO validation
            self.utxo_validator.validate_transaction(tx, check_utxo_spent=True)
            
            # Additional mempool-specific validation
            if self.mempool_validator:
                self.mempool_validator.validate_for_mempool(tx)
            
            return True, "Transaction is valid"
            
        except ValidationError as e:
            return False, e.message
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def validate_transaction_for_block(self, tx: Transaction) -> Tuple[bool, str]:
        """
        Validate transaction for block inclusion
        
        Returns:
            (is_valid, error_message)
        """
        try:
            # UTXO validation (don't check if spent since it's in a block)
            self.utxo_validator.validate_transaction(tx, check_utxo_spent=False)
            
            # Block-specific validation
            if self.block_validator:
                self.block_validator.validate_for_block(tx)
            
            return True, "Transaction is valid"
            
        except ValidationError as e:
            return False, e.message
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def validate_transaction_batch(self, transactions: List[Transaction]) -> List[Tuple[bool, str]]:
        """
        Validate a batch of transactions
        
        Returns:
            List of (is_valid, error_message) tuples
        """
        results = []
        
        for tx in transactions:
            try:
                is_valid, message = self.validate_transaction_for_mempool(tx)
                results.append((is_valid, message))
            except Exception as e:
                results.append((False, f"Batch validation error: {str(e)}"))
        
        return results
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        return {
            'utxo_validator': {
                'min_fee': str(self.utxo_validator.min_fee),
                'max_tx_size': self.utxo_validator.max_tx_size,
                'max_inputs': self.utxo_validator.max_inputs,
                'max_outputs': self.utxo_validator.max_outputs
            },
            'total_validations': getattr(self, '_total_validations', 0),
            'total_errors': getattr(self, '_total_errors', 0)
        }


# Utility functions
def create_transaction_validator(utxo_set: UTXOSet) -> TransactionValidator:
    """Create a transaction validator instance"""
    return TransactionValidator(utxo_set)


def validate_transaction_serialized(serialized_tx: str, utxo_set: UTXOSet) -> Tuple[bool, str]:
    """Validate a serialized transaction"""
    try:
        # Deserialize transaction
        tx_data = json.loads(serialized_tx)
        tx = Transaction(
            inputs=tx_data.get('inputs', []),
            outputs=tx_data.get('outputs', []),
            signature=tx_data.get('signature'),
            public_key=tx_data.get('public_key')
        )
        
        # Validate
        validator = TransactionValidator(utxo_set)
        return validator.validate_transaction_for_mempool(tx)
        
    except Exception as e:
        return False, f"Deserialization error: {str(e)}"


def check_double_spend(transactions: List[Transaction]) -> List[str]:
    """Check for double spends in a list of transactions"""
    spent_utxos = set()
    double_spends = []
    
    for tx in transactions:
        for inp in tx.inputs:
            utxo_key = f"{inp['txid']}:{inp['vout']}"
            if utxo_key in spent_utxos:
                double_spends.append(utxo_key)
            else:
                spent_utxos.add(utxo_key)
    
    return double_spends


def calculate_optimal_fee(tx_size: int, utxo_count: int, priority: str = 'medium') -> Decimal:
    """Calculate optimal transaction fee based on size and priority"""
    base_fee_rate = {
        'low': Decimal('0.00001'),
        'medium': Decimal('0.0001'),
        'high': Decimal('0.001')
    }
    
    fee_rate = base_fee_rate.get(priority, base_fee_rate['medium'])
    
    # Add extra fee for more inputs (complexity)
    complexity_fee = Decimal(utxo_count * 0.00001)
    
    return Decimal(tx_size) * fee_rate + complexity_fee
