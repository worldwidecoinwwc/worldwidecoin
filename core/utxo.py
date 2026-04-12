import json
import os
import hashlib

UTXO_FILE = "utxo.json"


class UTXOSet:

    def __init__(self, persistent=True):
        self.utxos = {}
        self.persistent = persistent

        if self.persistent:
            self.load()

    def save(self):
        if not self.persistent:
            return

        with open(UTXO_FILE, "w") as f:
            json.dump(self.utxos, f)

    def load(self):
        if not self.persistent:
            return

        if os.path.exists(UTXO_FILE):
            try:
                with open(UTXO_FILE) as f:
                    self.utxos = json.load(f)
            except (json.JSONDecodeError, IOError, ValueError) as e:
                print(f"Warning: Corrupted UTXO file, starting fresh: {e}")
                self.utxos = {}
                # Remove corrupted file
                try:
                    os.remove(UTXO_FILE)
                except:
                    pass

    def add_utxo(self, txid, index, address, amount):
        self.utxos[f"{txid}:{index}"] = {
            "address": address,
            "amount": amount
        }

    def spend_utxo(self, txid, index):
        self.utxos.pop(f"{txid}:{index}", None)

    def get_balance(self, address):
        return sum(
            u["amount"] for u in self.utxos.values()
            if u["address"] == address
        )

    def has_utxo(self, txid, index):
        return f"{txid}:{index}" in self.utxos

    def get_utxo(self, txid, index):
        return self.utxos.get(f"{txid}:{index}")

    def validate_transaction(self, tx):
        # Coinbase: no inputs, always valid from UTXO perspective
        if len(tx.inputs) == 0:
            return True

        # Input duplicates should not appear within a single tx
        seen = set()

        total_input = 0
        for inp in tx.inputs:
            txid = inp.get("txid")
            idx = inp.get("index")
            amount = inp.get("amount", 0)

            if txid is None or idx is None:
                return False

            key = f"{txid}:{idx}"
            if key in seen:
                return False
            seen.add(key)

            utxo = self.get_utxo(txid, idx)
            if not utxo:
                return False

            if amount <= 0 or amount > utxo.get("amount", 0):
                return False

            # Check ownership via public key
            if tx.public_key:
                expected_address = hashlib.sha256(bytes.fromhex(tx.public_key)).hexdigest()
                if utxo["address"] != expected_address:
                    return False

            total_input += amount

        total_output = sum(out.get("amount", 0) for out in tx.outputs)

        # Output cannot exceed input (no negative fees)
        if total_output > total_input:
            return False

        return True

    def get_all_utxos(self):
        """Get all UTXOs"""
        return self.utxos.copy()

    def find_spendable_utxos(self, address, amount):

        total = 0
        selected = []

        for key, utxo in self.utxos.items():

            if utxo["address"] == address:

                txid, index = key.split(":")

                selected.append({
                    "txid": txid,
                    "index": int(index),
                    "amount": utxo["amount"]
                })

                total += utxo["amount"]

                if total >= amount:
                    break

        return selected, total

    def apply_transaction(self, tx, validate=True):

        if validate and not self.validate_transaction(tx):
            raise Exception("Invalid transaction UTXO state")

        for inp in tx.inputs:
            self.spend_utxo(inp["txid"], inp["index"])

        txid = tx.hash()

        for i, out in enumerate(tx.outputs):
            self.add_utxo(txid, i, out["address"], out["amount"])

        self.save()