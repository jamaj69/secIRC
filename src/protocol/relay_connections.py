"""
Relay Server Connection Management

This module implements multi-protocol relay server connections including:
- TCP connections for direct server-to-server communication
- Tor protocol for anonymous connections
- WebSocket connections for web-based relays
"""

import asyncio
import ssl
import websockets
import socket
import struct
import time
import hashlib
import json
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict
import logging

from .message_types import MessageType, Message, HashIdentity
from .encryption import EndToEndEncryption


class ConnectionType(Enum):
    """Types of relay connections."""
    TCP = "tcp"
    TOR = "tor"
    WEBSOCKET = "websocket"


class ConnectionStatus(Enum):
    """Connection status states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    FAILED = "failed"
    RECONNECTING = "reconnecting"


@dataclass
class RelayConnection:
    """Represents a connection to another relay server."""
    
    relay_id: bytes                    # Hash identifier of the relay
    connection_type: ConnectionType    # Type of connection
    host: str                          # Host address
    port: int                          # Port number
    status: ConnectionStatus           # Current connection status
    connection: Optional[Any] = None   # Actual connection object
    last_heartbeat: int = 0            # Last heartbeat timestamp
    last_seen: int = 0                 # Last seen timestamp
    connection_attempts: int = 0       # Number of connection attempts
    max_attempts: int = 3              # Maximum connection attempts
    retry_delay: int = 30              # Delay between retry attempts
    priority: int = 1                  # Connection priority (1-10, higher is better)
    latency: float = 0.0               # Connection latency in milliseconds
    bandwidth: int = 0                 # Available bandwidth
    is_authenticated: bool = False     # Whether connection is authenticated
    public_key: Optional[bytes] = None # Relay's public key
    created_at: int = 0                # Connection creation timestamp
    
    def __post_init__(self):
        """Initialize timestamps if not provided."""
        current_time = int(time.time())
        if self.last_heartbeat == 0:
            self.last_heartbeat = current_time
        if self.last_seen == 0:
            self.last_seen = current_time
        if self.created_at == 0:
            self.created_at = current_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "relay_id": self.relay_id.hex(),
            "connection_type": self.connection_type.value,
            "host": self.host,
            "port": self.port,
            "status": self.status.value,
            "last_heartbeat": self.last_heartbeat,
            "last_seen": self.last_seen,
            "connection_attempts": self.connection_attempts,
            "max_attempts": self.max_attempts,
            "retry_delay": self.retry_delay,
            "priority": self.priority,
            "latency": self.latency,
            "bandwidth": self.bandwidth,
            "is_authenticated": self.is_authenticated,
            "public_key": self.public_key.hex() if self.public_key else None,
            "created_at": self.created_at
        }


@dataclass
class ConnectionConfig:
    """Configuration for relay connections."""
    
    max_connections: int = 10          # Maximum number of connections
    min_connections: int = 3           # Minimum number of connections
    connection_timeout: int = 30       # Connection timeout in seconds
    heartbeat_interval: int = 60       # Heartbeat interval in seconds
    reconnect_interval: int = 30       # Reconnect interval in seconds
    max_retry_attempts: int = 3        # Maximum retry attempts
    retry_delay: int = 30              # Delay between retries
    enable_tcp: bool = True            # Enable TCP connections
    enable_tor: bool = True            # Enable Tor connections
    enable_websocket: bool = True      # Enable WebSocket connections
    tcp_port: int = 6667               # Default TCP port
    websocket_port: int = 8080         # Default WebSocket port
    tor_port: int = 9050               # Default Tor SOCKS port
    ssl_enabled: bool = True           # Enable SSL/TLS
    ssl_cert_path: Optional[str] = None # SSL certificate path
    ssl_key_path: Optional[str] = None  # SSL private key path


class RelayConnectionManager:
    """Manages connections to other relay servers."""
    
    def __init__(self, config: ConnectionConfig, encryption: EndToEndEncryption):
        self.config = config
        self.encryption = encryption
        
        # Connection management
        self.connections: Dict[bytes, RelayConnection] = {}
        self.connection_tasks: Dict[bytes, asyncio.Task] = {}
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.reconnect_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "failed_connections": 0,
            "total_messages_sent": 0,
            "total_messages_received": 0,
            "total_bytes_sent": 0,
            "total_bytes_received": 0
        }
        
        # Event handlers
        self.connection_handlers: Dict[str, List] = defaultdict(list)
        
        # SSL context for secure connections
        self.ssl_context = None
        if config.ssl_enabled:
            self.ssl_context = self._create_ssl_context()
        
        self.logger = logging.getLogger(__name__)
    
    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context for secure connections."""
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE  # For self-signed certificates
        
        if self.config.ssl_cert_path and self.config.ssl_key_path:
            try:
                context.load_cert_chain(self.config.ssl_cert_path, self.config.ssl_key_path)
            except Exception as e:
                self.logger.warning(f"Failed to load SSL certificate: {e}")
        
        return context
    
    async def start_connection_manager(self) -> None:
        """Start the connection manager and background tasks."""
        self.logger.info("Starting relay connection manager...")
        
        # Start background tasks
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self.reconnect_task = asyncio.create_task(self._reconnect_loop())
        
        self.logger.info("Relay connection manager started")
    
    async def stop_connection_manager(self) -> None:
        """Stop the connection manager and close all connections."""
        self.logger.info("Stopping relay connection manager...")
        
        # Cancel background tasks
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        if self.reconnect_task:
            self.reconnect_task.cancel()
        
        # Close all connections
        for connection in self.connections.values():
            await self._close_connection(connection)
        
        # Cancel connection tasks
        for task in self.connection_tasks.values():
            task.cancel()
        
        self.logger.info("Relay connection manager stopped")
    
    async def add_relay_connection(self, relay_id: bytes, connection_type: ConnectionType,
                                 host: str, port: int, priority: int = 1) -> bool:
        """Add a new relay connection."""
        try:
            if relay_id in self.connections:
                self.logger.warning(f"Connection to relay {relay_id.hex()} already exists")
                return False
            
            if len(self.connections) >= self.config.max_connections:
                self.logger.warning("Maximum number of connections reached")
                return False
            
            connection = RelayConnection(
                relay_id=relay_id,
                connection_type=connection_type,
                host=host,
                port=port,
                status=ConnectionStatus.DISCONNECTED,
                priority=priority
            )
            
            self.connections[relay_id] = connection
            
            # Start connection task
            self.connection_tasks[relay_id] = asyncio.create_task(
                self._maintain_connection(connection)
            )
            
            self.stats["total_connections"] += 1
            self.logger.info(f"Added connection to relay {relay_id.hex()} ({connection_type.value}://{host}:{port})")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add relay connection: {e}")
            return False
    
    async def remove_relay_connection(self, relay_id: bytes) -> bool:
        """Remove a relay connection."""
        try:
            if relay_id not in self.connections:
                return False
            
            connection = self.connections[relay_id]
            await self._close_connection(connection)
            
            # Cancel connection task
            if relay_id in self.connection_tasks:
                self.connection_tasks[relay_id].cancel()
                del self.connection_tasks[relay_id]
            
            del self.connections[relay_id]
            
            if connection.status == ConnectionStatus.CONNECTED:
                self.stats["active_connections"] -= 1
            
            self.logger.info(f"Removed connection to relay {relay_id.hex()}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove relay connection: {e}")
            return False
    
    async def _maintain_connection(self, connection: RelayConnection) -> None:
        """Maintain a connection to a relay server."""
        while True:
            try:
                if connection.status == ConnectionStatus.DISCONNECTED:
                    await self._connect_to_relay(connection)
                elif connection.status == ConnectionStatus.CONNECTED:
                    await self._authenticate_connection(connection)
                elif connection.status == ConnectionStatus.FAILED:
                    await self._handle_connection_failure(connection)
                
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error maintaining connection to {connection.relay_id.hex()}: {e}")
                connection.status = ConnectionStatus.FAILED
                await asyncio.sleep(5)
    
    async def _connect_to_relay(self, connection: RelayConnection) -> None:
        """Connect to a relay server."""
        try:
            connection.status = ConnectionStatus.CONNECTING
            connection.connection_attempts += 1
            
            if connection.connection_attempts > connection.max_attempts:
                connection.status = ConnectionStatus.FAILED
                self.stats["failed_connections"] += 1
                return
            
            if connection.connection_type == ConnectionType.TCP:
                await self._connect_tcp(connection)
            elif connection.connection_type == ConnectionType.TOR:
                await self._connect_tor(connection)
            elif connection.connection_type == ConnectionType.WEBSOCKET:
                await self._connect_websocket(connection)
            
            if connection.connection is not None:
                connection.status = ConnectionStatus.CONNECTED
                connection.last_seen = int(time.time())
                self.stats["active_connections"] += 1
                self.logger.info(f"Connected to relay {connection.relay_id.hex()} via {connection.connection_type.value}")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to relay {connection.relay_id.hex()}: {e}")
            connection.status = ConnectionStatus.FAILED
            connection.connection = None
    
    async def _connect_tcp(self, connection: RelayConnection) -> None:
        """Connect via TCP."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(connection.host, connection.port),
                timeout=self.config.connection_timeout
            )
            connection.connection = (reader, writer)
            
        except asyncio.TimeoutError:
            raise Exception("TCP connection timeout")
        except Exception as e:
            raise Exception(f"TCP connection failed: {e}")
    
    async def _connect_tor(self, connection: RelayConnection) -> None:
        """Connect via Tor SOCKS proxy."""
        try:
            # Create SOCKS connection through Tor
            import socks
            
            # Create socket
            sock = socks.socksocket()
            sock.set_proxy(socks.SOCKS5, "127.0.0.1", self.config.tor_port)
            
            # Connect to target
            sock.connect((connection.host, connection.port))
            
            # Convert to asyncio stream
            reader, writer = await asyncio.open_connection(sock=sock)
            connection.connection = (reader, writer)
            
        except ImportError:
            raise Exception("PySocks library required for Tor connections")
        except Exception as e:
            raise Exception(f"Tor connection failed: {e}")
    
    async def _connect_websocket(self, connection: RelayConnection) -> None:
        """Connect via WebSocket."""
        try:
            protocol = "wss" if self.config.ssl_enabled else "ws"
            uri = f"{protocol}://{connection.host}:{connection.port}/relay"
            
            websocket = await asyncio.wait_for(
                websockets.connect(uri, ssl=self.ssl_context),
                timeout=self.config.connection_timeout
            )
            connection.connection = websocket
            
        except asyncio.TimeoutError:
            raise Exception("WebSocket connection timeout")
        except Exception as e:
            raise Exception(f"WebSocket connection failed: {e}")
    
    async def _authenticate_connection(self, connection: RelayConnection) -> None:
        """Authenticate the connection with the relay."""
        try:
            if connection.is_authenticated:
                return
            
            # Send authentication message
            auth_message = {
                "type": "auth",
                "relay_id": connection.relay_id.hex(),
                "timestamp": int(time.time()),
                "public_key": "our_public_key_here"  # Replace with actual public key
            }
            
            await self._send_message(connection, auth_message)
            
            # Wait for authentication response
            response = await self._receive_message(connection)
            
            if response and response.get("type") == "auth_success":
                connection.is_authenticated = True
                connection.status = ConnectionStatus.AUTHENTICATED
                self.logger.info(f"Authenticated with relay {connection.relay_id.hex()}")
            else:
                raise Exception("Authentication failed")
                
        except Exception as e:
            self.logger.error(f"Authentication failed for {connection.relay_id.hex()}: {e}")
            connection.status = ConnectionStatus.FAILED
    
    async def _send_message(self, connection: RelayConnection, message: Dict[str, Any]) -> bool:
        """Send a message through a connection."""
        try:
            if connection.connection is None:
                return False
            
            message_data = json.dumps(message).encode('utf-8')
            message_length = len(message_data)
            
            if connection.connection_type == ConnectionType.WEBSOCKET:
                await connection.connection.send(message_data)
            else:
                reader, writer = connection.connection
                writer.write(struct.pack('!I', message_length))
                writer.write(message_data)
                await writer.drain()
            
            self.stats["total_messages_sent"] += 1
            self.stats["total_bytes_sent"] += message_length
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send message to {connection.relay_id.hex()}: {e}")
            connection.status = ConnectionStatus.FAILED
            return False
    
    async def _receive_message(self, connection: RelayConnection) -> Optional[Dict[str, Any]]:
        """Receive a message from a connection."""
        try:
            if connection.connection is None:
                return None
            
            if connection.connection_type == ConnectionType.WEBSOCKET:
                message_data = await connection.connection.recv()
            else:
                reader, writer = connection.connection
                length_data = await reader.readexactly(4)
                message_length = struct.unpack('!I', length_data)[0]
                message_data = await reader.readexactly(message_length)
            
            message = json.loads(message_data.decode('utf-8'))
            connection.last_seen = int(time.time())
            
            self.stats["total_messages_received"] += 1
            self.stats["total_bytes_received"] += len(message_data)
            
            return message
            
        except Exception as e:
            self.logger.error(f"Failed to receive message from {connection.relay_id.hex()}: {e}")
            connection.status = ConnectionStatus.FAILED
            return None
    
    async def _close_connection(self, connection: RelayConnection) -> None:
        """Close a connection."""
        try:
            if connection.connection is not None:
                if connection.connection_type == ConnectionType.WEBSOCKET:
                    await connection.connection.close()
                else:
                    reader, writer = connection.connection
                    writer.close()
                    await writer.wait_closed()
                
                connection.connection = None
            
            connection.status = ConnectionStatus.DISCONNECTED
            connection.is_authenticated = False
            
        except Exception as e:
            self.logger.error(f"Error closing connection to {connection.relay_id.hex()}: {e}")
    
    async def _handle_connection_failure(self, connection: RelayConnection) -> None:
        """Handle connection failure and schedule retry."""
        try:
            await self._close_connection(connection)
            
            if connection.connection_attempts < connection.max_attempts:
                connection.status = ConnectionStatus.RECONNECTING
                await asyncio.sleep(connection.retry_delay)
                connection.status = ConnectionStatus.DISCONNECTED
            else:
                self.logger.warning(f"Max connection attempts reached for {connection.relay_id.hex()}")
                
        except Exception as e:
            self.logger.error(f"Error handling connection failure: {e}")
    
    async def _heartbeat_loop(self) -> None:
        """Send heartbeat messages to all connected relays."""
        while True:
            try:
                current_time = int(time.time())
                
                for connection in self.connections.values():
                    if connection.status == ConnectionStatus.AUTHENTICATED:
                        # Send heartbeat
                        heartbeat = {
                            "type": "heartbeat",
                            "timestamp": current_time
                        }
                        
                        success = await self._send_message(connection, heartbeat)
                        if success:
                            connection.last_heartbeat = current_time
                        else:
                            connection.status = ConnectionStatus.FAILED
                
                await asyncio.sleep(self.config.heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(10)
    
    async def _reconnect_loop(self) -> None:
        """Monitor and reconnect failed connections."""
        while True:
            try:
                current_time = int(time.time())
                
                for connection in self.connections.values():
                    if connection.status == ConnectionStatus.FAILED:
                        # Check if enough time has passed for retry
                        if current_time - connection.last_seen > connection.retry_delay:
                            connection.status = ConnectionStatus.DISCONNECTED
                            connection.connection_attempts = 0
                
                await asyncio.sleep(self.config.reconnect_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in reconnect loop: {e}")
                await asyncio.sleep(10)
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status."""
        return {
            "total_connections": len(self.connections),
            "active_connections": sum(1 for c in self.connections.values() 
                                    if c.status == ConnectionStatus.AUTHENTICATED),
            "connecting_connections": sum(1 for c in self.connections.values() 
                                        if c.status == ConnectionStatus.CONNECTING),
            "failed_connections": sum(1 for c in self.connections.values() 
                                    if c.status == ConnectionStatus.FAILED),
            "stats": self.stats,
            "connections": [c.to_dict() for c in self.connections.values()]
        }
    
    def get_available_connections(self) -> List[RelayConnection]:
        """Get list of available (authenticated) connections."""
        return [c for c in self.connections.values() 
                if c.status == ConnectionStatus.AUTHENTICATED]
    
    async def send_message_to_relay(self, relay_id: bytes, message: Dict[str, Any]) -> bool:
        """Send a message to a specific relay."""
        if relay_id not in self.connections:
            return False
        
        connection = self.connections[relay_id]
        if connection.status != ConnectionStatus.AUTHENTICATED:
            return False
        
        return await self._send_message(connection, message)
    
    async def broadcast_message(self, message: Dict[str, Any], exclude_relays: Optional[Set[bytes]] = None) -> int:
        """Broadcast a message to all connected relays."""
        if exclude_relays is None:
            exclude_relays = set()
        
        sent_count = 0
        for relay_id, connection in self.connections.items():
            if (relay_id not in exclude_relays and 
                connection.status == ConnectionStatus.AUTHENTICATED):
                if await self._send_message(connection, message):
                    sent_count += 1
        
        return sent_count
