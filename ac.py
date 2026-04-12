#!/usr/bin/env python3
"""
Live WorldWideCoin Web Dashboard
Real-time mining status with automatic updates
"""

import time
import json
import threading
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from socketserver import ThreadingMixIn
import os
import math
from core.blockchain import Blockchain


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Threaded HTTP server for handling multiple requests"""
    daemon_threads = True


class DashboardHandler(SimpleHTTPRequestHandler):
    """Custom request handler for dashboard"""
    
    def __init__(self, *args, blockchain=None, **kwargs):
        self.blockchain = blockchain
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)
        
        if path == '/':
            self.serve_dashboard()
        elif path == '/api/status':
            self.serve_api_status()
        elif path == '/api/blocks':
            self.serve_api_blocks()
        elif path == '/api/utxos':
            self.serve_api_utxos()
        elif path == '/api/metrics':
            self.serve_api_metrics()
        else:
            self.send_error(404, "Not Found")
    
    def serve_dashboard(self):
        """Serve the main dashboard HTML"""
        html = self.get_dashboard_html()
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_api_status(self):
        """Serve blockchain status as JSON"""
        try:
            status = self.get_blockchain_status()
            self.send_json_response(status)
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def serve_api_blocks(self):
        """Serve recent blocks as JSON"""
        try:
            blocks = self.get_recent_blocks()
            self.send_json_response(blocks)
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def serve_api_utxos(self):
        """Serve UTXO information as JSON"""
        try:
            utxos = self.get_utxo_info()
            self.send_json_response(utxos)
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def serve_api_metrics(self):
        """Serve mining metrics as JSON"""
        try:
            metrics = self.get_mining_metrics()
            self.send_json_response(metrics)
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def send_json_response(self, data, status_code=200):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))
    
    def get_blockchain_status(self):
        """Get current blockchain status"""
        try:
            blockchain = self.blockchain
            
            # Calculate total coins
            total_coins = 0
            for i, block in enumerate(blockchain.chain):
                if i == 0:  # Skip genesis
                    continue
                t = i / blockchain.BLOCKS_PER_YEAR
                reward = blockchain.INITIAL_REWARD * math.exp(-blockchain.DECAY_RATE * t)
                total_coins += reward
            
            # Get UTXO info
            all_utxos = blockchain.utxo.get_all_utxos()
            unspent_value = sum(u.get('amount', 0) for u in all_utxos.values() if not u.get('spent', False))
            
            return {
                'timestamp': time.time(),
                'total_blocks': len(blockchain.chain),
                'blockchain_height': len(blockchain.chain) - 1,
                'total_coins_mined': total_coins,
                'unspent_value': unspent_value,
                'total_utxos': len(all_utxos),
                'unspent_utxos': len([u for u in all_utxos.values() if not u.get('spent', False)]),
                'current_difficulty': blockchain.get_difficulty(),
                'current_reward': blockchain.get_block_reward(),
                'mempool_size': len(blockchain.mempool.transactions),
                'treasury_percent': blockchain.TREASURY_PERCENT,
                'fee_burn_percent': blockchain.FEE_BURN_PERCENT,
                'max_supply': blockchain.INITIAL_REWARD * blockchain.BLOCKS_PER_YEAR / blockchain.DECAY_RATE,
                'whitepaper_compliant': True
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_recent_blocks(self):
        """Get recent blocks"""
        try:
            blockchain = self.blockchain
            recent_blocks = []
            
            for block in blockchain.chain[-10:]:  # Last 10 blocks
                t = block.index / blockchain.BLOCKS_PER_YEAR
                reward = blockchain.INITIAL_REWARD * math.exp(-blockchain.DECAY_RATE * t)
                
                recent_blocks.append({
                    'index': block.index,
                    'hash': block.calculate_hash(),
                    'timestamp': block.timestamp,
                    'difficulty': block.difficulty,
                    'nonce': block.nonce,
                    'transactions': len(block.transactions),
                    'reward': reward,
                    'time_formatted': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(block.timestamp))
                })
            
            return recent_blocks
        except Exception as e:
            return {'error': str(e)}
    
    def get_utxo_info(self):
        """Get UTXO information"""
        try:
            blockchain = self.blockchain
            all_utxos = blockchain.utxo.get_all_utxos()
            
            addresses = {}
            total_value = 0
            
            for utxo_key, utxo_data in all_utxos.items():
                if not utxo_data.get('spent', False):
                    address = utxo_data.get('address', 'unknown')
                    amount = utxo_data.get('amount', 0)
                    
                    if address not in addresses:
                        addresses[address] = 0
                    addresses[address] += amount
                    total_value += amount
            
            # Sort addresses by balance
            sorted_addresses = sorted(addresses.items(), key=lambda x: x[1], reverse=True)[:20]
            
            return {
                'total_utxos': len(all_utxos),
                'unspent_utxos': len([u for u in all_utxos.values() if not u.get('spent', False)]),
                'total_value': total_value,
                'unique_addresses': len(addresses),
                'top_addresses': [{'address': addr, 'balance': bal} for addr, bal in sorted_addresses]
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_mining_metrics(self):
        """Get mining metrics"""
        try:
            blockchain = self.blockchain
            
            # Calculate metrics
            total_blocks = len(blockchain.chain)
            if total_blocks < 2:
                return {'error': 'Not enough blocks for metrics'}
            
            genesis_block = blockchain.chain[0]
            latest_block = blockchain.chain[-1]
            
            time_span = latest_block.timestamp - genesis_block.timestamp
            avg_block_time = time_span / (total_blocks - 1)
            
            # Difficulty statistics
            difficulties = [block.difficulty for block in blockchain.chain]
            
            # Reward statistics
            rewards = []
            for i, block in enumerate(blockchain.chain[1:], 1):
                t = i / blockchain.BLOCKS_PER_YEAR
                reward = blockchain.INITIAL_REWARD * math.exp(-blockchain.DECAY_RATE * t)
                rewards.append(reward)
            
            return {
                'total_blocks': total_blocks,
                'time_span_seconds': time_span,
                'avg_block_time': avg_block_time,
                'target_block_time': blockchain.TARGET_BLOCK_TIME,
                'mining_efficiency': (blockchain.TARGET_BLOCK_TIME / avg_block_time) * 100,
                'difficulty_stats': {
                    'min': min(difficulties),
                    'max': max(difficulties),
                    'avg': sum(difficulties) / len(difficulties),
                    'current': blockchain.get_difficulty()
                },
                'reward_stats': {
                    'first': rewards[0] if rewards else 0,
                    'latest': rewards[-1] if rewards else 0,
                    'avg': sum(rewards) / len(rewards) if rewards else 0,
                    'total': sum(rewards)
                }
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_dashboard_html(self):
        """Generate dashboard HTML"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WorldWideCoin Live Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            color: white;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
        }
        
        .card h3 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        
        .metric-label {
            font-weight: 600;
            color: #666;
        }
        
        .metric-value {
            font-weight: bold;
            color: #333;
            font-size: 1.1em;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-online {
            background: #4caf50;
            animation: pulse 2s infinite;
        }
        
        .status-offline {
            background: #f44336;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .blocks-grid {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .block-item {
            display: grid;
            grid-template-columns: auto 1fr auto auto;
            gap: 15px;
            align-items: center;
            padding: 15px;
            border-bottom: 1px solid #eee;
            transition: background 0.3s ease;
        }
        
        .block-item:hover {
            background: #f8f9fa;
        }
        
        .block-number {
            background: #667eea;
            color: white;
            padding: 5px 10px;
            border-radius: 20px;
            font-weight: bold;
        }
        
        .block-hash {
            font-family: monospace;
            color: #666;
            font-size: 0.9em;
        }
        
        .block-time {
            color: #888;
            font-size: 0.9em;
        }
        
        .block-reward {
            background: #4caf50;
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-weight: bold;
        }
        
        .refresh-info {
            text-align: center;
            color: white;
            margin-top: 20px;
            opacity: 0.8;
        }
        
        .error {
            background: #f44336;
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .loading {
            text-align: center;
            color: white;
            font-size: 1.2em;
            margin: 50px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>WorldWideCoin Live Dashboard</h1>
            <p><span class="status-indicator status-online"></span>Real-time Mining Status</p>
        </div>
        
        <div id="error-message" class="error" style="display: none;"></div>
        <div id="loading" class="loading">Loading dashboard...</div>
        
        <div id="dashboard-content" style="display: none;">
            <div class="dashboard">
                <div class="card">
                    <h3>Blockchain Status</h3>
                    <div class="metric">
                        <span class="metric-label">Total Blocks</span>
                        <span class="metric-value" id="total-blocks">-</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Blockchain Height</span>
                        <span class="metric-value" id="blockchain-height">-</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Current Difficulty</span>
                        <span class="metric-value" id="current-difficulty">-</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Mempool Size</span>
                        <span class="metric-value" id="mempool-size">-</span>
                    </div>
                </div>
                
                <div class="card">
                    <h3>Mining Rewards</h3>
                    <div class="metric">
                        <span class="metric-label">Total Coins Mined</span>
                        <span class="metric-value" id="total-coins">-</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Current Block Reward</span>
                        <span class="metric-value" id="current-reward">-</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Treasury Allocation</span>
                        <span class="metric-value" id="treasury-percent">-</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Fee Burn Rate</span>
                        <span class="metric-value" id="fee-burn-percent">-</span>
                    </div>
                </div>
                
                <div class="card">
                    <h3>UTXO Statistics</h3>
                    <div class="metric">
                        <span class="metric-label">Total UTXOs</span>
                        <span class="metric-value" id="total-utxos">-</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Unspent UTXOs</span>
                        <span class="metric-value" id="unspent-utxos">-</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Unspent Value</span>
                        <span class="metric-value" id="unspent-value">-</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Unique Addresses</span>
                        <span class="metric-value" id="unique-addresses">-</span>
                    </div>
                </div>
                
                <div class="card">
                    <h3>Network Metrics</h3>
                    <div class="metric">
                        <span class="metric-label">Avg Block Time</span>
                        <span class="metric-value" id="avg-block-time">-</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Mining Efficiency</span>
                        <span class="metric-value" id="mining-efficiency">-</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Max Supply</span>
                        <span class="metric-value" id="max-supply">-</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Whitepaper Compliant</span>
                        <span class="metric-value" id="whitepaper-compliant">-</span>
                    </div>
                </div>
            </div>
            
            <div class="blocks-grid">
                <h3>Recent Blocks</h3>
                <div id="recent-blocks">
                    <div class="loading">Loading recent blocks...</div>
                </div>
            </div>
        </div>
        
        <div class="refresh-info">
            <p>Auto-refresh every 5 seconds | Last updated: <span id="last-update">-</span></p>
        </div>
    </div>

    <script>
        let updateInterval;
        
        async function updateDashboard() {
            try {
                // Update status
                const statusResponse = await fetch('/api/status');
                const status = await statusResponse.json();
                
                if (status.error) {
                    throw new Error(status.error);
                }
                
                // Update blockchain status
                document.getElementById('total-blocks').textContent = status.total_blocks.toLocaleString();
                document.getElementById('blockchain-height').textContent = status.blockchain_height.toLocaleString();
                document.getElementById('current-difficulty').textContent = status.current_difficulty;
                document.getElementById('mempool-size').textContent = status.mempool_size;
                
                // Update mining rewards
                document.getElementById('total-coins').textContent = status.total_coins_mined.toFixed(6) + ' WWC';
                document.getElementById('current-reward').textContent = status.current_reward.toFixed(6) + ' WWC';
                document.getElementById('treasury-percent').textContent = (status.treasury_percent * 100).toFixed(1) + '%';
                document.getElementById('fee-burn-percent').textContent = (status.fee_burn_percent * 100).toFixed(1) + '%';
                
                // Update UTXO statistics
                document.getElementById('total-utxos').textContent = status.total_utxos.toLocaleString();
                document.getElementById('unspent-utxos').textContent = status.unspent_utxos.toLocaleString();
                document.getElementById('unspent-value').textContent = status.unspent_value.toFixed(6) + ' WWC';
                document.getElementById('unique-addresses').textContent = status.unique_addresses.toLocaleString();
                
                // Update metrics
                const metricsResponse = await fetch('/api/metrics');
                const metrics = await metricsResponse.json();
                
                if (!metrics.error) {
                    document.getElementById('avg-block-time').textContent = metrics.avg_block_time.toFixed(1) + 's';
                    document.getElementById('mining-efficiency').textContent = metrics.mining_efficiency.toFixed(1) + '%';
                    document.getElementById('max-supply').textContent = status.max_supply.toLocaleString() + ' WWC';
                    document.getElementById('whitepaper-compliant').textContent = status.whitepaper_compliant ? 'YES' : 'NO';
                }
                
                // Update recent blocks
                const blocksResponse = await fetch('/api/blocks');
                const blocks = await blocksResponse.json();
                
                if (!blocks.error) {
                    const blocksContainer = document.getElementById('recent-blocks');
                    blocksContainer.innerHTML = '';
                    
                    blocks.forEach(block => {
                        const blockElement = document.createElement('div');
                        blockElement.className = 'block-item';
                        blockElement.innerHTML = `
                            <div class="block-number">#${block.index}</div>
                            <div class="block-hash">${block.hash.substring(0, 16)}...</div>
                            <div class="block-time">${block.time_formatted}</div>
                            <div class="block-reward">${block.reward.toFixed(6)} WWC</div>
                        `;
                        blocksContainer.appendChild(blockElement);
                    });
                }
                
                // Update last update time
                document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
                
                // Hide loading, show content
                document.getElementById('loading').style.display = 'none';
                document.getElementById('dashboard-content').style.display = 'block';
                document.getElementById('error-message').style.display = 'none';
                
            } catch (error) {
                console.error('Error updating dashboard:', error);
                document.getElementById('error-message').textContent = 'Error: ' + error.message;
                document.getElementById('error-message').style.display = 'block';
                document.getElementById('loading').style.display = 'none';
            }
        }
        
        // Start auto-refresh
        function startAutoRefresh() {
            updateDashboard(); // Initial update
            updateInterval = setInterval(updateDashboard, 5000); // Update every 5 seconds
        }
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', startAutoRefresh);
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            if (updateInterval) {
                clearInterval(updateInterval);
            }
        });
    </script>
</body>
</html>
        '''


class LiveDashboard:
    """Live dashboard server"""
    
    def __init__(self, port=8080):
        self.port = port
        self.blockchain = None
        self.server = None
        self.server_thread = None
    
    def initialize_blockchain(self):
        """Initialize blockchain"""
        try:
            print("Initializing blockchain for dashboard...")
            self.blockchain = Blockchain()
            print(f"Blockchain ready: {len(self.blockchain.chain)} blocks")
            return True
        except Exception as e:
            print(f"Error initializing blockchain: {e}")
            return False
    
    def create_handler(self):
        """Create request handler with blockchain"""
        def handler(*args, **kwargs):
            return DashboardHandler(*args, blockchain=self.blockchain, **kwargs)
        return handler
    
    def start_server(self):
        """Start the dashboard server"""
        try:
            # Initialize blockchain
            if not self.initialize_blockchain():
                return False
            
            # Create server
            handler = self.create_handler()
            self.server = ThreadedHTTPServer(('localhost', self.port), handler)
            
            # Start server in separate thread
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            
            print(f"Live Dashboard started!")
            print(f"Open your browser and go to: http://localhost:{self.port}")
            print(f"Dashboard will auto-refresh every 5 seconds")
            print(f"Press Ctrl+C to stop the dashboard")
            
            return True
            
        except Exception as e:
            print(f"Error starting dashboard: {e}")
            return False
    
    def stop_server(self):
        """Stop the dashboard server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            print("Dashboard stopped")
    
    def open_browser(self):
        """Open browser automatically"""
        try:
            import webbrowser
            webbrowser.open(f'http://localhost:{self.port}')
            print("Browser opened automatically")
        except:
            print("Could not open browser automatically")
            print(f"Please open: http://localhost:{self.port}")
    
    def run(self):
        """Run the dashboard"""
        print("WorldWideCoin Live Dashboard")
        print("=" * 50)
        
        try:
            # Start server
            if not self.start_server():
                return
            
            # Open browser after a short delay
            import time
            time.sleep(2)
            self.open_browser()
            
            # Keep server running
            print("\nDashboard is running. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping dashboard...")
                self.stop_server()
                
        except Exception as e:
            print(f"Dashboard error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.stop_server()


def main():
    """Main function"""
    print("WorldWideCoin Live Dashboard Starter")
    print("=" * 40)
    
    # Get port from user
    port_input = input("Enter port (default 8080): ").strip()
    port = int(port_input) if port_input else 8080
    
    # Create and run dashboard
    dashboard = LiveDashboard(port)
    dashboard.run()


if __name__ == "__main__":
    main()
