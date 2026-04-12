# wallet/hardware_wallet.py
import time
import hashlib
from typing import Dict, List, Optional, Tuple
from ecdsa import SigningKey, VerifyingKey, SECP256k1
from core.transaction import Transaction

# Optional imports for hardware wallet support
try:
    import serial
    import hid
    HARDWARE_SUPPORT = True
except ImportError:
    HARDWARE_SUPPORT = False
    serial = None
    hid = None


class HardwareWallet:
    """Hardware wallet integration for WorldWideCoin"""
    
    def __init__(self):
        self.connected_device = None
        self.device_info = {}
        self.supported_devices = {
            "ledger_nano_s": {"vid": 0x2c97, "pid": 0x0001},
            "ledger_nano_x": {"vid": 0x2c97, "pid": 0x0004},
            "trezor_one": {"vid": 0x534c, "pid": 0x0001},
            "trezor_model_t": {"vid": 0x1209, "pid": 0x53c1}
        }
        
        print("🔌 Hardware wallet interface initialized")
    
    def scan_devices(self) -> List[Dict]:
        """Scan for connected hardware wallets"""
        print("Scanning for hardware devices...")
        
        devices = []
        
        if not HARDWARE_SUPPORT:
            print("Hardware support libraries not available - returning simulated devices")
            # Return simulated devices for testing
            return [
                {
                    "name": "Simulated Ledger Nano S",
                    "vendor_id": 0x2c97,
                    "product_id": 0x0001,
                    "path": "simulated_path_1",
                    "serial": "SIM001",
                    "interface": 0
                }
            ]
        
        try:
            # Scan USB HID devices
            hid_devices = hid.enumerate()
            
            for device in hid_devices:
                vendor_id = device['vendor_id']
                product_id = device['product_id']
                
                # Check if device is supported
                device_name = self._identify_device(vendor_id, product_id)
                if device_name:
                    device_info = {
                        "name": device_name,
                        "vendor_id": vendor_id,
                        "product_id": product_id,
                        "path": device['path'],
                        "serial": device.get('serial_number', ''),
                        "interface": device.get('interface_number', 0)
                    }
                    devices.append(device_info)
                    print(f"   Found: {device_name} ({vendor_id:04x}:{product_id:04x})")
        
        except Exception as e:
            print(f"⚠️ Device scan error: {e}")
        
        print(f"📱 Found {len(devices)} hardware wallet(s)")
        return devices
    
    def _identify_device(self, vendor_id: int, product_id: int) -> Optional[str]:
        """Identify device by vendor/product IDs"""
        for name, ids in self.supported_devices.items():
            if ids["vid"] == vendor_id and ids["pid"] == product_id:
                return name
        return None
    
    def connect_device(self, device_path: str) -> bool:
        """Connect to a specific hardware wallet"""
        try:
            print(f"Connecting to device at {device_path}...")
            
            if not HARDWARE_SUPPORT:
                # Simulate connection for testing
                self.connected_device = "simulated_device"
                self.device_info = {
                    "name": "Simulated Ledger Nano S",
                    "vendor_id": 0x2c97,
                    "product_id": 0x0001,
                    "serial": "SIM001",
                    "manufacturer": "Simulated"
                }
                print("Connected to simulated hardware wallet")
                return True
            
            # Attempt to open HID device
            self.connected_device = hid.device()
            self.connected_device.open_path(device_path)
            
            # Get device information
            self.device_info = self._get_device_info()
            
            print(f"✅ Connected to {self.device_info['name']}")
            print(f"   Serial: {self.device_info.get('serial', 'Unknown')}")
            print(f"   Firmware: {self.device_info.get('firmware', 'Unknown')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def disconnect_device(self):
        """Disconnect from hardware wallet"""
        if self.connected_device:
            try:
                self.connected_device.close()
                self.connected_device = None
                self.device_info = {}
                print("🔌 Hardware wallet disconnected")
            except Exception as e:
                print(f"⚠️ Disconnect error: {e}")
    
    def _get_device_info(self) -> Dict:
        """Get information from connected device"""
        if not self.connected_device:
            return {}
        
        info = {
            "name": self._identify_device(
                self.connected_device.get_vendor_id(),
                self.connected_device.get_product_id()
            ) or "Unknown",
            "vendor_id": self.connected_device.get_vendor_id(),
            "product_id": self.connected_device.get_product_id(),
            "serial": self.connected_device.get_serial_number_string(),
            "manufacturer": self.connected_device.get_manufacturer_string()
        }
        
        # Try to get firmware version
        try:
            firmware = self._send_command("GET_FIRMWARE")
            if firmware:
                info["firmware"] = firmware
        except:
            info["firmware"] = "Unknown"
        
        return info
    
    def _send_command(self, command: str, data: bytes = b'') -> Optional[bytes]:
        """Send command to hardware wallet"""
        if not self.connected_device:
            return None
        
        try:
            # Prepare command packet
            packet = self._prepare_packet(command, data)
            
            # Send to device
            self.connected_device.write(packet)
            
            # Wait for response
            time.sleep(0.1)
            response = self.connected_device.read(64)
            
            return response if response else None
            
        except Exception as e:
            print(f"⚠️ Command error: {e}")
            return None
    
    def _prepare_packet(self, command: str, data: bytes) -> bytes:
        """Prepare command packet for hardware wallet"""
        # Simple packet structure: [CMD_LEN][COMMAND][DATA_LEN][DATA][CHECKSUM]
        cmd_bytes = command.encode('utf-8')
        data_len = len(data)
        
        packet = bytearray()
        packet.append(len(cmd_bytes))
        packet.extend(cmd_bytes)
        packet.append(data_len)
        packet.extend(data)
        
        # Add checksum
        checksum = sum(packet) % 256
        packet.append(checksum)
        
        return bytes(packet)
    
    def get_public_key(self, derivation_path: str = "m/44'/0'/0'/0") -> Optional[str]:
        """
        Get public key from hardware wallet
        
        Args:
            derivation_path: BIP32 derivation path
        """
        if not self.connected_device:
            print("❌ No device connected")
            return None
        
        print(f"🔑 Requesting public key for path: {derivation_path}")
        
        try:
            # Send get public key command
            path_data = derivation_path.encode('utf-8')
            response = self._send_command("GET_PUBKEY", path_data)
            
            if response:
                # Parse response (simplified)
                pub_key = response[1:65].hex()  # Skip status byte
                print(f"✅ Public key retrieved: {pub_key[:16]}...")
                return pub_key
            
        except Exception as e:
            print(f"❌ Public key error: {e}")
        
        return None
    
    def sign_transaction(self, tx_data: Dict, derivation_path: str = "m/44'/0'/0'/0") -> Optional[str]:
        """
        Sign transaction with hardware wallet
        
        Args:
            tx_data: Transaction data to sign
            derivation_path: BIP32 derivation path for signing key
        """
        if not self.connected_device:
            print("❌ No device connected")
            return None
        
        print(f"✍️ Signing transaction with hardware wallet...")
        print(f"   Path: {derivation_path}")
        
        try:
            # Prepare transaction hash
            tx_json = json.dumps(tx_data, sort_keys=True)
            tx_hash = hashlib.sha256(tx_json.encode()).digest()
            
            # Send sign command
            sign_data = derivation_path.encode('utf-8') + tx_hash
            response = self._send_command("SIGN_TX", sign_data)
            
            if response:
                # Parse signature response
                status = response[0]
                if status == 0x00:  # Success
                    signature = response[1:65].hex()  # 64-byte signature + recovery byte
                    print(f"✅ Transaction signed: {signature[:16]}...")
                    return signature
                else:
                    print(f"❌ Signing failed with status: {status:02x}")
            
        except Exception as e:
            print(f"❌ Signing error: {e}")
        
        return None
    
    def verify_device(self) -> bool:
        """Verify hardware wallet authenticity"""
        if not self.connected_device:
            return False
        
        print("🔍 Verifying device authenticity...")
        
        try:
            # Get device certificate
            cert_response = self._send_command("GET_CERTIFICATE")
            if not cert_response:
                print("❌ Could not get device certificate")
                return False
            
            # Simple verification (in production, use proper certificate validation)
            device_cert = cert_response[1:].hex()
            
            # Check against known good certificates
            if self._is_known_certificate(device_cert):
                print("✅ Device verified as authentic")
                return True
            else:
                print("❌ Device certificate verification failed")
                return False
                
        except Exception as e:
            print(f"❌ Verification error: {e}")
            return False
    
    def _is_known_certificate(self, cert_hex: str) -> bool:
        """Check if certificate is from known manufacturer"""
        # Simplified check - in production, use proper certificate validation
        known_certs = [
            "a1b2c3d4e5f6...",  # Ledger certificate placeholder
            "f6e5d4c3b2a1...",  # Trezor certificate placeholder
        ]
        
        return any(cert_hex.startswith(known) for known in known_certs)
    
    def backup_device(self, backup_path: str) -> bool:
        """Create backup of hardware wallet"""
        if not self.connected_device:
            print("❌ No device connected")
            return False
        
        print(f"💾 Creating backup to {backup_path}...")
        
        try:
            # Get master public key
            master_pubkey = self.get_public_key("m")
            if not master_pubkey:
                return False
            
            # Create backup file
            backup_data = {
                "device_info": self.device_info,
                "master_public_key": master_pubkey,
                "backup_date": time.time(),
                "version": "1.0"
            }
            
            with open(backup_path, 'w') as f:
                import json
                json.dump(backup_data, f, indent=2)
            
            print("✅ Backup created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False
    
    def get_device_status(self) -> Dict:
        """Get current device status"""
        if not self.connected_device:
            return {"connected": False}
        
        status = {
            "connected": True,
            "device_info": self.device_info,
            "battery": None,
            "pin_enabled": None,
            "passphrase_enabled": None
        }
        
        try:
            # Get device status
            status_response = self._send_command("GET_STATUS")
            if status_response and len(status_response) > 1:
                flags = status_response[1]
                status["pin_enabled"] = bool(flags & 0x01)
                status["passphrase_enabled"] = bool(flags & 0x02)
                status["battery"] = (flags & 0xF0) >> 4  # Battery level (0-15)
            
        except Exception as e:
            print(f"⚠️ Status check error: {e}")
        
        return status
    
    def display_address_on_device(self, derivation_path: str = "m/44'/0'/0'/0") -> bool:
        """Display address on hardware wallet screen"""
        if not self.connected_device:
            print("❌ No device connected")
            return False
        
        print(f"📱 Displaying address on device...")
        
        try:
            # Get address for derivation path
            pubkey = self.get_public_key(derivation_path)
            if not pubkey:
                return False
            
            # Generate address
            address = hashlib.sha256(pubkey.encode()).hexdigest()
            
            # Send display command
            path_data = derivation_path.encode('utf-8')
            response = self._send_command("DISPLAY_ADDRESS", path_data)
            
            if response and response[0] == 0x00:
                print(f"✅ Address displayed: {address[:16]}...")
                print("   Confirm address on device screen")
                return True
            else:
                print("❌ Failed to display address")
                return False
                
        except Exception as e:
            print(f"❌ Display error: {e}")
            return False


class HardwareWalletManager:
    """Manager for multiple hardware wallets"""
    
    def __init__(self):
        self.wallets: Dict[str, HardwareWallet] = {}
        self.active_wallet: Optional[str] = None
    
    def add_wallet(self, name: str, wallet: HardwareWallet):
        """Add a hardware wallet to manager"""
        self.wallets[name] = wallet
        print(f"➕ Added hardware wallet: {name}")
    
    def remove_wallet(self, name: str):
        """Remove hardware wallet from manager"""
        if name in self.wallets:
            self.wallets[name].disconnect_device()
            del self.wallets[name]
            
            if self.active_wallet == name:
                self.active_wallet = None
            
            print(f"➖ Removed hardware wallet: {name}")
    
    def set_active_wallet(self, name: str) -> bool:
        """Set active hardware wallet"""
        if name not in self.wallets:
            print(f"❌ Wallet {name} not found")
            return False
        
        self.active_wallet = name
        print(f"🎯 Active wallet set to: {name}")
        return True
    
    def get_active_wallet(self) -> Optional[HardwareWallet]:
        """Get currently active hardware wallet"""
        if self.active_wallet:
            return self.wallets.get(self.active_wallet)
        return None
    
    def scan_all_wallets(self) -> Dict[str, List[Dict]]:
        """Scan all wallets for devices"""
        results = {}
        
        for name, wallet in self.wallets.items():
            devices = wallet.scan_devices()
            results[name] = devices
        
        return results
    
    def connect_all_available(self) -> Dict[str, bool]:
        """Connect to all available devices"""
        results = {}
        
        for name, wallet in self.wallets.items():
            devices = wallet.scan_devices()
            if devices:
                success = wallet.connect_device(devices[0]['path'])
                results[name] = success
            else:
                results[name] = False
        
        return results


# Utility functions
def auto_detect_and_connect() -> Optional[HardwareWallet]:
    """Auto-detect and connect to first available hardware wallet"""
    print("🔍 Auto-detecting hardware wallets...")
    
    wallet = HardwareWallet()
    devices = wallet.scan_devices()
    
    if devices:
        print(f"🔗 Connecting to {devices[0]['name']}...")
        if wallet.connect_device(devices[0]['path']):
            return wallet
    
    print("❌ No hardware wallets found")
    return None


HARDWARE_SUPPORT = True  # Add this line

def create_ledger_wallet() -> HardwareWallet:
    """Create Ledger-specific wallet interface"""
    wallet = HardwareWallet()
    # Add Ledger-specific initialization
    if HARDWARE_SUPPORT:
        print("Hardware wallet interface created")
    else:
        print("Hardware wallet support libraries not available - simulation mode")
    return wallet


def create_trezor_wallet() -> HardwareWallet:
    """Create Trezor-specific wallet interface"""
    wallet = HardwareWallet()
    # Add Trezor-specific initialization
    print("🔷 Trezor wallet interface created")
    return wallet
