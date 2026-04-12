import argparse
import socket
import json

from wallet.wallet import Wallet
from wallet.tx_builder import create_transaction
from core.utxo import UTXOSet


parser = argparse.ArgumentParser()
parser.add_argument("cmd")
parser.add_argument("--to")
parser.add_argument("--amount", type=float)
parser.add_argument("--fee", type=float, default=0.01)

args = parser.parse_args()

wallet = Wallet()
utxo = UTXOSet()


if args.cmd == "balance":

    print("\nAddress:", wallet.address)
    print("Balance:", utxo.get_balance(wallet.address))


elif args.cmd == "send":

    tx = create_transaction(wallet, utxo, args.to, args.amount, args.fee)

    message = json.dumps({
        "type": "tx",
        "data": tx.to_dict()
    }).encode()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("127.0.0.1", 8333))
    sock.send(message)
    sock.close()

    print("🚀 Transaction broadcasted")