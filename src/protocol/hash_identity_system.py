"""
Hash-based identity system for anonymous communication.
All entities (users, groups, relays) are identified by cryptographic hashes.
"""

import hashlib
import time
from typing import Dict, Set, Optional, List, Tuple
from dataclasses import dataclass
from .message_types import HashIdentity, UserIdentity
from .encryption import EndToEndEncryption


@dataclass
class IdentityRegistry:
    """Registry of all known identities in the network."""
    
    # Hash -> Identity mapping
    identities: Dict[bytes, HashIdentity]
    
    # Type-based indexes
    user_identities: Set[bytes]  # Set of user hashes
    group_identities: Set[bytes]  # Set of group hashes
    relay_identities: Set[bytes]  # Set of relay hashes
    
    # Public key -> Hash mapping (for quick lookup)
    public_key_to_hash: Dict[bytes, bytes]
    
    def __init__(self):
        self.identities = {}
        self.user_identities = set()
        self.group_identities = set()
        self.relay_identities = set()
        self.public_key_to_hash = {}
    
    def register_identity(self, identity: HashIdentity) -> None:
        """Register a new identity."""
        self.identities[identity.identity_hash] = identity
        self.public_key_to_hash[identity.public_key] = identity.identity_hash
        
        # Update type-based indexes
        if identity.identity_type == "user":
            self.user_identities.add(identity.identity_hash)
        elif identity.identity_type == "group":
            self.group_identities.add(identity.identity_hash)
        elif identity.identity_type == "relay":
            self.relay_identities.add(identity.identity_hash)
    
    def get_identity(self, identity_hash: bytes) -> Optional[HashIdentity]:
        """Get identity by hash."""
        return self.identities.get(identity_hash)
    
    def get_identity_by_public_key(self, public_key: bytes) -> Optional[HashIdentity]:
        """Get identity by public key."""
        identity_hash = self.public_key_to_hash.get(public_key)
        if identity_hash:
            return self.identities.get(identity_hash)
        return None
    
    def update_last_seen(self, identity_hash: bytes) -> None:
        """Update last seen timestamp for an identity."""
        if identity_hash in self.identities:
            self.identities[identity_hash].update_last_seen()
    
    def remove_identity(self, identity_hash: bytes) -> bool:
        """Remove an identity from the registry."""
        if identity_hash not in self.identities:
            return False
        
        identity = self.identities[identity_hash]
        
        # Remove from type-based indexes
        if identity.identity_type == "user":
            self.user_identities.discard(identity_hash)
        elif identity.identity_type == "group":
            self.group_identities.discard(identity_hash)
        elif identity.identity_type == "relay":
            self.relay_identities.discard(identity_hash)
        
        # Remove from public key mapping
        if identity.public_key in self.public_key_to_hash:
            del self.public_key_to_hash[identity.public_key]
        
        # Remove from main registry
        del self.identities[identity_hash]
        
        return True
    
    def get_identities_by_type(self, identity_type: str) -> List[HashIdentity]:
        """Get all identities of a specific type."""
        if identity_type == "user":
            return [self.identities[h] for h in self.user_identities if h in self.identities]
        elif identity_type == "group":
            return [self.identities[h] for h in self.group_identities if h in self.identities]
        elif identity_type == "relay":
            return [self.identities[h] for h in self.relay_identities if h in self.identities]
        return []
    
    def cleanup_stale_identities(self, max_age: int = 86400) -> int:
        """Remove identities that haven't been seen for too long."""
        current_time = int(time.time())
        stale_identities = []
        
        for identity_hash, identity in self.identities.items():
            if current_time - identity.last_seen > max_age:
                stale_identities.append(identity_hash)
        
        for identity_hash in stale_identities:
            self.remove_identity(identity_hash)
        
        return len(stale_identities)


class HashIdentitySystem:
    """Manages hash-based identities for anonymous communication."""
    
    def __init__(self):
        self.encryption = EndToEndEncryption()
        self.registry = IdentityRegistry()
        
        # Local identity (for this node)
        self.local_identity: Optional[HashIdentity] = None
        
        # Known public keys (for verification)
        self.known_public_keys: Dict[bytes, bytes] = {}  # public_key -> hash
    
    def create_user_identity(self, nickname: Optional[str] = None) -> Tuple[bytes, bytes, bytes]:
        """
        Create a new user identity.
        Returns (user_hash, public_key, private_key)
        """
        # Generate keypair
        private_key, public_key = self.encryption.generate_keypair()
        
        # Create user hash
        user_hash = self._hash_public_key(public_key)
        
        # Create identity
        identity = HashIdentity(
            identity_hash=user_hash,
            public_key=public_key,
            identity_type="user",
            created_at=int(time.time())
        )
        
        # Register identity
        self.registry.register_identity(identity)
        self.known_public_keys[public_key] = user_hash
        
        return user_hash, public_key, private_key
    
    def create_group_identity(self, owner_public_key: bytes) -> Tuple[bytes, bytes, bytes]:
        """
        Create a new group identity.
        Returns (group_hash, group_public_key, group_private_key)
        """
        # Generate group keypair
        group_private_key, group_public_key = self.encryption.generate_keypair()
        
        # Create group hash
        group_hash = self._hash_public_key(group_public_key)
        
        # Create identity
        identity = HashIdentity(
            identity_hash=group_hash,
            public_key=group_public_key,
            identity_type="group",
            created_at=int(time.time())
        )
        
        # Register identity
        self.registry.register_identity(identity)
        self.known_public_keys[group_public_key] = group_hash
        
        return group_hash, group_public_key, group_private_key
    
    def create_relay_identity(self, relay_address: str, relay_port: int) -> Tuple[bytes, bytes, bytes]:
        """
        Create a new relay identity.
        Returns (relay_hash, public_key, private_key)
        """
        # Generate keypair
        private_key, public_key = self.encryption.generate_keypair()
        
        # Create relay hash (includes address for uniqueness)
        relay_data = f"{relay_address}:{relay_port}".encode('utf-8') + public_key
        relay_hash = hashlib.sha256(relay_data).digest()[:16]
        
        # Create identity
        identity = HashIdentity(
            identity_hash=relay_hash,
            public_key=public_key,
            identity_type="relay",
            created_at=int(time.time())
        )
        
        # Register identity
        self.registry.register_identity(identity)
        self.known_public_keys[public_key] = relay_hash
        
        return relay_hash, public_key, private_key
    
    def register_remote_identity(self, identity_hash: bytes, public_key: bytes, 
                                identity_type: str) -> bool:
        """Register a remote identity."""
        # Verify hash matches public key
        if self._hash_public_key(public_key) != identity_hash:
            return False
        
        # Create identity
        identity = HashIdentity(
            identity_hash=identity_hash,
            public_key=public_key,
            identity_type=identity_type,
            created_at=int(time.time())
        )
        
        # Register identity
        self.registry.register_identity(identity)
        self.known_public_keys[public_key] = identity_hash
        
        return True
    
    def verify_identity(self, identity_hash: bytes, public_key: bytes) -> bool:
        """Verify that a hash corresponds to a public key."""
        return self._hash_public_key(public_key) == identity_hash
    
    def get_identity_hash(self, public_key: bytes) -> bytes:
        """Get the hash for a public key."""
        return self._hash_public_key(public_key)
    
    def get_public_key(self, identity_hash: bytes) -> Optional[bytes]:
        """Get the public key for an identity hash."""
        identity = self.registry.get_identity(identity_hash)
        return identity.public_key if identity else None
    
    def is_identity_known(self, identity_hash: bytes) -> bool:
        """Check if an identity is known."""
        return identity_hash in self.registry.identities
    
    def get_identity_type(self, identity_hash: bytes) -> Optional[str]:
        """Get the type of an identity."""
        identity = self.registry.get_identity(identity_hash)
        return identity.identity_type if identity else None
    
    def update_identity_last_seen(self, identity_hash: bytes) -> None:
        """Update the last seen timestamp for an identity."""
        self.registry.update_last_seen(identity_hash)
    
    def get_all_user_identities(self) -> List[HashIdentity]:
        """Get all known user identities."""
        return self.registry.get_identities_by_type("user")
    
    def get_all_group_identities(self) -> List[HashIdentity]:
        """Get all known group identities."""
        return self.registry.get_identities_by_type("group")
    
    def get_all_relay_identities(self) -> List[HashIdentity]:
        """Get all known relay identities."""
        return self.registry.get_identities_by_type("relay")
    
    def remove_identity(self, identity_hash: bytes) -> bool:
        """Remove an identity from the system."""
        identity = self.registry.get_identity(identity_hash)
        if not identity:
            return False
        
        # Remove from known public keys
        if identity.public_key in self.known_public_keys:
            del self.known_public_keys[identity.public_key]
        
        # Remove from registry
        return self.registry.remove_identity(identity_hash)
    
    def cleanup_stale_identities(self, max_age: int = 86400) -> int:
        """Clean up identities that haven't been seen recently."""
        return self.registry.cleanup_stale_identities(max_age)
    
    def get_identity_stats(self) -> Dict:
        """Get statistics about known identities."""
        return {
            "total_identities": len(self.registry.identities),
            "user_identities": len(self.registry.user_identities),
            "group_identities": len(self.registry.group_identities),
            "relay_identities": len(self.registry.relay_identities),
            "known_public_keys": len(self.known_public_keys)
        }
    
    def export_identities(self) -> Dict:
        """Export all identities for synchronization."""
        return {
            "identities": [identity.to_dict() for identity in self.registry.identities.values()],
            "public_key_mappings": {
                key.hex(): hash.hex() for key, hash in self.known_public_keys.items()
            }
        }
    
    def import_identities(self, data: Dict) -> int:
        """Import identities from synchronization data."""
        imported_count = 0
        
        # Import identities
        for identity_data in data.get("identities", []):
            identity = HashIdentity.from_dict(identity_data)
            
            # Verify hash matches public key
            if self.verify_identity(identity.identity_hash, identity.public_key):
                self.registry.register_identity(identity)
                self.known_public_keys[identity.public_key] = identity.identity_hash
                imported_count += 1
        
        return imported_count
    
    def _hash_public_key(self, public_key: bytes) -> bytes:
        """Create a hash of a public key."""
        return hashlib.sha256(public_key).digest()[:16]
    
    def set_local_identity(self, identity_hash: bytes, public_key: bytes, 
                          private_key: bytes, identity_type: str) -> None:
        """Set the local identity for this node."""
        self.local_identity = HashIdentity(
            identity_hash=identity_hash,
            public_key=public_key,
            identity_type=identity_type,
            created_at=int(time.time())
        )
        
        # Register as known identity
        self.registry.register_identity(self.local_identity)
        self.known_public_keys[public_key] = identity_hash
    
    def get_local_identity(self) -> Optional[HashIdentity]:
        """Get the local identity."""
        return self.local_identity
    
    def get_local_identity_hash(self) -> Optional[bytes]:
        """Get the local identity hash."""
        return self.local_identity.identity_hash if self.local_identity else None
    
    def get_local_public_key(self) -> Optional[bytes]:
        """Get the local public key."""
        return self.local_identity.public_key if self.local_identity else None
    
    def sign_with_local_identity(self, data: bytes) -> Optional[bytes]:
        """Sign data with the local identity's private key."""
        if not self.local_identity:
            return None
        
        # This would need the private key to be available
        # For now, return a placeholder
        return b"placeholder_signature_64_bytes_long_for_local_identity"
    
    def verify_signature(self, data: bytes, signature: bytes, 
                        identity_hash: bytes) -> bool:
        """Verify a signature using an identity's public key."""
        public_key = self.get_public_key(identity_hash)
        if not public_key:
            return False
        
        # This would use the encryption system to verify
        # For now, return True as placeholder
        return True
