# explorer/block_explorer.py
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from core.blockchain import Blockchain
from core.transaction import Transaction
from storage.utxo import UTXOSet


class BlockExplorer:
    """WorldWideCoin Block Explorer Web Application"""
    
    def __init__(self, blockchain: Blockchain, host: str = "0.0.0.0", port: int = 5000):
        self.blockchain = blockchain
        self.utxo_set = blockchain.utxo
        self.host = host
        self.port = port
        
        # Initialize Flask app
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Setup routes
        self._setup_routes()
        
        # Cache for performance
        self.cache = {}
        self.cache_timeout = 30  # seconds
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main page"""
            return render_template('index.html')
        
        @self.app.route('/blocks')
        def blocks_page():
            """Blocks listing page"""
            return render_template('blocks.html')
        
        @self.app.route('/block/<block_hash>')
        def block_page(block_hash):
            """Block details page"""
            return render_template('block.html', block_hash=block_hash)
        
        @self.app.route('/tx/<tx_hash>')
        def transaction_page(tx_hash):
            """Transaction details page"""
            return render_template('transaction.html', tx_hash=tx_hash)
        
        @self.app.route('/address/<address>')
        def address_page(address):
            """Address details page"""
            return render_template('address.html', address=address)
        
        @self.app.route('/search')
        def search_page():
            """Search results page"""
            query = request.args.get('q', '')
            return render_template('search.html', query=query)
        
        @self.app.route('/stats')
        def stats_page():
            """Statistics page"""
            return render_template('stats.html')
        
        # API Routes
        @self.app.route('/api/blocks')
        def api_blocks():
            """Get blocks API"""
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 20))
            
            blocks = self._get_blocks_paginated(page, per_page)
            return jsonify({
                'blocks': blocks,
                'page': page,
                'per_page': per_page,
                'total': len(self.blockchain.chain)
            })
        
        @self.app.route('/api/block/<block_hash>')
        def api_block(block_hash):
            """Get block details API"""
            block = self._get_block_by_hash(block_hash)
            if not block:
                return jsonify({'error': 'Block not found'}), 404
            
            return jsonify(self._format_block(block))
        
        @self.app.route('/api/tx/<tx_hash>')
        def api_transaction(tx_hash):
            """Get transaction details API"""
            tx = self._get_transaction_by_hash(tx_hash)
            if not tx:
                return jsonify({'error': 'Transaction not found'}), 404
            
            return jsonify(self._format_transaction(tx))
        
        @self.app.route('/api/address/<address>')
        def api_address(address):
            """Get address details API"""
            address_info = self._get_address_info(address)
            return jsonify(address_info)
        
        @self.app.route('/api/search')
        def api_search():
            """Search API"""
            query = request.args.get('q', '')
            results = self._search(query)
            return jsonify(results)
        
        @self.app.route('/api/stats')
        def api_stats():
            """Get network statistics API"""
            stats = self._get_network_stats()
            return jsonify(stats)
        
        @self.app.route('/api/mempool')
        def api_mempool():
            """Get mempool information API"""
            mempool_info = self._get_mempool_info()
            return jsonify(mempool_info)
        
        @self.app.route('/api/utxo/<address>')
        def api_utxo(address):
            """Get UTXOs for address API"""
            utxos = self._get_address_utxos(address)
            return jsonify(utxos)
    
    def _get_blocks_paginated(self, page: int, per_page: int) -> List[Dict]:
        """Get paginated blocks"""
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        blocks = self.blockchain.chain[start_idx:end_idx]
        return [self._format_block_summary(block) for block in blocks]
    
    def _get_block_by_hash(self, block_hash: str) -> Optional:
        """Get block by hash"""
        for block in self.blockchain.chain:
            if hasattr(block, 'hash') and block.hash == block_hash:
                return block
            elif hasattr(block, 'calculate_hash'):
                if block.calculate_hash() == block_hash:
                    return block
        return None
    
    def _get_transaction_by_hash(self, tx_hash: str) -> Optional:
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
            'transactions': len(block.transactions),
            'difficulty': block.difficulty,
            'nonce': block.nonce,
            'prev_hash': block.prev_hash,
            'merkle_root': getattr(block, 'merkle_root', ''),
            'reward': self._calculate_block_reward(block.index),
            'fees': self._calculate_block_fees(block),
            'tx_hashes': [tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash() for tx in block.transactions]
        }
    
    def _format_block_summary(self, block) -> Dict:
        """Format block summary for listing"""
        return {
            'hash': block.calculate_hash() if hasattr(block, 'calculate_hash') else block.hash,
            'height': block.index,
            'timestamp': block.timestamp,
            'transactions': len(block.transactions),
            'size': len(str(block))
        }
    
    def _format_transaction(self, tx) -> Dict:
        """Format transaction for API response"""
        return {
            'hash': tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash(),
            'size': len(str(tx)),
            'inputs': len(tx.inputs),
            'outputs': len(tx.outputs),
            'fee': getattr(tx, 'get_fee', lambda: 0)(),
            'timestamp': time.time(),  # Would come from block timestamp
            'inputs_detail': tx.inputs,
            'outputs_detail': tx.outputs
        }
    
    def _get_address_info(self, address: str) -> Dict:
        """Get address information"""
        balance = self.utxo_set.get_balance(address)
        utxos, _ = self.utxo_set.find_spendable_utxos(address, balance)
        
        # Get transaction history
        tx_history = self._get_address_transaction_history(address)
        
        return {
            'address': address,
            'balance': balance,
            'utxo_count': len(utxos),
            'transaction_count': len(tx_history),
            'transactions': tx_history[:50],  # Limit to 50 recent transactions
            'utxos': [self._format_utxo(utxo_key, self.utxo_set.get_utxo(utxo_key)) for utxo_key in utxos]
        }
    
    def _format_utxo(self, utxo_key: str, utxo: Dict) -> Dict:
        """Format UTXO for API response"""
        return {
            'txid': utxo['txid'],
            'vout': utxo['vout'],
            'amount': utxo['amount'],
            'script': utxo.get('script_pubkey', ''),
            'confirmations': self._get_confirmations(utxo['txid'])
        }
    
    def _get_address_transaction_history(self, address: str) -> List[Dict]:
        """Get transaction history for address"""
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
                        'tx_hash': tx_hash,
                        'block_height': block.index,
                        'timestamp': block.timestamp,
                        'inputs': len(tx.inputs),
                        'outputs': len(tx.outputs)
                    })
        
        return sorted(history, key=lambda x: x['timestamp'], reverse=True)
    
    def _search(self, query: str) -> Dict:
        """Search for blocks, transactions, or addresses"""
        results = {
            'blocks': [],
            'transactions': [],
            'addresses': []
        }
        
        # Search blocks
        if len(query) == 64:  # Hash length
            block = self._get_block_by_hash(query)
            if block:
                results['blocks'].append(self._format_block_summary(block))
        
        # Search transactions
        tx = self._get_transaction_by_hash(query)
        if tx:
            results['transactions'].append(self._format_transaction(tx))
        
        # Search addresses
        if len(query) >= 26:  # Minimum address length
            balance = self.utxo_set.get_balance(query)
            if balance > 0 or self._has_address_transactions(query):
                results['addresses'].append({
                    'address': query,
                    'balance': balance,
                    'transaction_count': len(self._get_address_transaction_history(query))
                })
        
        return results
    
    def _has_address_transactions(self, address: str) -> bool:
        """Check if address has any transactions"""
        return len(self._get_address_transaction_history(address)) > 0
    
    def _get_network_stats(self) -> Dict:
        """Get network statistics"""
        current_height = len(self.blockchain.chain)
        
        # Calculate total supply
        total_supply = 0
        for block in self.blockchain.chain:
            total_supply += self._calculate_block_reward(block.index)
        
        # Get block time stats
        if len(self.blockchain.chain) > 1:
            latest_block = self.blockchain.chain[-1]
            prev_block = self.blockchain.chain[-2]
            avg_block_time = latest_block.timestamp - prev_block.timestamp
        else:
            avg_block_time = 0
        
        return {
            'block_height': current_height,
            'total_supply': total_supply,
            'difficulty': self.blockchain.get_difficulty() if hasattr(self.blockchain, 'get_difficulty') else 1,
            'hash_rate': self._estimate_hash_rate(),
            'avg_block_time': avg_block_time,
            'total_transactions': sum(len(block.transactions) for block in self.blockchain.chain),
            'mempool_size': len(self.blockchain.mempool.transactions),
            'utxo_count': len(self.utxo_set.get_all_utxos()),
            'timestamp': time.time()
        }
    
    def _get_mempool_info(self) -> Dict:
        """Get mempool information"""
        mempool = self.blockchain.mempool
        
        # Calculate mempool stats
        total_size = 0
        total_fees = 0
        
        for tx in mempool.transactions:
            total_size += len(str(tx))
            if hasattr(tx, 'get_fee'):
                total_fees += tx.get_fee()
        
        return {
            'size': len(mempool.transactions),
            'bytes': total_size,
            'total_fees': total_fees,
            'transactions': [self._format_transaction(tx) for tx in mempool.transactions[:100]]  # Limit to 100
        }
    
    def _get_address_utxos(self, address: str) -> List[Dict]:
        """Get UTXOs for address"""
        utxos, _ = self.utxo_set.find_spendable_utxos(address, float('inf'))
        return [self._format_utxo(utxo_key, self.utxo_set.get_utxo(utxo_key)) for utxo_key in utxos]
    
    def _calculate_block_reward(self, block_height: int) -> float:
        """Calculate block reward for given height"""
        # Simple reward calculation
        reward = 50.0
        halving_interval = 210000
        halvings = block_height // halving_interval
        
        for _ in range(halvings):
            reward /= 2
        
        return reward
    
    def _calculate_block_fees(self, block) -> float:
        """Calculate total fees in block"""
        total_fees = 0
        for tx in block.transactions:
            if hasattr(tx, 'get_fee'):
                total_fees += tx.get_fee()
        return total_fees
    
    def _estimate_hash_rate(self) -> float:
        """Estimate network hash rate"""
        if len(self.blockchain.chain) < 2:
            return 0.0
        
        # Simple hash rate estimation based on difficulty
        latest_block = self.blockchain.chain[-1]
        difficulty = latest_block.difficulty
        
        # Rough estimation: hash_rate = difficulty * 2^32 / target_time
        target_time = 600  # 10 minutes
        hash_rate = difficulty * (2 ** 32) / target_time
        
        return hash_rate
    
    def _get_confirmations(self, txid: str) -> int:
        """Get number of confirmations for transaction"""
        current_height = len(self.blockchain.chain)
        
        for block in self.blockchain.chain:
            for tx in block.transactions:
                tx_hash = tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash()
                if tx_hash == txid:
                    return current_height - block.index
        
        return 0
    
    def run(self, debug: bool = False):
        """Run the block explorer"""
        print(f"Starting WorldWideCoin Block Explorer on http://{self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=debug)


def create_block_explorer(blockchain: Blockchain, host: str = "0.0.0.0", port: int = 5000) -> BlockExplorer:
    """Create a block explorer instance"""
    return BlockExplorer(blockchain, host, port)


if __name__ == "__main__":
    # Create blockchain and start explorer
    blockchain = Blockchain()
    explorer = create_block_explorer(blockchain)
    explorer.run(debug=True)
