import hashlib
import json


class Block:

    def __init__(self, index, prev_hash, transactions, timestamp, difficulty):
        self.index = index
        self.prev_hash = prev_hash
        self.transactions = transactions
        self.timestamp = timestamp
        self.difficulty = difficulty
        self.nonce = 0
        self.hash = None

    def calculate_hash(self):

        txs = [tx.to_dict() for tx in self.transactions]

        return hashlib.sha256(json.dumps({
            "index": self.index,
            "prev_hash": self.prev_hash,
            "transactions": txs,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "difficulty": self.difficulty
        }, sort_keys=True).encode()).hexdigest()

    def mine(self):

        prefix = "0" * self.difficulty

        while True:
            self.hash = self.calculate_hash()
            if self.hash.startswith(prefix):
                return self.hash
            self.nonce += 1