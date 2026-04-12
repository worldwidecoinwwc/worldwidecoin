from core.blockchain import Blockchain


def print_chain(blockchain):

    print("\n========= WORLDWIDECOIN BLOCKCHAIN =========\n")

    for block in blockchain.chain:

        print("Index:", block.index)
        print("Timestamp:", block.timestamp)
        print("Previous Hash:", block.previous_hash)
        print("Hash:", block.hash)
        print("Nonce:", block.nonce)
        print("Merkle Root:", block.merkle_root)
        print("Transactions:", block.transactions)

        print("------------------------------------")


def main():

    wwc = Blockchain()

    print("Genesis block created")

    print("\nMining block 1...")
    wwc.mine_pending_transactions("alice")

    tx = {
        "sender": "alice",
        "receiver": "bob",
        "amount": 0.5
    }

    wwc.add_transaction(tx)

    print("\nMining block 2...")
    wwc.mine_pending_transactions("alice")

    print("\nBalances")

    print("Alice:", wwc.get_balance("alice"))
    print("Bob:", wwc.get_balance("bob"))

    print_chain(wwc)


if __name__ == "__main__":
    main()