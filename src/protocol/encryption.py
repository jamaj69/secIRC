"""
End-to-end encryption for anonymous messaging.
Implements multiple encryption layers for maximum security.
"""

import os
import hashlib
from typing import Tuple, Optional
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from nacl.public import PrivateKey, PublicKey, Box
from nacl.secret import SecretBox
from nacl.utils import random
import argon2


class EndToEndEncryption:
    """Handles end-to-end encryption for anonymous messages."""
    
    def __init__(self):
        self.salt_length = 32
        self.nonce_length = 24
        self.key_length = 32
    
    def generate_keypair(self) -> Tuple[bytes, bytes]:
        """Generate a new RSA keypair for user identity."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        
        public_key = private_key.public_key()
        
        # Serialize keys
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return private_pem, public_pem
    
    def encrypt_private_key(self, private_key: bytes, password: str) -> bytes:
        """Encrypt private key with user password using Argon2."""
        # Generate salt
        salt = os.urandom(self.salt_length)
        
        # Derive key from password using Argon2
        key = argon2.hash_password(
            password.encode('utf-8'),
            salt=salt,
            time_cost=3,
            memory_cost=65536,
            parallelism=4,
            hash_len=32
        )
        
        # Encrypt private key with AES
        iv = os.urandom(16)
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv)
        )
        encryptor = cipher.encryptor()
        
        # Pad the private key to block size
        padded_key = self._pad_data(private_key, 16)
        encrypted_key = encryptor.update(padded_key) + encryptor.finalize()
        
        # Combine salt + iv + encrypted_key
        return salt + iv + encrypted_key
    
    def decrypt_private_key(self, encrypted_key: bytes, password: str) -> bytes:
        """Decrypt private key with user password."""
        if len(encrypted_key) < self.salt_length + 16:
            raise ValueError("Invalid encrypted key format")
        
        # Extract components
        salt = encrypted_key[:self.salt_length]
        iv = encrypted_key[self.salt_length:self.salt_length + 16]
        encrypted_data = encrypted_key[self.salt_length + 16:]
        
        # Derive key from password
        key = argon2.hash_password(
            password.encode('utf-8'),
            salt=salt,
            time_cost=3,
            memory_cost=65536,
            parallelism=4,
            hash_len=32
        )
        
        # Decrypt
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv)
        )
        decryptor = cipher.decryptor()
        
        decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()
        
        # Remove padding
        return self._unpad_data(decrypted_data)
    
    def encrypt_message(self, message: bytes, recipient_public_key: bytes, 
                       sender_private_key: bytes) -> bytes:
        """Encrypt message for recipient using hybrid encryption."""
        # Generate ephemeral keypair for this message
        ephemeral_private = PrivateKey.generate()
        ephemeral_public = ephemeral_private.public_key
        
        # Create shared secret
        recipient_key = PublicKey(recipient_public_key)
        box = Box(ephemeral_private, recipient_key)
        
        # Encrypt message
        nonce = random(self.nonce_length)
        encrypted_message = box.encrypt(message, nonce)
        
        # Sign with sender's private key
        signature = self._sign_message(encrypted_message, sender_private_key)
        
        # Combine: ephemeral_public + nonce + encrypted_message + signature
        return (ephemeral_public.encode() + nonce + 
                encrypted_message + signature)
    
    def decrypt_message(self, encrypted_data: bytes, recipient_private_key: bytes,
                       sender_public_key: bytes) -> bytes:
        """Decrypt message from sender."""
        if len(encrypted_data) < 32 + self.nonce_length + 64:
            raise ValueError("Invalid encrypted message format")
        
        # Extract components
        ephemeral_public = encrypted_data[:32]
        nonce = encrypted_data[32:32 + self.nonce_length]
        encrypted_message = encrypted_data[32 + self.nonce_length:-64]
        signature = encrypted_data[-64:]
        
        # Verify signature
        if not self._verify_signature(encrypted_message, signature, sender_public_key):
            raise ValueError("Invalid message signature")
        
        # Decrypt message
        ephemeral_key = PublicKey(ephemeral_public)
        recipient_key = PrivateKey(recipient_private_key)
        box = Box(recipient_key, ephemeral_key)
        
        decrypted_message = box.decrypt(encrypted_message, nonce)
        return decrypted_message
    
    def create_relay_encryption(self, relay_public_key: bytes) -> Tuple[bytes, bytes]:
        """Create encryption layer for relay server."""
        # Generate session key
        session_key = os.urandom(self.key_length)
        
        # Encrypt session key with relay's public key
        relay_key = serialization.load_pem_public_key(relay_public_key)
        encrypted_session_key = relay_key.encrypt(
            session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return session_key, encrypted_session_key
    
    def encrypt_for_relay(self, data: bytes, session_key: bytes) -> bytes:
        """Encrypt data for relay transmission."""
        nonce = os.urandom(12)  # AES-GCM nonce
        cipher = Cipher(
            algorithms.AES(session_key),
            modes.GCM(nonce)
        )
        encryptor = cipher.encryptor()
        
        encrypted_data = encryptor.update(data) + encryptor.finalize()
        
        # Return nonce + encrypted_data + tag
        return nonce + encrypted_data + encryptor.tag
    
    def decrypt_from_relay(self, encrypted_data: bytes, session_key: bytes) -> bytes:
        """Decrypt data from relay."""
        if len(encrypted_data) < 28:  # 12 nonce + 16 tag
            raise ValueError("Invalid relay encrypted data")
        
        nonce = encrypted_data[:12]
        tag = encrypted_data[-16:]
        encrypted_payload = encrypted_data[12:-16]
        
        cipher = Cipher(
            algorithms.AES(session_key),
            modes.GCM(nonce, tag)
        )
        decryptor = cipher.decryptor()
        
        return decryptor.update(encrypted_payload) + decryptor.finalize()
    
    def _sign_message(self, message: bytes, private_key: bytes) -> bytes:
        """Sign message with private key."""
        key = serialization.load_pem_private_key(private_key, password=None)
        signature = key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature
    
    def _verify_signature(self, message: bytes, signature: bytes, 
                         public_key: bytes) -> bool:
        """Verify message signature."""
        try:
            key = serialization.load_pem_public_key(public_key)
            key.verify(
                signature,
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False
    
    def _pad_data(self, data: bytes, block_size: int) -> bytes:
        """PKCS7 padding."""
        padding_length = block_size - (len(data) % block_size)
        padding = bytes([padding_length] * padding_length)
        return data + padding
    
    def _unpad_data(self, data: bytes) -> bytes:
        """Remove PKCS7 padding."""
        padding_length = data[-1]
        return data[:-padding_length]
