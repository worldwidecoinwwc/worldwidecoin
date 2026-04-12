import sys
from io import StringIO
from cli.cli import WWCCli
from wallet.wallet import Wallet


def test_cli_wallet_address():
    """Test wallet address command"""
    cli = WWCCli()
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    result = cli.cmd_wallet_address(None)

    output = sys.stdout.getvalue()
    sys.stdout = old_stdout

    assert result == 0
    assert "📮" in output
    assert cli.wallet.address in output


def test_cli_wallet_balance():
    """Test wallet balance command"""
    cli = WWCCli()
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    result = cli.cmd_wallet_balance(None)

    output = sys.stdout.getvalue()
    sys.stdout = old_stdout

    assert result == 0
    assert "💰" in output
    assert "WWC" in output


def test_cli_wallet_create():
    """Test wallet creation"""
    cli = WWCCli()
    old_address = cli.wallet.address

    old_stdout = sys.stdout
    sys.stdout = StringIO()

    result = cli.cmd_wallet_create(None)

    output = sys.stdout.getvalue()
    sys.stdout = old_stdout

    assert result == 0
    assert "✅" in output


def test_cli_node_info():
    """Test node info command"""
    cli = WWCCli()
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    result = cli.cmd_node_info(None)

    output = sys.stdout.getvalue()
    sys.stdout = old_stdout

    assert result == 0
    assert "🌐" in output
    assert "Chain height" in output


def test_cli_mempool():
    """Test mempool display"""
    cli = WWCCli()
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    result = cli.cmd_mempool(None)

    output = sys.stdout.getvalue()
    sys.stdout = old_stdout

    assert result == 0
    assert "📋" in output
    assert "Mempool" in output


def test_cli_block_query():
    """Test block query"""
    from core.blockchain import Blockchain
    from core.utxo import UTXOSet
    from storage.mempool import Mempool
    from core.block import Block
    import time
    
    # Create a fresh blockchain in memory (no persistence)
    bc = Blockchain()
    bc.chain = []
    bc.utxo = UTXOSet(persistent=False)
    bc.mempool = Mempool(bc.utxo)
    
    # Create genesis block
    genesis = Block(0, "0", [], time.time(), 1)
    genesis.mine()
    bc.chain.append(genesis)
    
    cli = WWCCli()
    cli.blockchain = bc
    
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    class Args:
        height = 0

    result = cli.cmd_block(Args())

    output = sys.stdout.getvalue()
    sys.stdout = old_stdout

    assert result == 0, f"Expected 0, got {result}. Output: {output}"
    assert "📦" in output
    assert "Block 0" in output


def test_cli_connect_peer():
    """Test peer connection"""
    cli = WWCCli()
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    class Args:
        peer = "127.0.0.1:8333"

    result = cli.cmd_node_connect(Args())

    output = sys.stdout.getvalue()
    sys.stdout = old_stdout

    assert result == 0
    assert "✅" in output
