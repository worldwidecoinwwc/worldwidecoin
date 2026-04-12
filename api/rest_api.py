#!/usr/bin/env python3
"""
WorldWideCoin REST API Server
Provides HTTP endpoints for blockchain operations
"""

from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
import json
from datetime import datetime

from core.blockchain import Blockchain
from wallet.wallet import Wallet
from core.transaction import Transaction
from network.node import Node
from config import Config


class WWCRestAPI:
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for web clients

        self.blockchain = Blockchain()
        self.wallet = Wallet()
        self.node = None
        self.config = Config()

        self.setup_routes()

    def setup_routes(self):
        """Setup all API routes"""

        def register_error_handlers():
            @self.app.errorhandler(HTTPException)
            def handle_http_exception(error):
                return jsonify({"error": error.description}), error.code

            @self.app.errorhandler(Exception)
            def handle_internal_error(error):
                return jsonify({"error": str(error)}), 500

        def parse_raw_transaction(data):
            if not data or 'inputs' not in data or 'outputs' not in data or 'signature' not in data or 'public_key' not in data:
                abort(400, "Missing raw transaction fields")

            return Transaction(
                inputs=data['inputs'],
                outputs=data['outputs'],
                signature=data['signature'],
                public_key=data['public_key']
            )

        def broadcast_transaction_raw(tx):
            if not tx.verify():
                abort(400, "Invalid transaction signature")
            if not self.blockchain.utxo.validate_transaction(tx):
                abort(400, "Invalid transaction UTXO state")
            self.blockchain.mempool.add_transaction(tx)
            return tx

        register_error_handlers()

        @self.app.route('/blocks', methods=['GET'])
        def get_blocks():
            """Get recent blocks (paginated)"""
            try:
                limit = min(int(request.args.get('limit', 10)), 50)  # Max 50 blocks
                offset = int(request.args.get('offset', 0))

                chain = self.blockchain.chain
                total = len(chain)

                if offset >= total:
                    return jsonify({"blocks": [], "total": total})

                start = max(0, total - offset - limit)
                end = total - offset

                blocks = []
                for i in range(start, end):
                    block = chain[i]
                    blocks.append({
                        "index": block.index,
                        "hash": block.hash,
                        "prev_hash": block.prev_hash,
                        "timestamp": block.timestamp,
                        "difficulty": block.difficulty,
                        "nonce": block.nonce,
                        "transactions": len(block.transactions)
                    })

                return jsonify({
                    "blocks": blocks,
                    "total": total,
                    "limit": limit,
                    "offset": offset
                })

            except HTTPException:
                raise
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/blocks/<int:height>', methods=['GET'])
        def get_block(height):
            """Get specific block by height"""
            try:
                if height < 0 or height >= len(self.blockchain.chain):
                    abort(404, "Block not found")

                block = self.blockchain.chain[height]

                transactions = []
                for tx in block.transactions:
                    transactions.append({
                        "id": tx.hash(),
                        "inputs": tx.inputs,
                        "outputs": tx.outputs,
                        "fee": tx.get_fee()
                    })

                return jsonify({
                    "index": block.index,
                    "hash": block.hash,
                    "prev_hash": block.prev_hash,
                    "timestamp": block.timestamp,
                    "difficulty": block.difficulty,
                    "nonce": block.nonce,
                    "transactions": transactions
                })

            except HTTPException:
                raise
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/tx/<txid>', methods=['GET'])
        def get_transaction(txid):
            """Get transaction by ID"""
            try:
                for block in self.blockchain.chain:
                    for tx in block.transactions:
                        if tx.hash() == txid:
                            return jsonify({
                                "id": tx.hash(),
                                "block_height": block.index,
                                "block_hash": block.hash,
                                "inputs": tx.inputs,
                                "outputs": tx.outputs,
                                "fee": tx.get_fee(),
                                "timestamp": block.timestamp
                            })

                abort(404, "Transaction not found")

            except HTTPException:
                raise
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/mempool', methods=['GET'])
        def get_mempool():
            """Get pending transactions"""
            try:
                transactions = []
                for tx in self.blockchain.mempool.transactions:
                    transactions.append({
                        "id": tx.hash(),
                        "inputs": tx.inputs,
                        "outputs": tx.outputs,
                        "fee": tx.get_fee()
                    })

                return jsonify({
                    "transactions": transactions,
                    "count": len(transactions)
                })

            except HTTPException:
                raise
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/wallet/balance', methods=['GET'])
        def get_balance():
            """Get wallet balance"""
            try:
                balance = self.blockchain.utxo.get_balance(self.wallet.address)
                return jsonify({
                    "address": self.wallet.address,
                    "balance": balance
                })

            except HTTPException:
                raise
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/wallet/address', methods=['GET'])
        def get_address():
            """Get wallet address"""
            try:
                return jsonify({
                    "address": self.wallet.address
                })

            except HTTPException:
                raise
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/tx', methods=['POST'])
        def submit_transaction():
            """Submit new transaction"""
            try:
                data = request.get_json()
                if not data:
                    abort(400, "Missing JSON data")

                # Raw signed transaction broadcast
                if 'inputs' in data and 'outputs' in data and 'signature' in data and 'public_key' in data:
                    tx = parse_raw_transaction(data)
                    tx = broadcast_transaction_raw(tx)

                    return jsonify({
                        "txid": tx.hash(),
                        "status": "broadcasted"
                    })

                # Legacy server-side send from API wallet
                if 'to_address' not in data or 'amount' not in data:
                    abort(400, "Missing 'to_address' or 'amount'")

                to_address = data['to_address']
                amount = float(data['amount'])

                if amount <= 0:
                    abort(400, "Amount must be positive")

                balance = self.blockchain.utxo.get_balance(self.wallet.address)
                if balance < amount:
                    abort(400, f"Insufficient balance: {balance} < {amount}")

                spendable, total = self.blockchain.utxo.find_spendable_utxos(
                    self.wallet.address, amount
                )

                if not spendable:
                    abort(400, "No spendable outputs found")

                tx = Transaction(
                    inputs=spendable,
                    outputs=[
                        {"address": to_address, "amount": amount},
                        {"address": self.wallet.address, "amount": total - amount}
                    ]
                )

                tx.signature = self.wallet.sign(tx.to_dict())
                tx.public_key = self.wallet.public_key.to_string().hex()

                self.blockchain.mempool.add_transaction(tx)

                return jsonify({
                    "txid": tx.hash(),
                    "status": "submitted",
                    "to": to_address,
                    "amount": amount
                })

            except HTTPException:
                raise
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/tx/broadcast', methods=['POST'])
        def broadcast_transaction():
            """Broadcast a raw signed transaction"""
            try:
                data = request.get_json()
                if not data:
                    abort(400, "Missing JSON data")

                tx = parse_raw_transaction(data)
                tx = broadcast_transaction_raw(tx)

                return jsonify({
                    "txid": tx.hash(),
                    "status": "broadcasted"
                })

            except HTTPException:
                raise
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/mine', methods=['POST'])
        def trigger_mining():
            """Trigger block mining"""
            try:
                count = int(request.args.get('count', 1))

                if count < 1 or count > 10:
                    abort(400, "Count must be between 1 and 10")

                blocks_mined = []
                for i in range(count):
                    block = self.blockchain.create_block(
                        miner_address=self.wallet.address,
                        reward=None
                    )
                    block.mine()
                    self.blockchain.add_block(block)

                    blocks_mined.append({
                        "index": block.index,
                        "hash": block.hash,
                        "transactions": len(block.transactions)
                    })

                return jsonify({
                    "blocks_mined": blocks_mined,
                    "count": len(blocks_mined)
                })

            except HTTPException:
                raise
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/peers', methods=['GET'])
        def get_peers():
            """Get connected peers"""
            try:
                peers = []
                if self.node:
                    peers = [f"{peer[0]}:{peer[1]}" for peer in self.node.peers]
                else:
                    peers = self.config.get_peers()

                return jsonify({
                    "peers": peers,
                    "count": len(peers)
                })

            except HTTPException:
                raise
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/peer', methods=['POST'])
        def add_peer():
            """Add a new peer to configuration"""
            try:
                data = request.get_json()
                if not data or 'host' not in data or 'port' not in data:
                    abort(400, "Missing 'host' or 'port'")

                host = data['host']
                port = int(data['port'])
                self.config.add_peer(host, port)

                return jsonify({
                    "status": "added",
                    "peer": f"{host}:{port}"
                })

            except HTTPException:
                raise
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/node/info', methods=['GET'])
        def get_node_info():
            """Get node information"""
            try:
                height = len(self.blockchain.chain)
                last_block = self.blockchain.get_last_block()

                return jsonify({
                    "chain_height": height,
                    "tip_hash": last_block.hash,
                    "tip_difficulty": last_block.difficulty,
                    "mempool_size": len(self.blockchain.mempool.transactions),
                    "peers_count": len(self.node.peers) if self.node else len(self.config.get_peers())
                })

            except HTTPException:
                raise
            except HTTPException:
                raise
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/status', methods=['GET'])
        def get_status():
            """Get node status"""
            return get_node_info()

        @self.app.route('/metrics', methods=['GET'])
        def get_metrics():
            """Get node metrics"""
            return jsonify({
                "chain_height": len(self.blockchain.chain),
                "mempool_size": len(self.blockchain.mempool.transactions),
                "utxo_count": len(self.blockchain.utxo.utxos),
                "peer_count": len(self.node.peers) if self.node else len(self.config.get_peers()),
                "version": "1.0.0"
            })

        # Additional endpoints for web dashboard compatibility
        @self.app.route('/chain', methods=['GET'])
        def get_chain():
            """Get blockchain data (alias for /blocks)"""
            return get_blocks()

        @self.app.route('/utxo/<address>', methods=['GET'])
        def get_address_balance(address):
            """Get balance for an address"""
            try:
                # Get all UTXOs for this address
                utxos = []
                for block in self.blockchain.chain:
                    for tx in block.transactions:
                        for i, output in enumerate(tx.outputs):
                            if output.get("address") == address:
                                utxos.append({
                                    "txid": tx.hash(),
                                    "vout": i,
                                    "amount": output.get("amount"),
                                    "address": output.get("address")
                                })

                total_balance = sum(utxo["amount"] for utxo in utxos)

                return jsonify({
                    "address": address,
                    "balance": total_balance,
                    "utxos": utxos
                })

            except HTTPException:
                raise
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/history/<address>', methods=['GET'])
        def get_address_history(address):
            """Get transaction history for an address"""
            try:
                history = []
                for block in self.blockchain.chain:
                    for tx in block.transactions:
                        is_sender = any(inp.get("address") == address for inp in tx.inputs)
                        is_receiver = any(out.get("address") == address for out in tx.outputs)
                        if not (is_sender or is_receiver):
                            continue

                        amount = sum(out.get("amount", 0) for out in tx.outputs if out.get("address") == address)
                        spent = sum(inp.get("amount", 0) for inp in tx.inputs if inp.get("address") == address)

                        history.append({
                            "id": tx.hash(),
                            "block_height": block.index,
                            "block_hash": block.hash,
                            "timestamp": block.timestamp,
                            "type": "sent" if is_sender else "received",
                            "amount": round(amount - spent, 8),
                            "inputs": tx.inputs,
                            "outputs": tx.outputs
                        })

                return jsonify({
                    "address": address,
                    "transactions": history
                })

            except HTTPException:
                raise
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/mining/status', methods=['GET'])
        def get_mining_status():
            """Get mining status"""
            try:
                return jsonify({
                    "is_mining": False,  # TODO: Implement actual mining status
                    "hash_rate": 0,
                    "blocks_mined": len(self.blockchain.chain) - 1,  # Genesis block doesn't count
                    "difficulty": self.blockchain.get_difficulty()
                })

            except HTTPException:
                raise
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0"
            })

    def run(self, host="0.0.0.0", port=5000, debug=False):
        """Run the API server"""
        print(f"🚀 Starting WorldWideCoin REST API on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug, use_reloader=False, threaded=True)


def main():
    api = WWCRestAPI()
    api.run()


if __name__ == "__main__":
    main()
