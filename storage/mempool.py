import threading


class Mempool:

    def __init__(self, utxo=None):
        self.transactions = []
        self.lock = threading.Lock()
        self.utxo = utxo

    def add_transaction(self, tx):
        with self.lock:
            if self.utxo:
                if not tx.verify():
                    raise Exception("Invalid transaction signature")
                if not self.utxo.validate_transaction(tx):
                    raise Exception("Invalid transaction UTXO state")

            self.transactions.append(tx)

    def get_transactions(self):
        with self.lock:
            return self.transactions[:]   # ✅ DO NOT CLEAR

    def clear(self):
        with self.lock:
            self.transactions = []