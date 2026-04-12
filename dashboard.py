#!/usr/bin/env python3
"""
Standalone WorldWideCoin Web Dashboard
No Flask templates required - everything built-in
"""

import json
import time
import webbrowser
from threading import Timer
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from core.blockchain import Blockchain


class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP request handler for dashboard"""
    
    def __init__(self, blockchain, *args, **kwargs):
        self.blockchain = blockchain
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)
        
        try:
            if path == '/':
                self.serve_home_page()
            elif path == '/blocks':
                self.serve_blocks_page()
            elif path == '/stats':
                self.serve_stats_page()
            elif path == '/api/info':
                self.serve_api_info()
            elif path == '/api/blocks':
                self.serve_api_blocks(query_params)
            elif path.startswith('/block/'):
                block_hash = path[7:]  # Remove '/block/' prefix
                self.serve_block_detail(block_hash)
            elif path.startswith('/tx/'):
                tx_hash = path[4:]  # Remove '/tx/' prefix
                self.serve_tx_detail(tx_hash)
            else:
                self.send_404()
        except Exception as e:
            self.send_error(500, f"Internal Server Error: {str(e)}")
    
    def serve_home_page(self):
        """Serve home page with HTML"""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>WorldWideCoin Dashboard</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
        .stat-item { text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; color: #3498db; }
        .links a { display: inline-block; margin: 10px; padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 4px; }
        .links a:hover { background: #2980b9; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>WorldWideCoin Dashboard</h1>
            <p>Real-time blockchain explorer and analytics</p>
        </div>
        
        <div class="card">
            <h2>Network Statistics</h2>
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-number" id="block-height">-</div>
                    <div>Block Height</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number" id="total-supply">-</div>
                    <div>Total Supply</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number" id="difficulty">-</div>
                    <div>Difficulty</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number" id="mempool-size">-</div>
                    <div>Mempool Size</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>Quick Links</h2>
            <div class="links">
                <a href="/blocks">View Blocks</a>
                <a href="/stats">Network Stats</a>
                <a href="/api/info">API Info</a>
                <a href="/api/blocks">API Blocks</a>
            </div>
        </div>
        
        <div class="card">
            <h2>Latest Block</h2>
            <div id="latest-block-info">Loading...</div>
        </div>
    </div>
    
    <script>
        // Load data
        fetch('/api/info')
            .then(response => response.json())
            .then(data => {
                document.getElementById('block-height').textContent = data.blocks;
                document.getElementById('total-supply').textContent = data.total_supply;
                document.getElementById('difficulty').textContent = data.difficulty;
                document.getElementById('mempool-size').textContent = data.mempool_size;
            });
        
        fetch('/api/blocks?limit=1')
            .then(response => response.json())
            .then(data => {
                if (data.blocks && data.blocks.length > 0) {
                    const block = data.blocks[0];
                    document.getElementById('latest-block-info').innerHTML = `
                        <p><strong>Height:</strong> ${block.height}</p>
                        <p><strong>Hash:</strong> ${block.hash}</p>
                        <p><strong>Timestamp:</strong> ${new Date(block.timestamp * 1000).toLocaleString()}</p>
                        <p><strong>Transactions:</strong> ${block.transactions}</p>
                    `;
                }
            });
        
        // Auto-refresh every 30 seconds
        setInterval(() => location.reload(), 30000);
    </script>
</body>
</html>
        """
        self.send_html_response(html)
    
    def serve_blocks_page(self):
        """Serve blocks page"""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>WorldWideCoin Blocks</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f8f9fa; }
        .hash { font-family: monospace; font-size: 0.9em; }
        .back-link { display: inline-block; margin-bottom: 20px; color: #3498db; text-decoration: none; }
        .back-link:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>WorldWideCoin Blocks</h1>
            <a href="/" class="back-link">« Back to Dashboard</a>
        </div>
        
        <div class="card">
            <h2>Recent Blocks</h2>
            <table id="blocks-table">
                <thead>
                    <tr>
                        <th>Height</th>
                        <th>Hash</th>
                        <th>Timestamp</th>
                        <th>Transactions</th>
                        <th>Difficulty</th>
                    </tr>
                </thead>
                <tbody id="blocks-tbody">
                    <tr><td colspan="5">Loading...</td></tr>
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        fetch('/api/blocks?limit=20')
            .then(response => response.json())
            .then(data => {
                const tbody = document.getElementById('blocks-tbody');
                tbody.innerHTML = '';
                
                data.blocks.forEach(block => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${block.height}</td>
                        <td class="hash">${block.hash}</td>
                        <td>${new Date(block.timestamp * 1000).toLocaleString()}</td>
                        <td>${block.transactions}</td>
                        <td>${block.difficulty}</td>
                    `;
                    tbody.appendChild(row);
                });
            })
            .catch(error => {
                document.getElementById('blocks-tbody').innerHTML = '<tr><td colspan="5">Error loading blocks</td></tr>';
            });
    </script>
</body>
</html>
        """
        self.send_html_response(html)
    
    def serve_stats_page(self):
        """Serve statistics page"""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>WorldWideCoin Statistics</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
        .stat-card { text-align: center; padding: 20px; background: #f8f9fa; border-radius: 8px; }
        .stat-number { font-size: 2.5em; font-weight: bold; color: #3498db; }
        .stat-label { font-size: 1.2em; color: #666; margin-top: 10px; }
        .back-link { display: inline-block; margin-bottom: 20px; color: #3498db; text-decoration: none; }
        .back-link:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>WorldWideCoin Network Statistics</h1>
            <a href="/" class="back-link">« Back to Dashboard</a>
        </div>
        
        <div class="card">
            <div class="stats-grid" id="stats-grid">
                <div class="stat-card">
                    <div class="stat-number" id="block-height">-</div>
                    <div class="stat-label">Block Height</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="total-supply">-</div>
                    <div class="stat-label">Total Supply</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="difficulty">-</div>
                    <div class="stat-label">Difficulty</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="mempool-size">-</div>
                    <div class="stat-label">Mempool Size</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>Network Information</h2>
            <div id="network-info">Loading...</div>
        </div>
    </div>
    
    <script>
        fetch('/api/info')
            .then(response => response.json())
            .then(data => {
                document.getElementById('block-height').textContent = data.blocks;
                document.getElementById('total-supply').textContent = data.total_supply;
                document.getElementById('difficulty').textContent = data.difficulty;
                document.getElementById('mempool-size').textContent = data.mempool_size;
                
                document.getElementById('network-info').innerHTML = `
                    <p><strong>Chain:</strong> ${data.chain}</p>
                    <p><strong>Version:</strong> ${data.version}</p>
                    <p><strong>Protocol Version:</strong> ${data.protocol_version}</p>
                    <p><strong>Best Block Hash:</strong> <code>${data.best_block_hash || 'N/A'}</code></p>
                `;
            });
        
        // Auto-refresh every 30 seconds
        setInterval(() => location.reload(), 30000);
    </script>
</body>
</html>
        """
        self.send_html_response(html)
    
    def serve_api_info(self):
        """Serve API info endpoint"""
        data = {
            'chain': 'WorldWideCoin',
            'blocks': len(self.blockchain.chain),
            'difficulty': self.blockchain.get_difficulty() if hasattr(self.blockchain, 'get_difficulty') else 1,
            'mempool_size': len(self.blockchain.mempool.transactions),
            'total_supply': sum(50.0 for _ in self.blockchain.chain),  # Simplified
            'version': '1.0.0',
            'protocol_version': '1.0.0',
            'best_block_hash': self.blockchain.chain[-1].calculate_hash() if self.blockchain.chain else None
        }
        self.send_json_response(data)
    
    def serve_api_blocks(self, query_params):
        """Serve API blocks endpoint"""
        limit = int(query_params.get('limit', [20])[0])
        page = int(query_params.get('page', [1])[0])
        
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
        
        data = {
            'blocks': blocks,
            'page': page,
            'limit': limit,
            'total': len(self.blockchain.chain)
        }
        self.send_json_response(data)
    
    def serve_block_detail(self, block_hash):
        """Serve block detail"""
        for block in self.blockchain.chain:
            current_hash = block.calculate_hash() if hasattr(block, 'calculate_hash') else block.hash
            if current_hash == block_hash:
                data = {
                    'hash': current_hash,
                    'height': block.index,
                    'timestamp': block.timestamp,
                    'transactions': len(block.transactions),
                    'difficulty': block.difficulty,
                    'nonce': block.nonce,
                    'prev_hash': block.prev_hash,
                    'tx_hashes': [tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash() for tx in block.transactions]
                }
                self.send_json_response(data)
                return
        
        self.send_404()
    
    def serve_tx_detail(self, tx_hash):
        """Serve transaction detail"""
        for block in self.blockchain.chain:
            for tx in block.transactions:
                current_tx_hash = tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash
                if current_tx_hash == tx_hash:
                    data = {
                        'hash': current_tx_hash,
                        'block_height': block.index,
                        'timestamp': block.timestamp,
                        'inputs': len(tx.inputs),
                        'outputs': len(tx.outputs),
                        'size': len(str(tx)),
                        'inputs_detail': tx.inputs,
                        'outputs_detail': tx.outputs
                    }
                    self.send_json_response(data)
                    return
        
        self.send_404()
    
    def send_html_response(self, html):
        """Send HTML response"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def send_json_response(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def send_404(self):
        """Send 404 response"""
        self.send_response(404)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'error': 'Not found'}).encode())
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


def open_browser(url):
    """Open browser after a short delay"""
    webbrowser.open(url)


def main():
    """Main function to start dashboard"""
    print("WorldWideCoin Web Dashboard")
    print("=" * 50)
    
    try:
        # Create blockchain
        print("Initializing blockchain...")
        blockchain = Blockchain()
        
        # Mine some blocks if needed
        if len(blockchain.chain) < 3:
            print("Mining initial blocks...")
            for i in range(3):
                block = blockchain.create_block(f"dashboard_miner_{i}")
                blockchain.add_block(block)
        
        print(f"Blockchain ready: {len(blockchain.chain)} blocks")
        
        # Create handler with blockchain
        def handler(*args, **kwargs):
            return DashboardHandler(blockchain, *args, **kwargs)
        
        # Start server
        server = HTTPServer(('127.0.0.1', 8080), handler)
        url = "http://127.0.0.1:8080"
        
        # Open browser after 2 seconds
        Timer(2.0, open_browser, [url]).start()
        
        print(f"\nDashboard is running at: {url}")
        print("Opening browser automatically...")
        print("\nAvailable pages:")
        print(f"  Home: {url}/")
        print(f"  Blocks: {url}/blocks")
        print(f"  Stats: {url}/stats")
        print("\nAPI endpoints:")
        print(f"  Info: {url}/api/info")
        print(f"  Blocks: {url}/api/blocks")
        print("\nPress Ctrl+C to stop")
        
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\nStopping dashboard...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
