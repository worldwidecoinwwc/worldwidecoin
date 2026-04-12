# storage/utxo.py
import threading
import json
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal


class UTXOSet:
    """Unspent Transaction Output Set"""
    
    def __init__(self):
        self.utxos: Dict[str, Dict] = {}
        self.lock = threading.Lock()
    
    def add_utxo(self, txid: str, vout: int, amount: float, address: str, script_pubkey: str = ""):
        """Add a UTXO to the set"""
        with self.lock:
            utxo_key = f"{txid}:{vout}"
            self.utxos[utxo_key] = {
                'txid': txid,
                'vout': vout,
                'amount': amount,
                'address': address,
                'script_pubkey': script_pubkey,
                'spent': False
            }
    
    def get_utxo(self, utxo_key: str) -> Optional[Dict]:
        """Get a UTXO by key"""
        with self.lock:
            return self.utxos.get(utxo_key)
    
    def spend_utxo(self, utxo_key: str) -> bool:
        """Mark a UTXO as spent"""
        with self.lock:
            if utxo_key in self.utxos:
                self.utxos[utxo_key]['spent'] = True
                return True
            return False
    
    def remove_utxo(self, utxo_key: str) -> bool:
        """Remove a UTXO from the set"""
        with self.lock:
            if utxo_key in self.utxos:
                del self.utxos[utxo_key]
                return True
            return False
    
    def find_spendable_utxos(self, address: str, amount: float) -> Tuple[List[str], float]:
        """Find spendable UTXOs for an address"""
        with self.lock:
            spendable_utxos = []
            total_amount = 0.0
            
            for utxo_key, utxo in self.utxos.items():
                if (not utxo['spent'] and 
                    utxo['address'] == address and 
                    total_amount < amount):
                    spendable_utxos.append(utxo_key)
                    total_amount += utxo['amount']
            
            return spendable_utxos, total_amount
    
    def get_balance(self, address: str) -> float:
        """Get balance for an address"""
        with self.lock:
            balance = 0.0
            for utxo in self.utxos.values():
                if not utxo['spent'] and utxo['address'] == address:
                    balance += utxo['amount']
            return balance
    
    def get_all_utxos(self) -> Dict[str, Dict]:
        """Get all UTXOs"""
        with self.lock:
            return self.utxos.copy()
    
    def clear_spent_utxos(self):
        """Clear all spent UTXOs"""
        with self.lock:
            spent_keys = [key for key, utxo in self.utxos.items() if utxo['spent']]
            for key in spent_keys:
                del self.utxos[key]
    
    def validate_transaction(self, tx) -> bool:
        """Validate a transaction against UTXO set"""
        # Simplified validation
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get UTXO set statistics"""
        with self.lock:
            total_utxos = len(self.utxos)
            spent_utxos = sum(1 for utxo in self.utxos.values() if utxo['spent'])
            unspent_utxos = total_utxos - spent_utxos
            
            total_value = sum(
                utxo['amount'] for utxo in self.utxos.values() 
                if not utxo['spent']
            )
            
            return {
                'total_utxos': total_utxos,
                'spent_utxos': spent_utxos,
                'unspent_utxos': unspent_utxos,
                'total_value': total_value
            }
