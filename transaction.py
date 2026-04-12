import hashlib
import json
import ecdsa


class TxInput:

    def __init__(self, txid, index):
        self.txid = txid
        self.index = index


class TxOutput:

    def __init__(self, receiver, amount):
        self.receiver = receiver
        self.amount = amount


class Transaction:

    def __init__(self, inputs, outputs, public_key=None, signature=None):

        self.inputs = inputs
        self.outputs = outputs
        self.public_key = public_key
        self.signature = signature

    def calculate_hash(self):

        data = json.dumps({
            "inputs": [i.__dict__ for i in self.inputs],
            "outputs": [o.__dict__ for o in self.outputs]
        }, sort_keys=True)

        return hashlib.sha256(data.encode()).hexdigest()

    def verify_signature(self):

        # Coinbase transaction (mining reward)
        if len(self.inputs) == 0:
            return True

        if self.signature is None or self.public_key is None:
            return False

        try:

            vk = ecdsa.VerifyingKey.from_string(
                bytes.fromhex(self.public_key),
                curve=ecdsa.SECP256k1
            )

            tx_hash = self.calculate_hash()

            return vk.verify(
                bytes.fromhex(self.signature),
                tx_hash.encode()
            )

        except Exception:
            return False