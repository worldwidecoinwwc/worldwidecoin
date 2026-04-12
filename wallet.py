import ecdsa
import hashlib
import binascii


class Wallet:

    def __init__(self):

        self.private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        self.public_key = self.private_key.get_verifying_key()

        self.address = self.generate_address()

    def generate_address(self):

        pubkey_bytes = self.public_key.to_string()

        sha = hashlib.sha256(pubkey_bytes).digest()
        ripemd = hashlib.new("ripemd160", sha).digest()

        return binascii.hexlify(ripemd).decode()

    def get_public_key(self):

        return self.public_key.to_string().hex()

    def sign(self, message):

        signature = self.private_key.sign(message.encode())

        return signature.hex()