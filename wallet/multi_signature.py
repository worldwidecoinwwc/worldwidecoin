# wallet/multi_signature.py
import json
import hashlib
from typing import List, Dict, Tuple, Optional
from ecdsa import SigningKey, VerifyingKey, SECP256k1
from core.transaction import Transaction


class MultiSigWallet:
    """Multi-signature wallet implementation (M-of-N)"""
    
    def __init__(self, required_signatures: int, total_signers: int):
        """
        Initialize multi-signature wallet
        
        Args:
            required_signatures: M - minimum signatures needed
            total_signers: N - total number of signers
        """
        if required_signatures > total_signers:
            raise ValueError("Required signatures cannot exceed total signers")
        
        self.m = required_signatures  # M in M-of-N
        self.n = total_signers     # N in M-of-N
        
        self.signers: List[Dict] = []  # List of signer info
        self.signatures: List[str] = []  # Collected signatures
        self.redeem_script: Optional[str] = None
        
        print(f"🔐 Multi-sig wallet created: {self.m}-of-{self.n}")
    
    def add_signer(self, public_key: str, name: str = "") -> int:
        """
        Add a signer to the multi-signature wallet
        
        Returns:
            signer index
        """
        signer_info = {
            "public_key": public_key,
            "name": name or f"Signer_{len(self.signers) + 1}",
            "index": len(self.signers)
        }
        
        self.signers.append(signer_info)
        print(f"➕ Added signer: {signer_info['name']} ({public_key[:16]}...)")
        
        return signer_info["index"]
    
    def remove_signer(self, signer_index: int) -> bool:
        """
        Remove a signer from the wallet
        """
        if 0 <= signer_index < len(self.signers):
            removed = self.signers.pop(signer_index)
            print(f"➖ Removed signer: {removed['name']}")
            return True
        return False
    
    def generate_redeem_script(self) -> str:
        """
        Generate the redeem script for multi-signature
        """
        if len(self.signers) != self.n:
            raise ValueError(f"Need exactly {self.n} signers")
        
        # Create script: OP_M <pubkeys...> OP_N OP_CHECKMULTISIG
        pubkeys = [signer["public_key"] for signer in self.signers]
        
        script_data = {
            "type": "multisig",
            "m": self.m,
            "n": self.n,
            "pubkeys": pubkeys
        }
        
        self.redeem_script = json.dumps(script_data, sort_keys=True)
        
        # Create multi-sig address (hash of redeem script)
        address = hashlib.sha256(self.redeem_script.encode()).hexdigest()
        
        print(f"📝 Generated {self.m}-of-{self.n} redeem script")
        print(f"🔗 Multi-sig address: {address[:16]}...")
        
        return address
    
    def create_multi_sig_transaction(self, inputs: List, outputs: List, fee: float = 0.01) -> Dict:
        """
        Create a multi-signature transaction template
        
        Returns:
            Transaction template with signing requirements
        """
        if not self.redeem_script:
            self.generate_redeem_script()
        
        # Create transaction template
        tx_template = {
            "version": 1,
            "inputs": inputs,
            "outputs": outputs,
            "fee": fee,
            "locktime": 0,
            "multisig": {
                "required": self.m,
                "total": self.n,
                "redeem_script": self.redeem_script,
                "signers": self.signers,
                "signatures": []
            }
        }
        
        print(f"📋 Created multi-sig transaction template")
        print(f"   Requires {self.m} of {self.n} signatures")
        print(f"   Fee: {fee} WWC")
        
        return tx_template
    
    def sign_transaction(self, tx_template: Dict, private_key: SigningKey, signer_index: int) -> bool:
        """
        Sign a multi-signature transaction
        
        Returns:
            True if signature added successfully
        """
        # Verify signer index is valid
        if signer_index >= len(self.signers):
            print(f"❌ Invalid signer index: {signer_index}")
            return False
        
        # Verify this signer hasn't already signed
        existing_sigs = tx_template["multisig"]["signatures"]
        for sig in existing_sigs:
            if sig.get("signer_index") == signer_index:
                print(f"⚠️ Signer {signer_index} already signed")
                return False
        
        # Create transaction hash to sign
        tx_data = {
            "inputs": tx_template["inputs"],
            "outputs": tx_template["outputs"],
            "fee": tx_template["fee"],
            "locktime": tx_template["locktime"]
        }
        
        message = json.dumps(tx_data, sort_keys=True).encode()
        digest = hashlib.sha256(message).digest()
        
        # Sign with private key
        signature = private_key.sign_digest(digest).hex()
        
        # Add signature to transaction
        signature_data = {
            "signer_index": signer_index,
            "signature": signature,
            "public_key": private_key.get_verifying_key().to_string().hex()
        }
        
        tx_template["multisig"]["signatures"].append(signature_data)
        
        signer_name = self.signers[signer_index]["name"]
        print(f"✅ {signer_name} signed transaction ({len(existing_sigs) + 1}/{self.m})")
        
        return True
    
    def is_fully_signed(self, tx_template: Dict) -> bool:
        """
        Check if transaction has sufficient signatures
        """
        signatures = tx_template["multisig"]["signatures"]
        return len(signatures) >= self.m
    
    def validate_signatures(self, tx_template: Dict) -> bool:
        """
        Validate all signatures in the transaction
        """
        signatures = tx_template["multisig"]["signatures"]
        
        if len(signatures) < self.m:
            print(f"❌ Insufficient signatures: {len(signatures)}/{self.m}")
            return False
        
        # Create transaction hash for verification
        tx_data = {
            "inputs": tx_template["inputs"],
            "outputs": tx_template["outputs"],
            "fee": tx_template["fee"],
            "locktime": tx_template["locktime"]
        }
        
        message = json.dumps(tx_data, sort_keys=True).encode()
        digest = hashlib.sha256(message).digest()
        
        # Verify each signature
        valid_sigs = 0
        for sig_data in signatures:
            try:
                # Get public key from signature
                pub_key_hex = sig_data["public_key"]
                pub_key = VerifyingKey.from_string(bytes.fromhex(pub_key))
                
                # Verify signature
                signature = bytes.fromhex(sig_data["signature"])
                if pub_key.verify_digest(signature, digest):
                    valid_sigs += 1
                else:
                    print(f"❌ Invalid signature from signer {sig_data['signer_index']}")
                    
            except Exception as e:
                print(f"❌ Signature verification error: {e}")
        
        is_valid = valid_sigs >= self.m
        print(f"🔍 Signature validation: {valid_sigs}/{len(signatures)} valid")
        
        return is_valid
    
    def finalize_transaction(self, tx_template: Dict) -> Transaction:
        """
        Convert multi-signature transaction template to standard Transaction
        """
        if not self.is_fully_signed(tx_template):
            raise ValueError("Transaction not fully signed")
        
        if not self.validate_signatures(tx_template):
            raise ValueError("Invalid signatures")
        
        # Create standard transaction
        tx = Transaction(
            inputs=tx_template["inputs"],
            outputs=tx_template["outputs"]
        )
        
        # Add multi-signature metadata
        tx.multisig_info = {
            "is_multisig": True,
            "m": self.m,
            "n": self.n,
            "redeem_script": self.redeem_script,
            "signatures": tx_template["multisig"]["signatures"]
        }
        
        print(f"🎯 Multi-sig transaction finalized")
        print(f"   Type: {self.m}-of-{self.n}")
        print(f"   Signatures: {len(tx_template['multisig']['signatures'])}")
        
        return tx
    
    def get_signer_info(self, signer_index: int) -> Optional[Dict]:
        """Get information about a specific signer"""
        if 0 <= signer_index < len(self.signers):
            return self.signers[signer_index]
        return None
    
    def list_signers(self) -> List[Dict]:
        """List all signers"""
        return self.signers.copy()
    
    def get_status(self) -> Dict:
        """Get wallet status"""
        return {
            "type": "multisig",
            "m": self.m,
            "n": self.n,
            "total_signers": len(self.signers),
            "has_redeem_script": self.redeem_script is not None,
            "address": hashlib.sha256(self.redeem_script.encode()).hexdigest() if self.redeem_script else None
        }


class MultiSigTransactionBuilder:
    """Builder for creating multi-signature transactions"""
    
    def __init__(self, multisig_wallet: MultiSigWallet):
        self.wallet = multisig_wallet
        self.tx_template = None
    
    def create_transaction(self, inputs: List, outputs: List, fee: float = 0.01) -> 'MultiSigTransactionBuilder':
        """Start building a multi-signature transaction"""
        self.tx_template = self.wallet.create_multi_sig_transaction(inputs, outputs, fee)
        return self
    
    def add_signature(self, private_key: SigningKey, signer_index: int) -> 'MultiSigTransactionBuilder':
        """Add a signature to the transaction"""
        if not self.tx_template:
            raise ValueError("Transaction not created yet")
        
        self.wallet.sign_transaction(self.tx_template, private_key, signer_index)
        return self
    
    def is_ready(self) -> bool:
        """Check if transaction is ready to finalize"""
        if not self.tx_template:
            return False
        
        return self.wallet.is_fully_signed(self.tx_template)
    
    def finalize(self) -> Transaction:
        """Finalize the multi-signature transaction"""
        if not self.is_ready():
            raise ValueError("Transaction not fully signed")
        
        return self.wallet.finalize_transaction(self.tx_template)
    
    def get_status(self) -> Dict:
        """Get current transaction status"""
        if not self.tx_template:
            return {"status": "not_created"}
        
        signatures = self.tx_template["multisig"]["signatures"]
        required = self.tx_template["multisig"]["required"]
        
        return {
            "status": "building",
            "signatures": len(signatures),
            "required": required,
            "ready": len(signatures) >= required,
            "m": self.wallet.m,
            "n": self.wallet.n
        }


# Utility functions for multi-signature operations
def create_2of3_multisig() -> MultiSigWallet:
    """Create a common 2-of-3 multi-signature wallet"""
    return MultiSigWallet(required_signatures=2, total_signers=3)


def create_corporate_multisig(directors: List[str], required: int = None) -> MultiSigWallet:
    """
    Create a corporate multi-signature wallet
    
    Args:
        directors: List of director public keys
        required: Required signatures (defaults to majority)
    """
    total = len(directors)
    if required is None:
        required = (total // 2) + 1  # Simple majority
    
    wallet = MultiSigWallet(required_signatures=required, total_signers=total)
    
    for i, pub_key in enumerate(directors):
        wallet.add_signer(pub_key, f"Director_{i+1}")
    
    return wallet


def validate_multisig_transaction(tx: Transaction) -> bool:
    """
    Validate a multi-signature transaction
    """
    if not hasattr(tx, 'multisig_info'):
        return True  # Not a multi-sig transaction
    
    multisig_info = tx.multisig_info
    
    # Check required signatures
    signatures = multisig_info.get("signatures", [])
    required = multisig_info.get("m", 1)
    
    if len(signatures) < required:
        return False
    
    # Verify each signature
    # (Implementation would depend on your specific verification logic)
    
    return True
