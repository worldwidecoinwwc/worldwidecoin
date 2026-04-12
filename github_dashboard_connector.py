#!/usr/bin/env python3
"""
GitHub Dashboard Connector
Connect local WorldWideCoin blockchain to GitHub Pages dashboard
"""

import json
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from core.blockchain import Blockchain


class GitHubDashboardConnector:
    """Connector to serve blockchain data for GitHub Pages dashboard"""
    
    def __init__(self, blockchain):
        self.blockchain = blockchain
        self.running = False
    
    def start_api_server(self, port=3000):
        """Start API server for GitHub Pages dashboard"""
        handler = self._create_handler()
        server = HTTPServer(('localhost', port), handler)
        
        print(f"API Server started on http://localhost:{port}")
        print("Your GitHub Pages dashboard can now connect to this local API")
        print("\nAPI Endpoints:")
        print(f"  http://localhost:{port}/api/blockchain/info")
        print(f"  http://localhost:{port}/api/blocks")
        print(f"  http://localhost:{port}/api/stats")
        print(f"  http://localhost:{port}/api/mempool")
        print("\nPress Ctrl+C to stop")
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping API server...")
            server.shutdown()
    
    def _create_handler(self):
        """Create HTTP request handler"""
        blockchain = self.blockchain
        
        class DashboardAPIHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                parsed_path = urlparse(self.path)
                path = parsed_path.path
                query_params = parse_qs(parsed_path.query)
                
                try:
                    if path == '/api/blockchain/info':
                        self._serve_blockchain_info()
                    elif path == '/api/blocks':
                        self._serve_blocks(query_params)
                    elif path == '/api/stats':
                        self._serve_stats()
                    elif path == '/api/mempool':
                        self._serve_mempool()
                    elif path == '/api/latest-block':
                        self._serve_latest_block()
                    elif path.startswith('/api/block/'):
                        block_hash = path[12:]  # Remove '/api/block/' prefix
                        self._serve_block_detail(block_hash)
                    else:
                        self._serve_cors()  # Handle CORS preflight
                except Exception as e:
                    self._send_error(500, str(e))
            
            def do_OPTIONS(self):
                """Handle CORS preflight requests"""
                self._serve_cors()
            
            def _serve_cors(self):
                """Serve CORS headers"""
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()
            
            def _serve_blockchain_info(self):
                """Serve blockchain information"""
                data = {
                    'chain': 'WorldWideCoin',
                    'blocks': len(blockchain.chain),
                    'difficulty': blockchain.get_difficulty() if hasattr(blockchain, 'get_difficulty') else 1,
                    'mempool_size': len(blockchain.mempool.transactions),
                    'total_supply': sum(50.0 for _ in blockchain.chain),  # Simplified
                    'version': '1.0.0',
                    'protocol_version': '1.0.0',
                    'best_block_hash': blockchain.chain[-1].calculate_hash() if blockchain.chain else None,
                    'timestamp': time.time()
                }
                self._send_json(data)
            
            def _serve_blocks(self, query_params):
                """Serve blocks data"""
                limit = int(query_params.get('limit', [20])[0])
                page = int(query_params.get('page', [1])[0])
                
                start_idx = (page - 1) * limit
                end_idx = start_idx + limit
                
                blocks = []
                for block in blockchain.chain[start_idx:end_idx]:
                    blocks.append({
                        'hash': block.calculate_hash(),
                        'height': block.index,
                        'timestamp': block.timestamp,
                        'transactions': len(block.transactions),
                        'size': len(str(block)),
                        'difficulty': block.difficulty,
                        'nonce': block.nonce,
                        'prev_hash': block.prev_hash
                    })
                
                data = {
                    'blocks': blocks,
                    'page': page,
                    'limit': limit,
                    'total': len(blockchain.chain),
                    'timestamp': time.time()
                }
                self._send_json(data)
            
            def _serve_stats(self):
                """Serve network statistics"""
                if not blockchain.chain:
                    stats = {
                        'height': 0,
                        'total_supply': 0,
                        'difficulty': 1,
                        'hash_rate': 0,
                        'mempool_size': 0,
                        'avg_block_time': 0,
                        'total_transactions': 0
                    }
                else:
                    # Calculate statistics
                    total_txs = sum(len(block.transactions) for block in blockchain.chain)
                    avg_block_time = 600  # Default 10 minutes
                    
                    if len(blockchain.chain) > 1:
                        times = []
                        for i in range(1, len(blockchain.chain)):
                            times.append(blockchain.chain[i].timestamp - blockchain.chain[i-1].timestamp)
                        if times:
                            avg_block_time = sum(times) / len(times)
                    
                    stats = {
                        'height': len(blockchain.chain),
                        'total_supply': sum(50.0 for _ in blockchain.chain),
                        'difficulty': blockchain.get_difficulty() if hasattr(blockchain, 'get_difficulty') else 1,
                        'hash_rate': blockchain.chain[-1].difficulty * (2 ** 32) / 600 if blockchain.chain else 0,
                        'mempool_size': len(blockchain.mempool.transactions),
                        'avg_block_time': avg_block_time,
                        'total_transactions': total_txs,
                        'timestamp': time.time()
                    }
                
                self._send_json(stats)
            
            def _serve_mempool(self):
                """Serve mempool information"""
                mempool_txs = []
                for tx in blockchain.mempool.transactions:
                    mempool_txs.append({
                        'hash': tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash(),
                        'size': len(str(tx)),
                        'inputs': len(tx.inputs),
                        'outputs': len(tx.outputs),
                        'fee': 0.001,  # Simplified
                        'timestamp': time.time()
                    })
                
                data = {
                    'size': len(mempool_txs),
                    'bytes': sum(len(str(tx)) for tx in blockchain.mempool.transactions),
                    'count': len(mempool_txs),
                    'transactions': mempool_txs,
                    'timestamp': time.time()
                }
                self._send_json(data)
            
            def _serve_latest_block(self):
                """Serve latest block"""
                if not blockchain.chain:
                    self._send_error(404, "No blocks available")
                    return
                
                block = blockchain.chain[-1]
                data = {
                    'hash': block.calculate_hash(),
                    'height': block.index,
                    'timestamp': block.timestamp,
                    'transactions': len(block.transactions),
                    'size': len(str(block)),
                    'difficulty': block.difficulty,
                    'nonce': block.nonce,
                    'prev_hash': block.prev_hash,
                    'tx_hashes': [tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash() for tx in block.transactions],
                    'reward': 50.0,  # Simplified
                    'timestamp': time.time()
                }
                self._send_json(data)
            
            def _serve_block_detail(self, block_hash):
                """Serve detailed block information"""
                for block in blockchain.chain:
                    if block.calculate_hash() == block_hash:
                        data = {
                            'hash': block.calculate_hash(),
                            'height': block.index,
                            'timestamp': block.timestamp,
                            'transactions': len(block.transactions),
                            'size': len(str(block)),
                            'difficulty': block.difficulty,
                            'nonce': block.nonce,
                            'prev_hash': block.prev_hash,
                            'merkle_root': getattr(block, 'merkle_root', ''),
                            'transactions_detail': [
                                {
                                    'hash': tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash(),
                                    'inputs': len(tx.inputs),
                                    'outputs': len(tx.outputs),
                                    'size': len(str(tx)),
                                    'inputs_detail': tx.inputs,
                                    'outputs_detail': tx.outputs
                                }
                                for tx in block.transactions
                            ]
                        }
                        self._send_json(data)
                        return
                
                self._send_error(404, "Block not found")
            
            def _send_json(self, data):
                """Send JSON response"""
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(data, indent=2).encode())
            
            def _send_error(self, code, message):
                """Send error response"""
                self.send_response(code)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': message}).encode())
            
            def log_message(self, format, *args):
                """Suppress default logging"""
                pass
        
        return DashboardAPIHandler
    
    def generate_dashboard_config(self):
        """Generate configuration for GitHub Pages dashboard"""
        config = {
            "api_base_url": "http://localhost:3000/api",
            "refresh_interval": 5000,  # 5 seconds
            "theme": "dark",
            "features": {
                "real_time_updates": True,
                "block_browser": True,
                "transaction_viewer": True,
                "network_stats": True,
                "mempool_monitor": True
            }
        }
        
        with open('dashboard_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print("Dashboard configuration saved to dashboard_config.json")
        return config


def main():
    """Main function to start connector"""
    print("WorldWideCoin GitHub Dashboard Connector")
    print("=" * 50)
    
    try:
        # Create blockchain
        print("Initializing blockchain...")
        blockchain = Blockchain()
        
        # Mine some initial blocks if needed
        if len(blockchain.chain) < 3:
            print("Mining initial blocks...")
            for i in range(3):
                block = blockchain.create_block(f"connector_miner_{i}")
                blockchain.add_block(block)
        
        print(f"Blockchain ready: {len(blockchain.chain)} blocks")
        
        # Create connector
        connector = GitHubDashboardConnector(blockchain)
        
        # Generate dashboard config
        config = connector.generate_dashboard_config()
        
        print(f"\nDashboard Configuration:")
        print(f"  API Base URL: {config['api_base_url']}")
        print(f"  Refresh Interval: {config['refresh_interval']}ms")
        print(f"  Theme: {config['theme']}")
        
        print(f"\nTo connect your GitHub Pages dashboard:")
        print(f"1. Update your dashboard's API URL to: {config['api_base_url']}")
        print(f"2. Start this API server")
        print(f"3. Your dashboard at https://worldwidecoinwwc.github.io/ will connect automatically")
        
        # Start API server
        connector.start_api_server()
        
    except KeyboardInterrupt:
        print("\nStopping connector...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
