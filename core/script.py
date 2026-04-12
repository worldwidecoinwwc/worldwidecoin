# core/script.py
import hashlib
import json
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from ecdsa import VerifyingKey, SECP256k1, BadSignatureError


class OpCode(Enum):
    """Script operation codes"""
    # Constants
    OP_0 = 0x00
    OP_1 = 0x51
    OP_16 = 0x60
    
    # Flow control
    OP_IF = 0x63
    OP_NOTIF = 0x64
    OP_ELSE = 0x67
    OP_ENDIF = 0x68
    OP_VERIFY = 0x69
    OP_RETURN = 0x6a
    
    # Stack operations
    OP_TOALTSTACK = 0x6b
    OP_FROMALTSTACK = 0x6c
    OP_IFDUP = 0x73
    OP_DEPTH = 0x74
    OP_DROP = 0x75
    OP_DUP = 0x76
    OP_NIP = 0x77
    OP_OVER = 0x78
    OP_PICK = 0x79
    OP_ROLL = 0x7a
    OP_ROT = 0x7b
    OP_SWAP = 0x7c
    OP_TUCK = 0x7d
    OP_2DROP = 0x6d
    OP_2DUP = 0x6e
    OP_3DUP = 0x6f
    OP_2OVER = 0x70
    OP_2ROT = 0x71
    OP_2SWAP = 0x72
    
    # String operations
    OP_CAT = 0x7e
    OP_SUBSTR = 0x7f
    OP_LEFT = 0x80
    OP_RIGHT = 0x81
    OP_SIZE = 0x82
    
    # Bitwise logic
    OP_INVERT = 0x83
    OP_AND = 0x84
    OP_OR = 0x85
    OP_XOR = 0x86
    OP_EQUAL = 0x87
    OP_EQUALVERIFY = 0x88
    OP_RESERVED1 = 0x89
    OP_RESERVED2 = 0x8a
    
    # Arithmetic
    OP_1ADD = 0x8b
    OP_1SUB = 0x8c
    OP_2MUL = 0x8d
    OP_2DIV = 0x8e
    OP_NEGATE = 0x8f
    OP_ABS = 0x90
    OP_NOT = 0x91
    OP_0NOTEQUAL = 0x92
    OP_ADD = 0x93
    OP_SUB = 0x94
    OP_MUL = 0x95
    OP_DIV = 0x96
    OP_MOD = 0x97
    OP_LSHIFT = 0x98
    OP_RSHIFT = 0x99
    
    # Crypto
    OP_RIPEMD160 = 0xa6
    OP_SHA1 = 0xa7
    OP_SHA256 = 0xa8
    OP_HASH160 = 0xa9
    OP_HASH256 = 0xaa
    OP_CODESEPARATOR = 0xab
    OP_CHECKSIG = 0xac
    OP_CHECKSIGVERIFY = 0xad
    OP_CHECKMULTISIG = 0xae
    OP_CHECKMULTISIGVERIFY = 0xaf
    
    # Locktime
    OP_CHECKLOCKTIMEVERIFY = 0xb1
    OP_CHECKSEQUENCEVERIFY = 0xb2


class ScriptError(Exception):
    """Script execution error"""
    def __init__(self, message: str, error_code: str = "SCRIPT_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class ScriptStack:
    """Script execution stack"""
    
    def __init__(self):
        self.items: List[bytes] = []
        self.alt_stack: List[bytes] = []
    
    def push(self, item: bytes):
        """Push item onto stack"""
        self.items.append(item)
    
    def pop(self) -> bytes:
        """Pop item from stack"""
        if not self.items:
            raise ScriptError("Stack underflow", "STACK_UNDERFLOW")
        return self.items.pop()
    
    def peek(self) -> bytes:
        """Peek at top item without removing"""
        if not self.items:
            raise ScriptError("Stack underflow", "STACK_UNDERFLOW")
        return self.items[-1]
    
    def size(self) -> int:
        """Get stack size"""
        return len(self.items)
    
    def swap(self, n: int):
        """Swap top item with nth item"""
        if n >= len(self.items):
            raise ScriptError("Invalid stack index for swap", "INVALID_SWAP")
        self.items[-1], self.items[-1-n] = self.items[-1-n], self.items[-1]
    
    def to_alt(self):
        """Move top item to alt stack"""
        if not self.items:
            raise ScriptError("Stack underflow", "STACK_UNDERFLOW")
        item = self.items.pop()
        self.alt_stack.append(item)
    
    def from_alt(self):
        """Move item from alt stack to main stack"""
        if not self.alt_stack:
            raise ScriptError("Alt stack underflow", "ALT_STACK_UNDERFLOW")
        item = self.alt_stack.pop()
        self.items.append(item)


class Script:
    """Bitcoin-like script interpreter"""
    
    def __init__(self):
        self.stack = ScriptStack()
        self.codeseparator = 0
        self.max_stack_size = 1000
        self.max_script_size = 10000
    
    def execute(self, script_sig: bytes, script_pubkey: bytes, tx: Dict = None, input_index: int = 0) -> bool:
        """
        Execute script
        
        Args:
            script_sig: Signature script (from transaction input)
            script_pubkey: Pubkey script (from UTXO)
            tx: Transaction data (for signature verification)
            input_index: Index of the input being verified
            
        Returns:
            True if script executed successfully, False otherwise
        """
        try:
            # Reset state
            self.stack = ScriptStack()
            self.codeseparator = 0
            
            # Execute script_sig
            if not self._execute_script_bytes(script_sig, tx, input_index):
                return False
            
            # Execute script_pubkey
            if not self._execute_script_bytes(script_pubkey, tx, input_index):
                return False
            
            # Check if stack has True value on top
            if self.stack.size() == 0:
                return False
            
            top_item = self.stack.pop()
            return self._cast_to_bool(top_item)
            
        except ScriptError:
            return False
        except Exception:
            return False
    
    def _execute_script_bytes(self, script: bytes, tx: Dict = None, input_index: int = 0) -> bool:
        """Execute script bytes"""
        if len(script) > self.max_script_size:
            raise ScriptError("Script too large", "SCRIPT_TOO_LARGE")
        
        i = 0
        while i < len(script):
            opcode = script[i]
            i += 1
            
            # Handle data push
            if opcode <= 0x4e:  # OP_PUSHDATA1, OP_PUSHDATA2, OP_PUSHDATA4
                data_size, data = self._parse_data_push(script, i, opcode)
                i += data_size
                self.stack.push(data)
                continue
            
            # Handle opcodes
            if not self._execute_opcode(opcode, script, i, tx, input_index):
                return False
        
        return True
    
    def _parse_data_push(self, script: bytes, pos: int, opcode: int) -> Tuple[int, bytes]:
        """Parse data push operation"""
        if opcode < 0x4c:  # Direct push
            size = opcode
            if pos + size > len(script):
                raise ScriptError("Invalid data push", "INVALID_PUSH")
            return size, script[pos:pos+size]
        
        elif opcode == 0x4c:  # OP_PUSHDATA1
            if pos >= len(script):
                raise ScriptError("Invalid OP_PUSHDATA1", "INVALID_PUSHDATA1")
            size = script[pos]
            pos += 1
            if pos + size > len(script):
                raise ScriptError("Invalid OP_PUSHDATA1 data", "INVALID_PUSHDATA1_DATA")
            return size + 1, script[pos:pos+size]
        
        elif opcode == 0x4d:  # OP_PUSHDATA2
            if pos + 2 > len(script):
                raise ScriptError("Invalid OP_PUSHDATA2", "INVALID_PUSHDATA2")
            size = int.from_bytes(script[pos:pos+2], 'little')
            pos += 2
            if pos + size > len(script):
                raise ScriptError("Invalid OP_PUSHDATA2 data", "INVALID_PUSHDATA2_DATA")
            return size + 2, script[pos:pos+size]
        
        elif opcode == 0x4e:  # OP_PUSHDATA4
            if pos + 4 > len(script):
                raise ScriptError("Invalid OP_PUSHDATA4", "INVALID_PUSHDATA4")
            size = int.from_bytes(script[pos:pos+4], 'little')
            pos += 4
            if pos + size > len(script):
                raise ScriptError("Invalid OP_PUSHDATA4 data", "INVALID_PUSHDATA4_DATA")
            return size + 4, script[pos:pos+size]
        
        else:
            raise ScriptError(f"Invalid push opcode: {opcode}", "INVALID_PUSH_OPCODE")
    
    def _execute_opcode(self, opcode: int, script: bytes, pos: int, tx: Dict = None, input_index: int = 0) -> bool:
        """Execute a single opcode"""
        try:
            op = OpCode(opcode)
        except ValueError:
            # Unknown opcode - disable
            return False
        
        # Stack operations
        if op == OpCode.OP_DUP:
            if self.stack.size() == 0:
                return False
            item = self.stack.peek()
            self.stack.push(item)
        
        elif op == OpCode.OP_DROP:
            if self.stack.size() == 0:
                return False
            self.stack.pop()
        
        elif op == OpCode.OP_2DROP:
            if self.stack.size() < 2:
                return False
            self.stack.pop()
            self.stack.pop()
        
        elif op == OpCode.OP_2DUP:
            if self.stack.size() < 2:
                return False
            item1 = self.stack.items[-2]
            item2 = self.stack.items[-1]
            self.stack.push(item1)
            self.stack.push(item2)
        
        elif op == OpCode.OP_SWAP:
            if self.stack.size() < 2:
                return False
            self.stack.swap(1)
        
        elif op == OpCode.OP_TOALTSTACK:
            self.stack.to_alt()
        
        elif op == OpCode.OP_FROMALTSTACK:
            self.stack.from_alt()
        
        # Arithmetic operations
        elif op == OpCode.OP_1ADD:
            if self.stack.size() == 0:
                return False
            item = self.stack.pop()
            value = self._cast_to_int(item)
            result = self._int_to_bytes(value + 1)
            self.stack.push(result)
        
        elif op == OpCode.OP_1SUB:
            if self.stack.size() == 0:
                return False
            item = self.stack.pop()
            value = self._cast_to_int(item)
            result = self._int_to_bytes(value - 1)
            self.stack.push(result)
        
        elif op == OpCode.OP_ADD:
            if self.stack.size() < 2:
                return False
            item1 = self.stack.pop()
            item2 = self.stack.pop()
            value1 = self._cast_to_int(item1)
            value2 = self._cast_to_int(item2)
            result = self._int_to_bytes(value1 + value2)
            self.stack.push(result)
        
        elif op == OpCode.OP_SUB:
            if self.stack.size() < 2:
                return False
            item1 = self.stack.pop()
            item2 = self.stack.pop()
            value1 = self._cast_to_int(item1)
            value2 = self._cast_to_int(item2)
            result = self._int_to_bytes(value1 - value2)
            self.stack.push(result)
        
        # Bitwise operations
        elif op == OpCode.OP_EQUAL:
            if self.stack.size() < 2:
                return False
            item1 = self.stack.pop()
            item2 = self.stack.pop()
            result = self._int_to_bytes(1 if item1 == item2 else 0)
            self.stack.push(result)
        
        elif op == OpCode.OP_EQUALVERIFY:
            if self.stack.size() < 2:
                return False
            item1 = self.stack.pop()
            item2 = self.stack.pop()
            if item1 != item2:
                return False
        
        # Crypto operations
        elif op == OpCode.OP_SHA256:
            if self.stack.size() == 0:
                return False
            item = self.stack.pop()
            hash_result = hashlib.sha256(item).digest()
            self.stack.push(hash_result)
        
        elif op == OpCode.OP_HASH160:
            if self.stack.size() == 0:
                return False
            item = self.stack.pop()
            sha256_hash = hashlib.sha256(item).digest()
            ripemd160_hash = hashlib.new('ripemd160', sha256_hash).digest()
            self.stack.push(ripemd160_hash)
        
        elif op == OpCode.OP_CHECKSIG:
            if self.stack.size() < 2:
                return False
            pubkey = self.stack.pop()
            signature = self.stack.pop()
            
            if not tx or input_index is None:
                return False
            
            # Create sighash
            sighash = self._create_sighash(tx, input_index)
            
            # Verify signature
            if self._verify_signature(pubkey, signature, sighash):
                self.stack.push(self._int_to_bytes(1))
            else:
                self.stack.push(self._int_to_bytes(0))
        
        elif op == OpCode.OP_CHECKMULTISIG:
            if self.stack.size() < 3:
                return False
            # Simplified multisig verification
            # In practice, this would be more complex
            return self._verify_multisig(tx, input_index)
        
        # Control flow
        elif op == OpCode.OP_IF:
            # Simplified IF implementation
            if self.stack.size() == 0:
                return False
            condition = self._cast_to_bool(self.stack.pop())
            if not condition:
                # Skip to OP_ELSE or OP_ENDIF
                return self._skip_to_else_or_endif(script, pos)
        
        elif op == OpCode.OP_ENDIF:
            # Just continue execution
            pass
        
        elif op == OpCode.OP_RETURN:
            # OP_RETURN immediately fails
            return False
        
        # Constants
        elif op == OpCode.OP_1:
            self.stack.push(self._int_to_bytes(1))
        
        elif op == OpCode.OP_0:
            self.stack.push(b'')
        
        else:
            # Unsupported opcode
            return False
        
        return True
    
    def _skip_to_else_or_endif(self, script: bytes, pos: int) -> bool:
        """Skip to OP_ELSE or OP_ENDIF"""
        depth = 1
        i = pos
        
        while i < len(script) and depth > 0:
            opcode = script[i]
            i += 1
            
            if opcode == OpCode.OP_IF.value or opcode == OpCode.OP_NOTIF.value:
                depth += 1
            elif opcode == OpCode.OP_ENDIF.value:
                depth -= 1
            elif opcode == OpCode.OP_ELSE.value and depth == 1:
                break
        
        return True
    
    def _verify_multisig(self, tx: Dict, input_index: int) -> bool:
        """Simplified multisig verification"""
        # This is a simplified implementation
        # In practice, multisig verification is more complex
        try:
            # Get number of signatures and pubkeys
            n_pubkeys = self._cast_to_int(self.stack.pop())
            pubkeys = []
            for _ in range(n_pubkeys):
                if self.stack.size() == 0:
                    return False
                pubkeys.append(self.stack.pop())
            
            n_sigs = self._cast_to_int(self.stack.pop())
            signatures = []
            for _ in range(n_sigs):
                if self.stack.size() == 0:
                    return False
                signatures.append(self.stack.pop())
            
            # Verify each signature against corresponding pubkey
            sighash = self._create_sighash(tx, input_index)
            
            for sig, pubkey in zip(signatures, pubkeys):
                if not self._verify_signature(pubkey, sig, sighash):
                    return False
            
            self.stack.push(self._int_to_bytes(1))
            return True
            
        except:
            return False
    
    def _create_sighash(self, tx: Dict, input_index: int) -> bytes:
        """Create signature hash for transaction"""
        # Simplified sighash creation
        # In practice, this would include sighash type and other details
        tx_copy = json.dumps(tx, sort_keys=True).encode()
        return hashlib.sha256(tx_copy).digest()
    
    def _verify_signature(self, pubkey: bytes, signature: bytes, message: bytes) -> bool:
        """Verify ECDSA signature"""
        try:
            # Convert pubkey bytes to VerifyingKey
            vk = VerifyingKey.from_string(pubkey, curve=SECP256k1)
            
            # Verify signature
            vk.verify_digest(signature, message)
            return True
            
        except BadSignatureError:
            return False
        except Exception:
            return False
    
    def _cast_to_bool(self, item: bytes) -> bool:
        """Cast bytes to boolean"""
        # Interpret as little-endian integer
        if len(item) == 0:
            return False
        
        # Check if any byte is non-zero
        for byte in item:
            if byte != 0:
                return True
        
        return False
    
    def _cast_to_int(self, item: bytes) -> int:
        """Cast bytes to integer"""
        if len(item) > 4:
            # Limit to 4 bytes for simplicity
            item = item[:4]
        
        return int.from_bytes(item, 'little', signed=True)
    
    def _int_to_bytes(self, value: int) -> bytes:
        """Convert integer to bytes"""
        if value == 0:
            return b''
        
        # Use little-endian
        byte_length = (value.bit_length() + 7) // 8
        return value.to_bytes(byte_length, 'little', signed=True)


class ScriptBuilder:
    """Helper class for building scripts"""
    
    @staticmethod
    def p2pkh(pubkey_hash: bytes) -> bytes:
        """Create Pay-to-Public-Key-Hash script"""
        script = bytearray()
        script.extend([OpCode.OP_DUP.value])
        script.extend([OpCode.OP_HASH160.value])
        script.append(len(pubkey_hash))
        script.extend(pubkey_hash)
        script.extend([OpCode.OP_EQUALVERIFY.value])
        script.extend([OpCode.OP_CHECKSIG.value])
        return bytes(script)
    
    @staticmethod
    def p2pk(pubkey: bytes) -> bytes:
        """Create Pay-to-Public-Key script"""
        script = bytearray()
        script.append(len(pubkey))
        script.extend(pubkey)
        script.extend([OpCode.OP_CHECKSIG.value])
        return bytes(script)
    
    @staticmethod
    def multisig(m: int, pubkeys: List[bytes]) -> bytes:
        """Create m-of-n multisig script"""
        script = bytearray()
        script.append(m)
        
        for pubkey in pubkeys:
            script.append(len(pubkey))
            script.extend(pubkey)
        
        script.append(len(pubkeys))
        script.extend([OpCode.OP_CHECKMULTISIG.value])
        return bytes(script)
    
    @staticmethod
    def create_signature_script(signature: bytes, pubkey: bytes) -> bytes:
        """Create signature script for P2PKH"""
        script = bytearray()
        script.append(len(signature))
        script.extend(signature)
        script.append(len(pubkey))
        script.extend(pubkey)
        return bytes(script)


# Utility functions
def create_p2pkh_script(pubkey: str) -> bytes:
    """Create P2PKH script from public key string"""
    pubkey_bytes = bytes.fromhex(pubkey)
    pubkey_hash = hashlib.new('ripemd160', hashlib.sha256(pubkey_bytes).digest()).digest()
    return ScriptBuilder.p2pkh(pubkey_hash)


def create_p2pk_script(pubkey: str) -> bytes:
    """Create P2PK script from public key string"""
    pubkey_bytes = bytes.fromhex(pubkey)
    return ScriptBuilder.p2pk(pubkey_bytes)


def verify_script(script_sig: str, script_pubkey: str, tx: Dict = None, input_index: int = 0) -> bool:
    """Verify script execution"""
    script_sig_bytes = bytes.fromhex(script_sig) if script_sig else b''
    script_pubkey_bytes = bytes.fromhex(script_pubkey) if script_pubkey else b''
    
    script = Script()
    return script.execute(script_sig_bytes, script_pubkey_bytes, tx, input_index)


def script_to_hex(script: bytes) -> str:
    """Convert script to hex string"""
    return script.hex()


def hex_to_script(hex_string: str) -> bytes:
    """Convert hex string to script bytes"""
    return bytes.fromhex(hex_string)
