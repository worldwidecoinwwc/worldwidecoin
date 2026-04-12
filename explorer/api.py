# explorer/api.py
import json
import time
from typing import Dict, List, Optional, Any
from flask import Flask, request, jsonify
from flask_cors import CORS
from core.blockchain import Blockchain
from core.transaction import Transaction
from storage.utxo import UTXOSet


class BlockExplorerAPI:
    """RESTful API for WorldWideCoin Block Explorer"""
    
    def __init__(self, blockchain: Blockchain):
        self.blockchain = blockchain
        self.utxo_set = blockchain.utxo
        
        # Initialize Flask app
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Setup API routes
        self._setup_api_routes()
        
        # API version
        self.api_version = "v1"
    
    def _setup_api_routes(self):
        """Setup API routes"""
        
        # Blockchain endpoints
        @self.app.route(f'/api/{self.api_version}/blockchain/info')
        def blockchain_info():
            """Get blockchain information"""
            return jsonify(self._get_blockchain_info())
        
        @self.app.route(f'/api/{self.api_version}/blockchain/stats')
        def blockchain_stats():
            """Get blockchain statistics"""
            return jsonify(self._get_blockchain_stats())
        
        # Block endpoints
        @self.app.route(f'/api/{self.api_version}/blocks')
        def blocks():
            """Get blocks with pagination"""
            page = int(request.args.get('page', 1))
            limit = int(request.args.get('limit', 20))
            sort = request.args.get('sort', 'desc')
            
            return jsonify(self._get_blocks(page, limit, sort))
        
        @self.app.route(f'/api/{self.api_version}/block/<block_hash>')
        def block_detail(block_hash):
            """Get block details"""
            block = self._get_block_by_hash(block_hash)
            if not block:
                return jsonify({'error': 'Block not found'}), 404
            
            return jsonify(self._format_block(block))
        
        @self.app.route(f'/api/{self.api_version}/block/<block_hash>/raw')
        def block_raw(block_hash):
            """Get raw block data"""
            block = self._get_block_by_hash(block_hash)
            if not block:
                return jsonify({'error': 'Block not found'}), 404
            
            return jsonify(self._get_raw_block(block))
        
        @self.app.route(f'/api/{self.api_version}/block/latest')
        def latest_block():
            """Get latest block"""
            if not self.blockchain.chain:
                return jsonify({'error': 'No blocks found'}), 404
            
            latest = self.blockchain.chain[-1]
            return jsonify(self._format_block(latest))
        
        # Transaction endpoints
        @self.app.route(f'/api/{self.api_version}/transaction/<tx_hash>')
        def transaction_detail(tx_hash):
            """Get transaction details"""
            tx = self._get_transaction_by_hash(tx_hash)
            if not tx:
                return jsonify({'error': 'Transaction not found'}), 404
            
            return jsonify(self._format_transaction(tx))
        
        @self.app.route(f'/api/{self.api_version}/transaction/<tx_hash>/raw')
        def transaction_raw(tx_hash):
            """Get raw transaction data"""
            tx = self._get_transaction_by_hash(tx_hash)
            if not tx:
                return jsonify({'error': 'Transaction not found'}), 404
            
            return jsonify(self._get_raw_transaction(tx))
        
        @self.app.route(f'/api/{self.api_version}/transaction/<tx_hash>/confirmations')
        def transaction_confirmations(tx_hash):
            """Get transaction confirmations"""
            confirmations = self._get_transaction_confirmations(tx_hash)
            if confirmations == -1:
                return jsonify({'error': 'Transaction not found'}), 404
            
            return jsonify({'confirmations': confirmations})
        
        # Address endpoints
        @self.app.route(f'/api/{self.api_version}/address/<address>')
        def address_detail(address):
            """Get address details"""
            address_info = self._get_address_info(address)
            return jsonify(address_info)
        
        @self.app.route(f'/api/{self.api_version}/address/<address>/balance')
        def address_balance(address):
            """Get address balance"""
            balance = self.utxo_set.get_balance(address)
            return jsonify({'address': address, 'balance': balance})
        
        @self.app.route(f'/api/{self.api_version}/address/<address>/utxos')
        def address_utxos(address):
            """Get address UTXOs"""
            utxos = self._get_address_utxos(address)
            return jsonify({'address': address, 'utxos': utxos})
        
        @self.app.route(f'/api/{self.api_version}/address/<address>/transactions')
        def address_transactions(address):
            """Get address transaction history"""
            page = int(request.args.get('page', 1))
            limit = int(request.args.get('limit', 50))
            
            history = self._get_address_transaction_history(address, page, limit)
            return jsonify({
                'address': address,
                'transactions': history['transactions'],
                'page': history['page'],
                'limit': history['limit'],
                'total': history['total']
            })
        
        # Mempool endpoints
        @self.app.route(f'/api/{self.api_version}/mempool')
        def mempool_info():
            """Get mempool information"""
            return jsonify(self._get_mempool_info())
        
        @self.app.route(f'/api/{self.api_version}/mempool/transactions')
        def mempool_transactions():
            """Get mempool transactions"""
            limit = int(request.args.get('limit', 100))
            return jsonify(self._get_mempool_transactions(limit))
        
        # Search endpoints
        @self.app.route(f'/api/{self.api_version}/search')
        def search():
            """Search blockchain"""
            query = request.args.get('q', '')
            type_filter = request.args.get('type', 'all')  # all, block, tx, address
            limit = int(request.args.get('limit', 20))
            
            results = self._search(query, type_filter, limit)
            return jsonify(results)
        
        # Utility endpoints
        @self.app.route(f'/api/{self.api_version}/utils/estimate-fee')
        def estimate_fee():
            """Estimate transaction fee"""
            tx_size = int(request.args.get('size', 250))
            priority = request.args.get('priority', 'medium')
            
            fee = self._estimate_fee(tx_size, priority)
            return jsonify({'fee': fee, 'size': tx_size, 'priority': priority})
        
        @self.app.route(f'/api/{self.api_version}/utils/validate-address')
        def validate_address():
            """Validate address format"""
            address = request.args.get('address', '')
            is_valid = self._validate_address(address)
            return jsonify({'address': address, 'valid': is_valid})
        
        @self.app.route(f'/api/{self.api_version}/health')
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': time.time(),
                'blockchain_height': len(self.blockchain.chain),
                'api_version': self.api_version
            })
    
    def _get_blockchain_info(self) -> Dict:
        """Get blockchain information"""
        return {
            'chain': 'WorldWideCoin',
            'blocks': len(self.blockchain.chain),
            'best_block_hash': self.blockchain.chain[-1].calculate_hash() if self.blockchain.chain else None,
            'difficulty': self.blockchain.get_difficulty() if hasattr(self.blockchain, 'get_difficulty') else 1,
            'mempool_size': len(self.blockchain.mempool.transactions),
            'version': '1.0.0',
            'protocol_version': '1.0.0'
        }
    
    def _get_blockchain_stats(self) -> Dict:
        """Get blockchain statistics"""
        if not self.blockchain.chain:
            return {'error': 'No blocks available'}
        
        total_txs = sum(len(block.transactions) for block in self.blockchain.chain)
        total_supply = sum(self._calculate_block_reward(block.index) for block in self.blockchain.chain)
        
        # Calculate average block time
        avg_block_time = 0
        if len(self.blockchain.chain) > 1:
            times = []
            for i in range(1, len(self.blockchain.chain)):
                times.append(self.blockchain.chain[i].timestamp - self.blockchain.chain[i-1].timestamp)
            avg_block_time = sum(times) / len(times)
        
        return {
            'blocks': len(self.blockchain.chain),
            'transactions': total_txs,
            'total_supply': total_supply,
            'difficulty': self.blockchain.get_difficulty() if hasattr(self.blockchain, 'get_difficulty') else 1,
            'hash_rate': self._estimate_hash_rate(),
            'avg_block_time': avg_block_time,
            'block_size_avg': sum(len(str(block)) for block in self.blockchain.chain) / len(self.blockchain.chain),
            'utxo_set_size': len(self.utxo_set.get_all_utxos()),
            'timestamp': time.time()
        }
    
    def _get_blocks(self, page: int, limit: int, sort: str) -> Dict:
        """Get paginated blocks"""
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        
        blocks = self.blockchain.chain
        if sort == 'desc':
            blocks = blocks[::-1]
        
        paginated_blocks = blocks[start_idx:end_idx]
        
        return {
            'blocks': [self._format_block_summary(block) for block in paginated_blocks],
            'page': page,
            'limit': limit,
            'total': len(self.blockchain.chain),
            'pages': (len(self.blockchain.chain) + limit - 1) // limit
        }
    
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
    
    def _format_block(self, block) -> Dict:
        """Format block for API response"""
        return {
            'hash': block.calculate_hash() if hasattr(block, 'calculate_hash') else block.hash,
            'height': block.index,
            'timestamp': block.timestamp,
            'size': len(str(block)),
            'version': 1,
            'merkle_root': getattr(block, 'merkle_root', ''),
            'nonce': block.nonce,
            'bits': block.difficulty,
            'difficulty': block.difficulty,
            'previousblockhash': block.prev_hash,
            'nextblockhash': self._get_next_block_hash(block.index),
            'tx': [tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash() for tx in block.transactions],
            'time': int(block.timestamp),
            'mediantime': int(block.timestamp),
            'chainwork': self._calculate_chainwork(block.difficulty),
            'nTx': len(block.transactions),
            'fees': self._calculate_block_fees(block),
            'reward': self._calculate_block_reward(block.index)
        }
    
    def _format_block_summary(self, block) -> Dict:
        """Format block summary for listing"""
        return {
            'hash': block.calculate_hash() if hasattr(block, 'calculate_hash') else block.hash,
            'height': block.index,
            'timestamp': block.timestamp,
            'size': len(str(block)),
            'tx_count': len(block.transactions),
            'difficulty': block.difficulty
        }
    
    def _format_transaction(self, tx) -> Dict:
        """Format transaction for API response"""
        return {
            'txid': tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash(),
            'version': 1,
            'size': len(str(tx)),
            'locktime': getattr(tx, 'locktime', 0),
            'vin': self._format_inputs(tx.inputs),
            'vout': self._format_outputs(tx.outputs),
            'blockhash': self._get_transaction_block_hash(tx),
            'confirmations': self._get_transaction_confirmations(tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash()),
            'time': int(time.time()),  # Would come from block
            'blocktime': int(time.time()),
            'fee': getattr(tx, 'get_fee', lambda: 0)(),
            'value': self._calculate_transaction_value(tx)
        }
    
    def _format_inputs(self, inputs: List) -> List[Dict]:
        """Format transaction inputs"""
        formatted_inputs = []
        for inp in inputs:
            formatted_input = {
                'coinbase': False,
                'txid': inp.get('txid', ''),
                'vout': inp.get('vout', 0),
                'scriptSig': {
                    'asm': inp.get('script_sig', ''),
                    'hex': inp.get('script_sig', '')
                },
                'sequence': 4294967295  # Default sequence
            }
            formatted_inputs.append(formatted_input)
        return formatted_inputs
    
    def _format_outputs(self, outputs: List) -> List[Dict]:
        """Format transaction outputs"""
        formatted_outputs = []
        for i, out in enumerate(outputs):
            formatted_output = {
                'value': int(out.get('amount', 0) * 100000000),  # Convert to satoshis
                'n': i,
                'scriptPubKey': {
                    'asm': out.get('script_pubkey', ''),
                    'hex': out.get('script_pubkey', ''),
                    'reqSigs': 1,
                    'type': 'pubkeyhash',
                    'addresses': [out.get('address', '')]
                }
            }
            formatted_outputs.append(formatted_output)
        return formatted_outputs
    
    def _get_address_info(self, address: str) -> Dict:
        """Get address information"""
        balance = self.utxo_set.get_balance(address)
        utxos, _ = self.utxo_set.find_spendable_utxos(address, balance)
        
        return {
            'address': address,
            'balance': balance,
            'balance_sat': int(balance * 100000000),
            'txCount': len(self._get_address_transaction_history(address)),
            'unconfirmedTxCount': 0,  # Would need mempool checking
            'txs': self._get_address_transaction_history(address)[:50]
        }
    
    def _get_address_transaction_history(self, address: str, page: int = 1, limit: int = 50) -> Dict:
        """Get paginated address transaction history"""
        history = []
        
        for block in self.blockchain.chain:
            for tx in block.transactions:
                tx_hash = tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash()
                
                # Check if transaction involves this address
                involves_address = False
                
                # Check inputs
                for inp in tx.inputs:
                    if 'address' in inp and inp['address'] == address:
                        involves_address = True
                        break
                
                # Check outputs
                if not involves_address:
                    for out in tx.outputs:
                        if 'address' in out and out['address'] == address:
                            involves_address = True
                            break
                
                if involves_address:
                    history.append({
                        'txid': tx_hash,
                        'blockheight': block.index,
                        'time': int(block.timestamp),
                        'value': self._calculate_transaction_value(tx),
                        'size': len(str(tx))
                    })
        
        # Sort by time (newest first)
        history.sort(key=lambda x: x['time'], reverse=True)
        
        # Paginate
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_history = history[start_idx:end_idx]
        
        return {
            'transactions': paginated_history,
            'page': page,
            'limit': limit,
            'total': len(history),
            'pages': (len(history) + limit - 1) // limit
        }
    
    def _get_address_utxos(self, address: str) -> List[Dict]:
        """Get address UTXOs"""
        utxos, _ = self.utxo_set.find_spendable_utxos(address, float('inf'))
        formatted_utxos = []
        
        for utxo_key in utxos:
            utxo = self.utxo_set.get_utxo(utxo_key)
            if utxo:
                formatted_utxos.append({
                    'txid': utxo['txid'],
                    'vout': utxo['vout'],
                    'amount': utxo['amount'],
                    'script': utxo.get('script_pubkey', ''),
                    'confirmations': self._get_confirmations(utxo['txid'])
                })
        
        return formatted_utxos
    
    def _get_mempool_info(self) -> Dict:
        """Get mempool information"""
        mempool = self.blockchain.mempool
        
        total_size = 0
        total_fees = 0
        
        for tx in mempool.transactions:
            total_size += len(str(tx))
            if hasattr(tx, 'get_fee'):
                total_fees += tx.get_fee()
        
        return {
            'size': len(mempool.transactions),
            'bytes': total_size,
            'usage': total_size / 1000000,  # Percentage of 1MB limit
            'maxmempool': 1000000,
            'totalfee': total_fees,
            'tx': [tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash() for tx in mempool.transactions[:1000]]
        }
    
    def _get_mempool_transactions(self, limit: int = 100) -> Dict:
        """Get mempool transactions"""
        mempool = self.blockchain.mempool
        transactions = []
        
        for tx in mempool.transactions[:limit]:
            transactions.append({
                'txid': tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash(),
                'size': len(str(tx)),
                'fee': getattr(tx, 'get_fee', lambda: 0)(),
                'time': time.time()
            })
        
        return {
            'transactions': transactions,
            'size': len(transactions),
            'limit': limit
        }
    
    def _search(self, query: str, type_filter: str, limit: int) -> Dict:
        """Search blockchain"""
        results = {
            'blocks': [],
            'transactions': [],
            'addresses': []
        }
        
        if type_filter in ['all', 'block'] and len(query) == 64:
            block = self._get_block_by_hash(query)
            if block:
                results['blocks'].append(self._format_block_summary(block))
        
        if type_filter in ['all', 'tx'] and len(query) == 64:
            tx = self._get_transaction_by_hash(query)
            if tx:
                results['transactions'].append({
                    'txid': tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash(),
                    'size': len(str(tx)),
                    'time': time.time()
                })
        
        if type_filter in ['all', 'address'] and len(query) >= 26:
            balance = self.utxo_set.get_balance(query)
            if balance > 0 or self._has_address_transactions(query):
                results['addresses'].append({
                    'address': query,
                    'balance': balance,
                    'txCount': len(self._get_address_transaction_history(query))
                })
        
        # Limit results
        for key in results:
            results[key] = results[key][:limit]
        
        return results
    
    def _estimate_fee(self, tx_size: int, priority: str) -> Dict:
        """Estimate transaction fee"""
        # Simple fee estimation
        fee_rates = {
            'low': 0.00001,
            'medium': 0.0001,
            'high': 0.001
        }
        
        fee_rate = fee_rates.get(priority, fee_rates['medium'])
        fee = tx_size * fee_rate
        
        return {
            'fee': fee,
            'size': tx_size,
            'priority': priority,
            'fee_rate': fee_rate
        }
    
    def _validate_address(self, address: str) -> bool:
        """Validate address format"""
        # Simple validation - check length and characters
        if len(address) < 26 or len(address) > 35:
            return False
        
        valid_chars = set('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz')
        return all(c in valid_chars for c in address)
    
    def _get_next_block_hash(self, block_index: int) -> Optional[str]:
        """Get next block hash"""
        if block_index + 1 < len(self.blockchain.chain):
            next_block = self.blockchain.chain[block_index + 1]
            return next_block.calculate_hash() if hasattr(next_block, 'calculate_hash') else next_block.hash
        return None
    
    def _get_transaction_block_hash(self, tx) -> Optional[str]:
        """Get block hash containing transaction"""
        for block in self.blockchain.chain:
            if tx in block.transactions:
                return block.calculate_hash() if hasattr(block, 'calculate_hash') else block.hash
        return None
    
    def _get_transaction_confirmations(self, tx_hash: str) -> int:
        """Get transaction confirmations"""
        if not self.blockchain.chain:
            return -1
        
        current_height = len(self.blockchain.chain)
        
        for block in self.blockchain.chain:
            for tx in block.transactions:
                current_tx_hash = tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash()
                if current_tx_hash == tx_hash:
                    return current_height - block.index
        
        return -1
    
    def _get_confirmations(self, txid: str) -> int:
        """Get confirmations for transaction ID"""
        return self._get_transaction_confirmations(txid)
    
    def _calculate_chainwork(self, difficulty: int) -> str:
        """Calculate chain work"""
        return str(difficulty * (2 ** 32))
    
    def _calculate_block_fees(self, block) -> float:
        """Calculate total fees in block"""
        total_fees = 0
        for tx in block.transactions:
            if hasattr(tx, 'get_fee'):
                total_fees += tx.get_fee()
        return total_fees
    
    def _calculate_block_reward(self, block_height: int) -> float:
        """Calculate block reward"""
        reward = 50.0
        halving_interval = 210000
        halvings = block_height // halving_interval
        
        for _ in range(halvings):
            reward /= 2
        
        return reward
    
    def _estimate_hash_rate(self) -> float:
        """Estimate network hash rate"""
        if not self.blockchain.chain:
            return 0.0
        
        latest_block = self.blockchain.chain[-1]
        difficulty = latest_block.difficulty
        
        target_time = 600  # 10 minutes
        return difficulty * (2 ** 32) / target_time
    
    def _calculate_transaction_value(self, tx) -> float:
        """Calculate total transaction value"""
        return sum(out.get('amount', 0) for out in tx.outputs)
    
    def _get_raw_block(self, block) -> Dict:
        """Get raw block data"""
        return {
            'hash': block.calculate_hash() if hasattr(block, 'calculate_hash') else block.hash,
            'data': str(block),
            'hex': str(block).encode().hex()
        }
    
    def _get_raw_transaction(self, tx) -> Dict:
        """Get raw transaction data"""
        return {
            'txid': tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash(),
            'data': str(tx),
            'hex': str(tx).encode().hex()
        }
    
    def _has_address_transactions(self, address: str) -> bool:
        """Check if address has transactions"""
        return len(self._get_address_transaction_history(address)) > 0
    
    def create_app(self) -> Flask:
        """Create Flask app"""
        return self.app


def create_explorer_api(blockchain: Blockchain) -> BlockExplorerAPI:
    """Create block explorer API instance"""
    return BlockExplorerAPI(blockchain)


if __name__ == "__main__":
    # Create blockchain and API
    blockchain = Blockchain()
    api = create_explorer_api(blockchain)
    
    # Run API server
    app = api.create_app()
    app.run(host="0.0.0.0", port=5001, debug=True)
