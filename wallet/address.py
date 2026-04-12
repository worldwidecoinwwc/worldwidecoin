import hashlib


def pubkey_to_address(pubkey_bytes):

    sha = hashlib.sha256(pubkey_bytes).digest()

    ripemd = hashlib.new("ripemd160", sha).digest()

    return ripemd.hex()