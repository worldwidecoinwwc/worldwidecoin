# C:\Users\jinum\worldwidecoin\core\transaction.py

import hashlib
import json
from ecdsa import VerifyingKey, SECP256k1


class Transaction:
    def __init__(self, inputs, outputs, signature=None, public_key=None):
        self.inputs = inputs or []
        self.outputs = outputs or []
        self.signature = signature
        self.public_key = public_key

    def to_dict(self):
        """
        Convert transaction to dictionary (used for hashing & signing)
        """
        return {
            "inputs": self.inputs,
            "outputs": self.outputs
        }

    def hash(self):
        """
        Generate SHA-256 hash of the transaction
        """
        tx_string = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(tx_string.encode()).hexdigest()

    def calculate_hash(self):
        """
        Generate SHA-256 hash of the transaction (alias for hash())
        """
        return self.hash()

    def get_fee(self):
        """
        Calculate transaction fee = total_input - total_output
        """
        total_input = sum(inp.get("amount", 0) for inp in self.inputs)
        total_output = sum(out.get("amount", 0) for out in self.outputs)
        return total_input - total_output

    def verify(self):
        """
        Verify transaction signature
        """

        # ✅ Coinbase transaction (mining reward)
        if len(self.inputs) == 0:
            return True

        # ❌ Missing signature or public key
        if not self.signature or not self.public_key:
            return False

        try:
            # Load public key
            vk = VerifyingKey.from_string(
                bytes.fromhex(self.public_key),
                curve=SECP256k1
            )

            # Prepare message digest
            message = json.dumps(self.to_dict(), sort_keys=True).encode()
            digest = hashlib.sha256(message).digest()

            # Verify signature over digest
            return vk.verify_digest(bytes.fromhex(self.signature), digest)

        except Exception:
            # Any failure → invalid transaction
            return False