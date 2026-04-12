from core.blockchain import Blockchain
from wallet.wallet import Wallet


def test_block_mining():

    bc = Blockchain()

    miner = Wallet()

    block = bc.create_block(
        miner_address=miner.address,
        reward=1
    )

    block.mine()

    bc.add_block(block)

    assert len(bc.chain) >= 1