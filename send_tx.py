import socket
import json

from wallet.wallet import Wallet
from core.transaction import Transaction


# create wallets
sender = Wallet()
receiver = Wallet()

# create transaction
tx = Transaction(
    inputs=[],  # simplified for now
    outputs=[
        {"address": receiver.address, "amount": 5}
    ]
)

# sign transaction
tx.signature = sender.sign(tx.to_dict())
tx.public_key = sender.public_key.to_string().hex()

message = {
    "type": "transaction",
    "data": tx.to_dict()
}

# send to node
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("127.0.0.1", 8333))

sock.send(json.dumps(message).encode())
sock.close()

print("🚀 Transaction sent")