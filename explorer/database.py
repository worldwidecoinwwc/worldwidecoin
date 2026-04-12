# explorer/database.py
import sqlite3
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from core.blockchain import Blockchain
from core.transaction import Transaction
from storage.utxo import UTXOSet


class BlockExplorerDatabase:
    """Database for block explorer with indexing and search capabilities"""
    
    def __init__(self, db_path: str = "explorer.db"):
        self.db_path = db_path
        self.connection = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database schema"""
        self.connection = sqlite3.connect(self.db_path)
        cursor = self.connection.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hash TEXT UNIQUE NOT NULL,
                height INTEGER UNIQUE NOT NULL,
                timestamp INTEGER NOT NULL,
                size INTEGER NOT NULL,
                difficulty INTEGER NOT NULL,
                nonce INTEGER NOT NULL,
                prev_hash TEXT NOT NULL,
                merkle_root TEXT,
                reward REAL NOT NULL,
                fees REAL NOT NULL,
                tx_count INTEGER NOT NULL,
                data TEXT NOT NULL,
                created_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tx_hash TEXT UNIQUE NOT NULL,
                block_hash TEXT NOT NULL,
                block_height INTEGER NOT NULL,
                timestamp INTEGER NOT NULL,
                size INTEGER NOT NULL,
                inputs_count INTEGER NOT NULL,
                outputs_count INTEGER NOT NULL,
                fee REAL NOT NULL,
                value REAL NOT NULL,
                data TEXT NOT NULL,
                created_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transaction_inputs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tx_hash TEXT NOT NULL,
                input_index INTEGER NOT NULL,
                prev_tx_hash TEXT NOT NULL,
                prev_output_index INTEGER NOT NULL,
                script_sig TEXT,
                sequence INTEGER NOT NULL,
                address TEXT,
                amount REAL NOT NULL,
                created_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transaction_outputs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tx_hash TEXT NOT NULL,
                output_index INTEGER NOT NULL,
                amount REAL NOT NULL,
                script_pubkey TEXT,
                address TEXT NOT NULL,
                spent BOOLEAN DEFAULT FALSE,
                spending_tx_hash TEXT,
                created_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS addresses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT UNIQUE NOT NULL,
                balance REAL DEFAULT 0.0,
                tx_count INTEGER DEFAULT 0,
                first_seen INTEGER,
                last_seen INTEGER,
                created_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS address_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT NOT NULL,
                tx_hash TEXT NOT NULL,
                block_height INTEGER NOT NULL,
                timestamp INTEGER NOT NULL,
                type TEXT NOT NULL, -- 'sent' or 'received'
                amount REAL NOT NULL,
                created_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT UNIQUE NOT NULL,
                value REAL NOT NULL,
                timestamp INTEGER NOT NULL,
                created_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_blocks_height ON blocks(height)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_blocks_timestamp ON blocks(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_block_hash ON transactions(block_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_block_height ON transactions(block_height)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transaction_inputs_address ON transaction_inputs(address)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transaction_outputs_address ON transaction_outputs(address)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transaction_outputs_spent ON transaction_outputs(spent)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_address_transactions_address ON address_transactions(address)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_address_transactions_timestamp ON address_transactions(timestamp)')
        
        self.connection.commit()
    
    def index_blockchain(self, blockchain: Blockchain):
        """Index entire blockchain"""
        print(f"Indexing {len(blockchain.chain)} blocks...")
        
        start_time = time.time()
        
        for block in blockchain.chain:
            self._index_block(block)
        
        end_time = time.time()
        print(f"Blockchain indexed in {end_time - start_time:.2f} seconds")
        
        # Update statistics
        self._update_statistics(blockchain)
    
    def _index_block(self, block):
        """Index a single block"""
        cursor = self.connection.cursor()
        
        block_hash = block.calculate_hash() if hasattr(block, 'calculate_hash') else block.hash
        
        # Insert block
        cursor.execute('''
            INSERT OR REPLACE INTO blocks 
            (hash, height, timestamp, size, difficulty, nonce, prev_hash, merkle_root, reward, fees, tx_count, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            block_hash,
            block.index,
            int(block.timestamp),
            len(str(block)),
            block.difficulty,
            block.nonce,
            block.prev_hash,
            getattr(block, 'merkle_root', ''),
            self._calculate_block_reward(block.index),
            self._calculate_block_fees(block),
            len(block.transactions),
            json.dumps(self._serialize_block(block))
        ))
        
        # Index transactions
        for tx in block.transactions:
            self._index_transaction(tx, block)
        
        self.connection.commit()
    
    def _index_transaction(self, tx, block):
        """Index a single transaction"""
        cursor = self.connection.cursor()
        
        tx_hash = tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash
        block_hash = block.calculate_hash() if hasattr(block, 'calculate_hash') else block.hash
        
        # Calculate transaction value and fee
        total_input = 0.0
        total_output = 0.0
        
        for inp in tx.inputs:
            if 'amount' in inp:
                total_input += inp['amount']
        
        for out in tx.outputs:
            if 'amount' in out:
                total_output += out['amount']
        
        fee = total_input - total_output
        
        # Insert transaction
        cursor.execute('''
            INSERT OR REPLACE INTO transactions 
            (tx_hash, block_hash, block_height, timestamp, size, inputs_count, outputs_count, fee, value, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            tx_hash,
            block_hash,
            block.index,
            int(block.timestamp),
            len(str(tx)),
            len(tx.inputs),
            len(tx.outputs),
            fee,
            total_output,
            json.dumps(self._serialize_transaction(tx))
        ))
        
        # Index inputs
        for i, inp in enumerate(tx.inputs):
            cursor.execute('''
                INSERT INTO transaction_inputs 
                (tx_hash, input_index, prev_tx_hash, prev_output_index, script_sig, sequence, address, amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tx_hash,
                i,
                inp.get('txid', ''),
                inp.get('vout', 0),
                inp.get('script_sig', ''),
                inp.get('sequence', 4294967295),
                inp.get('address', ''),
                inp.get('amount', 0.0)
            ))
        
        # Index outputs
        for i, out in enumerate(tx.outputs):
            cursor.execute('''
                INSERT INTO transaction_outputs 
                (tx_hash, output_index, amount, script_pubkey, address)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                tx_hash,
                i,
                out.get('amount', 0.0),
                out.get('script_pubkey', ''),
                out.get('address', '')
            ))
            
            # Update address
            address = out.get('address', '')
            if address:
                self._update_address(address, block.timestamp, out.get('amount', 0.0))
        
        self.connection.commit()
    
    def _update_address(self, address: str, timestamp: int, amount: float):
        """Update address record"""
        cursor = self.connection.cursor()
        
        # Check if address exists
        cursor.execute('SELECT balance, tx_count, first_seen FROM addresses WHERE address = ?', (address,))
        result = cursor.fetchone()
        
        if result:
            balance, tx_count, first_seen = result
            new_balance = balance + amount
            new_tx_count = tx_count + 1
            new_first_seen = min(first_seen, timestamp)
            
            cursor.execute('''
                UPDATE addresses 
                SET balance = ?, tx_count = ?, first_seen = ?, last_seen = ?
                WHERE address = ?
            ''', (new_balance, new_tx_count, new_first_seen, timestamp, address))
        else:
            cursor.execute('''
                INSERT INTO addresses (address, balance, tx_count, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?)
            ''', (address, amount, 1, timestamp, timestamp))
    
    def _update_statistics(self, blockchain: Blockchain):
        """Update network statistics"""
        cursor = self.connection.cursor()
        current_time = int(time.time())
        
        # Calculate statistics
        total_blocks = len(blockchain.chain)
        total_txs = sum(len(block.transactions) for block in blockchain.chain)
        total_supply = sum(self._calculate_block_reward(block.index) for block in blockchain.chain)
        
        # Insert statistics
        stats = [
            ('total_blocks', total_blocks),
            ('total_transactions', total_txs),
            ('total_supply', total_supply),
            ('hash_rate', self._estimate_hash_rate()),
            ('difficulty', blockchain.get_difficulty() if hasattr(blockchain, 'get_difficulty') else 1),
            ('utxo_count', len(blockchain.utxo.get_all_utxos())),
            ('mempool_size', len(blockchain.mempool.transactions))
        ]
        
        for metric_name, value in stats:
            cursor.execute('''
                INSERT OR REPLACE INTO statistics (metric_name, value, timestamp)
                VALUES (?, ?, ?)
            ''', (metric_name, value, current_time))
        
        self.connection.commit()
    
    def get_block_by_hash(self, block_hash: str) -> Optional[Dict]:
        """Get block by hash"""
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM blocks WHERE hash = ?', (block_hash,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_block_dict(row)
        return None
    
    def get_block_by_height(self, height: int) -> Optional[Dict]:
        """Get block by height"""
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM blocks WHERE height = ?', (height,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_block_dict(row)
        return None
    
    def get_blocks_paginated(self, page: int, limit: int, sort: str = 'desc') -> Dict:
        """Get paginated blocks"""
        cursor = self.connection.cursor()
        
        order = 'DESC' if sort == 'desc' else 'ASC'
        offset = (page - 1) * limit
        
        cursor.execute(f'''
            SELECT * FROM blocks 
            ORDER BY height {order}
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        rows = cursor.fetchall()
        
        cursor.execute('SELECT COUNT(*) FROM blocks')
        total = cursor.fetchone()[0]
        
        return {
            'blocks': [self._row_to_block_dict(row) for row in rows],
            'page': page,
            'limit': limit,
            'total': total,
            'pages': (total + limit - 1) // limit
        }
    
    def get_transaction_by_hash(self, tx_hash: str) -> Optional[Dict]:
        """Get transaction by hash"""
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM transactions WHERE tx_hash = ?', (tx_hash,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_transaction_dict(row)
        return None
    
    def get_address_info(self, address: str) -> Optional[Dict]:
        """Get address information"""
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM addresses WHERE address = ?', (address,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_address_dict(row)
        return None
    
    def get_address_transactions(self, address: str, page: int = 1, limit: int = 50) -> Dict:
        """Get address transaction history"""
        cursor = self.connection.cursor()
        
        offset = (page - 1) * limit
        
        cursor.execute('''
            SELECT t.*, at.type, at.amount
            FROM transactions t
            JOIN address_transactions at ON t.tx_hash = at.tx_hash
            WHERE at.address = ?
            ORDER BY at.timestamp DESC
            LIMIT ? OFFSET ?
        ''', (address, limit, offset))
        
        rows = cursor.fetchall()
        
        cursor.execute('''
            SELECT COUNT(*)
            FROM address_transactions
            WHERE address = ?
        ''', (address,))
        total = cursor.fetchone()[0]
        
        return {
            'transactions': [self._row_to_transaction_dict(row) for row in rows],
            'page': page,
            'limit': limit,
            'total': total,
            'pages': (total + limit - 1) // limit
        }
    
    def get_address_utxos(self, address: str) -> List[Dict]:
        """Get address UTXOs"""
        cursor = self.connection.cursor()
        
        cursor.execute('''
            SELECT to.*
            FROM transaction_outputs to
            WHERE to.address = ? AND to.spent = FALSE
            ORDER BY to.created_at DESC
        ''', (address,))
        
        rows = cursor.fetchall()
        return [self._row_to_output_dict(row) for row in rows]
    
    def search(self, query: str, limit: int = 20) -> Dict:
        """Search blockchain"""
        results = {
            'blocks': [],
            'transactions': [],
            'addresses': []
        }
        
        cursor = self.connection.cursor()
        
        # Search blocks
        if len(query) == 64:
            cursor.execute('SELECT * FROM blocks WHERE hash = ? LIMIT 1', (query,))
            block_row = cursor.fetchone()
            if block_row:
                results['blocks'].append(self._row_to_block_dict(block_row))
        
        # Search transactions
        if len(query) == 64:
            cursor.execute('SELECT * FROM transactions WHERE tx_hash = ? LIMIT 1', (query,))
            tx_row = cursor.fetchone()
            if tx_row:
                results['transactions'].append(self._row_to_transaction_dict(tx_row))
        
        # Search addresses
        if len(query) >= 26:
            cursor.execute('SELECT * FROM addresses WHERE address = ? LIMIT 1', (query,))
            address_row = cursor.fetchone()
            if address_row:
                results['addresses'].append(self._row_to_address_dict(address_row))
        
        return results
    
    def get_statistics(self) -> Dict:
        """Get network statistics"""
        cursor = self.connection.cursor()
        cursor.execute('SELECT metric_name, value FROM statistics ORDER BY metric_name')
        rows = cursor.fetchall()
        
        stats = {}
        for metric_name, value in rows:
            stats[metric_name] = value
        
        return stats
    
    def get_latest_blocks(self, limit: int = 10) -> List[Dict]:
        """Get latest blocks"""
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM blocks ORDER BY height DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        
        return [self._row_to_block_dict(row) for row in rows]
    
    def get_latest_transactions(self, limit: int = 10) -> List[Dict]:
        """Get latest transactions"""
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM transactions ORDER BY timestamp DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        
        return [self._row_to_transaction_dict(row) for row in rows]
    
    def get_rich_addresses(self, limit: int = 100) -> List[Dict]:
        """Get richest addresses"""
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM addresses WHERE balance > 0 ORDER BY balance DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        
        return [self._row_to_address_dict(row) for row in rows]
    
    def _row_to_block_dict(self, row) -> Dict:
        """Convert database row to block dictionary"""
        columns = [desc[0] for desc in cursor.description]
        block_dict = dict(zip(columns, row))
        
        # Parse JSON data
        if 'data' in block_dict:
            block_dict['data'] = json.loads(block_dict['data'])
        
        return block_dict
    
    def _row_to_transaction_dict(self, row) -> Dict:
        """Convert database row to transaction dictionary"""
        columns = [desc[0] for desc in cursor.description]
        tx_dict = dict(zip(columns, row))
        
        # Parse JSON data
        if 'data' in tx_dict:
            tx_dict['data'] = json.loads(tx_dict['data'])
        
        return tx_dict
    
    def _row_to_address_dict(self, row) -> Dict:
        """Convert database row to address dictionary"""
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))
    
    def _row_to_output_dict(self, row) -> Dict:
        """Convert database row to output dictionary"""
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))
    
    def _serialize_block(self, block) -> Dict:
        """Serialize block for storage"""
        return {
            'hash': block.calculate_hash() if hasattr(block, 'calculate_hash') else block.hash,
            'height': block.index,
            'timestamp': block.timestamp,
            'transactions': [self._serialize_transaction(tx) for tx in block.transactions],
            'difficulty': block.difficulty,
            'nonce': block.nonce,
            'prev_hash': block.prev_hash
        }
    
    def _serialize_transaction(self, tx) -> Dict:
        """Serialize transaction for storage"""
        return {
            'hash': tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash,
            'inputs': tx.inputs,
            'outputs': tx.outputs,
            'signature': getattr(tx, 'signature', ''),
            'public_key': getattr(tx, 'public_key', '')
        }
    
    def _calculate_block_reward(self, block_height: int) -> float:
        """Calculate block reward"""
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
        # Simple estimation based on latest block difficulty
        cursor = self.connection.cursor()
        cursor.execute('SELECT difficulty FROM blocks ORDER BY height DESC LIMIT 1')
        row = cursor.fetchone()
        
        if row:
            difficulty = row[0]
            target_time = 600  # 10 minutes
            return difficulty * (2 ** 32) / target_time
        
        return 0.0
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def create_explorer_database(db_path: str = "explorer.db") -> BlockExplorerDatabase:
    """Create block explorer database instance"""
    return BlockExplorerDatabase(db_path)


# Utility functions
def index_blockchain_data(blockchain: Blockchain, db_path: str = "explorer.db"):
    """Index blockchain data into database"""
    with create_explorer_database(db_path) as db:
        db.index_blockchain(blockchain)
        print("Blockchain indexing completed")


def search_explorer_database(query: str, db_path: str = "explorer.db") -> Dict:
    """Search explorer database"""
    with create_explorer_database(db_path) as db:
        return db.search(query)
