import os
import json
import hashlib
from ecdsa import SigningKey, SECP256k1

FILE = "wallet.json"


class Wallet:

    def __init__(self):

        if os.path.exists(FILE):
            self.load()
        else:
            self.create()
            self.save()

    def create(self):
        self.private_key = SigningKey.generate(curve=SECP256k1)
        self.public_key = self.private_key.get_verifying_key()
        self.address = hashlib.sha256(self.public_key.to_string()).hexdigest()

    def sign(self, data):
        payload = json.dumps(data, sort_keys=True).encode()
        digest = hashlib.sha256(payload).digest()
        return self.private_key.sign_digest(digest).hex()

    def sign_transaction(self, data):
        return self.sign(data)

    def save(self):
        with open(FILE, "w") as f:
            json.dump({"pk": self.private_key.to_string().hex()}, f)

    def load(self):
        with open(FILE) as f:
            data = json.load(f)

        self.private_key = SigningKey.from_string(bytes.fromhex(data["pk"]), curve=SECP256k1)
        self.public_key = self.private_key.get_verifying_key()
        self.address = hashlib.sha256(self.public_key.to_string()).hexdigest()