# explorer/analytics.py
import time
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from core.blockchain import Blockchain
from storage.utxo import UTXOSet


class AnalyticsEngine:
    """Analytics engine for WorldWideCoin blockchain"""
    
    def __init__(self, blockchain: Blockchain, database=None):
        self.blockchain = blockchain
        self.utxo_set = blockchain.utxo
        self.database = database
        
        # Cache for analytics data
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes
    
    def get_network_overview(self) -> Dict:
        """Get network overview statistics"""
        cache_key = 'network_overview'
        if self._is_cached(cache_key):
            return self.cache[cache_key]
        
        overview = {
            'blockchain': self._get_blockchain_stats(),
            'network': self._get_network_stats(),
            'transactions': self._get_transaction_stats(),
            'addresses': self._get_address_stats(),
            'mining': self._get_mining_stats(),
            'timestamp': int(time.time())
        }
        
        self._cache_data(cache_key, overview)
        return overview
    
    def _get_blockchain_stats(self) -> Dict:
        """Get blockchain statistics"""
        if not self.blockchain.chain:
            return {
                'height': 0,
                'total_supply': 0.0,
                'difficulty': 1,
                'hash_rate': 0.0,
                'avg_block_time': 0.0
            }
        
        current_height = len(self.blockchain.chain)
        total_supply = sum(self._calculate_block_reward(block.index) for block in self.blockchain.chain)
        
        # Calculate average block time
        avg_block_time = 0.0
        if len(self.blockchain.chain) > 1:
            times = []
            for i in range(1, len(self.blockchain.chain)):
                times.append(self.blockchain.chain[i].timestamp - self.blockchain.chain[i-1].timestamp)
            avg_block_time = sum(times) / len(times)
        
        return {
            'height': current_height,
            'total_supply': total_supply,
            'difficulty': self.blockchain.get_difficulty() if hasattr(self.blockchain, 'get_difficulty') else 1,
            'hash_rate': self._estimate_hash_rate(),
            'avg_block_time': avg_block_time,
            'latest_block': self._format_block_summary(self.blockchain.chain[-1])
        }
    
    def _get_network_stats(self) -> Dict:
        """Get network statistics"""
        return {
            'utxo_count': len(self.utxo_set.get_all_utxos()),
            'mempool_size': len(self.blockchain.mempool.transactions),
            'mempool_bytes': sum(len(str(tx)) for tx in self.blockchain.mempool.transactions),
            'active_addresses': self._count_active_addresses(),
            'total_addresses': self._count_total_addresses(),
            'network_hashrate': self._estimate_hash_rate(),
            'difficulty': self.blockchain.get_difficulty() if hasattr(self.blockchain, 'get_difficulty') else 1
        }
    
    def _get_transaction_stats(self) -> Dict:
        """Get transaction statistics"""
        total_txs = sum(len(block.transactions) for block in self.blockchain.chain)
        
        if not self.blockchain.chain:
            return {
                'total_transactions': 0,
                'tx_rate': 0.0,
                'avg_tx_size': 0.0,
                'avg_fee': 0.0,
                'total_fees': 0.0
            }
        
        # Calculate transaction rate (tx/hour)
        time_span = self.blockchain.chain[-1].timestamp - self.blockchain.chain[0].timestamp
        tx_rate = (total_txs / time_span) * 3600 if time_span > 0 else 0
        
        # Calculate average transaction size
        total_size = sum(len(str(tx)) for block in self.blockchain.chain for tx in block.transactions)
        avg_tx_size = total_size / total_txs if total_txs > 0 else 0
        
        # Calculate average fee
        total_fees = sum(self._calculate_block_fees(block) for block in self.blockchain.chain)
        avg_fee = total_fees / total_txs if total_txs > 0 else 0
        
        return {
            'total_transactions': total_txs,
            'tx_rate': tx_rate,
            'avg_tx_size': avg_tx_size,
            'avg_fee': avg_fee,
            'total_fees': total_fees,
            'transactions_per_block': total_txs / len(self.blockchain.chain)
        }
    
    def _get_address_stats(self) -> Dict:
        """Get address statistics"""
        addresses = self._get_all_addresses()
        
        if not addresses:
            return {
                'total_addresses': 0,
                'active_addresses': 0,
                'rich_addresses': [],
                'address_distribution': {},
                'avg_balance': 0.0
            }
        
        balances = [self.utxo_set.get_balance(addr) for addr in addresses]
        active_addresses = [addr for addr in addresses if self.utxo_set.get_balance(addr) > 0]
        
        # Get rich addresses (top 10)
        rich_addresses = sorted(
            [{'address': addr, 'balance': self.utxo_set.get_balance(addr)} for addr in active_addresses],
            key=lambda x: x['balance'],
            reverse=True
        )[:10]
        
        # Address distribution
        distribution = {
            'empty': len([b for b in balances if b == 0]),
            'small': len([b for b in balances if 0 < b <= 1]),
            'medium': len([b for b in balances if 1 < b <= 10]),
            'large': len([b for b in balances if 10 < b <= 100]),
            'huge': len([b for b in balances if b > 100])
        }
        
        avg_balance = sum(balances) / len(balances) if balances else 0
        
        return {
            'total_addresses': len(addresses),
            'active_addresses': len(active_addresses),
            'rich_addresses': rich_addresses,
            'address_distribution': distribution,
            'avg_balance': avg_balance,
            'total_balance': sum(balances)
        }
    
    def _get_mining_stats(self) -> Dict:
        """Get mining statistics"""
        if not self.blockchain.chain:
            return {
                'total_mined': 0,
                'difficulty_trend': [],
                'block_rewards': [],
                'hashrate_trend': []
            }
        
        # Calculate difficulty trend (last 100 blocks)
        difficulty_trend = []
        rewards = []
        
        start_idx = max(0, len(self.blockchain.chain) - 100)
        for block in self.blockchain.chain[start_idx:]:
            difficulty_trend.append({
                'height': block.index,
                'difficulty': block.difficulty,
                'timestamp': block.timestamp
            })
            rewards.append({
                'height': block.index,
                'reward': self._calculate_block_reward(block.index),
                'fees': self._calculate_block_fees(block),
                'timestamp': block.timestamp
            })
        
        return {
            'total_mined': len(self.blockchain.chain),
            'difficulty_trend': difficulty_trend,
            'block_rewards': rewards,
            'current_difficulty': self.blockchain.chain[-1].difficulty,
            'avg_difficulty': sum(block.difficulty for block in self.blockchain.chain) / len(self.blockchain.chain)
        }
    
    def get_chart_data(self, chart_type: str, period: str = '24h') -> Dict:
        """Get chart data for analytics"""
        if chart_type == 'blocks':
            return self._get_blocks_chart(period)
        elif chart_type == 'transactions':
            return self._get_transactions_chart(period)
        elif chart_type == 'difficulty':
            return self._get_difficulty_chart(period)
        elif chart_type == 'hashrate':
            return self._get_hashrate_chart(period)
        elif chart_type == 'supply':
            return self._get_supply_chart(period)
        else:
            return {'error': f'Unknown chart type: {chart_type}'}
    
    def _get_blocks_chart(self, period: str) -> Dict:
        """Get blocks over time chart data"""
        time_range = self._get_time_range(period)
        blocks = self._get_blocks_in_range(time_range)
        
        # Group by hour
        hourly_data = defaultdict(int)
        for block in blocks:
            hour = datetime.fromtimestamp(block.timestamp).strftime('%Y-%m-%d %H:00')
            hourly_data[hour] += 1
        
        return {
            'type': 'blocks',
            'period': period,
            'data': [
                {'time': hour, 'count': count}
                for hour, count in sorted(hourly_data.items())
            ]
        }
    
    def _get_transactions_chart(self, period: str) -> Dict:
        """Get transactions over time chart data"""
        time_range = self._get_time_range(period)
        blocks = self._get_blocks_in_range(time_range)
        
        # Group by hour
        hourly_data = defaultdict(int)
        for block in blocks:
            hour = datetime.fromtimestamp(block.timestamp).strftime('%Y-%m-%d %H:00')
            hourly_data[hour] += len(block.transactions)
        
        return {
            'type': 'transactions',
            'period': period,
            'data': [
                {'time': hour, 'count': count}
                for hour, count in sorted(hourly_data.items())
            ]
        }
    
    def _get_difficulty_chart(self, period: str) -> Dict:
        """Get difficulty over time chart data"""
        time_range = self._get_time_range(period)
        blocks = self._get_blocks_in_range(time_range)
        
        return {
            'type': 'difficulty',
            'period': period,
            'data': [
                {
                    'time': datetime.fromtimestamp(block.timestamp).isoformat(),
                    'difficulty': block.difficulty,
                    'height': block.index
                }
                for block in blocks
            ]
        }
    
    def _get_hashrate_chart(self, period: str) -> Dict:
        """Get hash rate over time chart data"""
        time_range = self._get_time_range(period)
        blocks = self._get_blocks_in_range(time_range)
        
        return {
            'type': 'hashrate',
            'period': period,
            'data': [
                {
                    'time': datetime.fromtimestamp(block.timestamp).isoformat(),
                    'hashrate': self._estimate_hash_rate_for_difficulty(block.difficulty),
                    'height': block.index
                }
                for block in blocks
            ]
        }
    
    def _get_supply_chart(self, period: str) -> Dict:
        """Get total supply over time chart data"""
        time_range = self._get_time_range(period)
        blocks = self._get_blocks_in_range(time_range)
        
        cumulative_supply = 0
        supply_data = []
        
        for block in blocks:
            cumulative_supply += self._calculate_block_reward(block.index)
            supply_data.append({
                'time': datetime.fromtimestamp(block.timestamp).isoformat(),
                'supply': cumulative_supply,
                'height': block.index
            })
        
        return {
            'type': 'supply',
            'period': period,
            'data': supply_data
        }
    
    def get_address_analytics(self, address: str) -> Dict:
        """Get detailed analytics for an address"""
        balance = self.utxo_set.get_balance(address)
        utxos, _ = self.utxo_set.find_spendable_utxos(address, balance)
        
        # Get transaction history
        tx_history = self._get_address_transaction_history(address)
        
        # Calculate statistics
        total_sent = 0
        total_received = 0
        first_tx = None
        last_tx = None
        
        for tx_info in tx_history:
            if not first_tx:
                first_tx = tx_info
            last_tx = tx_info
            
            # This is simplified - would need to analyze inputs/outputs properly
            total_received += tx_info.get('amount', 0)
        
        return {
            'address': address,
            'balance': balance,
            'utxo_count': len(utxos),
            'transaction_count': len(tx_history),
            'total_sent': total_sent,
            'total_received': total_received,
            'first_transaction': first_tx,
            'last_transaction': last_tx,
            'activity': self._calculate_address_activity(tx_history),
            'rich_rank': self._get_address_rich_rank(address)
        }
    
    def get_block_analytics(self, block_hash: str) -> Dict:
        """Get detailed analytics for a block"""
        block = self._get_block_by_hash(block_hash)
        if not block:
            return {'error': 'Block not found'}
        
        # Calculate block statistics
        total_fees = self._calculate_block_fees(block)
        total_reward = self._calculate_block_reward(block.index)
        
        # Analyze transactions
        tx_stats = self._analyze_block_transactions(block)
        
        return {
            'block': self._format_block_summary(block),
            'reward': total_reward,
            'fees': total_fees,
            'total_value': total_reward + total_fees,
            'transaction_stats': tx_stats,
            'mining_time': self._estimate_mining_time(block),
            'difficulty': block.difficulty,
            'hash_rate': self._estimate_hash_rate_for_difficulty(block.difficulty)
        }
    
    def get_transaction_analytics(self, tx_hash: str) -> Dict:
        """Get detailed analytics for a transaction"""
        tx = self._get_transaction_by_hash(tx_hash)
        if not tx:
            return {'error': 'Transaction not found'}
        
        # Calculate transaction metrics
        total_input = sum(inp.get('amount', 0) for inp in tx.inputs)
        total_output = sum(out.get('amount', 0) for out in tx.outputs)
        fee = total_input - total_output
        
        return {
            'transaction': self._format_transaction_summary(tx),
            'fee': fee,
            'fee_rate': fee / len(str(tx)) if len(str(tx)) > 0 else 0,
            'total_input': total_input,
            'total_output': total_output,
            'size': len(str(tx)),
            'inputs_count': len(tx.inputs),
            'outputs_count': len(tx.outputs),
            'confirmations': self._get_transaction_confirmations(tx_hash),
            'addresses': self._get_transaction_addresses(tx)
        }
    
    def get_real_time_metrics(self) -> Dict:
        """Get real-time network metrics"""
        return {
            'current_height': len(self.blockchain.chain),
            'mempool_size': len(self.blockchain.mempool.transactions),
            'mempool_bytes': sum(len(str(tx)) for tx in self.blockchain.mempool.transactions),
            'hash_rate': self._estimate_hash_rate(),
            'difficulty': self.blockchain.get_difficulty() if hasattr(self.blockchain, 'get_difficulty') else 1,
            'total_supply': sum(self._calculate_block_reward(block.index) for block in self.blockchain.chain),
            'active_addresses': self._count_active_addresses(),
            'timestamp': int(time.time())
        }
    
    def _get_time_range(self, period: str) -> Tuple[float, float]:
        """Get time range for period"""
        now = time.time()
        
        if period == '1h':
            return now - 3600, now
        elif period == '24h':
            return now - 86400, now
        elif period == '7d':
            return now - 604800, now
        elif period == '30d':
            return now - 2592000, now
        else:
            return now - 86400, now  # Default to 24h
    
    def _get_blocks_in_range(self, time_range: Tuple[float, float]) -> List:
        """Get blocks within time range"""
        start_time, end_time = time_range
        return [block for block in self.blockchain.chain if start_time <= block.timestamp <= end_time]
    
    def _get_all_addresses(self) -> List[str]:
        """Get all addresses from blockchain"""
        addresses = set()
        
        for block in self.blockchain.chain:
            for tx in block.transactions:
                for out in tx.outputs:
                    if 'address' in out:
                        addresses.add(out['address'])
        
        return list(addresses)
    
    def _count_active_addresses(self) -> int:
        """Count addresses with non-zero balance"""
        addresses = self._get_all_addresses()
        return sum(1 for addr in addresses if self.utxo_set.get_balance(addr) > 0)
    
    def _count_total_addresses(self) -> int:
        """Count all unique addresses"""
        return len(self._get_all_addresses())
    
    def _get_address_transaction_history(self, address: str) -> List[Dict]:
        """Get transaction history for address"""
        history = []
        
        for block in self.blockchain.chain:
            for tx in block.transactions:
                tx_hash = tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash()
                
                # Check if transaction involves this address
                involves_address = False
                
                for out in tx.outputs:
                    if 'address' in out and out['address'] == address:
                        involves_address = True
                        break
                
                if involves_address:
                    history.append({
                        'tx_hash': tx_hash,
                        'block_height': block.index,
                        'timestamp': block.timestamp,
                        'amount': sum(out.get('amount', 0) for out in tx.outputs if out.get('address') == address)
                    })
        
        return sorted(history, key=lambda x: x['timestamp'], reverse=True)
    
    def _calculate_address_activity(self, tx_history: List[Dict]) -> Dict:
        """Calculate address activity metrics"""
        if not tx_history:
            return {'frequency': 0, 'avg_interval': 0, 'last_activity': 0}
        
        # Calculate transaction frequency (tx/day)
        time_span = tx_history[0]['timestamp'] - tx_history[-1]['timestamp']
        frequency = (len(tx_history) / time_span) * 86400 if time_span > 0 else 0
        
        # Calculate average interval between transactions
        intervals = []
        for i in range(1, len(tx_history)):
            intervals.append(tx_history[i-1]['timestamp'] - tx_history[i]['timestamp'])
        
        avg_interval = sum(intervals) / len(intervals) if intervals else 0
        
        return {
            'frequency': frequency,
            'avg_interval': avg_interval,
            'last_activity': tx_history[0]['timestamp']
        }
    
    def _get_address_rich_rank(self, address: str) -> int:
        """Get address rank by balance"""
        addresses = self._get_all_addresses()
        balances = [(addr, self.utxo_set.get_balance(addr)) for addr in addresses]
        balances.sort(key=lambda x: x[1], reverse=True)
        
        for rank, (addr, _) in enumerate(balances, 1):
            if addr == address:
                return rank
        
        return len(balances)
    
    def _analyze_block_transactions(self, block) -> Dict:
        """Analyze transactions in a block"""
        tx_sizes = [len(str(tx)) for tx in block.transactions]
        tx_fees = [self._calculate_tx_fee(tx) for tx in block.transactions]
        
        return {
            'count': len(block.transactions),
            'avg_size': sum(tx_sizes) / len(tx_sizes) if tx_sizes else 0,
            'total_size': sum(tx_sizes),
            'avg_fee': sum(tx_fees) / len(tx_fees) if tx_fees else 0,
            'total_fees': sum(tx_fees),
            'coinbase_tx': 1 if block.transactions and len(block.transactions[0].inputs) == 0 else 0
        }
    
    def _estimate_mining_time(self, block) -> float:
        """Estimate mining time for block"""
        difficulty = block.difficulty
        # Simplified estimation
        return difficulty * 10  # Rough estimate in seconds
    
    def _get_transaction_addresses(self, tx) -> List[str]:
        """Get all addresses involved in transaction"""
        addresses = []
        
        for out in tx.outputs:
            if 'address' in out:
                addresses.append(out['address'])
        
        return list(set(addresses))
    
    def _format_block_summary(self, block) -> Dict:
        """Format block summary"""
        return {
            'hash': block.calculate_hash() if hasattr(block, 'calculate_hash') else block.hash,
            'height': block.index,
            'timestamp': block.timestamp,
            'size': len(str(block)),
            'transactions': len(block.transactions),
            'difficulty': block.difficulty
        }
    
    def _format_transaction_summary(self, tx) -> Dict:
        """Format transaction summary"""
        return {
            'hash': tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash,
            'size': len(str(tx)),
            'inputs': len(tx.inputs),
            'outputs': len(tx.outputs),
            'fee': self._calculate_tx_fee(tx)
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
    
    def _get_transaction_confirmations(self, tx_hash: str) -> int:
        """Get transaction confirmations"""
        if not self.blockchain.chain:
            return 0
        
        current_height = len(self.blockchain.chain)
        
        for block in self.blockchain.chain:
            for tx in block.transactions:
                current_tx_hash = tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash()
                if current_tx_hash == tx_hash:
                    return current_height - block.index
        
        return 0
    
    def _calculate_tx_fee(self, tx) -> float:
        """Calculate transaction fee"""
        total_input = sum(inp.get('amount', 0) for inp in tx.inputs)
        total_output = sum(out.get('amount', 0) for out in tx.outputs)
        return total_input - total_output
    
    def _calculate_block_fees(self, block) -> float:
        """Calculate total fees in block"""
        return sum(self._calculate_tx_fee(tx) for tx in block.transactions)
    
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
        return self._estimate_hash_rate_for_difficulty(latest_block.difficulty)
    
    def _estimate_hash_rate_for_difficulty(self, difficulty: int) -> float:
        """Estimate hash rate from difficulty"""
        target_time = 600  # 10 minutes
        return difficulty * (2 ** 32) / target_time
    
    def _is_cached(self, key: str) -> bool:
        """Check if data is cached"""
        return key in self.cache and time.time() - self.cache[key]['timestamp'] < self.cache_timeout
    
    def _cache_data(self, key: str, data: Any):
        """Cache data"""
        self.cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def clear_cache(self):
        """Clear analytics cache"""
        self.cache.clear()


def create_analytics_engine(blockchain: Blockchain, database=None) -> AnalyticsEngine:
    """Create analytics engine instance"""
    return AnalyticsEngine(blockchain, database)


# Utility functions
def get_network_analytics(blockchain: Blockchain) -> Dict:
    """Get network analytics"""
    analytics = create_analytics_engine(blockchain)
    return analytics.get_network_overview()


def get_address_analytics(blockchain: Blockchain, address: str) -> Dict:
    """Get address analytics"""
    analytics = create_analytics_engine(blockchain)
    return analytics.get_address_analytics(address)


def get_block_analytics(blockchain: Blockchain, block_hash: str) -> Dict:
    """Get block analytics"""
    analytics = create_analytics_engine(blockchain)
    return analytics.get_block_analytics(block_hash)
