#!/usr/bin/env python3
"""
Quick WorldWideCoin Dashboard
Starts automatically without user input
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
    """Threaded HTTP server"""
    daemon_threads = True


class QuickDashboardHandler(SimpleHTTPRequestHandler):
    """Quick dashboard handler"""
    
    def __init__(self, *args, blockchain=None, **kwargs):
        self.blockchain = blockchain
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        """Suppress log messages"""
        pass
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            self.serve_dashboard()
        elif self.path == '/api/status':
            self.serve_api_status()
        elif self.path == '/api/blocks':
            self.serve_api_blocks()
        else:
            self.send_error(404)
    
    def serve_dashboard(self):
        """Serve dashboard HTML"""
        html = self.get_dashboard_html()
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_api_status(self):
        """Serve status API"""
        try:
            status = self.get_status()
            self.send_json_response(status)
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def serve_api_blocks(self):
        """Serve blocks API"""
        try:
            blocks = self.get_blocks()
            self.send_json_response(blocks)
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def send_json_response(self, data, status_code=200):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))
    
    def get_status(self):
        """Get blockchain status"""
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
    
    def get_blocks(self):
        """Get recent blocks"""
        try:
            blockchain = self.blockchain
            recent_blocks = []
            
            for block in blockchain.chain[-10:]:
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
    
    def get_dashboard_html(self):
        """Get dashboard HTML"""
        return '''
<!DOCTYPE html>
<html>
<head>
    <title>WorldWideCoin Quick Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            margin: 0; 
            padding: 20px; 
            color: white;
        }
        .container { 
            max-width: 1000px; 
            margin: 0 auto; 
        }
        .header { 
            text-align: center; 
            margin-bottom: 30px; 
        }
        .header h1 { 
            font-size: 2.5em; 
            margin-bottom: 10px; 
        }
        .dashboard { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
            gap: 20px; 
            margin-bottom: 30px; 
        }
        .card { 
            background: white; 
            border-radius: 10px; 
            padding: 20px; 
            box-shadow: 0 5px 15px rgba(0,0,0,0.3); 
            color: #333;
        }
        .card h3 { 
            color: #667eea; 
            margin-bottom: 15px; 
        }
        .metric { 
            display: flex; 
            justify-content: space-between; 
            margin-bottom: 10px; 
            padding: 8px; 
            background: #f8f9fa; 
            border-radius: 5px; 
        }
        .metric-value { 
            font-weight: bold; 
        }
        .blocks { 
            background: white; 
            border-radius: 10px; 
            padding: 20px; 
            box-shadow: 0 5px 15px rgba(0,0,0,0.3); 
            color: #333;
        }
        .block { 
            display: grid; 
            grid-template-columns: auto 1fr auto; 
            gap: 10px; 
            padding: 10px; 
            border-bottom: 1px solid #eee; 
            align-items: center;
        }
        .block-number { 
            background: #667eea; 
            color: white; 
            padding: 5px 10px; 
            border-radius: 15px; 
            font-weight: bold; 
        }
        .block-hash { 
            font-family: monospace; 
            color: #666; 
            font-size: 0.9em; 
        }
        .block-reward { 
            background: #4caf50; 
            color: white; 
            padding: 5px 10px; 
            border-radius: 10px; 
            font-weight: bold; 
        }
        .status { 
            text-align: center; 
            margin-top: 20px; 
            opacity: 0.8; 
        }
        .online { 
            color: #4caf50; 
        }
        .loading { 
            text-align: center; 
            font-size: 1.2em; 
            margin: 50px 0; 
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>WorldWideCoin Dashboard</h1>
            <p class="online">Live Status</p>
        </div>
        
        <div id="loading" class="loading">Loading...</div>
        <div id="content" style="display: none;">
            <div class="dashboard">
                <div class="card">
                    <h3>Blockchain</h3>
                    <div class="metric">
                        <span>Total Blocks</span>
                        <span class="metric-value" id="total-blocks">-</span>
                    </div>
                    <div class="metric">
                        <span>Difficulty</span>
                        <span class="metric-value" id="difficulty">-</span>
                    </div>
                    <div class="metric">
                        <span>Mempool</span>
                        <span class="metric-value" id="mempool">-</span>
                    </div>
                </div>
                
                <div class="card">
                    <h3>Mining</h3>
                    <div class="metric">
                        <span>Total Coins</span>
                        <span class="metric-value" id="total-coins">-</span>
                    </div>
                    <div class="metric">
                        <span>Current Reward</span>
                        <span class="metric-value" id="current-reward">-</span>
                    </div>
                    <div class="metric">
                        <span>Treasury</span>
                        <span class="metric-value" id="treasury">-</span>
                    </div>
                </div>
                
                <div class="card">
                    <h3>UTXOs</h3>
                    <div class="metric">
                        <span>Total UTXOs</span>
                        <span class="metric-value" id="total-utxos">-</span>
                    </div>
                    <div class="metric">
                        <span>Unspent UTXOs</span>
                        <span class="metric-value" id="unspent-utxos">-</span>
                    </div>
                    <div class="metric">
                        <span>Unspent Value</span>
                        <span class="metric-value" id="unspent-value">-</span>
                    </div>
                </div>
            </div>
            
            <div class="blocks">
                <h3>Recent Blocks</h3>
                <div id="blocks-list">
                    <div class="loading">Loading blocks...</div>
                </div>
            </div>
        </div>
        
        <div class="status">
            <p>Auto-refresh every 5 seconds | Last updated: <span id="last-update">-</span></p>
        </div>
    </div>

    <script>
        async function update() {
            try {
                const response = await fetch('/api/status');
                const status = await response.json();
                
                if (status.error) throw new Error(status.error);
                
                document.getElementById('total-blocks').textContent = status.total_blocks.toLocaleString();
                document.getElementById('difficulty').textContent = status.current_difficulty;
                document.getElementById('mempool').textContent = status.mempool_size;
                document.getElementById('total-coins').textContent = status.total_coins_mined.toFixed(6) + ' WWC';
                document.getElementById('current-reward').textContent = status.current_reward.toFixed(6) + ' WWC';
                document.getElementById('treasury').textContent = (status.treasury_percent * 100) + '%';
                document.getElementById('total-utxos').textContent = status.total_utxos.toLocaleString();
                document.getElementById('unspent-utxos').textContent = status.unspent_utxos.toLocaleString();
                document.getElementById('unspent-value').textContent = status.unspent_value.toFixed(6) + ' WWC';
                
                const blocksResponse = await fetch('/api/blocks');
                const blocks = await blocksResponse.json();
                
                if (!blocks.error) {
                    const blocksList = document.getElementById('blocks-list');
                    blocksList.innerHTML = '';
                    
                    blocks.forEach(block => {
                        const blockDiv = document.createElement('div');
                        blockDiv.className = 'block';
                        blockDiv.innerHTML = `
                            <div class="block-number">#${block.index}</div>
                            <div class="block-hash">${block.hash.substring(0, 16)}...</div>
                            <div class="block-reward">${block.reward.toFixed(6)} WWC</div>
                        `;
                        blocksList.appendChild(blockDiv);
                    });
                }
                
                document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
                document.getElementById('loading').style.display = 'none';
                document.getElementById('content').style.display = 'block';
                
            } catch (error) {
                console.error('Error:', error);
                document.getElementById('loading').textContent = 'Error: ' + error.message;
            }
        }
        
        setInterval(update, 5000);
        update();
    </script>
</body>
</html>
        '''


def start_quick_dashboard():
    """Start quick dashboard"""
    print("WorldWideCoin Quick Dashboard")
    print("=" * 40)
    
    try:
        # Initialize blockchain
        print("Initializing blockchain...")
        blockchain = Blockchain()
        print(f"Blockchain ready: {len(blockchain.chain)} blocks")
        
        # Create handler
        def handler(*args, **kwargs):
            return QuickDashboardHandler(*args, blockchain=blockchain, **kwargs)
        
        # Start server
        server = ThreadedHTTPServer(('localhost', 8080), handler)
        
        # Start server thread
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        
        print("Dashboard started!")
        print("Open: http://localhost:8080")
        print("Auto-refresh every 5 seconds")
        print("Press Ctrl+C to stop")
        
        # Open browser
        time.sleep(2)
        try:
            webbrowser.open('http://localhost:8080')
            print("Browser opened")
        except:
            print("Could not open browser automatically")
        
        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping dashboard...")
            server.shutdown()
            server.server_close()
            print("Dashboard stopped")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    start_quick_dashboard()
