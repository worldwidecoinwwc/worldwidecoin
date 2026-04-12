from flask import Flask, request, jsonify
import threading

from main import Blockchain
from transaction import Transaction, TxOutput
from p2p import P2PNode


app = Flask(__name__)

blockchain = Blockchain()

# --------------------------------
# P2P NETWORK
# --------------------------------

P2P_PORT = 6000

p2p = P2PNode("127.0.0.1", P2P_PORT, blockchain)

threading.Thread(target=p2p.start_server, daemon=True).start()


# --------------------------------
# VIEW BLOCKCHAIN
# --------------------------------

@app.route("/chain", methods=["GET"])
def chain():

    chain_data = []

    for block in blockchain.chain:

        chain_data.append({

            "index": block.index,
            "hash": block.hash,
            "previous_hash": block.previous_hash,
            "nonce": block.nonce,
            "transactions": [
                tx.calculate_hash() for tx in block.transactions
            ]

        })

    return jsonify({
        "length": len(chain_data),
        "chain": chain_data
    })


# --------------------------------
# MINE BLOCK
# --------------------------------

@app.route("/mine", methods=["GET"])
def mine():

    miner = request.args.get("miner")

    if miner is None:
        return jsonify({"error": "miner address required"}), 400

    blockchain.mine_pending_transactions(miner)

    latest_block = blockchain.chain[-1]

    # broadcast block to peers
    p2p.broadcast_block(vars(latest_block))

    return jsonify({
        "message": "Block mined and broadcasted"
    })


# --------------------------------
# ADD TRANSACTION
# --------------------------------

@app.route("/transaction", methods=["POST"])
def transaction():

    data = request.get_json()

    receiver = data.get("receiver")
    amount = data.get("amount")

    if receiver is None or amount is None:

        return jsonify({
            "error": "Invalid transaction"
        }), 400

    tx = Transaction([], [TxOutput(receiver, amount)])

    blockchain.mempool.append(tx)

    # broadcast transaction
    p2p.broadcast_transaction(tx.__dict__)

    return jsonify({
        "message": "Transaction added to mempool"
    })


# --------------------------------
# MEMPOOL
# --------------------------------

@app.route("/mempool", methods=["GET"])
def mempool():

    return jsonify({

        "transactions": [
            tx.calculate_hash() for tx in blockchain.mempool
        ]

    })


# --------------------------------
# CONNECT PEER
# --------------------------------

@app.route("/connect_peer", methods=["POST"])
def connect_peer():

    data = request.get_json()

    host = data.get("host")
    port = data.get("port")

    p2p.connect_peer(host, port)

    return jsonify({
        "message": "peer connected"
    })


# --------------------------------
# RUN NODE
# --------------------------------

if __name__ == "__main__":

    import sys

    port = 5000

    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    print("HTTP node running on port", port)
    print("P2P port:", P2P_PORT)

    app.run(host="127.0.0.1", port=port)