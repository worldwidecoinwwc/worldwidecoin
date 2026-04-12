from flask import Flask, render_template, request, jsonify
import json
import os

from core.utxo import UTXOSet

app = Flask(__name__)

CHAIN_FILE = "chain.json"


def load_chain():
    if not os.path.exists(CHAIN_FILE):
        return []

    with open(CHAIN_FILE, "r") as f:
        return json.load(f)


# ----------------------
# HOME
# ----------------------
@app.route("/")
def index():
    chain = load_chain()

    total_blocks = len(chain)

    return render_template(
        "index.html",
        chain=list(reversed(chain))[:10],
        total_blocks=total_blocks
    )


# ----------------------
# BLOCK
# ----------------------
@app.route("/block/<int:index>")
def block(index):
    for b in load_chain():
        if b["index"] == index:
            return render_template("block.html", block=b)
    return "Block not found"


# ----------------------
# TRANSACTION PAGE
# ----------------------
@app.route("/tx/<txid>")
def tx(txid):

    for block in load_chain():
        for tx in block["transactions"]:
            # simple txid (hash of dict)
            if str(tx) == txid:
                return render_template("tx.html", tx=tx)

    return "Transaction not found"


# ----------------------
# ADDRESS
# ----------------------
@app.route("/address/<address>")
def address(address):
    utxo = UTXOSet()
    balance = utxo.get_balance(address)

    return render_template(
        "address.html",
        address=address,
        balance=balance
    )


# ----------------------
# SEARCH
# ----------------------
@app.route("/search")
def search():
    q = request.args.get("q")

    if q.isdigit():
        return f"/block/{q}"

    return f"/address/{q}"


# ----------------------
# API
# ----------------------
@app.route("/api/stats")
def stats():
    chain = load_chain()

    return jsonify({
        "blocks": len(chain),
        "last_block": chain[-1]["index"] if chain else 0
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)