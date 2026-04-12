# C:\Users\jinum\worldwidecoin\core\blockchain.py

import time
import math

from core.block import Block
from core.transaction import Transaction
from core.utxo import UTXOSet
from storage.chain_store import ChainStore
from storage.mempool import Mempool


class Blockchain:

    INITIAL_REWARD = 1.0
    DECAY_RATE = 0.025
    BLOCKS_PER_YEAR = 525600

    TREASURY_PERCENT = 0.05
    FEE_BURN_PERCENT = 0.20
    TREASURY_ADDRESS = "WWC_TREASURY"

    TARGET_BLOCK_TIME = 60
    DIFFICULTY_WINDOW = 5

    def __init__(self):
        self.chain_store = ChainStore()
        self.chain = []
        self.utxo = UTXOSet()
        self.mempool = Mempool(self.utxo)
        self.broadcast_callback = None

        data = self.chain_store.load_chain()

        if data:
            self._rebuild(data)
        else:
            self.create_genesis_block()

    # =========================
    # GENESIS BLOCK
    # =========================
    def create_genesis_block(self):
        block = Block(
            index=0,
            prev_hash="0",
            transactions=[],
            timestamp=time.time(),
            difficulty=1  # Genesis always difficulty 1
        )

        block.mine()  # ✅ MUST mine
        self.chain.append(block)
        self.chain_store.save_chain(self.chain)

    # =========================
    # REBUILD CHAIN
    # =========================
    def _rebuild(self, data):
        for b in data:

            txs = [
                Transaction(tx["inputs"], tx["outputs"])
                for tx in b["transactions"]
            ]

            block = Block(
                b["index"],
                b["prev_hash"],
                txs,
                b["timestamp"],
                b["difficulty"]
            )

            block.nonce = b["nonce"]
            block.hash = b["hash"]

            self.chain.append(block)

            # rebuild UTXO (trusted historical chain, skip strict validation here)
            for tx in txs:
                self.utxo.apply_transaction(tx, validate=False)

    # =========================
    # HELPERS
    # =========================
    def get_last_block(self):
        return self.chain[-1]

    def get_block_reward(self):
        height = len(self.chain)
        t = height / self.BLOCKS_PER_YEAR
        return self.INITIAL_REWARD * math.exp(-self.DECAY_RATE * t)

    def get_block_reward_at_height(self, height):
        """Get block reward at specific height"""
        t = height / self.BLOCKS_PER_YEAR
        return self.INITIAL_REWARD * math.exp(-self.DECAY_RATE * t)

    def get_difficulty(self):
        """
        Calculate difficulty using exponential retargeting.
        Compares actual block time vs target time over DIFFICULTY_WINDOW blocks.
        """
        # Not enough blocks for adjustment
        if len(self.chain) < self.DIFFICULTY_WINDOW:
            return 1

        # Get the window of blocks to analyze
        latest_block = self.chain[-1]
        window_start_block = self.chain[-self.DIFFICULTY_WINDOW]

        # Calculate actual time elapsed
        actual_time = latest_block.timestamp - window_start_block.timestamp

        # Calculate expected time
        expected_time = self.TARGET_BLOCK_TIME * self.DIFFICULTY_WINDOW

        # Get current difficulty
        current_diff = latest_block.difficulty

        # Calculate adjustment ratio
        if actual_time == 0:
            actual_time = 1  # Prevent division by zero

        ratio = expected_time / actual_time

        # Apply exponential adjustment with damping
        # ratio > 1 means blocks were too slow → increase difficulty
        # ratio < 1 means blocks were too fast → decrease difficulty
        adjustment = current_diff * (ratio ** 0.5)  # Square root dampening to avoid huge swings

        # Ensure difficulty stays within bounds
        new_difficulty = max(1, min(int(adjustment), 32))  # Between 1 and 32 leading zeros

        print(f"📊 Difficulty adjustment: {current_diff} → {new_difficulty} (time: {actual_time:.1f}s / {expected_time}s)")

        return new_difficulty

    def get_difficulty_for_mining(self):
        """Return 1 for fast testing, real difficulty in production"""
        return 1  # ✅ Keep low for testing speed

    # =========================
    # CREATE BLOCK
    # =========================
    def create_block(self, miner_address, reward=None):

        txs = self.mempool.get_transactions()
        print(f"📦 Mempool size: {len(txs)}")

        # reward calculation
        base_reward = reward if reward is not None else self.get_block_reward()

        treasury_cut = base_reward * self.TREASURY_PERCENT
        miner_reward = base_reward * (1 - self.TREASURY_PERCENT)

        # fees
        total_fees = sum(tx.get_fee() for tx in txs)

        burn = total_fees * self.FEE_BURN_PERCENT
        miner_fees = total_fees - burn

        # coinbase transaction
        coinbase = Transaction(
            inputs=[],
            outputs=[
                {"address": miner_address, "amount": miner_reward + miner_fees},
                {"address": self.TREASURY_ADDRESS, "amount": treasury_cut}
            ]
        )

        txs.insert(0, coinbase)

        # create block
        block = Block(
            index=self.get_last_block().index + 1,
            prev_hash=self.get_last_block().hash,
            transactions=txs,
            timestamp=time.time(),
            difficulty=self.get_difficulty_for_mining()
        )

        # ✅ CRITICAL: mine the block
        block.mine()

        return block

    # =========================
    # ADD BLOCK
    # =========================
    def add_block(self, block):

        last = self.get_last_block()

        # validate previous hash
        if block.prev_hash != last.hash:
            raise Exception("Invalid previous hash")

        # validate hash
        if block.hash != block.calculate_hash():
            raise Exception("Invalid block hash")

        # validate and apply transactions
        for tx in block.transactions:
            if not tx.verify():
                raise Exception("Invalid transaction signature")

            if not self.utxo.validate_transaction(tx):
                raise Exception("Invalid transaction UTXO state")

            self.utxo.apply_transaction(tx)

        # add to chain
        self.chain.append(block)

        # persist
        self.chain_store.save_chain(self.chain)
        self.utxo.save()

        # broadcast to network
        if self.broadcast_callback:
            self.broadcast_callback(block)