# wallet/advanced_wallet.py
import os
import json
import time
import hashlib
from typing import Dict, List, Optional, Union
from ecdsa import SigningKey, VerifyingKey, SECP256k1
from core.transaction import Transaction
from wallet.multi_signature import MultiSigWallet, MultiSigTransactionBuilder
from wallet.hardware_wallet import HardwareWallet, HardwareWalletManager
from wallet.staking import StakingManager, StakingPool


class AdvancedWallet:
    """Advanced wallet with multi-sig, hardware, and staking support"""
    
    def __init__(self, wallet_type: str = "software", config_file: str = "advanced_wallet.json"):
        self.wallet_type = wallet_type  # software, hardware, multisig, staking
        self.config_file = config_file
        
        # Core wallet components
        self.software_wallet = None
        self.hardware_wallet = None
        self.multisig_wallet = None
        self.staking_manager = None
        
        # Wallet state
        self.address = None
        self.public_key = None
        self.private_key = None
        
        # Advanced features
        self.wallets: Dict[str, Dict] = {}  # Multiple wallet management
        self.transaction_history: List[Dict] = []
        self.preferences: Dict = {
            "default_fee": 0.01,
            "max_fee": 1.0,
            "auto_backup": True,
            "require_pin": False,
            "pin": ""
        }
        
        # Load or create wallet
        self._load_or_create_wallet()
        
        print(f"🔐 Advanced wallet initialized: {wallet_type}")
    
    def _load_or_create_wallet(self):
        """Load existing wallet or create new one"""
        if os.path.exists(self.config_file):
            self._load_wallet()
        else:
            self._create_wallet()
            self._save_wallet()
    
    def _load_wallet(self):
        """Load wallet from file"""
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            self.wallet_type = data.get("type", "software")
            self.preferences = data.get("preferences", self.preferences)
            self.transaction_history = data.get("transaction_history", [])
            self.wallets = data.get("wallets", {})
            
            # Load based on type
            if self.wallet_type == "software":
                self._load_software_wallet(data)
            elif self.wallet_type == "hardware":
                self._load_hardware_wallet(data)
            elif self.wallet_type == "multisig":
                self._load_multisig_wallet(data)
            
            print(f"📁 Wallet loaded: {self.wallet_type}")
            
        except Exception as e:
            print(f"❌ Failed to load wallet: {e}")
            self._create_wallet()
    
    def _load_software_wallet(self, data: Dict):
        """Load software wallet components"""
        if "private_key" in data:
            self.private_key = SigningKey.from_string(
                bytes.fromhex(data["private_key"]), 
                curve=SECP256k1
            )
            self.public_key = self.private_key.get_verifying_key()
            self.address = hashlib.sha256(self.public_key.to_string()).hexdigest()
    
    def _load_hardware_wallet(self, data: Dict):
        """Load hardware wallet components"""
        device_info = data.get("hardware_device", {})
        if device_info:
            self.hardware_wallet = HardwareWallet()
            if self.hardware_wallet.connect_device(device_info.get("path", "")):
                self.address = self.hardware_wallet.get_public_key()
                print("🔗 Hardware wallet connected")
    
    def _load_multisig_wallet(self, data: Dict):
        """Load multi-signature wallet components"""
        multisig_config = data.get("multisig_config", {})
        if multisig_config:
            m = multisig_config.get("m", 2)
            n = multisig_config.get("n", 3)
            self.multisig_wallet = MultiSigWallet(m, n)
            
            # Load signers
            signers = multisig_config.get("signers", [])
            for signer in signers:
                self.multisig_wallet.add_signer(
                    signer["public_key"], 
                    signer.get("name", "")
                )
            
            # Generate address
            self.address = self.multisig_wallet.generate_redeem_script()
    
    def _create_wallet(self):
        """Create new wallet based on type"""
        if self.wallet_type == "software":
            self._create_software_wallet()
        elif self.wallet_type == "hardware":
            self._create_hardware_wallet()
        elif self.wallet_type == "multisig":
            self._create_multisig_wallet()
        elif self.wallet_type == "staking":
            self._create_staking_wallet()
    
    def _create_software_wallet(self):
        """Create software wallet"""
        self.private_key = SigningKey.generate(curve=SECP256k1)
        self.public_key = self.private_key.get_verifying_key()
        self.address = hashlib.sha256(self.public_key.to_string()).hexdigest()
        
        print("🔑 Software wallet created")
        print(f"   Address: {self.address}")
    
    def _create_hardware_wallet(self):
        """Create hardware wallet interface"""
        self.hardware_wallet = HardwareWallet()
        
        # Scan for devices
        devices = self.hardware_wallet.scan_devices()
        if devices:
            # Auto-connect to first device
            device_path = devices[0]["path"]
            if self.hardware_wallet.connect_device(device_path):
                self.address = self.hardware_wallet.get_public_key()
                print("🔗 Hardware wallet connected")
        else:
            print("⚠️ No hardware wallet found")
    
    def _create_multisig_wallet(self):
        """Create multi-signature wallet"""
        self.multisig_wallet = MultiSigWallet(2, 3)  # 2-of-3 default
        
        # Add some sample signers (in production, these would be real keys)
        self.multisig_wallet.add_signer("sample_pubkey_1", "Alice")
        self.multisig_wallet.add_signer("sample_pubkey_2", "Bob")
        self.multisig_wallet.add_signer("sample_pubkey_3", "Charlie")
        
        self.address = self.multisig_wallet.generate_redeem_script()
        
        print("🔐 Multi-sig wallet created (2-of-3)")
        print(f"   Address: {self.address}")
    
    def _create_staking_wallet(self):
        """Create staking-enabled wallet"""
        # Create base software wallet first
        self._create_software_wallet()
        
        # Initialize staking manager
        self.staking_manager = StakingManager(None)  # Would pass blockchain instance
        
        print("🏊 Staking wallet created")
    
    def _save_wallet(self):
        """Save wallet to file"""
        data = {
            "type": self.wallet_type,
            "address": self.address,
            "preferences": self.preferences,
            "transaction_history": self.transaction_history,
            "wallets": self.wallets,
            "updated_at": time.time()
        }
        
        # Add type-specific data
        if self.wallet_type == "software" and self.private_key:
            data["private_key"] = self.private_key.to_string().hex()
        elif self.wallet_type == "hardware" and self.hardware_wallet:
            data["hardware_device"] = self.hardware_wallet.get_device_status()
        elif self.wallet_type == "multisig" and self.multisig_wallet:
            data["multisig_config"] = {
                "m": self.multisig_wallet.m,
                "n": self.multisig_wallet.n,
                "signers": self.multisig_wallet.list_signers()
            }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            print("💾 Wallet saved")
        except Exception as e:
            print(f"❌ Failed to save wallet: {e}")
    
    def create_transaction(self, to_address: str, amount: float, 
                      fee: Optional[float] = None) -> Optional[Transaction]:
        """Create transaction based on wallet type"""
        if fee is None:
            fee = self.preferences["default_fee"]
        
        if self.wallet_type == "software":
            return self._create_software_transaction(to_address, amount, fee)
        elif self.wallet_type == "hardware":
            return self._create_hardware_transaction(to_address, amount, fee)
        elif self.wallet_type == "multisig":
            return self._create_multisig_transaction(to_address, amount, fee)
        else:
            print(f"❌ Transactions not supported for {self.wallet_type} wallet")
            return None
    
    def _create_software_transaction(self, to_address: str, amount: float, fee: float) -> Transaction:
        """Create transaction with software wallet"""
        # This would integrate with the actual UTXO and transaction building logic
        # For now, return a basic transaction structure
        tx = Transaction(
            inputs=[],  # Would be populated from UTXO
            outputs=[{
                "address": to_address,
                "amount": amount
            }]
        )
        
        # Sign transaction
        message = tx.to_dict()
        tx.signature = self.private_key.sign_digest(
            hashlib.sha256(json.dumps(message, sort_keys=True).encode()).digest()
        ).hex()
        tx.public_key = self.public_key.to_string().hex()
        
        return tx
    
    def _create_hardware_transaction(self, to_address: str, amount: float, fee: float) -> Transaction:
        """Create transaction with hardware wallet"""
        if not self.hardware_wallet:
            raise ValueError("Hardware wallet not connected")
        
        # Prepare transaction data
        tx_data = {
            "outputs": [{
                "address": to_address,
                "amount": amount
            }],
            "fee": fee
        }
        
        # Sign with hardware wallet
        signature = self.hardware_wallet.sign_transaction(tx_data)
        if signature:
            tx = Transaction(inputs=[], outputs=tx_data["outputs"])
            tx.signature = signature
            tx.public_key = self.hardware_wallet.get_public_key()
            return tx
        
        raise ValueError("Hardware wallet signing failed")
    
    def _create_multisig_transaction(self, to_address: str, amount: float, fee: float) -> Transaction:
        """Create multi-signature transaction"""
        if not self.multisig_wallet:
            raise ValueError("Multi-sig wallet not initialized")
        
        # Create multi-sig transaction template
        tx_template = self.multisig_wallet.create_multi_sig_transaction(
            inputs=[],  # Would be populated from UTXO
            outputs=[{
                "address": to_address,
                "amount": amount
            }],
            fee=fee
        )
        
        print(f"📋 Multi-sig transaction created: {self.multisig_wallet.m}-of-{self.multisig_wallet.n}")
        print(f"   Requires {self.multisig_wallet.m} signatures")
        
        # Return template - would need actual signing process
        return tx_template
    
    def sign_multisig_transaction(self, tx_template: Dict, private_key: SigningKey, signer_index: int) -> bool:
        """Sign a multi-signature transaction"""
        if not self.multisig_wallet:
            return False
        
        return self.multisig_wallet.sign_transaction(tx_template, private_key, signer_index)
    
    def finalize_multisig_transaction(self, tx_template: Dict) -> Transaction:
        """Finalize multi-signature transaction"""
        if not self.multisig_wallet:
            raise ValueError("Multi-sig wallet not initialized")
        
        return self.multisig_wallet.finalize_transaction(tx_template)
    
    def delegate_stake(self, pool_address: str, amount: float, validator_address: str) -> bool:
        """Delegate stake to a pool"""
        if not self.staking_manager:
            print("❌ Staking not available for this wallet type")
            return False
        
        return self.staking_manager.delegate_to_pool(pool_address, self.address, amount, validator_address)
    
    def undelegate_stake(self, pool_address: str, amount: float, validator_address: str) -> bool:
        """Undelegate stake from a pool"""
        if not self.staking_manager:
            print("❌ Staking not available for this wallet type")
            return False
        
        return self.staking_manager.delegate_to_pool(pool_address, self.address, -amount, validator_address)
    
    def get_staking_info(self) -> Dict:
        """Get staking information"""
        if not self.staking_manager:
            return {"staking_enabled": False}
        
        info = self.staking_manager.get_staking_info(self.address)
        info["staking_enabled"] = True
        return info
    
    def backup_wallet(self, backup_path: str = None) -> bool:
        """Backup wallet"""
        if not backup_path:
            backup_path = f"wallet_backup_{int(time.time())}.json"
        
        try:
            # Basic backup - copy wallet file
            import shutil
            shutil.copy2(self.config_file, backup_path)
            
            # Additional hardware wallet backup
            if self.wallet_type == "hardware" and self.hardware_wallet:
                self.hardware_wallet.backup_device(f"{backup_path}_hardware")
            
            print(f"💾 Wallet backed up to {backup_path}")
            return True
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False
    
    def restore_wallet(self, backup_path: str) -> bool:
        """Restore wallet from backup"""
        try:
            if not os.path.exists(backup_path):
                print(f"❌ Backup file not found: {backup_path}")
                return False
            
            # Restore wallet file
            import shutil
            shutil.copy2(backup_path, self.config_file)
            
            # Reload wallet
            self._load_wallet()
            
            print(f"📂 Wallet restored from {backup_path}")
            return True
            
        except Exception as e:
            print(f"❌ Restore failed: {e}")
            return False
    
    def add_transaction_to_history(self, tx: Transaction, status: str = "pending"):
        """Add transaction to history"""
        history_entry = {
            "tx_hash": tx.calculate_hash() if hasattr(tx, 'calculate_hash') else "unknown",
            "type": "sent" if tx.outputs and any(out.get("address") != self.address for out in tx.outputs) else "received",
            "amount": sum(out.get("amount", 0) for out in tx.outputs),
            "fee": getattr(tx, 'fee', 0),
            "status": status,
            "timestamp": time.time(),
            "inputs": tx.inputs if hasattr(tx, 'inputs') else [],
            "outputs": tx.outputs if hasattr(tx, 'outputs') else []
        }
        
        self.transaction_history.append(history_entry)
        
        # Keep history manageable
        if len(self.transaction_history) > 1000:
            self.transaction_history = self.transaction_history[-1000:]
        
        # Auto-save if enabled
        if self.preferences.get("auto_backup", True):
            self._save_wallet()
    
    def get_transaction_history(self, limit: int = 50) -> List[Dict]:
        """Get transaction history"""
        return self.transaction_history[-limit:]
    
    def get_balance(self) -> float:
        """Get wallet balance (placeholder - would query blockchain)"""
        # This would integrate with blockchain to get actual balance
        print(f"💰 Balance query for {self.address}")
        return 0.0  # Placeholder
    
    def get_wallet_info(self) -> Dict:
        """Get comprehensive wallet information"""
        info = {
            "type": self.wallet_type,
            "address": self.address,
            "preferences": self.preferences,
            "transaction_count": len(self.transaction_history),
            "updated_at": time.time()
        }
        
        # Add type-specific info
        if self.wallet_type == "software":
            info["has_private_key"] = self.private_key is not None
        elif self.wallet_type == "hardware":
            info["hardware_connected"] = self.hardware_wallet is not None
            if self.hardware_wallet:
                info["hardware_status"] = self.hardware_wallet.get_device_status()
        elif self.wallet_type == "multisig":
            if self.multisig_wallet:
                multisig_status = self.multisig_wallet.get_status()
                info.update(multisig_status)
        elif self.wallet_type == "staking":
            info["staking_enabled"] = self.staking_manager is not None
            if self.staking_manager:
                info["staking_info"] = self.get_staking_info()
        
        return info
    
    def update_preferences(self, preferences: Dict):
        """Update wallet preferences"""
        self.preferences.update(preferences)
        self._save_wallet()
        print("⚙️ Preferences updated")
    
    def set_pin(self, pin: str) -> bool:
        """Set wallet PIN"""
        if len(pin) < 4:
            print("❌ PIN must be at least 4 digits")
            return False
        
        self.preferences["pin"] = pin
        self.preferences["require_pin"] = True
        self._save_wallet()
        print("🔐 PIN set")
        return True
    
    def verify_pin(self, pin: str) -> bool:
        """Verify wallet PIN"""
        if not self.preferences.get("require_pin", False):
            return True
        
        return pin == self.preferences.get("pin", "")
    
    def lock_wallet(self):
        """Lock wallet (require PIN for operations)"""
        if self.preferences.get("require_pin", False):
            print("🔒 Wallet locked")
            # In production, would encrypt private key
    
    def unlock_wallet(self, pin: str) -> bool:
        """Unlock wallet"""
        if self.verify_pin(pin):
            print("🔓 Wallet unlocked")
            # In production, would decrypt private key
            return True
        else:
            print("❌ Incorrect PIN")
            return False


class WalletManager:
    """Manager for multiple advanced wallets"""
    
    def __init__(self, config_dir: str = "wallets"):
        self.config_dir = config_dir
        self.wallets: Dict[str, AdvancedWallet] = {}
        self.active_wallet: Optional[str] = None
        
        # Create config directory if it doesn't exist
        os.makedirs(config_dir, exist_ok=True)
        
        # Load existing wallets
        self._load_wallets()
        
        print("🔐 Advanced wallet manager initialized")
    
    def _load_wallets(self):
        """Load all wallets from config directory"""
        try:
            for filename in os.listdir(self.config_dir):
                if filename.endswith(".json"):
                    wallet_name = filename[:-5]  # Remove .json extension
                    wallet_path = os.path.join(self.config_dir, filename)
                    
                    # Create wallet instance
                    wallet = AdvancedWallet(config_file=wallet_path)
                    self.wallets[wallet_name] = wallet
                    
                    print(f"📁 Loaded wallet: {wallet_name}")
        
        except Exception as e:
            print(f"❌ Error loading wallets: {e}")
    
    def create_wallet(self, name: str, wallet_type: str = "software") -> bool:
        """Create new wallet"""
        if name in self.wallets:
            print(f"❌ Wallet {name} already exists")
            return False
        
        wallet_path = os.path.join(self.config_dir, f"{name}.json")
        wallet = AdvancedWallet(wallet_type=wallet_type, config_file=wallet_path)
        
        self.wallets[name] = wallet
        print(f"✅ Created wallet: {name} ({wallet_type})")
        
        return True
    
    def delete_wallet(self, name: str) -> bool:
        """Delete wallet"""
        if name not in self.wallets:
            print(f"❌ Wallet {name} not found")
            return False
        
        if name == self.active_wallet:
            self.active_wallet = None
        
        wallet_path = os.path.join(self.config_dir, f"{name}.json")
        
        try:
            os.remove(wallet_path)
            del self.wallets[name]
            print(f"🗑️ Deleted wallet: {name}")
            return True
        except Exception as e:
            print(f"❌ Failed to delete wallet: {e}")
            return False
    
    def set_active_wallet(self, name: str) -> bool:
        """Set active wallet"""
        if name not in self.wallets:
            print(f"❌ Wallet {name} not found")
            return False
        
        self.active_wallet = name
        print(f"🎯 Active wallet: {name}")
        return True
    
    def get_active_wallet(self) -> Optional[AdvancedWallet]:
        """Get currently active wallet"""
        if self.active_wallet:
            return self.wallets.get(self.active_wallet)
        return None
    
    def list_wallets(self) -> Dict[str, Dict]:
        """List all wallets with basic info"""
        wallet_list = {}
        
        for name, wallet in self.wallets.items():
            info = wallet.get_wallet_info()
            wallet_list[name] = {
                "type": info["type"],
                "address": info["address"],
                "transaction_count": info["transaction_count"]
            }
        
        return wallet_list
    
    def backup_all_wallets(self, backup_dir: str = None) -> bool:
        """Backup all wallets"""
        if not backup_dir:
            backup_dir = f"wallet_backup_{int(time.time())}"
        
        try:
            os.makedirs(backup_dir, exist_ok=True)
            
            for name, wallet in self.wallets.items():
                backup_path = os.path.join(backup_dir, f"{name}.json")
                wallet.backup_wallet(backup_path)
            
            print(f"💾 All wallets backed up to {backup_dir}")
            return True
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False


# Utility functions
def create_wallet_suite():
    """Create a complete wallet suite"""
    print("🏗️ Creating advanced wallet suite...")
    
    # Create wallet manager
    manager = WalletManager()
    
    # Create different wallet types
    manager.create_wallet("main", "software")
    manager.create_wallet("hardware", "hardware")
    manager.create_wallet("multisig", "multisig")
    manager.create_wallet("staking", "staking")
    
    print("✅ Wallet suite created")
    return manager


def import_wallet_from_seed(seed_phrase: str, wallet_name: str = "imported") -> AdvancedWallet:
    """Import wallet from seed phrase"""
    print(f"🌱 Importing wallet from seed: {wallet_name}")
    
    # Convert seed to private key (simplified)
    seed_hash = hashlib.sha256(seed_phrase.encode()).digest()
    private_key = SigningKey.from_string(seed_hash, curve=SECP256k1)
    
    # Create wallet with imported key
    wallet = AdvancedWallet(wallet_type="software")
    wallet.private_key = private_key
    wallet.public_key = private_key.get_verifying_key()
    wallet.address = hashlib.sha256(wallet.public_key.to_string()).hexdigest()
    
    print(f"✅ Wallet imported: {wallet.address[:16]}...")
    return wallet
