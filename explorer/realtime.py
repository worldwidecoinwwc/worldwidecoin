# explorer/realtime.py
import time
import json
import threading
import queue
from typing import Dict, List, Optional, Any, Callable
from flask_socketio import SocketIO, emit
from core.blockchain import Blockchain
from core.transaction import Transaction
from storage.utxo import UTXOSet


class RealTimeUpdates:
    """Real-time updates system for WorldWideCoin block explorer"""
    
    def __init__(self, blockchain: Blockchain, socketio: Optional[SocketIO] = None):
        self.blockchain = blockchain
        self.utxo_set = blockchain.utxo
        self.socketio = socketio
        
        # Event queue for updates
        self.event_queue = queue.Queue()
        self.subscribers = {}
        
        # Update intervals (seconds)
        self.update_intervals = {
            'network_stats': 30,
            'mempool': 10,
            'latest_blocks': 15,
            'latest_transactions': 15
        }
        
        # Background threads
        self.running = False
        self.update_threads = {}
        
        # Event callbacks
        self.event_callbacks = {}
        
        print("Real-time updates system initialized")
    
    def start(self):
        """Start real-time updates"""
        if self.running:
            return
        
        self.running = True
        print("Starting real-time updates...")
        
        # Start background update threads
        self._start_update_threads()
        
        # Start event processor
        event_thread = threading.Thread(target=self._process_events, daemon=True)
        event_thread.start()
        
        print("Real-time updates started")
    
    def stop(self):
        """Stop real-time updates"""
        if not self.running:
            return
        
        self.running = False
        print("Stopping real-time updates...")
        
        # Wait for threads to finish
        for thread in self.update_threads.values():
            thread.join(timeout=2)
        
        print("Real-time updates stopped")
    
    def _start_update_threads(self):
        """Start background update threads"""
        
        # Network stats updates
        network_thread = threading.Thread(
            target=self._network_stats_updater,
            daemon=True
        )
        network_thread.start()
        self.update_threads['network'] = network_thread
        
        # Mempool updates
        mempool_thread = threading.Thread(
            target=self._mempool_updater,
            daemon=True
        )
        mempool_thread.start()
        self.update_threads['mempool'] = mempool_thread
        
        # Latest blocks updates
        blocks_thread = threading.Thread(
            target=self._latest_blocks_updater,
            daemon=True
        )
        blocks_thread.start()
        self.update_threads['blocks'] = blocks_thread
        
        # Latest transactions updates
        tx_thread = threading.Thread(
            target=self._latest_transactions_updater,
            daemon=True
        )
        tx_thread.start()
        self.update_threads['transactions'] = tx_thread
    
    def _network_stats_updater(self):
        """Background thread for network stats updates"""
        while self.running:
            try:
                stats = self._get_network_stats()
                self._emit_event('network_stats', stats)
                time.sleep(self.update_intervals['network_stats'])
            except Exception as e:
                print(f"Network stats updater error: {e}")
                time.sleep(5)
    
    def _mempool_updater(self):
        """Background thread for mempool updates"""
        while self.running:
            try:
                mempool_info = self._get_mempool_info()
                self._emit_event('mempool', mempool_info)
                time.sleep(self.update_intervals['mempool'])
            except Exception as e:
                print(f"Mempool updater error: {e}")
                time.sleep(5)
    
    def _latest_blocks_updater(self):
        """Background thread for latest blocks updates"""
        while self.running:
            try:
                latest_blocks = self._get_latest_blocks()
                self._emit_event('latest_blocks', latest_blocks)
                time.sleep(self.update_intervals['latest_blocks'])
            except Exception as e:
                print(f"Latest blocks updater error: {e}")
                time.sleep(5)
    
    def _latest_transactions_updater(self):
        """Background thread for latest transactions updates"""
        while self.running:
            try:
                latest_transactions = self._get_latest_transactions()
                self._emit_event('latest_transactions', latest_transactions)
                time.sleep(self.update_intervals['latest_transactions'])
            except Exception as e:
                print(f"Latest transactions updater error: {e}")
                time.sleep(5)
    
    def _process_events(self):
        """Process events from queue"""
        while self.running:
            try:
                # Get event from queue
                event = self.event_queue.get(timeout=1)
                
                # Process event
                self._handle_event(event)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Event processor error: {e}")
    
    def _handle_event(self, event: Dict):
        """Handle individual event"""
        event_type = event.get('type')
        data = event.get('data')
        
        # Call registered callbacks
        if event_type in self.event_callbacks:
            for callback in self.event_callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"Event callback error: {e}")
        
        # Emit to WebSocket clients
        if self.socketio:
            self.socketio.emit(event_type, data)
    
    def _emit_event(self, event_type: str, data: Any):
        """Emit event to queue"""
        event = {
            'type': event_type,
            'data': data,
            'timestamp': time.time()
        }
        
        try:
            self.event_queue.put_nowait(event)
        except queue.Full:
            # Queue is full, drop oldest event
            try:
                self.event_queue.get_nowait()
                self.event_queue.put_nowait(event)
            except queue.Empty:
                pass
    
    def subscribe(self, client_id: str, event_types: List[str]):
        """Subscribe client to event types"""
        if client_id not in self.subscribers:
            self.subscribers[client_id] = set()
        
        self.subscribers[client_id].update(event_types)
        
        # Send current data for subscribed events
        for event_type in event_types:
            if event_type == 'network_stats':
                stats = self._get_network_stats()
                self._send_to_client(client_id, event_type, stats)
            elif event_type == 'mempool':
                mempool_info = self._get_mempool_info()
                self._send_to_client(client_id, event_type, mempool_info)
            elif event_type == 'latest_blocks':
                latest_blocks = self._get_latest_blocks()
                self._send_to_client(client_id, event_type, latest_blocks)
            elif event_type == 'latest_transactions':
                latest_transactions = self._get_latest_transactions()
                self._send_to_client(client_id, event_type, latest_transactions)
    
    def unsubscribe(self, client_id: str, event_types: List[str]):
        """Unsubscribe client from event types"""
        if client_id in self.subscribers:
            self.subscribers[client_id].difference_update(event_types)
            
            if not self.subscribers[client_id]:
                del self.subscribers[client_id]
    
    def unsubscribe_all(self, client_id: str):
        """Unsubscribe client from all events"""
        if client_id in self.subscribers:
            del self.subscribers[client_id]
    
    def add_event_callback(self, event_type: str, callback: Callable):
        """Add callback for event type"""
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
        
        self.event_callbacks[event_type].append(callback)
    
    def remove_event_callback(self, event_type: str, callback: Callable):
        """Remove callback for event type"""
        if event_type in self.event_callbacks:
            try:
                self.event_callbacks[event_type].remove(callback)
            except ValueError:
                pass
    
    def _send_to_client(self, client_id: str, event_type: str, data: Any):
        """Send data to specific client"""
        if self.socketio and client_id in self.subscribers:
            if event_type in self.subscribers[client_id]:
                self.socketio.emit(event_type, data, room=client_id)
    
    def _get_network_stats(self) -> Dict:
        """Get current network statistics"""
        if not self.blockchain.chain:
            return {
                'height': 0,
                'total_supply': 0.0,
                'difficulty': 1,
                'hash_rate': 0.0,
                'mempool_size': 0,
                'utxo_count': 0,
                'timestamp': time.time()
            }
        
        current_height = len(self.blockchain.chain)
        total_supply = sum(self._calculate_block_reward(block.index) for block in self.blockchain.chain)
        
        return {
            'height': current_height,
            'total_supply': total_supply,
            'difficulty': self.blockchain.get_difficulty() if hasattr(self.blockchain, 'get_difficulty') else 1,
            'hash_rate': self._estimate_hash_rate(),
            'mempool_size': len(self.blockchain.mempool.transactions),
            'mempool_bytes': sum(len(str(tx)) for tx in self.blockchain.mempool.transactions),
            'utxo_count': len(self.utxo_set.get_all_utxos()),
            'timestamp': time.time()
        }
    
    def _get_mempool_info(self) -> Dict:
        """Get current mempool information"""
        mempool = self.blockchain.mempool
        
        total_size = 0
        total_fees = 0
        tx_count = len(mempool.transactions)
        
        for tx in mempool.transactions:
            total_size += len(str(tx))
            if hasattr(tx, 'get_fee'):
                total_fees += tx.get_fee()
        
        return {
            'size': tx_count,
            'bytes': total_size,
            'total_fees': total_fees,
            'avg_fee': total_fees / tx_count if tx_count > 0 else 0,
            'timestamp': time.time()
        }
    
    def _get_latest_blocks(self) -> List[Dict]:
        """Get latest blocks"""
        if not self.blockchain.chain:
            return []
        
        latest_blocks = []
        start_idx = max(0, len(self.blockchain.chain) - 10)
        
        for block in self.blockchain.chain[start_idx:]:
            latest_blocks.append({
                'hash': block.calculate_hash() if hasattr(block, 'calculate_hash') else block.hash,
                'height': block.index,
                'timestamp': block.timestamp,
                'transactions': len(block.transactions),
                'size': len(str(block)),
                'difficulty': block.difficulty,
                'reward': self._calculate_block_reward(block.index)
            })
        
        return latest_blocks
    
    def _get_latest_transactions(self) -> List[Dict]:
        """Get latest transactions"""
        latest_transactions = []
        
        # Get transactions from latest blocks
        start_idx = max(0, len(self.blockchain.chain) - 5)
        
        for block in self.blockchain.chain[start_idx:]:
            for tx in block.transactions:
                latest_transactions.append({
                    'hash': tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash,
                    'block_hash': block.calculate_hash() if hasattr(block, 'calculate_hash') else block.hash,
                    'block_height': block.index,
                    'timestamp': block.timestamp,
                    'size': len(str(tx)),
                    'inputs': len(tx.inputs),
                    'outputs': len(tx.outputs),
                    'fee': self._calculate_tx_fee(tx) if hasattr(tx, 'get_fee') else 0,
                    'amount': sum(out.get('amount', 0) for out in tx.outputs)
                })
        
        # Sort by timestamp (newest first) and limit to 50
        latest_transactions.sort(key=lambda x: x['timestamp'], reverse=True)
        return latest_transactions[:50]
    
    def notify_new_block(self, block):
        """Notify about new block"""
        block_data = {
            'hash': block.calculate_hash() if hasattr(block, 'calculate_hash') else block.hash,
            'height': block.index,
            'timestamp': block.timestamp,
            'transactions': len(block.transactions),
            'size': len(str(block)),
            'difficulty': block.difficulty,
            'reward': self._calculate_block_reward(block.index)
        }
        
        self._emit_event('new_block', block_data)
    
    def notify_new_transaction(self, tx, block):
        """Notify about new transaction"""
        tx_data = {
            'hash': tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash,
            'block_hash': block.calculate_hash() if hasattr(block, 'calculate_hash') else block.hash,
            'block_height': block.index,
            'timestamp': block.timestamp,
            'size': len(str(tx)),
            'inputs': len(tx.inputs),
            'outputs': len(tx.outputs),
            'fee': self._calculate_tx_fee(tx) if hasattr(tx, 'get_fee') else 0,
            'amount': sum(out.get('amount', 0) for out in tx.outputs)
        }
        
        self._emit_event('new_transaction', tx_data)
    
    def notify_mempool_update(self, action: str, tx):
        """Notify about mempool update"""
        tx_data = {
            'hash': tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash,
            'size': len(str(tx)),
            'inputs': len(tx.inputs),
            'outputs': len(tx.outputs),
            'fee': self._calculate_tx_fee(tx) if hasattr(tx, 'get_fee') else 0,
            'amount': sum(out.get('amount', 0) for out in tx.outputs),
            'action': action  # 'added' or 'removed'
        }
        
        self._emit_event('mempool_update', tx_data)
    
    def get_subscriber_count(self) -> int:
        """Get number of active subscribers"""
        return len(self.subscribers)
    
    def get_subscription_stats(self) -> Dict:
        """Get subscription statistics"""
        stats = {
            'total_subscribers': len(self.subscribers),
            'subscriptions_by_type': {},
            'total_subscriptions': 0
        }
        
        for client_id, event_types in self.subscribers.items():
            for event_type in event_types:
                if event_type not in stats['subscriptions_by_type']:
                    stats['subscriptions_by_type'][event_type] = 0
                stats['subscriptions_by_type'][event_type] += 1
                stats['total_subscriptions'] += 1
        
        return stats
    
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
    
    def _estimate_hash_rate(self) -> float:
        """Estimate network hash rate"""
        if not self.blockchain.chain:
            return 0.0
        
        latest_block = self.blockchain.chain[-1]
        difficulty = latest_block.difficulty
        
        target_time = 600  # 10 minutes
        return difficulty * (2 ** 32) / target_time


class WebSocketHandler:
    """WebSocket handler for real-time updates"""
    
    def __init__(self, realtime: RealTimeUpdates):
        self.realtime = realtime
        self.socketio = SocketIO()
        self._setup_socketio_events()
    
    def _setup_socketio_events(self):
        """Setup SocketIO event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            print(f"Client connected")
            emit('connected', {'message': 'Connected to WorldWideCoin real-time updates'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print(f"Client disconnected")
        
        @self.socketio.on('subscribe')
        def handle_subscribe(data):
            """Subscribe to real-time updates"""
            client_id = request.sid if hasattr(request, 'sid') else 'default'
            event_types = data.get('events', [])
            
            self.realtime.subscribe(client_id, event_types)
            emit('subscribed', {'events': event_types})
        
        @self.socketio.on('unsubscribe')
        def handle_unsubscribe(data):
            """Unsubscribe from real-time updates"""
            client_id = request.sid if hasattr(request, 'sid') else 'default'
            event_types = data.get('events', [])
            
            self.realtime.unsubscribe(client_id, event_types)
            emit('unsubscribed', {'events': event_types})
        
        @self.socketio.on('get_network_stats')
        def handle_get_network_stats():
            """Get current network stats"""
            stats = self.realtime._get_network_stats()
            emit('network_stats', stats)
        
        @self.socketio.on('get_mempool_info')
        def handle_get_mempool_info():
            """Get current mempool info"""
            mempool_info = self.realtime._get_mempool_info()
            emit('mempool', mempool_info)
        
        @self.socketio.on('get_latest_blocks')
        def handle_get_latest_blocks():
            """Get latest blocks"""
            blocks = self.realtime._get_latest_blocks()
            emit('latest_blocks', blocks)
        
        @self.socketio.on('get_latest_transactions')
        def handle_get_latest_transactions():
            """Get latest transactions"""
            transactions = self.realtime._get_latest_transactions()
            emit('latest_transactions', transactions)
    
    def get_socketio(self) -> SocketIO:
        """Get SocketIO instance"""
        return self.socketio


def create_realtime_updates(blockchain: Blockchain, socketio: Optional[SocketIO] = None) -> RealTimeUpdates:
    """Create real-time updates system"""
    return RealTimeUpdates(blockchain, socketio)


def create_websocket_handler(realtime: RealTimeUpdates) -> WebSocketHandler:
    """Create WebSocket handler"""
    return WebSocketHandler(realtime)


# Utility functions
def start_realtime_updates(blockchain: Blockchain):
    """Start real-time updates system"""
    realtime = create_realtime_updates(blockchain)
    realtime.start()
    return realtime


def notify_new_block(blockchain: Blockchain, block):
    """Notify about new block (utility function)"""
    # This would be called when a new block is added to the blockchain
    if hasattr(blockchain, 'realtime_updates'):
        blockchain.realtime_updates.notify_new_block(block)


def notify_new_transaction(blockchain: Blockchain, tx, block):
    """Notify about new transaction (utility function)"""
    # This would be called when a new transaction is added to a block
    if hasattr(blockchain, 'realtime_updates'):
        blockchain.realtime_updates.notify_new_transaction(tx, block)
