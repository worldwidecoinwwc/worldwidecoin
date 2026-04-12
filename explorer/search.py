# explorer/search.py
import re
import time
from typing import Dict, List, Optional, Any, Tuple
from core.blockchain import Blockchain
from core.transaction import Transaction
from storage.utxo import UTXOSet


class SearchEngine:
    """Advanced search engine for WorldWideCoin blockchain"""
    
    def __init__(self, blockchain: Blockchain, database=None):
        self.blockchain = blockchain
        self.utxo_set = blockchain.utxo
        self.database = database
        
        # Search index for performance
        self.search_index = {}
        self._build_search_index()
    
    def _build_search_index(self):
        """Build search index for fast lookups"""
        print("Building search index...")
        
        self.search_index = {
            'blocks': {},
            'transactions': {},
            'addresses': {},
            'keywords': {}
        }
        
        # Index blocks
        for block in self.blockchain.chain:
            block_hash = block.calculate_hash() if hasattr(block, 'calculate_hash') else block.hash
            self.search_index['blocks'][block_hash] = {
                'height': block.index,
                'timestamp': block.timestamp,
                'hash': block_hash,
                'tx_count': len(block.transactions)
            }
        
        # Index transactions
        for block in self.blockchain.chain:
            for tx in block.transactions:
                tx_hash = tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash
                self.search_index['transactions'][tx_hash] = {
                    'block_hash': block.calculate_hash() if hasattr(block, 'calculate_hash') else block.hash,
                    'block_height': block.index,
                    'timestamp': block.timestamp,
                    'hash': tx_hash,
                    'inputs_count': len(tx.inputs),
                    'outputs_count': len(tx.outputs)
                }
        
        # Index addresses
        addresses = set()
        for block in self.blockchain.chain:
            for tx in block.transactions:
                for out in tx.outputs:
                    if 'address' in out:
                        addresses.add(out['address'])
        
        for address in addresses:
            balance = self.utxo_set.get_balance(address)
            tx_count = self._count_address_transactions(address)
            
            self.search_index['addresses'][address] = {
                'address': address,
                'balance': balance,
                'tx_count': tx_count,
                'first_seen': self._get_address_first_seen(address),
                'last_seen': self._get_address_last_seen(address)
            }
        
        print(f"Search index built: {len(self.search_index['blocks'])} blocks, "
              f"{len(self.search_index['transactions'])} transactions, "
              f"{len(self.search_index['addresses'])} addresses")
    
    def search(self, query: str, search_type: str = 'all', limit: int = 50) -> Dict:
        """
        Search blockchain for blocks, transactions, or addresses
        
        Args:
            query: Search query
            search_type: 'all', 'block', 'tx', 'address'
            limit: Maximum results per type
            
        Returns:
            Search results dictionary
        """
        query = query.strip()
        if not query:
            return {'error': 'Empty query'}
        
        results = {
            'blocks': [],
            'transactions': [],
            'addresses': [],
            'query': query,
            'search_type': search_type,
            'total_results': 0
        }
        
        # Determine search type based on query format
        if search_type == 'all':
            search_type = self._detect_query_type(query)
        
        # Perform search based on type
        if search_type in ['all', 'block']:
            results['blocks'] = self._search_blocks(query, limit)
        
        if search_type in ['all', 'tx', 'transaction']:
            results['transactions'] = self._search_transactions(query, limit)
        
        if search_type in ['all', 'address']:
            results['addresses'] = self._search_addresses(query, limit)
        
        # Calculate total results
        results['total_results'] = (
            len(results['blocks']) + 
            len(results['transactions']) + 
            len(results['addresses'])
        )
        
        return results
    
    def _detect_query_type(self, query: str) -> str:
        """Detect query type based on format"""
        # Hash pattern (64 hex characters)
        if re.match(r'^[0-9a-fA-F]{64}$', query):
            return 'block'
        
        # Address pattern (26-35 base58 characters)
        if re.match(r'^[1-9A-HJ-NP-Za-km-z]{26,35}$', query):
            return 'address'
        
        # Height pattern (digits)
        if query.isdigit():
            return 'block'
        
        # Amount pattern (decimal number)
        if re.match(r'^\d+\.?\d*$', query):
            return 'address'
        
        return 'all'
    
    def _search_blocks(self, query: str, limit: int) -> List[Dict]:
        """Search blocks"""
        results = []
        
        # Search by hash
        if re.match(r'^[0-9a-fA-F]{64}$', query):
            block = self._get_block_by_hash(query)
            if block:
                results.append(self._format_block_result(block))
        
        # Search by height
        elif query.isdigit():
            height = int(query)
            if 0 <= height < len(self.blockchain.chain):
                block = self.blockchain.chain[height]
                results.append(self._format_block_result(block))
        
        # Search by timestamp range
        elif re.match(r'^\d{10}$', query):
            timestamp = int(query)
            blocks = self._get_blocks_by_timestamp(timestamp)
            results.extend([self._format_block_result(block) for block in blocks[:limit]])
        
        # Keyword search
        else:
            blocks = self._keyword_search_blocks(query)
            results.extend([self._format_block_result(block) for block in blocks[:limit]])
        
        return results
    
    def _search_transactions(self, query: str, limit: int) -> List[Dict]:
        """Search transactions"""
        results = []
        
        # Search by hash
        if re.match(r'^[0-9a-fA-F]{64}$', query):
            tx = self._get_transaction_by_hash(query)
            if tx:
                results.append(self._format_transaction_result(tx))
        
        # Search by amount
        elif re.match(r'^\d+\.?\d*$', query):
            amount = float(query)
            txs = self._get_transactions_by_amount(amount)
            results.extend([self._format_transaction_result(tx) for tx in txs[:limit]])
        
        # Keyword search
        else:
            txs = self._keyword_search_transactions(query)
            results.extend([self._format_transaction_result(tx) for tx in txs[:limit]])
        
        return results
    
    def _search_addresses(self, query: str, limit: int) -> List[Dict]:
        """Search addresses"""
        results = []
        
        # Search by address
        if re.match(r'^[1-9A-HJ-NP-Za-km-z]{26,35}$', query):
            address_info = self._get_address_info(query)
            if address_info and address_info['balance'] > 0:
                results.append(address_info)
        
        # Search by balance
        elif re.match(r'^\d+\.?\d*$', query):
            balance = float(query)
            addresses = self._get_addresses_by_balance(balance)
            results.extend(addresses[:limit])
        
        # Keyword search
        else:
            addresses = self._keyword_search_addresses(query)
            results.extend(addresses[:limit])
        
        return results
    
    def _get_block_by_hash(self, block_hash: str):
        """Get block by hash"""
        for block in self.blockchain.chain:
            if hasattr(block, 'calculate_hash'):
                if block.calculate_hash() == block_hash:
                    return block
            elif hasattr(block, 'hash'):
                if block.hash == block_hash:
                    return block
        return None
    
    def _get_transaction_by_hash(self, tx_hash: str):
        """Get transaction by hash"""
        for block in self.blockchain.chain:
            for tx in block.transactions:
                if hasattr(tx, 'calculate_hash'):
                    if tx.calculate_hash() == tx_hash:
                        return tx
                elif hasattr(tx, 'hash'):
                    if tx.hash() == tx_hash:
                        return tx
        return None
    
    def _get_blocks_by_timestamp(self, timestamp: int, window: int = 3600) -> List:
        """Get blocks by timestamp (within window)"""
        start_time = timestamp - window // 2
        end_time = timestamp + window // 2
        
        return [
            block for block in self.blockchain.chain
            if start_time <= block.timestamp <= end_time
        ]
    
    def _get_transactions_by_amount(self, amount: float, tolerance: float = 0.01) -> List:
        """Get transactions by amount (within tolerance)"""
        results = []
        
        for block in self.blockchain.chain:
            for tx in block.transactions:
                for out in tx.outputs:
                    if 'amount' in out:
                        tx_amount = out['amount']
                        if abs(tx_amount - amount) <= tolerance:
                            results.append(tx)
                            break
        
        return results
    
    def _get_addresses_by_balance(self, balance: float, tolerance: float = 0.01) -> List[Dict]:
        """Get addresses by balance (within tolerance)"""
        results = []
        
        for address in self.search_index['addresses']:
            addr_info = self.search_index['addresses'][address]
            if abs(addr_info['balance'] - balance) <= tolerance:
                results.append({
                    'address': address,
                    'balance': addr_info['balance'],
                    'tx_count': addr_info['tx_count']
                })
        
        # Sort by balance (highest first)
        results.sort(key=lambda x: x['balance'], reverse=True)
        
        return results
    
    def _keyword_search_blocks(self, query: str) -> List:
        """Keyword search in blocks"""
        query_lower = query.lower()
        results = []
        
        for block in self.blockchain.chain:
            # Search in block hash
            block_hash = block.calculate_hash() if hasattr(block, 'calculate_hash') else block.hash
            if query_lower in block_hash.lower():
                results.append(block)
                continue
            
            # Search in transaction hashes
            for tx in block.transactions:
                tx_hash = tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash
                if query_lower in tx_hash.lower():
                    results.append(block)
                    break
        
        return results
    
    def _keyword_search_transactions(self, query: str) -> List:
        """Keyword search in transactions"""
        query_lower = query.lower()
        results = []
        
        for block in self.blockchain.chain:
            for tx in block.transactions:
                # Search in transaction hash
                tx_hash = tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash
                if query_lower in tx_hash.lower():
                    results.append(tx)
                    continue
                
                # Search in addresses
                for out in tx.outputs:
                    if 'address' in out and query_lower in out['address'].lower():
                        results.append(tx)
                        break
        
        return results
    
    def _keyword_search_addresses(self, query: str) -> List[Dict]:
        """Keyword search in addresses"""
        query_lower = query.lower()
        results = []
        
        for address, info in self.search_index['addresses'].items():
            if query_lower in address.lower():
                results.append({
                    'address': address,
                    'balance': info['balance'],
                    'tx_count': info['tx_count']
                })
        
        return results
    
    def _format_block_result(self, block) -> Dict:
        """Format block for search results"""
        return {
            'type': 'block',
            'hash': block.calculate_hash() if hasattr(block, 'calculate_hash') else block.hash,
            'height': block.index,
            'timestamp': block.timestamp,
            'transactions': len(block.transactions),
            'size': len(str(block)),
            'difficulty': block.difficulty,
            'reward': self._calculate_block_reward(block.index)
        }
    
    def _format_transaction_result(self, tx) -> Dict:
        """Format transaction for search results"""
        return {
            'type': 'transaction',
            'hash': tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash,
            'size': len(str(tx)),
            'inputs': len(tx.inputs),
            'outputs': len(tx.outputs),
            'fee': self._calculate_tx_fee(tx),
            'amount': sum(out.get('amount', 0) for out in tx.outputs)
        }
    
    def _get_address_info(self, address: str) -> Optional[Dict]:
        """Get address information"""
        balance = self.utxo_set.get_balance(address)
        if balance == 0:
            return None
        
        return {
            'type': 'address',
            'address': address,
            'balance': balance,
            'tx_count': self._count_address_transactions(address),
            'utxo_count': len(self._get_address_utxos(address))
        }
    
    def _get_address_utxos(self, address: str) -> List:
        """Get address UTXOs"""
        utxos, _ = self.utxo_set.find_spendable_utxos(address, float('inf'))
        return utxos
    
    def _count_address_transactions(self, address: str) -> int:
        """Count transactions for address"""
        count = 0
        
        for block in self.blockchain.chain:
            for tx in block.transactions:
                # Check if transaction involves this address
                for out in tx.outputs:
                    if 'address' in out and out['address'] == address:
                        count += 1
                        break
        
        return count
    
    def _get_address_first_seen(self, address: str) -> Optional[int]:
        """Get first seen timestamp for address"""
        first_seen = None
        
        for block in self.blockchain.chain:
            for tx in block.transactions:
                for out in tx.outputs:
                    if 'address' in out and out['address'] == address:
                        first_seen = block.timestamp
                        break
            if first_seen:
                break
        
        return first_seen
    
    def _get_address_last_seen(self, address: str) -> Optional[int]:
        """Get last seen timestamp for address"""
        last_seen = None
        
        for block in self.blockchain.chain:
            for tx in block.transactions:
                for out in tx.outputs:
                    if 'address' in out and out['address'] == address:
                        last_seen = block.timestamp
        
        return last_seen
    
    def _calculate_block_reward(self, block_height: int) -> float:
        """Calculate block reward"""
        reward = 50.0
        halving_interval = 210000
        halvings = block_height // halving_interval
        
        for _ in range(halvings):
            reward /= 2
        
        return reward
    
    def _calculate_tx_fee(self, tx) -> float:
        """Calculate transaction fee"""
        total_input = sum(inp.get('amount', 0) for inp in tx.inputs)
        total_output = sum(out.get('amount', 0) for out in tx.outputs)
        return total_input - total_output
    
    def advanced_search(self, criteria: Dict) -> Dict:
        """Advanced search with multiple criteria"""
        results = {
            'blocks': [],
            'transactions': [],
            'addresses': [],
            'criteria': criteria,
            'total_results': 0
        }
        
        # Block search criteria
        if 'blocks' in criteria:
            block_criteria = criteria['blocks']
            blocks = self._advanced_block_search(block_criteria)
            results['blocks'] = [self._format_block_result(block) for block in blocks]
        
        # Transaction search criteria
        if 'transactions' in criteria:
            tx_criteria = criteria['transactions']
            txs = self._advanced_transaction_search(tx_criteria)
            results['transactions'] = [self._format_transaction_result(tx) for tx in txs]
        
        # Address search criteria
        if 'addresses' in criteria:
            addr_criteria = criteria['addresses']
            addresses = self._advanced_address_search(addr_criteria)
            results['addresses'] = addresses
        
        results['total_results'] = (
            len(results['blocks']) + 
            len(results['transactions']) + 
            len(results['addresses'])
        )
        
        return results
    
    def _advanced_block_search(self, criteria: Dict) -> List:
        """Advanced block search"""
        results = []
        
        for block in self.blockchain.chain:
            match = True
            
            # Height range
            if 'height_min' in criteria and block.index < criteria['height_min']:
                match = False
            if 'height_max' in criteria and block.index > criteria['height_max']:
                match = False
            
            # Timestamp range
            if 'timestamp_min' in criteria and block.timestamp < criteria['timestamp_min']:
                match = False
            if 'timestamp_max' in criteria and block.timestamp > criteria['timestamp_max']:
                match = False
            
            # Transaction count range
            if 'tx_count_min' in criteria and len(block.transactions) < criteria['tx_count_min']:
                match = False
            if 'tx_count_max' in criteria and len(block.transactions) > criteria['tx_count_max']:
                match = False
            
            # Difficulty range
            if 'difficulty_min' in criteria and block.difficulty < criteria['difficulty_min']:
                match = False
            if 'difficulty_max' in criteria and block.difficulty > criteria['difficulty_max']:
                match = False
            
            if match:
                results.append(block)
        
        return results
    
    def _advanced_transaction_search(self, criteria: Dict) -> List:
        """Advanced transaction search"""
        results = []
        
        for block in self.blockchain.chain:
            for tx in block.transactions:
                match = True
                
                # Size range
                tx_size = len(str(tx))
                if 'size_min' in criteria and tx_size < criteria['size_min']:
                    match = False
                if 'size_max' in criteria and tx_size > criteria['size_max']:
                    match = False
                
                # Input count range
                if 'inputs_min' in criteria and len(tx.inputs) < criteria['inputs_min']:
                    match = False
                if 'inputs_max' in criteria and len(tx.inputs) > criteria['inputs_max']:
                    match = False
                
                # Output count range
                if 'outputs_min' in criteria and len(tx.outputs) < criteria['outputs_min']:
                    match = False
                if 'outputs_max' in criteria and len(tx.outputs) > criteria['outputs_max']:
                    match = False
                
                # Fee range
                fee = self._calculate_tx_fee(tx)
                if 'fee_min' in criteria and fee < criteria['fee_min']:
                    match = False
                if 'fee_max' in criteria and fee > criteria['fee_max']:
                    match = False
                
                # Amount range
                amount = sum(out.get('amount', 0) for out in tx.outputs)
                if 'amount_min' in criteria and amount < criteria['amount_min']:
                    match = False
                if 'amount_max' in criteria and amount > criteria['amount_max']:
                    match = False
                
                if match:
                    results.append(tx)
        
        return results
    
    def _advanced_address_search(self, criteria: Dict) -> List[Dict]:
        """Advanced address search"""
        results = []
        
        for address, info in self.search_index['addresses'].items():
            match = True
            
            # Balance range
            if 'balance_min' in criteria and info['balance'] < criteria['balance_min']:
                match = False
            if 'balance_max' in criteria and info['balance'] > criteria['balance_max']:
                match = False
            
            # Transaction count range
            if 'tx_count_min' in criteria and info['tx_count'] < criteria['tx_count_min']:
                match = False
            if 'tx_count_max' in criteria and info['tx_count'] > criteria['tx_count_max']:
                match = False
            
            # First seen range
            if 'first_seen_min' in criteria and info['first_seen'] and info['first_seen'] < criteria['first_seen_min']:
                match = False
            if 'first_seen_max' in criteria and info['first_seen'] and info['first_seen'] > criteria['first_seen_max']:
                match = False
            
            if match:
                results.append({
                    'type': 'address',
                    'address': address,
                    'balance': info['balance'],
                    'tx_count': info['tx_count']
                })
        
        return results
    
    def get_search_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """Get search suggestions for query"""
        suggestions = []
        query_lower = query.lower()
        
        # Block hash suggestions
        for block_hash in list(self.search_index['blocks'].keys())[:1000]:
            if query_lower in block_hash.lower():
                suggestions.append(block_hash)
                if len(suggestions) >= limit:
                    break
        
        # Address suggestions
        if len(suggestions) < limit:
            for address in list(self.search_index['addresses'].keys())[:1000]:
                if query_lower in address.lower():
                    suggestions.append(address)
                    if len(suggestions) >= limit:
                        break
        
        return suggestions
    
    def rebuild_index(self):
        """Rebuild search index"""
        self._build_search_index()


def create_search_engine(blockchain: Blockchain, database=None) -> SearchEngine:
    """Create search engine instance"""
    return SearchEngine(blockchain, database)


# Utility functions
def search_blockchain(blockchain: Blockchain, query: str, search_type: str = 'all') -> Dict:
    """Search blockchain"""
    search = create_search_engine(blockchain)
    return search.search(query, search_type)


def advanced_search_blockchain(blockchain: Blockchain, criteria: Dict) -> Dict:
    """Advanced search blockchain"""
    search = create_search_engine(blockchain)
    return search.advanced_search(criteria)
