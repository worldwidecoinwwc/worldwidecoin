import hashlib


def hash_pair(a, b):

    return hashlib.sha256((a + b).encode()).hexdigest()


def merkle_root(transactions):

    if len(transactions) == 0:
        return hashlib.sha256("empty".encode()).hexdigest()

    hashes = []

    for tx in transactions:

        tx_hash = tx.calculate_hash()

        hashes.append(tx_hash)

    while len(hashes) > 1:

        new_hashes = []

        for i in range(0, len(hashes), 2):

            left = hashes[i]

            if i + 1 < len(hashes):
                right = hashes[i + 1]
            else:
                right = left

            new_hashes.append(hash_pair(left, right))

        hashes = new_hashes

    return hashes[0]