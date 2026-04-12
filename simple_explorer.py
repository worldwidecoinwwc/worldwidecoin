#!/usr/bin/env python3
"""
Simple WorldWideCoin Block Explorer
Minimal version to avoid Flask template errors
"""

import json
import time
from flask import Flask, jsonify, request
from flask_cors import CORS
from core.blockchain import Blockchain


class SimpleBlockExplorer:
    """Simple block explorer without templates"""
    
    def __init__(self, blockchain):
        self.blockchain = blockchain
        self.app = Flask(__name__)
        CORS(self.app)
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup basic routes"""
        
        @self.app.route('/')
        def home():
            """Home page with basic info"""
            try:
                info = {
                    'name': 'WorldWideCoin Block Explorer',
                    'status': 'running',
                    'blocks': len(self.blockchain.chain),
                    'timestamp': time.time(),
                    'endpoints': [
                        '/',
                        '/blocks',
                        '/stats',
                        '/api/v1/blockchain/info',
                        '/api/v1/blocks'
                    ]
                }
                return jsonify(info)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/blocks')
        def blocks():
            """Blocks listing"""
            try:
                blocks = []
                for block in self.blockchain.chain[-10:]:  # Last 10 blocks
                    blocks.append({
                        'hash': block.calculate_hash() if hasattr(block, 'calculate_hash') else block.hash,
                        'height': block.index,
                        'timestamp': block.timestamp,
                        'transactions': len(block.transactions),
                        'difficulty': block.difficulty
                    })
                
                return jsonify({
                    'blocks': blocks,
                    'total': len(self.blockchain.chain)
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/stats')
        def stats():
            """Network statistics"""
            try:
                stats = {
                    'height': len(self.blockchain.chain),
                    'total_supply': sum(50.0 for _ in self.blockchain.chain),  # Simplified
                    'difficulty': self.blockchain.get_difficulty() if hasattr(self.blockchain, 'get_difficulty') else 1,
                    'mempool_size': len(self.blockchain.mempool.transactions),
                    'timestamp': time.time()
                }
                return jsonify(stats)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/v1/blockchain/info')
        def api_info():
            """API blockchain info"""
            try:
                return jsonify({
                    'chain': 'WorldWideCoin',
                    'blocks': len(self.blockchain.chain),
                    'difficulty': self.blockchain.get_difficulty() if hasattr(self.blockchain, 'get_difficulty') else 1,
                    'mempool_size': len(self.blockchain.mempool.transactions),
                    'version': '1.0.0'
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/v1/blocks')
        def api_blocks():
            """API blocks endpoint"""
            try:
                page = int(request.args.get('page', 1))
                limit = int(request.args.get('limit', 20))
                
                start_idx = (page - 1) * limit
                end_idx = start_idx + limit
                
                blocks = []
                for block in self.blockchain.chain[start_idx:end_idx]:
                    blocks.append({
                        'hash': block.calculate_hash() if hasattr(block, 'calculate_hash') else block.hash,
                        'height': block.index,
                        'timestamp': block.timestamp,
                        'transactions': len(block.transactions),
                        'size': len(str(block)),
                        'difficulty': block.difficulty
                    })
                
                return jsonify({
                    'blocks': blocks,
                    'page': page,
                    'limit': limit,
                    'total': len(self.blockchain.chain)
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/block/<block_hash>')
        def block_detail(block_hash):
            """Block details"""
            try:
                for block in self.blockchain.chain:
                    block_hash_current = block.calculate_hash() if hasattr(block, 'calculate_hash') else block.hash
                    if block_hash_current == block_hash:
                        return jsonify({
                            'hash': block_hash_current,
                            'height': block.index,
                            'timestamp': block.timestamp,
                            'transactions': len(block.transactions),
                            'difficulty': block.difficulty,
                            'nonce': block.nonce,
                            'prev_hash': block.prev_hash,
                            'tx_hashes': [tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash() for tx in block.transactions]
                        })
                
                return jsonify({'error': 'Block not found'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/tx/<tx_hash>')
        def transaction_detail(tx_hash):
            """Transaction details"""
            try:
                for block in self.blockchain.chain:
                    for tx in block.transactions:
                        current_tx_hash = tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash
                        if current_tx_hash == tx_hash:
                            return jsonify({
                                'hash': current_tx_hash,
                                'block_height': block.index,
                                'timestamp': block.timestamp,
                                'inputs': len(tx.inputs),
                                'outputs': len(tx.outputs),
                                'size': len(str(tx)),
                                'inputs_detail': tx.inputs,
                                'outputs_detail': tx.outputs
                            })
                
                return jsonify({'error': 'Transaction not found'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/address/<address>')
        def address_detail(address):
            """Address details"""
            try:
                balance = self.blockchain.utxo.get_balance(address)
                return jsonify({
                    'address': address,
                    'balance': balance,
                    'transaction_count': 0  # Simplified
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/search')
        def search():
            """Search functionality"""
            try:
                query = request.args.get('q', '')
                results = {
                    'blocks': [],
                    'transactions': [],
                    'addresses': []
                }
                
                # Search blocks
                if len(query) == 64:  # Hash length
                    for block in self.blockchain.chain:
                        block_hash = block.calculate_hash() if hasattr(block, 'calculate_hash') else block.hash
                        if query in block_hash:
                            results['blocks'].append({
                                'hash': block_hash,
                                'height': block.index,
                                'timestamp': block.timestamp
                            })
                
                # Search transactions
                for block in self.blockchain.chain:
                    for tx in block.transactions:
                        tx_hash = tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash
                        if query in tx_hash:
                            results['transactions'].append({
                                'hash': tx_hash,
                                'block_height': block.index,
                                'timestamp': block.timestamp
                            })
                
                return jsonify(results)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({'error': 'Not found'}), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({'error': 'Internal server error'}), 500
    
    def run(self, host='127.0.0.1', port=5000, debug=False):
        """Run the simple explorer"""
        print(f"Starting Simple WorldWideCoin Explorer on http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)


def main():
    """Main function to start simple explorer"""
    print("WorldWideCoin Simple Block Explorer")
    print("=" * 50)
    
    try:
        # Create blockchain
        print("Initializing blockchain...")
        blockchain = Blockchain()
        
        # Mine some blocks if needed
        if len(blockchain.chain) < 3:
            print("Mining initial blocks...")
            for i in range(3):
                block = blockchain.create_block(f"initial_miner_{i}")
                blockchain.add_block(block)
        
        print(f"Blockchain ready: {len(blockchain.chain)} blocks")
        
        # Create and run simple explorer
        explorer = SimpleBlockExplorer(blockchain)
        
        print("\nSimple Explorer is running!")
        print("Open your browser and go to: http://127.0.0.1:5000")
        print("\nAvailable endpoints:")
        print("  http://127.0.0.1:5000/ - Home")
        print("  http://127.0.0.1:5000/blocks - Blocks list")
        print("  http://127.0.0.1:5000/stats - Network stats")
        print("  http://127.0.0.1:5000/search?q=<hash> - Search")
        print("\nAPI endpoints:")
        print("  http://127.0.0.1:5000/api/v1/blockchain/info")
        print("  http://127.0.0.1:5000/api/v1/blocks")
        print("\nPress Ctrl+C to stop")
        
        explorer.run(debug=False)
        
    except KeyboardInterrupt:
        print("\nStopping explorer...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
