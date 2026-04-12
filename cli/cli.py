#!/usr/bin/env python3
"""
WorldWideCoin CLI - Operator interface for blockchain operations
"""

import sys
import argparse
import json
from pathlib import Path

from core.blockchain import Blockchain
from wallet.wallet import Wallet
from core.transaction import Transaction
from network.node import Node


class WWCCli:
    def __init__(self):
        self.blockchain = Blockchain()
        self.wallet = Wallet()
        self.node = None

    def cmd_wallet_address(self, args):
        """Show wallet address"""
        print(f"📮 Your address: {self.wallet.address}")
        return 0

    def cmd_wallet_balance(self, args):
        """Check wallet balance"""
        balance = self.blockchain.utxo.get_balance(self.wallet.address)
        print(f"💰 Balance: {balance} WWC")
        return 0

    def cmd_wallet_create(self, args):
        """Generate new wallet (overwrites existing)"""
        self.wallet.create()
        self.wallet.save()
        print(f"✅ New wallet created: {self.wallet.address}")
        return 0

    def cmd_send(self, args):
        """Send transaction: send <to_address> <amount>"""
        if not args.to_address or not args.amount:
            print("❌ Usage: send <to_address> <amount>")
            return 1

        try:
            amount = float(args.amount)
            balance = self.blockchain.utxo.get_balance(self.wallet.address)

            if balance < amount:
                print(f"❌ Insufficient balance: {balance} < {amount}")
                return 1

            # Find spendable UTXOs
            spendable, total = self.blockchain.utxo.find_spendable_utxos(
                self.wallet.address, amount
            )

            if not spendable:
                print("❌ No spendable outputs found")
                return 1

            # Create transaction
            tx = Transaction(
                inputs=spendable,
                outputs=[
                    {"address": args.to_address, "amount": amount},
                    {"address": self.wallet.address, "amount": total - amount}  # Change
                ]
            )

            # Sign transaction
            tx.signature = self.wallet.sign(tx.to_dict())
            tx.public_key = self.wallet.public_key.to_string().hex()

            # Add to mempool
            self.blockchain.mempool.add_transaction(tx)

            print(f"✅ Transaction created: {tx.hash()}")
            print(f"   To: {args.to_address}")
            print(f"   Amount: {amount} WWC")
            return 0

        except Exception as e:
            print(f"❌ Error: {e}")
            return 1

    def cmd_mine(self, args):
        """Mine blocks: mine <count> [optional]"""
        count = int(args.count) if args.count else 1

        try:
            for i in range(count):
                print(f"⛏️  Mining block {i+1}/{count}...")
                block = self.blockchain.create_block(
                    miner_address=self.wallet.address,
                    reward=None
                )
                block.mine()
                self.blockchain.add_block(block)
                print(f"✅ Block {block.index} mined: {block.hash}")

            return 0
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1

    def cmd_node_info(self, args):
        """Show node and chain information"""
        height = len(self.blockchain.chain)
        last_block = self.blockchain.get_last_block()

        print(f"🌐 Node Information")
        print(f"   Chain height: {height}")
        print(f"   Tip hash: {last_block.hash}")
        print(f"   Tip difficulty: {last_block.difficulty}")
        print(f"   Mempool size: {len(self.blockchain.mempool.transactions)}")

        if self.node:
            print(f"   Peers connected: {len(self.node.peers)}")
            for peer in self.node.peers:
                print(f"      - {peer[0]}:{peer[1]}")

        return 0

    def cmd_node_connect(self, args):
        """Connect to peer: node-connect <host:port>"""
        if not args.peer:
            print("❌ Usage: node-connect <host:port>")
            return 1

        try:
            if not self.node:
                self.node = Node()

            host, port = args.peer.split(":")
            port = int(port)
            self.node.connect_peer(host, port)
            print(f"✅ Peer registered: {host}:{port}")
            return 0
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1

    def cmd_sync(self, args):
        """Sync chain with peers"""
        if not self.node or not self.node.peers:
            print("❌ No peers registered. Use 'node-connect' first.")
            return 1

        try:
            print(f"🔄 Syncing with {len(self.node.peers)} peer(s)...")
            for peer in self.node.peers:
                print(f"   Syncing with {peer[0]}:{peer[1]}...")
                self.node.sync_with_peer(peer)

            print(f"✅ Sync complete. Chain height: {len(self.blockchain.chain)}")
            return 0
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1

    def cmd_block(self, args):
        """Query block: block <height>"""
        if args.height is None:
            print("❌ Usage: block <height>")
            return 1

        try:
            height = int(args.height)
            if height < 0 or height >= len(self.blockchain.chain):
                print(f"❌ Invalid block height: {height}")
                return 1

            block = self.blockchain.chain[height]
            print(f"📦 Block {height}")
            print(f"   Hash: {block.hash}")
            print(f"   Prev hash: {block.prev_hash}")
            print(f"   Timestamp: {block.timestamp}")
            print(f"   Difficulty: {block.difficulty}")
            print(f"   Nonce: {block.nonce}")
            print(f"   Transactions: {len(block.transactions)}")

            for i, tx in enumerate(block.transactions):
                print(f"      {i}: {tx.hash()} ({len(tx.inputs)} in, {len(tx.outputs)} out)")

            return 0
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1

    def cmd_tx(self, args):
        """Query transaction: tx <txid>"""
        if not args.txid:
            print("❌ Usage: tx <txid>")
            return 1

        try:
            txid = args.txid
            found = False

            for block in self.blockchain.chain:
                for tx in block.transactions:
                    if tx.hash() == txid:
                        print(f"💸 Transaction {txid}")
                        print(f"   Inputs: {len(tx.inputs)}")
                        for inp in tx.inputs:
                            print(f"      - {inp['txid']}:{inp['index']} ({inp.get('amount', 0)} WWC)")

                        print(f"   Outputs: {len(tx.outputs)}")
                        for out in tx.outputs:
                            print(f"      - {out['address']}: {out['amount']} WWC")

                        print(f"   Fee: {tx.get_fee()}")
                        found = True
                        break

                if found:
                    break

            if not found:
                print(f"❌ Transaction not found: {txid}")
                return 1

            return 0
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1

    def cmd_mempool(self, args):
        """Show pending transactions"""
        txs = self.blockchain.mempool.transactions
        print(f"📋 Mempool ({len(txs)} transactions)")

        for i, tx in enumerate(txs):
            print(f"   {i+1}. {tx.hash()} ({len(tx.inputs)} in, {len(tx.outputs)} out, fee: {tx.get_fee()})")

        return 0

    def cmd_api(self, args):
        """Start REST API server: api [--host HOST] [--port PORT]"""
        try:
            from api.rest_api import WWCRestAPI

            host = args.host if args.host else "0.0.0.0"
            port = int(args.port) if args.port else 5000

            print(f"🌐 Starting REST API server on {host}:{port}")
            print("   Press Ctrl+C to stop")

            api = WWCRestAPI()
            api.run(host=host, port=port, debug=False)

            return 0
        except KeyboardInterrupt:
            print("\n🛑 REST API server stopped")
            return 0
        except Exception as e:
            print(f"❌ Error starting API server: {e}")
            return 1

            return 1

    def run(self):
        """Parse arguments and dispatch commands"""
        parser = argparse.ArgumentParser(
            description="WorldWideCoin CLI Operator Interface",
            prog="wwc"
        )

        subparsers = parser.add_subparsers(dest="command", help="Command to run")

        # Wallet commands
        subparsers.add_parser("wallet-address", help="Show wallet address")
        subparsers.add_parser("wallet-balance", help="Show wallet balance")
        subparsers.add_parser("wallet-create", help="Create new wallet")

        # Transaction commands
        send_parser = subparsers.add_parser("send", help="Send transaction")
        send_parser.add_argument("to_address", help="Recipient address")
        send_parser.add_argument("amount", help="Amount to send")

        # Mining commands
        mine_parser = subparsers.add_parser("mine", help="Mine blocks")
        mine_parser.add_argument("count", nargs="?", default=1, help="Number of blocks to mine")

        # Node commands
        subparsers.add_parser("node-info", help="Show node information")

        connect_parser = subparsers.add_parser("node-connect", help="Connect to peer")
        connect_parser.add_argument("peer", help="Peer address (host:port)")

        subparsers.add_parser("sync", help="Sync chain with peers")

        # Query commands
        block_parser = subparsers.add_parser("block", help="Query block")
        block_parser.add_argument("height", type=int, help="Block height")

        tx_parser = subparsers.add_parser("tx", help="Query transaction")
        tx_parser.add_argument("txid", help="Transaction ID")

        subparsers.add_parser("mempool", help="Show pending transactions")

        # API commands
        api_parser = subparsers.add_parser("api", help="Start REST API server")
        api_parser.add_argument("--host", help="Host to bind to (default: 0.0.0.0)")
        api_parser.add_argument("--port", type=int, help="Port to bind to (default: 5000)")

        # Parse and dispatch
        args = parser.parse_args()

        if not args.command:
            parser.print_help()
            return 1

        # Map commands to methods
        command_map = {
            "wallet-address": self.cmd_wallet_address,
            "wallet-balance": self.cmd_wallet_balance,
            "wallet-create": self.cmd_wallet_create,
            "send": self.cmd_send,
            "mine": self.cmd_mine,
            "node-info": self.cmd_node_info,
            "node-connect": self.cmd_node_connect,
            "sync": self.cmd_sync,
            "block": self.cmd_block,
            "tx": self.cmd_tx,
            "mempool": self.cmd_mempool,
            "api": self.cmd_api,
        }

        handler = command_map.get(args.command)
        if handler:
            return handler(args)
        else:
            print(f"❌ Unknown command: {args.command}")
            return 1


def main():
    cli = WWCCli()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()
