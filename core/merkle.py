import hashlib
import json


def hash_data(data):

    return hashlib.sha256(
        json.dumps(data, sort_keys=True).encode()
    ).hexdigest()


def build_merkle_root(transactions):

    if len(transactions) == 0:
        return hash_data("empty")

    hashes = [hash_data(tx) for tx in transactions]

    while len(hashes) > 1:

        # duplicate last hash if odd
        if len(hashes) % 2 == 1:
            hashes.append(hashes[-1])

        new_level = []

        for i in range(0, len(hashes), 2):

            combined = hashes[i] + hashes[i + 1]

            new_hash = hashlib.sha256(
                combined.encode()
            ).hexdigest()

            new_level.append(new_hash)

        hashes = new_level

    return hashes[0]