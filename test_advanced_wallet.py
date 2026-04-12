#!/usr/bin/env python3
"""
Phase 5 Advanced Wallet Testing Suite
Tests multi-signature, hardware wallet, and staking functionality
"""

import time
import json
import tempfile
import os
from wallet.multi_signature import MultiSigWallet, MultiSigTransactionBuilder
from wallet.hardware_wallet import HardwareWallet, HardwareWalletManager
from wallet.staking import StakingPool, StakingManager
from wallet.advanced_wallet import AdvancedWallet, WalletManager
from ecdsa import SigningKey, SECP256k1


def test_multi_signature_wallet():
    """Test 1: Multi-signature wallet functionality"""
    print("=== TEST 1: Multi-Signature Wallet ===")
    
    # Create 2-of-3 multi-sig wallet
    multisig = MultiSigWallet(required_signatures=2, total_signers=3)
    
    # Add signers
    key1 = SigningKey.generate(curve=SECP256k1)
    key2 = SigningKey.generate(curve=SECP256k1)
    key3 = SigningKey.generate(curve=SECP256k1)
    
    multisig.add_signer(key1.get_verifying_key().to_string().hex(), "Alice")
    multisig.add_signer(key2.get_verifying_key().to_string().hex(), "Bob")
    multisig.add_signer(key3.get_verifying_key().to_string().hex(), "Charlie")
    
    # Generate address
    address = multisig.generate_redeem_script()
    print(f"Multi-sig address: {address[:16]}...")
    
    # Create transaction
    tx_template = multisig.create_multi_sig_transaction(
        inputs=[{"txid": "abc123", "vout": 0}],
        outputs=[{"address": "recipient123", "amount": 10.0}],
        fee=0.01
    )
    
    # Sign with first signer
    signed1 = multisig.sign_transaction(tx_template, key1, 0)
    print(f"Signer 1 signed: {signed1}")
    
    # Sign with second signer
    signed2 = multisig.sign_transaction(tx_template, key2, 1)
    print(f"Signer 2 signed: {signed2}")
    
    # Check if fully signed
    is_fully_signed = multisig.is_fully_signed(tx_template)
    print(f"Transaction fully signed: {is_fully_signed}")
    
    # Validate signatures
    is_valid = multisig.validate_signatures(tx_template)
    print(f"Signatures valid: {is_valid}")
    
    if is_fully_signed and is_valid:
        try:
            finalized_tx = multisig.finalize_transaction(tx_template)
            print(f"Transaction finalized: {type(finalized_tx).__name__}")
        except Exception as e:
            print(f"Finalization error: {e}")
    
    print()


def test_hardware_wallet_simulation():
    """Test 2: Hardware wallet simulation"""
    print("=== TEST 2: Hardware Wallet Simulation ===")
    
    # Create hardware wallet (simulation)
    hw_wallet = HardwareWallet()
    
    # Test device scanning
    devices = hw_wallet.scan_devices()
    print(f"Devices found: {len(devices)}")
    
    # Since we don't have actual hardware, test the interface
    print("Hardware wallet interface tests:")
    
    # Test packet preparation
    test_command = "GET_PUBKEY"
    test_data = b"test_derivation_path"
    packet = hw_wallet._prepare_packet(test_command, test_data)
    print(f"Packet prepared: {len(packet)} bytes")
    
    # Test device identification
    ledger_id = hw_wallet._identify_device(0x2c97, 0x0001)
    trezor_id = hw_wallet._identify_device(0x534c, 0x0001)
    print(f"Ledger ID: {ledger_id}")
    print(f"Trezor ID: {trezor_id}")
    
    # Test wallet manager
    manager = HardwareWalletManager()
    manager.add_wallet("test_wallet", hw_wallet)
    manager.set_active_wallet("test_wallet")
    
    active = manager.get_active_wallet()
    print(f"Active wallet: {active is not None}")
    
    print()


def test_staking_pool():
    """Test 3: Staking pool functionality"""
    print("=== TEST 3: Staking Pool ===")
    
    # Create staking pool
    pool = StakingPool("pool_address_123", commission_rate=0.05)
    
    # Add validators
    pool.add_validator("validator_1", commission_rate=0.10)
    pool.add_validator("validator_2", commission_rate=0.08)
    pool.add_validator("validator_3", commission_rate=0.12)
    
    # Add delegators
    pool.delegate_stake("delegator_1", 100.0, "validator_1")
    pool.delegate_stake("delegator_2", 50.0, "validator_1")
    pool.delegate_stake("delegator_3", 75.0, "validator_2")
    
    # Select active validators
    active_validators = pool.select_active_validators(max_validators=2)
    print(f"Active validators: {len(active_validators)}")
    
    # Calculate rewards
    rewards = pool.calculate_rewards(epoch_duration=86400)
    print(f"Rewards distributed to {len(rewards)} participants")
    
    # Get pool statistics
    stats = pool.get_pool_stats()
    print(f"Pool stats:")
    print(f"   Total staked: {stats['total_staked']:.2f} WWC")
    print(f"   Total delegators: {stats['total_delegators']}")
    print(f"   Total validators: {stats['total_validators']}")
    
    print()


def test_advanced_wallet():
    """Test 4: Advanced wallet functionality"""
    print("=== TEST 4: Advanced Wallet ===")
    
    # Test different wallet types
    wallet_types = ["software", "multisig", "staking"]
    
    for wallet_type in wallet_types:
        print(f"Testing {wallet_type} wallet...")
        
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_file = f.name
        
        try:
            wallet = AdvancedWallet(wallet_type=wallet_type, config_file=config_file)
            
            # Get wallet info
            info = wallet.get_wallet_info()
            print(f"   Type: {info['type']}")
            print(f"   Address: {info['address'][:16] if info['address'] else 'None'}...")
            
            # Test preferences
            wallet.update_preferences({"default_fee": 0.02, "auto_backup": True})
            
            # Test PIN
            pin_set = wallet.set_pin("1234")
            print(f"   PIN set: {pin_set}")
            
            # Test transaction creation
            try:
                tx = wallet.create_transaction("recipient123", 10.0, 0.01)
                print(f"   Transaction created: {type(tx).__name__}")
            except Exception as e:
                print(f"   Transaction error: {e}")
            
            # Test backup
            backup_path = config_file + ".backup"
            backup_success = wallet.backup_wallet(backup_path)
            print(f"   Backup success: {backup_success}")
            
        finally:
            # Cleanup
            try:
                os.unlink(config_file)
                if os.path.exists(backup_path):
                    os.unlink(backup_path)
            except:
                pass
        
        print()
    
    print()


def test_wallet_manager():
    """Test 5: Wallet manager functionality"""
    print("=== TEST 5: Wallet Manager ===")
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = WalletManager(config_dir=temp_dir)
        
        # Create different wallet types
        manager.create_wallet("main", "software")
        manager.create_wallet("hardware", "hardware")
        manager.create_wallet("multisig", "multisig")
        manager.create_wallet("staking", "staking")
        
        # List wallets
        wallet_list = manager.list_wallets()
        print(f"Created {len(wallet_list)} wallets:")
        for name, info in wallet_list.items():
            print(f"   {name}: {info['type']} ({info['address'][:16]}...)")
        
        # Set active wallet
        manager.set_active_wallet("main")
        active = manager.get_active_wallet()
        print(f"Active wallet: {active is not None}")
        
        # Test backup
        backup_success = manager.backup_all_wallets()
        print(f"Backup success: {backup_success}")
    
    print()


def test_staking_manager():
    """Test 6: Staking manager functionality"""
    print("=== TEST 6: Staking Manager ===")
    
    # Create staking manager
    manager = StakingManager(None)  # Would pass blockchain instance
    
    # Create pools
    pool1 = manager.create_pool("pool_1", commission_rate=0.05)
    pool2 = manager.create_pool("pool_2", commission_rate=0.03)
    
    # Add validators to pools
    pool1.add_validator("validator_a", commission_rate=0.08)
    pool1.add_validator("validator_b", commission_rate=0.10)
    
    pool2.add_validator("validator_c", commission_rate=0.06)
    
    # Delegate stakes
    manager.delegate_to_pool("pool_1", "delegator_1", 100.0, "validator_a")
    manager.delegate_to_pool("pool_1", "delegator_2", 50.0, "validator_b")
    manager.delegate_to_pool("pool_2", "delegator_3", 75.0, "validator_c")
    
    # Get system stats
    system_stats = manager.get_system_stats()
    print(f"System stats:")
    print(f"   Total pools: {system_stats['total_pools']}")
    print(f"   Total staked: {system_stats['total_staked']:.2f} WWC")
    print(f"   Total delegators: {system_stats['total_delegators']}")
    print(f"   Total validators: {system_stats['total_validators']}")
    
    # Process epoch (simplified)
    print("Processing epoch...")
    # manager.process_epoch()  # Would require full blockchain integration
    
    print()


def test_transaction_builder():
    """Test 7: Multi-sig transaction builder"""
    print("=== TEST 7: Transaction Builder ===")
    
    # Create multi-sig wallet
    multisig = MultiSigWallet(2, 3)
    
    # Add signers
    key1 = SigningKey.generate(curve=SECP256k1)
    key2 = SigningKey.generate(curve=SECP256k1)
    key3 = SigningKey.generate(curve=SECP256k1)
    
    multisig.add_signer(key1.get_verifying_key().to_string().hex(), "Alice")
    multisig.add_signer(key2.get_verifying_key().to_string().hex(), "Bob")
    multisig.add_signer(key3.get_verifying_key().to_string().hex(), "Charlie")
    
    # Create transaction builder
    builder = MultiSigTransactionBuilder(multisig)
    
    # Build transaction
    builder.create_transaction(
        inputs=[{"txid": "abc123", "vout": 0}],
        outputs=[{"address": "recipient123", "amount": 25.0}],
        fee=0.02
    )
    
    # Add signatures
    builder.add_signature(key1, 0)
    builder.add_signature(key2, 1)
    
    # Check status
    status = builder.get_status()
    print(f"Transaction status:")
    print(f"   Signatures: {status['signatures']}/{status['required']}")
    print(f"   Ready: {status['ready']}")
    
    # Finalize if ready
    if builder.is_ready():
        try:
            finalized_tx = builder.finalize()
            print(f"Transaction finalized: {type(finalized_tx).__name__}")
        except Exception as e:
            print(f"Finalization error: {e}")
    
    print()


def test_wallet_integration():
    """Test 8: Wallet integration scenarios"""
    print("=== TEST 8: Wallet Integration ===")
    
    # Create wallet suite
    manager = WalletManager()
    
    # Create different wallet types
    manager.create_wallet("personal", "software")
    manager.create_wallet("business", "multisig")
    manager.create_wallet("investment", "staking")
    
    # Test switching between wallets
    wallets_to_test = ["personal", "business", "investment"]
    
    for wallet_name in wallets_to_test:
        manager.set_active_wallet(wallet_name)
        wallet = manager.get_active_wallet()
        
        info = wallet.get_wallet_info()
        print(f"Wallet: {wallet_name}")
        print(f"   Type: {info['type']}")
        print(f"   Address: {info['address'][:16] if info['address'] else 'None'}...")
        
        # Test transaction creation
        try:
            tx = wallet.create_transaction("test_recipient", 5.0, 0.01)
            print(f"   Transaction: {type(tx).__name__}")
        except Exception as e:
            print(f"   Transaction: {type(e).__name__}")
        
        # Test staking for staking wallet
        if wallet_name == "investment":
            staking_info = wallet.get_staking_info()
            print(f"   Staking enabled: {staking_info.get('staking_enabled', False)}")
        
        print()
    
    print()


def main():
    """Run all Phase 5 advanced wallet tests"""
    print("WorldWideCoin Phase 5 - Advanced Wallet Testing")
    print("=" * 50)
    
    tests = [
        test_multi_signature_wallet,
        test_hardware_wallet_simulation,
        test_staking_pool,
        test_advanced_wallet,
        test_wallet_manager,
        test_staking_manager,
        test_transaction_builder,
        test_wallet_integration
    ]
    
    for i, test in enumerate(tests, 1):
        try:
            test()
        except Exception as e:
            print(f"Test {i} failed: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    print("=" * 50)
    print("Phase 5 Advanced Wallet Testing Complete!")


if __name__ == "__main__":
    main()
