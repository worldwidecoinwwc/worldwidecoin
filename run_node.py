import threading
import time
import argparse

from network.node import Node
from wallet.wallet import Wallet


def main():

    # ----------------------
    # ARGUMENTS
    # ----------------------
    parser = argparse.ArgumentParser()

    parser.add_argument("--port", type=int, default=8333)
    parser.add_argument("--peer", help="peer in format host:port")

    args = parser.parse_args()

    # ----------------------
    # INIT NODE + WALLET
    # ----------------------
    node = Node(port=args.port)
    wallet = Wallet()

    print(f"🌐 Node starting on port {args.port}")
    print(f"💰 Miner address: {wallet.address}")

    # ----------------------
    # CONNECT PEER (optional)
    # ----------------------
    if args.peer:
        try:
            host, port = args.peer.split(":")
            node.connect_peer(host, int(port))
            print(f"🔗 Connected to peer {host}:{port}")
        except:
            print("⚠ Invalid peer format. Use host:port")

    # ----------------------
    # MINER LOOP
    # ----------------------
    def miner():

        while True:

            try:
                # ⏳ Wait for transactions to enter mempool
                time.sleep(6)

                # Create block
                block = node.blockchain.create_block(wallet.address)

                print(f"📦 Mempool size: {len(block.transactions) - 1}")

                # Mine block
                print("⛏️ Mining block...")
                block.mine()

                # Add block to chain
                node.blockchain.add_block(block)

                print(f"✅ Block {block.index} mined | Hash: {block.hash[:10]}...")

            except Exception as e:
                print(f"❌ Miner error: {e}")
                time.sleep(3)

    # ----------------------
    # START THREADS
    # ----------------------
    miner_thread = threading.Thread(target=miner, daemon=True)
    miner_thread.start()

    # ----------------------
    # START NODE SERVER
    # ----------------------
    try:
        node.start()
    except KeyboardInterrupt:
        print("\n🛑 Node stopped")


# ----------------------
# ENTRY POINT
# ----------------------
if __name__ == "__main__":
    main()