"""
Anonymous messaging protocol implementation using UDP.
Handles message routing through relay servers with end-to-end encryption.
"""

import asyncio
import socket
import struct
import time
import random
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from .message_types import Message, MessageType, RelayInfo, UserIdentity
from .encryption import EndToEndEncryption
from .relay_discovery import RelayDiscovery


@dataclass
class ProtocolConfig:
    """Configuration for the anonymous protocol."""
    
    # Network settings
    local_port: int = 0  # 0 for random port
    max_packet_size: int = 1400  # UDP MTU
    connection_timeout: int = 30
    retry_attempts: int = 3
    
    # Security settings
    max_relay_chain_length: int = 5
    message_ttl: int = 300  # 5 minutes
    encryption_layers: int = 2
    
    # Discovery settings
    discovery_interval: int = 300  # 5 minutes
    max_known_relays: int = 50


class AnonymousProtocol:
    """Main protocol handler for anonymous messaging."""
    
    def __init__(self, config: ProtocolConfig = None):
        self.config = config or ProtocolConfig()
        self.encryption = EndToEndEncryption()
        self.relay_discovery = RelayDiscovery()
        
        # Network components
        self.socket: Optional[asyncio.DatagramProtocol] = None
        self.transport: Optional[asyncio.DatagramTransport] = None
        self.local_address: Optional[tuple] = None
        
        # User identity
        self.user_identity: Optional[UserIdentity] = None
        self.password: Optional[str] = None
        
        # Message handling
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.pending_messages: Dict[bytes, asyncio.Future] = {}
        
        # Relay management
        self.active_relays: List[RelayInfo] = []
        self.relay_sessions: Dict[bytes, bytes] = {}  # relay_id -> session_key
        
        # Statistics
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "relays_discovered": 0,
            "encryption_errors": 0
        }
    
    async def start(self, password: str) -> None:
        """Start the anonymous protocol."""
        self.password = password
        
        # Load or create user identity
        await self._load_user_identity()
        
        # Start network listener
        await self._start_network_listener()
        
        # Start relay discovery
        await self._start_relay_discovery()
        
        # Start background tasks
        asyncio.create_task(self._cleanup_expired_messages())
        asyncio.create_task(self._maintain_relay_connections())
    
    async def stop(self) -> None:
        """Stop the anonymous protocol."""
        if self.transport:
            self.transport.close()
        
        # Save relay information
        self.relay_discovery.save_relays("relays.json")
    
    async def send_message(self, recipient_id: bytes, message_text: str) -> bool:
        """Send an anonymous message to a recipient."""
        try:
            # Create message
            message = Message(
                message_type=MessageType.TEXT_MESSAGE,
                payload=message_text.encode('utf-8'),
                timestamp=int(time.time()),
                message_id=os.urandom(16)
            )
            
            # Encrypt message for recipient
            encrypted_message = self.encryption.encrypt_message(
                message.to_bytes(),
                recipient_id,  # This should be recipient's public key
                self.user_identity.private_key
            )
            
            # Create relay chain
            relay_chain = self.relay_discovery.get_relay_chain(
                self.config.max_relay_chain_length
            )
            
            if not relay_chain:
                print("No relay servers available")
                return False
            
            # Route message through relay chain
            success = await self._route_message(encrypted_message, relay_chain)
            
            if success:
                self.stats["messages_sent"] += 1
            
            return success
            
        except Exception as e:
            print(f"Failed to send message: {e}")
            self.stats["encryption_errors"] += 1
            return False
    
    async def _route_message(self, encrypted_message: bytes, 
                           relay_chain: List[RelayInfo]) -> bool:
        """Route message through relay chain."""
        try:
            # Create routing message
            routing_message = self._create_routing_message(
                encrypted_message, relay_chain
            )
            
            # Send to first relay in chain
            first_relay = relay_chain[0]
            success = await self._send_to_relay(routing_message, first_relay)
            
            return success
            
        except Exception as e:
            print(f"Failed to route message: {e}")
            return False
    
    def _create_routing_message(self, encrypted_message: bytes, 
                              relay_chain: List[RelayInfo]) -> bytes:
        """Create routing message with relay chain information."""
        # Message structure:
        # [1 byte: chain_length][relay_chain][encrypted_message]
        
        chain_length = len(relay_chain)
        chain_data = b""
        
        for relay in relay_chain:
            # Each relay entry: [16 bytes: relay_id][4 bytes: port][address_length][address]
            chain_data += relay.server_id
            chain_data += struct.pack("!I", relay.port)
            address_bytes = relay.address.encode('utf-8')
            chain_data += struct.pack("!B", len(address_bytes))
            chain_data += address_bytes
        
        return struct.pack("!B", chain_length) + chain_data + encrypted_message
    
    async def _send_to_relay(self, message: bytes, relay: RelayInfo) -> bool:
        """Send message to a specific relay server."""
        try:
            # Get or create session with relay
            session_key = await self._get_relay_session(relay)
            
            if not session_key:
                return False
            
            # Encrypt message for relay
            encrypted_message = self.encryption.encrypt_for_relay(
                message, session_key
            )
            
            # Send UDP packet
            if self.transport:
                self.transport.sendto(
                    encrypted_message, 
                    (relay.address, relay.port)
                )
                return True
            
            return False
            
        except Exception as e:
            print(f"Failed to send to relay {relay.address}: {e}")
            self.relay_discovery.update_relay_reputation(
                relay.server_id, False
            )
            return False
    
    async def _get_relay_session(self, relay: RelayInfo) -> Optional[bytes]:
        """Get or create encrypted session with relay."""
        if relay.server_id in self.relay_sessions:
            return self.relay_sessions[relay.server_id]
        
        try:
            # Create new session
            session_key, encrypted_session_key = self.encryption.create_relay_encryption(
                relay.public_key
            )
            
            # Send session key to relay (this would be implemented)
            # For now, just store the session key
            self.relay_sessions[relay.server_id] = session_key
            
            return session_key
            
        except Exception as e:
            print(f"Failed to create session with relay: {e}")
            return None
    
    async def _start_network_listener(self) -> None:
        """Start UDP network listener."""
        loop = asyncio.get_event_loop()
        
        class Protocol(asyncio.DatagramProtocol):
            def __init__(self, handler):
                self.handler = handler
            
            def datagram_received(self, data, addr):
                asyncio.create_task(self.handler._handle_incoming_message(data, addr))
        
        self.socket = Protocol(self)
        self.transport, _ = await loop.create_datagram_endpoint(
            lambda: self.socket,
            local_addr=('0.0.0.0', self.config.local_port)
        )
        
        # Get actual local address
        sock = self.transport.get_extra_info('socket')
        self.local_address = sock.getsockname()
        
        print(f"Started anonymous protocol on {self.local_address}")
    
    async def _handle_incoming_message(self, data: bytes, addr: tuple) -> None:
        """Handle incoming UDP message."""
        try:
            # Try to decrypt message from relay
            # This is simplified - in reality, we'd need to identify which relay sent it
            for relay_id, session_key in self.relay_sessions.items():
                try:
                    decrypted_data = self.encryption.decrypt_from_relay(
                        data, session_key
                    )
                    
                    # Parse routing message
                    message = self._parse_routing_message(decrypted_data)
                    if message:
                        await self._process_message(message)
                        self.stats["messages_received"] += 1
                    break
                    
                except:
                    continue
                    
        except Exception as e:
            print(f"Failed to handle incoming message: {e}")
    
    def _parse_routing_message(self, data: bytes) -> Optional[Message]:
        """Parse routing message and extract actual message."""
        try:
            if len(data) < 1:
                return None
            
            # Extract chain length
            chain_length = struct.unpack("!B", data[:1])[0]
            offset = 1
            
            # Skip relay chain information
            for _ in range(chain_length):
                if offset + 16 + 4 + 1 > len(data):
                    return None
                
                offset += 16  # relay_id
                offset += 4   # port
                address_length = struct.unpack("!B", data[offset:offset+1])[0]
                offset += 1 + address_length  # address
            
            # Extract encrypted message
            encrypted_message = data[offset:]
            
            # Decrypt message (this would use recipient's private key)
            # For now, return None as we need the actual decryption logic
            
            return None
            
        except Exception as e:
            print(f"Failed to parse routing message: {e}")
            return None
    
    async def _process_message(self, message: Message) -> None:
        """Process received message."""
        if message.message_type in self.message_handlers:
            handler = self.message_handlers[message.message_type]
            await handler(message)
    
    async def _load_user_identity(self) -> None:
        """Load or create user identity."""
        try:
            # Try to load existing identity
            with open("user_identity.json", "r") as f:
                identity_data = json.load(f)
            
            # Decrypt private key
            private_key = self.encryption.decrypt_private_key(
                bytes.fromhex(identity_data["encrypted_private_key"]),
                self.password
            )
            
            self.user_identity = UserIdentity(
                user_id=bytes.fromhex(identity_data["user_id"]),
                public_key=bytes.fromhex(identity_data["public_key"]),
                private_key=private_key,
                nickname=identity_data.get("nickname")
            )
            
        except FileNotFoundError:
            # Create new identity
            await self._create_user_identity()
        except Exception as e:
            print(f"Failed to load user identity: {e}")
            await self._create_user_identity()
    
    async def _create_user_identity(self) -> None:
        """Create new user identity."""
        private_key, public_key = self.encryption.generate_keypair()
        
        # Encrypt private key with password
        encrypted_private_key = self.encryption.encrypt_private_key(
            private_key, self.password
        )
        
        self.user_identity = UserIdentity(
            user_id=os.urandom(16),
            public_key=public_key,
            private_key=private_key
        )
        
        # Save identity
        identity_data = {
            "user_id": self.user_identity.user_id.hex(),
            "public_key": public_key.hex(),
            "encrypted_private_key": encrypted_private_key.hex(),
            "nickname": self.user_identity.nickname
        }
        
        with open("user_identity.json", "w") as f:
            json.dump(identity_data, f, indent=2)
    
    async def _start_relay_discovery(self) -> None:
        """Start relay discovery process."""
        # Initial discovery
        relays = await self.relay_discovery.discover_relays()
        for relay in relays:
            self.relay_discovery.add_relay(relay)
        
        self.stats["relays_discovered"] = len(relays)
        
        # Periodic discovery
        async def periodic_discovery():
            while True:
                await asyncio.sleep(self.config.discovery_interval)
                try:
                    new_relays = await self.relay_discovery.discover_relays()
                    for relay in new_relays:
                        self.relay_discovery.add_relay(relay)
                except Exception as e:
                    print(f"Periodic discovery failed: {e}")
        
        asyncio.create_task(periodic_discovery())
    
    async def _cleanup_expired_messages(self) -> None:
        """Clean up expired pending messages."""
        while True:
            await asyncio.sleep(60)  # Check every minute
            
            current_time = time.time()
            expired_messages = []
            
            for message_id, future in self.pending_messages.items():
                if future.done():
                    expired_messages.append(message_id)
            
            for message_id in expired_messages:
                del self.pending_messages[message_id]
    
    async def _maintain_relay_connections(self) -> None:
        """Maintain connections with relay servers."""
        while True:
            await asyncio.sleep(300)  # Check every 5 minutes
            
            # Update relay reputations and remove inactive ones
            current_time = time.time()
            inactive_relays = []
            
            for relay in self.relay_discovery.known_relays.values():
                if current_time - relay.last_seen > 3600:  # 1 hour
                    inactive_relays.append(relay.server_id)
            
            for relay_id in inactive_relays:
                self.relay_discovery.remove_relay(relay_id)
    
    def register_message_handler(self, message_type: MessageType, 
                               handler: Callable) -> None:
        """Register a handler for a specific message type."""
        self.message_handlers[message_type] = handler
    
    def get_stats(self) -> Dict[str, Any]:
        """Get protocol statistics."""
        return {
            **self.stats,
            "active_relays": len(self.relay_discovery.known_relays),
            "local_address": self.local_address,
            "user_id": self.user_identity.user_id.hex() if self.user_identity else None
        }
