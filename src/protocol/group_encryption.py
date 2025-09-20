"""
Group Encryption System.
Implements group message encryption/decryption with proper key management
for secure group communication while maintaining end-to-end encryption.
"""

import asyncio
import hashlib
import json
import os
import time
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict

from .encryption import EndToEndEncryption


class GroupKeyAlgorithm(Enum):
    """Group key encryption algorithms."""
    
    AES_256_GCM = "aes_256_gcm"
    CHACHA20_POLY1305 = "chacha20_poly1305"
    XSALSA20_POLY1305 = "xsalsa20_poly1305"


class KeyDerivationFunction(Enum):
    """Key derivation functions."""
    
    PBKDF2 = "pbkdf2"
    ARGON2 = "argon2"
    SCRYPT = "scrypt"


@dataclass
class GroupKeyMaterial:
    """Group key material for encryption."""
    
    group_id: bytes                      # Group identifier
    key_id: bytes                        # Key identifier
    algorithm: GroupKeyAlgorithm         # Encryption algorithm
    key: bytes                           # Encryption key
    nonce: bytes                         # Nonce/IV
    salt: bytes                          # Salt for key derivation
    created_at: int                      # Creation timestamp
    expires_at: int                      # Expiration timestamp
    version: int                         # Key version
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "group_id": self.group_id.hex(),
            "key_id": self.key_id.hex(),
            "algorithm": self.algorithm.value,
            "key": self.key.hex(),
            "nonce": self.nonce.hex(),
            "salt": self.salt.hex(),
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "version": self.version
        }


@dataclass
class EncryptedGroupMessage:
    """Encrypted group message."""
    
    message_id: bytes                    # Message identifier
    group_id: bytes                      # Group identifier
    sender_id: bytes                     # Sender identifier
    encrypted_content: bytes             # Encrypted message content
    key_id: bytes                        # Group key identifier
    nonce: bytes                         # Nonce used for encryption
    timestamp: int                       # Message timestamp
    signature: bytes                     # Message signature
    algorithm: GroupKeyAlgorithm         # Encryption algorithm used
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "message_id": self.message_id.hex(),
            "group_id": self.group_id.hex(),
            "sender_id": self.sender_id.hex(),
            "encrypted_content": self.encrypted_content.hex(),
            "key_id": self.key_id.hex(),
            "nonce": self.nonce.hex(),
            "timestamp": self.timestamp,
            "signature": self.signature.hex(),
            "algorithm": self.algorithm.value
        }


@dataclass
class GroupKeyDistribution:
    """Group key distribution to members."""
    
    group_id: bytes                      # Group identifier
    key_id: bytes                        # Key identifier
    encrypted_keys: Dict[bytes, bytes]   # User ID -> encrypted group key
    key_material: GroupKeyMaterial       # Group key material
    distribution_timestamp: int          # Distribution timestamp
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "group_id": self.group_id.hex(),
            "key_id": self.key_id.hex(),
            "encrypted_keys": {user_id.hex(): key.hex() for user_id, key in self.encrypted_keys.items()},
            "key_material": self.key_material.to_dict(),
            "distribution_timestamp": self.distribution_timestamp
        }


class GroupEncryptionSystem:
    """Group encryption system for secure group communication."""
    
    def __init__(self, encryption: EndToEndEncryption):
        self.encryption = encryption
        
        # Group key management
        self.group_keys: Dict[bytes, Dict[bytes, GroupKeyMaterial]] = defaultdict(dict)  # group_id -> key_id -> key_material
        self.active_group_keys: Dict[bytes, GroupKeyMaterial] = {}  # group_id -> active_key_material
        self.user_group_keys: Dict[bytes, Dict[bytes, bytes]] = defaultdict(dict)  # user_id -> group_id -> encrypted_key
        
        # Key distribution
        self.key_distributions: Dict[bytes, GroupKeyDistribution] = {}  # key_id -> distribution
        
        # Configuration
        self.default_algorithm = GroupKeyAlgorithm.AES_256_GCM
        self.key_size = 32  # 256 bits
        self.nonce_size = 12  # 96 bits for GCM
        self.salt_size = 16  # 128 bits
        self.key_rotation_interval = 86400  # 24 hours
        
        # Statistics
        self.stats = {
            "keys_generated": 0,
            "keys_distributed": 0,
            "messages_encrypted": 0,
            "messages_decrypted": 0,
            "key_rotations": 0,
            "encryption_errors": 0,
            "decryption_errors": 0
        }
    
    # Group Key Generation
    
    async def generate_group_key(self, group_id: bytes, group_members: List[bytes]) -> GroupKeyMaterial:
        """Generate a new group key."""
        try:
            # Generate random key material
            key = os.urandom(self.key_size)
            nonce = os.urandom(self.nonce_size)
            salt = os.urandom(self.salt_size)
            
            # Create key ID
            key_id = hashlib.sha256(
                group_id + key + nonce + salt + str(time.time()).encode()
            ).digest()[:16]
            
            # Create key material
            key_material = GroupKeyMaterial(
                group_id=group_id,
                key_id=key_id,
                algorithm=self.default_algorithm,
                key=key,
                nonce=nonce,
                salt=salt,
                created_at=int(time.time()),
                expires_at=int(time.time()) + self.key_rotation_interval,
                version=len(self.group_keys[group_id]) + 1
            )
            
            # Store key material
            self.group_keys[group_id][key_id] = key_material
            self.active_group_keys[group_id] = key_material
            
            # Distribute key to group members
            await self._distribute_group_key(key_material, group_members)
            
            self.stats["keys_generated"] += 1
            return key_material
            
        except Exception as e:
            print(f"❌ Failed to generate group key: {e}")
            self.stats["encryption_errors"] += 1
            raise
    
    async def _distribute_group_key(self, key_material: GroupKeyMaterial, group_members: List[bytes]) -> None:
        """Distribute group key to all members."""
        try:
            encrypted_keys = {}
            
            for user_id in group_members:
                # Get user's public key (simplified - in real implementation, fetch from identity system)
                user_public_key = await self._get_user_public_key(user_id)
                
                # Encrypt group key with user's public key
                encrypted_group_key = self.encryption.encrypt_message(key_material.key, user_public_key)
                encrypted_keys[user_id] = encrypted_group_key
                
                # Store encrypted key for user
                self.user_group_keys[user_id][key_material.group_id] = encrypted_group_key
            
            # Create key distribution
            key_distribution = GroupKeyDistribution(
                group_id=key_material.group_id,
                key_id=key_material.key_id,
                encrypted_keys=encrypted_keys,
                key_material=key_material,
                distribution_timestamp=int(time.time())
            )
            
            # Store key distribution
            self.key_distributions[key_material.key_id] = key_distribution
            
            self.stats["keys_distributed"] += 1
            
        except Exception as e:
            print(f"❌ Failed to distribute group key: {e}")
            self.stats["encryption_errors"] += 1
            raise
    
    async def _get_user_public_key(self, user_id: bytes) -> bytes:
        """Get user's public key (simplified implementation)."""
        # In real implementation, fetch from identity system
        # For now, generate a dummy key
        return os.urandom(32)
    
    # Message Encryption
    
    async def encrypt_group_message(self, group_id: bytes, sender_id: bytes, content: bytes) -> Optional[EncryptedGroupMessage]:
        """Encrypt a message for a group."""
        try:
            # Get active group key
            if group_id not in self.active_group_keys:
                print(f"❌ No active key for group {group_id.hex()}")
                return None
            
            key_material = self.active_group_keys[group_id]
            
            # Generate message ID
            message_id = hashlib.sha256(
                group_id + sender_id + content + str(time.time()).encode()
            ).digest()[:16]
            
            # Generate unique nonce for this message
            message_nonce = os.urandom(self.nonce_size)
            
            # Encrypt message content
            encrypted_content = await self._encrypt_content(content, key_material.key, message_nonce, key_material.algorithm)
            
            # Create message signature
            signature = await self._sign_message(message_id, group_id, sender_id, encrypted_content, key_material.key)
            
            # Create encrypted message
            encrypted_message = EncryptedGroupMessage(
                message_id=message_id,
                group_id=group_id,
                sender_id=sender_id,
                encrypted_content=encrypted_content,
                key_id=key_material.key_id,
                nonce=message_nonce,
                timestamp=int(time.time()),
                signature=signature,
                algorithm=key_material.algorithm
            )
            
            self.stats["messages_encrypted"] += 1
            return encrypted_message
            
        except Exception as e:
            print(f"❌ Failed to encrypt group message: {e}")
            self.stats["encryption_errors"] += 1
            return None
    
    async def _encrypt_content(self, content: bytes, key: bytes, nonce: bytes, algorithm: GroupKeyAlgorithm) -> bytes:
        """Encrypt message content."""
        try:
            if algorithm == GroupKeyAlgorithm.AES_256_GCM:
                return await self._encrypt_aes_gcm(content, key, nonce)
            elif algorithm == GroupKeyAlgorithm.CHACHA20_POLY1305:
                return await self._encrypt_chacha20_poly1305(content, key, nonce)
            elif algorithm == GroupKeyAlgorithm.XSALSA20_POLY1305:
                return await self._encrypt_xsalsa20_poly1305(content, key, nonce)
            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")
                
        except Exception as e:
            print(f"❌ Failed to encrypt content: {e}")
            raise
    
    async def _encrypt_aes_gcm(self, content: bytes, key: bytes, nonce: bytes) -> bytes:
        """Encrypt using AES-256-GCM."""
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            
            aesgcm = AESGCM(key)
            encrypted_data = aesgcm.encrypt(nonce, content, None)
            return encrypted_data
            
        except Exception as e:
            print(f"❌ AES-GCM encryption failed: {e}")
            raise
    
    async def _encrypt_chacha20_poly1305(self, content: bytes, key: bytes, nonce: bytes) -> bytes:
        """Encrypt using ChaCha20-Poly1305."""
        try:
            from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
            
            chacha = ChaCha20Poly1305(key)
            encrypted_data = chacha.encrypt(nonce, content, None)
            return encrypted_data
            
        except Exception as e:
            print(f"❌ ChaCha20-Poly1305 encryption failed: {e}")
            raise
    
    async def _encrypt_xsalsa20_poly1305(self, content: bytes, key: bytes, nonce: bytes) -> bytes:
        """Encrypt using XSalsa20-Poly1305."""
        try:
            from nacl.secret import SecretBox
            
            box = SecretBox(key)
            encrypted_data = box.encrypt(content, nonce)
            return encrypted_data
            
        except Exception as e:
            print(f"❌ XSalsa20-Poly1305 encryption failed: {e}")
            raise
    
    async def _sign_message(self, message_id: bytes, group_id: bytes, sender_id: bytes, 
                           encrypted_content: bytes, key: bytes) -> bytes:
        """Sign message for integrity."""
        try:
            # Create message hash
            message_data = message_id + group_id + sender_id + encrypted_content
            message_hash = hashlib.sha256(message_data).digest()
            
            # Sign with group key (simplified)
            signature = hashlib.hmac.new(key, message_hash, hashlib.sha256).digest()
            return signature
            
        except Exception as e:
            print(f"❌ Failed to sign message: {e}")
            raise
    
    # Message Decryption
    
    async def decrypt_group_message(self, encrypted_message: EncryptedGroupMessage, user_id: bytes) -> Optional[bytes]:
        """Decrypt a group message for a user."""
        try:
            # Get group key for user
            if user_id not in self.user_group_keys:
                print(f"❌ No group keys for user {user_id.hex()}")
                return None
            
            if encrypted_message.group_id not in self.user_group_keys[user_id]:
                print(f"❌ No key for group {encrypted_message.group_id.hex()}")
                return None
            
            # Get encrypted group key
            encrypted_group_key = self.user_group_keys[user_id][encrypted_message.group_id]
            
            # Decrypt group key with user's private key
            group_key = await self._decrypt_group_key(encrypted_group_key, user_id)
            if not group_key:
                print(f"❌ Failed to decrypt group key for user {user_id.hex()}")
                return None
            
            # Verify message signature
            if not await self._verify_message_signature(encrypted_message, group_key):
                print(f"❌ Invalid message signature")
                return None
            
            # Decrypt message content
            content = await self._decrypt_content(
                encrypted_message.encrypted_content,
                group_key,
                encrypted_message.nonce,
                encrypted_message.algorithm
            )
            
            self.stats["messages_decrypted"] += 1
            return content
            
        except Exception as e:
            print(f"❌ Failed to decrypt group message: {e}")
            self.stats["decryption_errors"] += 1
            return None
    
    async def _decrypt_group_key(self, encrypted_group_key: bytes, user_id: bytes) -> Optional[bytes]:
        """Decrypt group key with user's private key."""
        try:
            # Get user's private key (simplified - in real implementation, fetch from identity system)
            user_private_key = await self._get_user_private_key(user_id)
            
            # Decrypt group key
            group_key = self.encryption.decrypt_message(encrypted_group_key, user_private_key)
            return group_key
            
        except Exception as e:
            print(f"❌ Failed to decrypt group key: {e}")
            return None
    
    async def _get_user_private_key(self, user_id: bytes) -> bytes:
        """Get user's private key (simplified implementation)."""
        # In real implementation, fetch from identity system
        # For now, generate a dummy key
        return os.urandom(32)
    
    async def _verify_message_signature(self, encrypted_message: EncryptedGroupMessage, group_key: bytes) -> bool:
        """Verify message signature."""
        try:
            # Create message hash
            message_data = (
                encrypted_message.message_id +
                encrypted_message.group_id +
                encrypted_message.sender_id +
                encrypted_message.encrypted_content
            )
            message_hash = hashlib.sha256(message_data).digest()
            
            # Verify signature
            expected_signature = hashlib.hmac.new(group_key, message_hash, hashlib.sha256).digest()
            return expected_signature == encrypted_message.signature
            
        except Exception as e:
            print(f"❌ Failed to verify message signature: {e}")
            return False
    
    async def _decrypt_content(self, encrypted_content: bytes, key: bytes, nonce: bytes, algorithm: GroupKeyAlgorithm) -> bytes:
        """Decrypt message content."""
        try:
            if algorithm == GroupKeyAlgorithm.AES_256_GCM:
                return await self._decrypt_aes_gcm(encrypted_content, key, nonce)
            elif algorithm == GroupKeyAlgorithm.CHACHA20_POLY1305:
                return await self._decrypt_chacha20_poly1305(encrypted_content, key, nonce)
            elif algorithm == GroupKeyAlgorithm.XSALSA20_POLY1305:
                return await self._decrypt_xsalsa20_poly1305(encrypted_content, key, nonce)
            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")
                
        except Exception as e:
            print(f"❌ Failed to decrypt content: {e}")
            raise
    
    async def _decrypt_aes_gcm(self, encrypted_content: bytes, key: bytes, nonce: bytes) -> bytes:
        """Decrypt using AES-256-GCM."""
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            
            aesgcm = AESGCM(key)
            decrypted_data = aesgcm.decrypt(nonce, encrypted_content, None)
            return decrypted_data
            
        except Exception as e:
            print(f"❌ AES-GCM decryption failed: {e}")
            raise
    
    async def _decrypt_chacha20_poly1305(self, encrypted_content: bytes, key: bytes, nonce: bytes) -> bytes:
        """Decrypt using ChaCha20-Poly1305."""
        try:
            from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
            
            chacha = ChaCha20Poly1305(key)
            decrypted_data = chacha.decrypt(nonce, encrypted_content, None)
            return decrypted_data
            
        except Exception as e:
            print(f"❌ ChaCha20-Poly1305 decryption failed: {e}")
            raise
    
    async def _decrypt_xsalsa20_poly1305(self, encrypted_content: bytes, key: bytes, nonce: bytes) -> bytes:
        """Decrypt using XSalsa20-Poly1305."""
        try:
            from nacl.secret import SecretBox
            
            box = SecretBox(key)
            decrypted_data = box.decrypt(encrypted_content)
            return decrypted_data
            
        except Exception as e:
            print(f"❌ XSalsa20-Poly1305 decryption failed: {e}")
            raise
    
    # Key Management
    
    async def rotate_group_key(self, group_id: bytes, group_members: List[bytes]) -> Optional[GroupKeyMaterial]:
        """Rotate group key."""
        try:
            # Generate new group key
            new_key_material = await self.generate_group_key(group_id, group_members)
            
            # Mark old keys as inactive
            for key_id, key_material in self.group_keys[group_id].items():
                if key_id != new_key_material.key_id:
                    key_material.expires_at = int(time.time())
            
            self.stats["key_rotations"] += 1
            return new_key_material
            
        except Exception as e:
            print(f"❌ Failed to rotate group key: {e}")
            return None
    
    async def add_user_to_group(self, group_id: bytes, user_id: bytes) -> bool:
        """Add user to group and distribute group key."""
        try:
            if group_id not in self.active_group_keys:
                print(f"❌ No active key for group {group_id.hex()}")
                return False
            
            key_material = self.active_group_keys[group_id]
            
            # Get user's public key
            user_public_key = await self._get_user_public_key(user_id)
            
            # Encrypt group key with user's public key
            encrypted_group_key = self.encryption.encrypt_message(key_material.key, user_public_key)
            
            # Store encrypted key for user
            self.user_group_keys[user_id][group_id] = encrypted_group_key
            
            # Update key distribution
            if key_material.key_id in self.key_distributions:
                self.key_distributions[key_material.key_id].encrypted_keys[user_id] = encrypted_group_key
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to add user to group: {e}")
            return False
    
    async def remove_user_from_group(self, group_id: bytes, user_id: bytes) -> bool:
        """Remove user from group and rotate group key."""
        try:
            # Remove user's group key
            if user_id in self.user_group_keys and group_id in self.user_group_keys[user_id]:
                del self.user_group_keys[user_id][group_id]
            
            # Rotate group key to exclude user
            # Get current group members (simplified)
            group_members = [uid for uid in self.user_group_keys.keys() if group_id in self.user_group_keys[uid]]
            group_members.append(user_id)  # Include user for rotation
            
            await self.rotate_group_key(group_id, group_members)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to remove user from group: {e}")
            return False
    
    # Public API
    
    def get_group_key_info(self, group_id: bytes) -> Optional[Dict]:
        """Get group key information."""
        if group_id not in self.active_group_keys:
            return None
        
        key_material = self.active_group_keys[group_id]
        return {
            "group_id": group_id.hex(),
            "key_id": key_material.key_id.hex(),
            "algorithm": key_material.algorithm.value,
            "version": key_material.version,
            "created_at": key_material.created_at,
            "expires_at": key_material.expires_at,
            "is_active": True
        }
    
    def get_user_group_keys(self, user_id: bytes) -> List[Dict]:
        """Get group keys for a user."""
        if user_id not in self.user_group_keys:
            return []
        
        group_keys = []
        for group_id, encrypted_key in self.user_group_keys[user_id].items():
            group_key_info = self.get_group_key_info(group_id)
            if group_key_info:
                group_key_info["encrypted_key"] = encrypted_key.hex()
                group_keys.append(group_key_info)
        
        return group_keys
    
    def get_encryption_stats(self) -> Dict:
        """Get encryption statistics."""
        return {
            **self.stats,
            "active_group_keys_count": len(self.active_group_keys),
            "total_group_keys_count": sum(len(keys) for keys in self.group_keys.values()),
            "user_group_keys_count": sum(len(keys) for keys in self.user_group_keys.values()),
            "key_distributions_count": len(self.key_distributions)
        }
    
    def get_key_distribution(self, key_id: bytes) -> Optional[Dict]:
        """Get key distribution information."""
        if key_id not in self.key_distributions:
            return None
        
        return self.key_distributions[key_id].to_dict()
