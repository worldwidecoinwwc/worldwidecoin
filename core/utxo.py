import json
import os
import hashlib
import tempfile
import shutil
import time

UTXO_FILE = "utxo.json"
UTXO_BACKUP_FILE = "utxo_backup.json"


class UTXOSet:

    def __init__(self, persistent=True):
        self.utxos = {}
        self.persistent = persistent

        if self.persistent:
            self.load()

    def save(self):
        """Save UTXO set with simple write approach to avoid file locking"""
        if not self.persistent:
            return

        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Create backup if file exists and this is first attempt
                if attempt == 0 and os.path.exists(UTXO_FILE):
                    try:
                        shutil.copy2(UTXO_FILE, UTXO_BACKUP_FILE)
                    except:
                        pass  # Backup is optional
                
                # Simple direct write with retry logic
                with open(UTXO_FILE, 'w') as f:
                    json.dump(self.utxos, f, indent=2, separators=(',', ': '))
                    f.flush()
                # Success - exit retry loop
                return
                
            except Exception as e:
                if attempt == max_retries - 1:  # Last attempt failed
                    print(f"Error saving UTXO file after {max_retries} attempts: {e}")
                    # Try to restore from backup as last resort
                    if os.path.exists(UTXO_BACKUP_FILE):
                        try:
                            shutil.copy2(UTXO_BACKUP_FILE, UTXO_FILE)
                            print("Restored UTXO file from backup")
                        except:
                            print("Failed to restore UTXO backup")
                    # Don't raise exception to allow mining to continue
                    return
                else:
                    # Wait before retry
                    time.sleep(0.1)

    def load(self):
        """Load UTXO set with robust error handling and backup recovery"""
        if not self.persistent:
            return

        # Try to load main file first
        if os.path.exists(UTXO_FILE):
            try:
                with open(UTXO_FILE, 'r') as f:
                    content = f.read()
                    if content.strip():  # Check if file is not empty
                        self.utxos = json.loads(content)
                        return
                    else:
                        print("Warning: Empty UTXO file, starting fresh")
                        self.utxos = {}
                        return
            except (json.JSONDecodeError, IOError, ValueError) as e:
                print(f"Warning: Corrupted UTXO file: {e}")
                
                # Try to restore from backup
                if os.path.exists(UTXO_BACKUP_FILE):
                    try:
                        print("Attempting to restore from backup...")
                        with open(UTXO_BACKUP_FILE, 'r') as f:
                            content = f.read()
                            if content.strip():
                                self.utxos = json.loads(content)
                                # Restore the backup as main file
                                shutil.copy2(UTXO_BACKUP_FILE, UTXO_FILE)
                                print("Successfully restored from backup")
                                return
                            else:
                                print("Backup file is also empty")
                    except Exception as backup_error:
                        print(f"Failed to restore from backup: {backup_error}")
                
                # If both main and backup failed, start fresh
                print("Starting with fresh UTXO set")
                self.utxos = {}
                
                # Remove corrupted files
                for file_path in [UTXO_FILE, UTXO_BACKUP_FILE]:
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    except:
                        pass
        else:
            # No UTXO file exists, start fresh
            self.utxos = {}

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