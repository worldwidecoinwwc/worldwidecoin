import json
import os

CHAIN_FILE = "chain.json"


class ChainStore:

    def save_chain(self, chain):

        data = []

        for b in chain:
            data.append({
                "index": b.index,
                "prev_hash": b.prev_hash,
                "timestamp": b.timestamp,
                "difficulty": b.difficulty,
                "nonce": b.nonce,
                "hash": b.hash,
                "transactions": [tx.to_dict() for tx in b.transactions]
            })

        with open(CHAIN_FILE, "w") as f:
            json.dump(data, f)

    def load_chain(self):

        if not os.path.exists(CHAIN_FILE):
            return []
        
        try:
            with open(CHAIN_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, ValueError) as e:
            print(f"Warning: Corrupted chain file, starting fresh: {e}")
            # Remove corrupted file
            try:
                os.remove(CHAIN_FILE)
            except:
                pass
            return []