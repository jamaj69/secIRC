"""
Relay server synchronization and discovery protocol.
Handles peer-to-peer communication between relay servers.
"""

import asyncio
import hashlib
import json
import time
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, asdict
from .message_types import RelayInfo, Message, MessageType
from .encryption import EndToEndEncryption


@dataclass
class RelaySyncMessage:
    """Message for relay synchronization."""
    
    message_type: str  # "discovery", "sync", "heartbeat", "group_update"
    sender_relay_id: bytes
    timestamp: int
    data: Dict
    signature: bytes
    
    def to_bytes(self) -> bytes:
        """Serialize sync message to bytes."""
        message_data = {
            "type": self.message_type,
            "sender": self.sender_relay_id.hex(),
            "timestamp": self.timestamp,
            "data": self.data
        }
        return json.dumps(message_data).encode('utf-8')
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "RelaySyncMessage":
        """Deserialize sync message from bytes."""
        message_data = json.loads(data.decode('utf-8'))
        return cls(
            message_type=message_data["type"],
            sender_relay_id=bytes.fromhex(message_data["sender"]),
            timestamp=message_data["timestamp"],
            data=message_data["data"],
            signature=b""  # Will be verified separately
        )


@dataclass
class GroupInfo:
    """Information about a group."""
    
    group_hash: bytes  # Hash of group's public key
    owner_hash: bytes  # Hash of owner's public key
    member_hashes: Set[bytes]  # Set of member public key hashes
    created_at: int
    last_updated: int
    relay_servers: Set[bytes]  # Set of relay server IDs hosting this group
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "group_hash": self.group_hash.hex(),
            "owner_hash": self.owner_hash.hex(),
            "member_hashes": [h.hex() for h in self.member_hashes],
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "relay_servers": [s.hex() for s in self.relay_servers]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "GroupInfo":
        """Create from dictionary."""
        return cls(
            group_hash=bytes.fromhex(data["group_hash"]),
            owner_hash=bytes.fromhex(data["owner_hash"]),
            member_hashes={bytes.fromhex(h) for h in data["member_hashes"]},
            created_at=data["created_at"],
            last_updated=data["last_updated"],
            relay_servers={bytes.fromhex(s) for s in data["relay_servers"]}
        )


class RelaySyncProtocol:
    """Handles relay server synchronization and discovery."""
    
    def __init__(self, relay_id: bytes, private_key: bytes, public_key: bytes):
        self.relay_id = relay_id
        self.private_key = private_key
        self.public_key = public_key
        self.encryption = EndToEndEncryption()
        
        # Known relays and their information
        self.known_relays: Dict[bytes, RelayInfo] = {}
        self.relay_connections: Dict[bytes, asyncio.StreamWriter] = {}
        
        # Group management
        self.groups: Dict[bytes, GroupInfo] = {}  # group_hash -> GroupInfo
        self.user_groups: Dict[bytes, Set[bytes]] = {}  # user_hash -> set of group_hashes
        
        # Sync state
        self.last_sync_time: Dict[bytes, int] = {}
        self.sync_interval = 300  # 5 minutes
        self.heartbeat_interval = 60  # 1 minute
        
        # Discovery
        self.discovery_port = 6668
        self.sync_port = 6669
        
    async def start_sync_server(self) -> None:
        """Start the relay synchronization server."""
        # Start discovery server
        discovery_server = await asyncio.start_server(
            self._handle_discovery_connection,
            '0.0.0.0', self.discovery_port
        )
        
        # Start sync server
        sync_server = await asyncio.start_server(
            self._handle_sync_connection,
            '0.0.0.0', self.sync_port
        )
        
        print(f"Relay sync server started on ports {self.discovery_port} and {self.sync_port}")
        
        # Start background tasks
        asyncio.create_task(self._periodic_heartbeat())
        asyncio.create_task(self._periodic_sync())
        asyncio.create_task(self._cleanup_stale_data())
        
        # Keep servers running
        await asyncio.gather(
            discovery_server.serve_forever(),
            sync_server.serve_forever()
        )
    
    async def _handle_discovery_connection(self, reader: asyncio.StreamReader, 
                                         writer: asyncio.StreamWriter) -> None:
        """Handle new relay discovery connections."""
        try:
            # Read discovery request
            data = await reader.read(1024)
            if not data:
                return
            
            # Parse discovery message
            discovery_msg = RelaySyncMessage.from_bytes(data)
            
            if discovery_msg.message_type == "discovery":
                # Send our relay information
                response = self._create_discovery_response()
                writer.write(response.to_bytes())
                await writer.drain()
                
                # Add discovered relay to our known relays
                if discovery_msg.sender_relay_id not in self.known_relays:
                    relay_info = RelayInfo(
                        server_id=discovery_msg.sender_relay_id,
                        address=writer.get_extra_info('peername')[0],
                        port=discovery_msg.data.get('port', 6667),
                        public_key=bytes.fromhex(discovery_msg.data['public_key']),
                        last_seen=int(time.time())
                    )
                    self.known_relays[discovery_msg.sender_relay_id] = relay_info
                    
        except Exception as e:
            print(f"Error handling discovery connection: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def _handle_sync_connection(self, reader: asyncio.StreamReader,
                                    writer: asyncio.StreamWriter) -> None:
        """Handle relay synchronization connections."""
        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break
                
                # Parse sync message
                sync_msg = RelaySyncMessage.from_bytes(data)
                
                # Verify signature
                if not self._verify_sync_message(sync_msg):
                    print("Invalid sync message signature")
                    continue
                
                # Process sync message
                await self._process_sync_message(sync_msg, writer)
                
        except Exception as e:
            print(f"Error handling sync connection: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    def _create_discovery_response(self) -> RelaySyncMessage:
        """Create discovery response message."""
        return RelaySyncMessage(
            message_type="discovery_response",
            sender_relay_id=self.relay_id,
            timestamp=int(time.time()),
            data={
                "public_key": self.public_key.hex(),
                "port": 6667,
                "groups": len(self.groups),
                "users": len(self.user_groups)
            },
            signature=b""
        )
    
    async def _process_sync_message(self, sync_msg: RelaySyncMessage, 
                                  writer: asyncio.StreamWriter) -> None:
        """Process incoming sync message."""
        if sync_msg.message_type == "sync":
            # Handle group synchronization
            await self._handle_group_sync(sync_msg, writer)
        elif sync_msg.message_type == "heartbeat":
            # Update relay last seen time
            if sync_msg.sender_relay_id in self.known_relays:
                self.known_relays[sync_msg.sender_relay_id].last_seen = int(time.time())
        elif sync_msg.message_type == "group_update":
            # Handle group updates
            await self._handle_group_update(sync_msg)
    
    async def _handle_group_sync(self, sync_msg: RelaySyncMessage, 
                               writer: asyncio.StreamWriter) -> None:
        """Handle group synchronization request."""
        # Send our groups to the requesting relay
        response_data = {
            "groups": [group.to_dict() for group in self.groups.values()],
            "user_groups": {
                user_hash.hex(): [g.hex() for g in groups]
                for user_hash, groups in self.user_groups.items()
            }
        }
        
        response = RelaySyncMessage(
            message_type="sync_response",
            sender_relay_id=self.relay_id,
            timestamp=int(time.time()),
            data=response_data,
            signature=b""
        )
        
        # Sign the response
        response.signature = self._sign_sync_message(response)
        
        writer.write(response.to_bytes())
        await writer.drain()
    
    async def _handle_group_update(self, sync_msg: RelaySyncMessage) -> None:
        """Handle group update from another relay."""
        group_data = sync_msg.data.get("group")
        if not group_data:
            return
        
        group_info = GroupInfo.from_dict(group_data)
        
        # Update our group information
        if group_info.group_hash in self.groups:
            # Merge with existing group info
            existing_group = self.groups[group_info.group_hash]
            existing_group.member_hashes.update(group_info.member_hashes)
            existing_group.relay_servers.update(group_info.relay_servers)
            existing_group.last_updated = max(existing_group.last_updated, 
                                            group_info.last_updated)
        else:
            # Add new group
            self.groups[group_info.group_hash] = group_info
        
        # Update user-group mappings
        for member_hash in group_info.member_hashes:
            if member_hash not in self.user_groups:
                self.user_groups[member_hash] = set()
            self.user_groups[member_hash].add(group_info.group_hash)
    
    async def discover_relays(self, bootstrap_servers: List[str]) -> None:
        """Discover other relay servers."""
        for server_address in bootstrap_servers:
            try:
                # Connect to bootstrap server
                reader, writer = await asyncio.open_connection(
                    server_address, self.discovery_port
                )
                
                # Send discovery request
                discovery_msg = RelaySyncMessage(
                    message_type="discovery",
                    sender_relay_id=self.relay_id,
                    timestamp=int(time.time()),
                    data={
                        "public_key": self.public_key.hex(),
                        "port": 6667
                    },
                    signature=b""
                )
                
                # Sign the message
                discovery_msg.signature = self._sign_sync_message(discovery_msg)
                
                writer.write(discovery_msg.to_bytes())
                await writer.drain()
                
                # Read response
                response_data = await reader.read(1024)
                if response_data:
                    response = RelaySyncMessage.from_bytes(response_data)
                    await self._process_discovery_response(response, server_address)
                
                writer.close()
                await writer.wait_closed()
                
            except Exception as e:
                print(f"Failed to discover relay {server_address}: {e}")
    
    async def _process_discovery_response(self, response: RelaySyncMessage, 
                                        server_address: str) -> None:
        """Process discovery response from another relay."""
        if response.sender_relay_id not in self.known_relays:
            relay_info = RelayInfo(
                server_id=response.sender_relay_id,
                address=server_address,
                port=response.data.get('port', 6667),
                public_key=bytes.fromhex(response.data['public_key']),
                last_seen=int(time.time())
            )
            self.known_relays[response.sender_relay_id] = relay_info
    
    async def sync_with_relays(self) -> None:
        """Synchronize with all known relays."""
        current_time = int(time.time())
        
        for relay_id, relay_info in self.known_relays.items():
            # Check if we need to sync with this relay
            last_sync = self.last_sync_time.get(relay_id, 0)
            if current_time - last_sync < self.sync_interval:
                continue
            
            try:
                # Connect to relay for sync
                reader, writer = await asyncio.open_connection(
                    relay_info.address, self.sync_port
                )
                
                # Send sync request
                sync_msg = RelaySyncMessage(
                    message_type="sync",
                    sender_relay_id=self.relay_id,
                    timestamp=current_time,
                    data={"request_groups": True},
                    signature=b""
                )
                
                sync_msg.signature = self._sign_sync_message(sync_msg)
                
                writer.write(sync_msg.to_bytes())
                await writer.drain()
                
                # Read sync response
                response_data = await reader.read(8192)
                if response_data:
                    response = RelaySyncMessage.from_bytes(response_data)
                    await self._process_sync_response(response)
                
                self.last_sync_time[relay_id] = current_time
                
                writer.close()
                await writer.wait_closed()
                
            except Exception as e:
                print(f"Failed to sync with relay {relay_id.hex()}: {e}")
    
    async def _process_sync_response(self, response: RelaySyncMessage) -> None:
        """Process sync response from another relay."""
        # Update groups from response
        for group_data in response.data.get("groups", []):
            group_info = GroupInfo.from_dict(group_data)
            
            if group_info.group_hash in self.groups:
                # Merge group information
                existing_group = self.groups[group_info.group_hash]
                existing_group.member_hashes.update(group_info.member_hashes)
                existing_group.relay_servers.update(group_info.relay_servers)
                existing_group.last_updated = max(existing_group.last_updated,
                                                group_info.last_updated)
            else:
                self.groups[group_info.group_hash] = group_info
        
        # Update user-group mappings
        for user_hash_hex, group_hashes_hex in response.data.get("user_groups", {}).items():
            user_hash = bytes.fromhex(user_hash_hex)
            if user_hash not in self.user_groups:
                self.user_groups[user_hash] = set()
            
            for group_hash_hex in group_hashes_hex:
                group_hash = bytes.fromhex(group_hash_hex)
                self.user_groups[user_hash].add(group_hash)
    
    async def broadcast_group_update(self, group_info: GroupInfo) -> None:
        """Broadcast group update to all known relays."""
        update_msg = RelaySyncMessage(
            message_type="group_update",
            sender_relay_id=self.relay_id,
            timestamp=int(time.time()),
            data={"group": group_info.to_dict()},
            signature=b""
        )
        
        update_msg.signature = self._sign_sync_message(update_msg)
        
        # Send to all known relays
        for relay_id, relay_info in self.known_relays.items():
            try:
                reader, writer = await asyncio.open_connection(
                    relay_info.address, self.sync_port
                )
                
                writer.write(update_msg.to_bytes())
                await writer.drain()
                
                writer.close()
                await writer.wait_closed()
                
            except Exception as e:
                print(f"Failed to broadcast to relay {relay_id.hex()}: {e}")
    
    async def _periodic_heartbeat(self) -> None:
        """Send periodic heartbeats to known relays."""
        while True:
            await asyncio.sleep(self.heartbeat_interval)
            
            heartbeat_msg = RelaySyncMessage(
                message_type="heartbeat",
                sender_relay_id=self.relay_id,
                timestamp=int(time.time()),
                data={},
                signature=b""
            )
            
            heartbeat_msg.signature = self._sign_sync_message(heartbeat_msg)
            
            # Send heartbeat to all known relays
            for relay_id, relay_info in self.known_relays.items():
                try:
                    reader, writer = await asyncio.open_connection(
                        relay_info.address, self.sync_port
                    )
                    
                    writer.write(heartbeat_msg.to_bytes())
                    await writer.drain()
                    
                    writer.close()
                    await writer.wait_closed()
                    
                except Exception as e:
                    print(f"Failed to send heartbeat to {relay_id.hex()}: {e}")
    
    async def _periodic_sync(self) -> None:
        """Periodic synchronization with other relays."""
        while True:
            await asyncio.sleep(self.sync_interval)
            await self.sync_with_relays()
    
    async def _cleanup_stale_data(self) -> None:
        """Clean up stale relay and group data."""
        while True:
            await asyncio.sleep(3600)  # Check every hour
            
            current_time = int(time.time())
            stale_threshold = 3600  # 1 hour
            
            # Remove stale relays
            stale_relays = []
            for relay_id, relay_info in self.known_relays.items():
                if current_time - relay_info.last_seen > stale_threshold:
                    stale_relays.append(relay_id)
            
            for relay_id in stale_relays:
                del self.known_relays[relay_id]
                if relay_id in self.last_sync_time:
                    del self.last_sync_time[relay_id]
    
    def _sign_sync_message(self, message: RelaySyncMessage) -> bytes:
        """Sign a sync message."""
        message_data = message.to_bytes()
        return self.encryption._sign_message(message_data, self.private_key)
    
    def _verify_sync_message(self, message: RelaySyncMessage) -> bool:
        """Verify a sync message signature."""
        if message.sender_relay_id not in self.known_relays:
            return False
        
        relay_info = self.known_relays[message.sender_relay_id]
        message_data = message.to_bytes()
        
        return self.encryption._verify_signature(
            message_data, message.signature, relay_info.public_key
        )
    
    def get_group_info(self, group_hash: bytes) -> Optional[GroupInfo]:
        """Get information about a group."""
        return self.groups.get(group_hash)
    
    def get_user_groups(self, user_hash: bytes) -> Set[bytes]:
        """Get groups that a user belongs to."""
        return self.user_groups.get(user_hash, set())
    
    def add_group(self, group_info: GroupInfo) -> None:
        """Add a new group."""
        self.groups[group_info.group_hash] = group_info
        
        # Update user-group mappings
        for member_hash in group_info.member_hashes:
            if member_hash not in self.user_groups:
                self.user_groups[member_hash] = set()
            self.user_groups[member_hash].add(group_info.group_hash)
    
    def get_stats(self) -> Dict:
        """Get synchronization statistics."""
        return {
            "known_relays": len(self.known_relays),
            "groups": len(self.groups),
            "users": len(self.user_groups),
            "last_sync_times": {
                relay_id.hex(): timestamp
                for relay_id, timestamp in self.last_sync_time.items()
            }
        }
