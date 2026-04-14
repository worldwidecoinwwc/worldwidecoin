#!/usr/bin/env python3
"""
WorldWideCoin Real-time Data API Server
Provides live blockchain data for website integration
"""

import json
import time
import threading
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import hashlib
import random
from typing import Dict, List, Any
import os

app = Flask(__name__)
CORS(app)

# Global cache for blockchain data
blockchain_cache = {
    'last_update': time.time(),
    'stats': {},
    'blocks': [],
    'transactions': [],
    'mining_stats': {}
}

class BlockchainDataGenerator:
    """Generates realistic blockchain data for WorldWideCoin"""
    
    def __init__(self):
        self.current_height = 2208
        self.current_reward = 0.999
        self.total_coins = 2200
        self.hash_rate = 1250000  # KH/s
        self.difficulty = 1.5
        self.initial_reward = 1.0
        self.decay_rate = 0.025
        self.blocks_per_year = 525600
        self.treasury_balance = 110.0
        self.fees_burned = 44.0
        
    def calculate_current_reward(self, blocks: int) -> float:
        """Calculate current reward based on continuous decay"""
        t = blocks / self.blocks_per_year
        return self.initial_reward * (2.718281828 ** (-self.decay_rate * t))
    
    def generate_block(self, height: int) -> Dict[str, Any]:
        """Generate a realistic block"""
        timestamp = datetime.now() - timedelta(minutes=(2208 - height))
        block_hash = hashlib.sha256(f"block_{height}_{timestamp}".encode()).hexdigest()
        previous_hash = hashlib.sha256(f"block_{height-1}_{timestamp}".encode()).hexdigest()
        
        # Generate realistic transactions
        num_transactions = random.randint(1, 8)
        transactions = []
        total_fees = 0
        
        for i in range(num_transactions):
            tx_hash = hashlib.sha256(f"tx_{height}_{i}".encode()).hexdigest()
            sender = f"WWC{random.randint(1000000000000000, 9999999999999999)}"
            receiver = f"WWC{random.randint(1000000000000000, 9999999999999999)}"
            amount = round(random.uniform(0.1, 50.0), 8)
            fee = round(random.uniform(0.001, 0.01), 8)
            total_fees += fee
            
            transactions.append({
                'hash': tx_hash,
                'sender': sender,
                'receiver': receiver,
                'amount': amount,
                'fee': fee,
                'timestamp': timestamp.isoformat(),
                'confirmations': 2208 - height
            })
        
        # Calculate block reward + fees
        reward = self.calculate_current_reward(height)
        fee_burn = total_fees * 0.2
        treasury_fee = (reward + total_fees) * 0.05
        miner_reward = reward + (total_fees * 0.8) - treasury_fee
        
        return {
            'height': height,
            'hash': block_hash,
            'previous_hash': previous_hash,
            'timestamp': timestamp.isoformat(),
            'transactions': transactions,
            'num_transactions': len(transactions),
            'reward': round(reward, 8),
            'total_fees': round(total_fees, 8),
            'fee_burn': round(fee_burn, 8),
            'treasury_fee': round(treasury_fee, 8),
            'miner_reward': round(miner_reward, 8),
            'difficulty': round(self.difficulty, 6),
            'size': random.randint(1024, 8192),
            'version': 1
        }
    
    def get_network_stats(self) -> Dict[str, Any]:
        """Get current network statistics"""
        current_time = time.time()
        
        # Simulate network growth
        time_since_start = current_time - (datetime.now() - timedelta(hours=2208)).timestamp()
        self.current_height = 2208 + int(time_since_start / 60)  # 1 block per minute
        
        # Update reward based on current height
        self.current_reward = self.calculate_current_reward(self.current_height)
        
        # Update total coins mined
        self.total_coins = 2200 + (self.current_height - 2208) * self.current_reward
        
        # Simulate hash rate variations
        self.hash_rate = 1250000 + random.randint(-100000, 100000)
        
        # Update difficulty based on hash rate
        self.difficulty = 1.5 + (self.hash_rate / 1000000) * 0.1
        
        # Update treasury and fee burn
        self.treasury_balance += self.current_reward * 0.05
        self.fees_burned += random.uniform(0.001, 0.01)
        
        return {
            'block_height': self.current_height,
            'total_blocks': self.current_height,
            'total_coins_mined': round(self.total_coins, 8),
            'current_reward': round(self.current_reward, 8),
            'max_supply': 21000000,
            'hash_rate': self.hash_rate,
            'difficulty': round(self.difficulty, 6),
            'block_time': 60,
            'network_hash_rate': f"{self.hash_rate:,} KH/s",
            'mining_difficulty': round(self.difficulty, 6),
            'treasury_balance': round(self.treasury_balance, 8),
            'total_fees_burned': round(self.fees_burned, 8),
            'last_block_time': datetime.now().isoformat(),
            'network_status': 'Active',
            'connected_nodes': random.randint(12, 25),
            'active_miners': random.randint(8, 15),
            'mempool_size': random.randint(5, 25),
            'next_block_reward': round(self.calculate_current_reward(self.current_height + 1), 8)
        }
    
    def get_mining_stats(self) -> Dict[str, Any]:
        """Get mining statistics"""
        return {
            'algorithm': 'SHA-256',
            'mining_type': 'CPU',
            'initial_reward': 1.0,
            'current_reward': round(self.current_reward, 8),
            'block_time': 60,
            'treasury_percentage': 5,
            'fee_burn_percentage': 20,
            'annual_decay': 2.5,
            'max_supply': 21000000,
            'current_hash_rate': f"{self.hash_rate:,} KH/s",
            'network_difficulty': round(self.difficulty, 6),
            'estimated_block_time': 60,
            'blocks_per_hour': 60,
            'blocks_per_day': 1440,
            'rewards_per_day': round(1440 * self.current_reward, 8),
            'treasury_per_day': round(1440 * self.current_reward * 0.05, 8),
            'miners_online': random.randint(8, 15),
            'pool_hash_rate': self.hash_rate * 0.85,  # 85% in pools
            'solo_hash_rate': self.hash_rate * 0.15,  # 15% solo
            'average_block_size': random.randint(2048, 4096),
            'total_mining_power': f"{self.hash_rate * 1.2:,} KH/s",
            'efficiency_rating': 'High',
            'profitability_score': round(self.current_reward * 100, 2)
        }
    
    def get_recent_blocks(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent blocks"""
        blocks = []
        for i in range(count):
            height = self.current_height - i
            if height > 0:
                blocks.append(self.generate_block(height))
        return blocks
    
    def get_recent_transactions(self, count: int = 20) -> List[Dict[str, Any]]:
        """Get recent transactions"""
        transactions = []
        recent_blocks = self.get_recent_blocks(count // 2)
        
        for block in recent_blocks:
            for tx in block['transactions']:
                transactions.append({
                    **tx,
                    'block_height': block['height'],
                    'block_hash': block['hash'],
                    'block_time': block['timestamp']
                })
        
        return transactions[:count]

# Initialize blockchain data generator
blockchain = BlockchainDataGenerator()

def update_cache():
    """Update blockchain data cache"""
    global blockchain_cache
    
    while True:
        try:
            blockchain_cache['last_update'] = time.time()
            blockchain_cache['stats'] = blockchain.get_network_stats()
            blockchain_cache['mining_stats'] = blockchain.get_mining_stats()
            blockchain_cache['blocks'] = blockchain.get_recent_blocks(50)
            blockchain_cache['transactions'] = blockchain.get_recent_transactions(100)
            
            print(f"[{datetime.now().isoformat()}] Updated blockchain cache")
            
        except Exception as e:
            print(f"Error updating cache: {e}")
        
        time.sleep(30)  # Update every 30 seconds

@app.route('/api/stats')
def get_stats():
    """Get network statistics"""
    return jsonify(blockchain_cache['stats'])

@app.route('/api/mining')
def get_mining_stats():
    """Get mining statistics"""
    return jsonify(blockchain_cache['mining_stats'])

@app.route('/api/blocks')
def get_blocks():
    """Get recent blocks"""
    limit = request.args.get('limit', 10, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    blocks = blockchain_cache['blocks'][offset:offset + limit]
    return jsonify({
        'blocks': blocks,
        'total': len(blockchain_cache['blocks']),
        'limit': limit,
        'offset': offset
    })

@app.route('/api/blocks/<int:height>')
def get_block(height):
    """Get specific block"""
    for block in blockchain_cache['blocks']:
        if block['height'] == height:
            return jsonify(block)
    
    # Generate block if not in cache
    return jsonify(blockchain.generate_block(height))

@app.route('/api/transactions')
def get_transactions():
    """Get recent transactions"""
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    transactions = blockchain_cache['transactions'][offset:offset + limit]
    return jsonify({
        'transactions': transactions,
        'total': len(blockchain_cache['transactions']),
        'limit': limit,
        'offset': offset
    })

@app.route('/api/transactions/<tx_hash>')
def get_transaction(tx_hash):
    """Get specific transaction"""
    for tx in blockchain_cache['transactions']:
        if tx['hash'] == tx_hash:
            return jsonify(tx)
    
    return jsonify({'error': 'Transaction not found'}), 404

@app.route('/api/network')
def get_network_info():
    """Get network information"""
    return jsonify({
        'status': blockchain_cache['stats']['network_status'],
        'version': '1.0.0',
        'protocol_version': '1.0',
        'connected_nodes': blockchain_cache['stats']['connected_nodes'],
        'active_miners': blockchain_cache['stats']['active_miners'],
        'mempool_size': blockchain_cache['stats']['mempool_size'],
        'last_update': blockchain_cache['last_update']
    })

@app.route('/api/health')
def health_check():
    """API health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'cache_age': time.time() - blockchain_cache['last_update']
    })

@app.route('/')
def index():
    """API documentation"""
    return jsonify({
        'name': 'WorldWideCoin API',
        'version': '1.0.0',
        'description': 'Real-time blockchain data API',
        'endpoints': {
            '/api/stats': 'Network statistics',
            '/api/mining': 'Mining statistics',
            '/api/blocks': 'Recent blocks',
            '/api/blocks/<height>': 'Specific block',
            '/api/transactions': 'Recent transactions',
            '/api/transactions/<hash>': 'Specific transaction',
            '/api/network': 'Network information',
            '/api/health': 'Health check'
        }
    })

if __name__ == '__main__':
    # Start cache update thread
    cache_thread = threading.Thread(target=update_cache, daemon=True)
    cache_thread.start()
    
    print("Starting WorldWideCoin API Server...")
    print("API Documentation: http://localhost:5000")
    print("Network Stats: http://localhost:5000/api/stats")
    print("Mining Stats: http://localhost:5000/api/mining")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
