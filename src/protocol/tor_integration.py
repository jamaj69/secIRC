"""
Tor Integration Module for secIRC

This module provides transparent Tor proxy integration using multiple
Tor packages for robust and flexible Tor connectivity.
"""

import asyncio
import socket
import ssl
import time
import logging
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass
from enum import Enum
import struct

# Try to import Tor packages (optional dependencies)
try:
    import socks
    PYSOCKS_AVAILABLE = True
except ImportError:
    PYSOCKS_AVAILABLE = False

try:
    from tor_proxy import tor_proxy
    TOR_PROXY_AVAILABLE = True
except ImportError:
    TOR_PROXY_AVAILABLE = False

try:
    from torpy.http.requests import TorRequests
    from torpy import TorClient
    TORPY_AVAILABLE = True
except ImportError:
    TORPY_AVAILABLE = False

try:
    import stem
    from stem import Signal
    from stem.control import Controller
    STEM_AVAILABLE = True
except ImportError:
    STEM_AVAILABLE = False


class TorMethod(Enum):
    """Available Tor connection methods."""
    PYSOCKS = "pysocks"           # PySocks with SOCKS5 proxy
    TOR_PROXY = "tor_proxy"       # tor-proxy package
    TORPY = "torpy"              # Pure Python Tor implementation
    STEM = "stem"                # Tor controller with stem


@dataclass
class TorConfig:
    """Configuration for Tor integration."""
    
    method: TorMethod = TorMethod.PYSOCKS
    socks_host: str = "127.0.0.1"
    socks_port: int = 9050
    control_host: str = "127.0.0.1"
    control_port: int = 9051
    control_password: Optional[str] = None
    circuit_timeout: int = 60
    max_circuit_dirtiness: int = 600
    enable_ip_rotation: bool = True
    ip_rotation_interval: int = 300  # 5 minutes
    enable_circuit_verification: bool = True
    custom_tor_binary: Optional[str] = None
    tor_data_dir: Optional[str] = None
    log_level: str = "INFO"


@dataclass
class TorConnection:
    """Represents a Tor connection."""
    
    connection_id: str
    method: TorMethod
    socks_proxy: Optional[Tuple[str, int]] = None
    circuit_id: Optional[str] = None
    exit_node: Optional[str] = None
    created_at: int = 0
    last_used: int = 0
    is_active: bool = False
    
    def __post_init__(self):
        if self.created_at == 0:
            self.created_at = int(time.time())
        if self.last_used == 0:
            self.last_used = self.created_at


class TorIntegration:
    """Transparent Tor integration for secIRC relay connections."""
    
    def __init__(self, config: TorConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.connections: Dict[str, TorConnection] = {}
        self.controller: Optional[Controller] = None
        self.tor_client: Optional[TorClient] = None
        self.tor_proxy_port: Optional[int] = None
        
        # Check available methods
        self.available_methods = self._check_available_methods()
        self.logger.info(f"Available Tor methods: {[m.value for m in self.available_methods]}")
        
        # Validate configuration
        if self.config.method not in self.available_methods:
            raise ValueError(f"Tor method {self.config.method.value} not available. "
                           f"Available methods: {[m.value for m in self.available_methods]}")
    
    def _check_available_methods(self) -> List[TorMethod]:
        """Check which Tor methods are available."""
        available = []
        
        if PYSOCKS_AVAILABLE:
            available.append(TorMethod.PYSOCKS)
        
        if TOR_PROXY_AVAILABLE:
            available.append(TorMethod.TOR_PROXY)
        
        if TORPY_AVAILABLE:
            available.append(TorMethod.TORPY)
        
        if STEM_AVAILABLE:
            available.append(TorMethod.STEM)
        
        return available
    
    async def initialize(self) -> bool:
        """Initialize Tor integration."""
        try:
            self.logger.info(f"Initializing Tor integration with method: {self.config.method.value}")
            
            if self.config.method == TorMethod.PYSOCKS:
                return await self._initialize_pysocks()
            elif self.config.method == TorMethod.TOR_PROXY:
                return await self._initialize_tor_proxy()
            elif self.config.method == TorMethod.TORPY:
                return await self._initialize_torpy()
            elif self.config.method == TorMethod.STEM:
                return await self._initialize_stem()
            else:
                raise ValueError(f"Unsupported Tor method: {self.config.method.value}")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize Tor integration: {e}")
            return False
    
    async def _initialize_pysocks(self) -> bool:
        """Initialize PySocks-based Tor connection."""
        try:
            # Test SOCKS connection
            test_socket = socks.socksocket()
            test_socket.set_proxy(socks.SOCKS5, self.config.socks_host, self.config.socks_port)
            test_socket.settimeout(10)
            
            # Try to connect to a test address
            test_socket.connect(("check.torproject.org", 80))
            test_socket.close()
            
            self.logger.info("PySocks Tor connection initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"PySocks initialization failed: {e}")
            return False
    
    async def _initialize_tor_proxy(self) -> bool:
        """Initialize tor-proxy package."""
        try:
            # Start tor-proxy
            self.tor_proxy_port = tor_proxy()
            self.logger.info(f"tor-proxy started on port {self.tor_proxy_port}")
            return True
            
        except Exception as e:
            self.logger.error(f"tor-proxy initialization failed: {e}")
            return False
    
    async def _initialize_torpy(self) -> bool:
        """Initialize Torpy (pure Python Tor)."""
        try:
            self.tor_client = TorClient()
            self.logger.info("Torpy client initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Torpy initialization failed: {e}")
            return False
    
    async def _initialize_stem(self) -> bool:
        """Initialize Stem Tor controller."""
        try:
            if self.config.control_password:
                self.controller = Controller.from_port(
                    address=self.config.control_host,
                    port=self.config.control_port
                )
                self.controller.authenticate(password=self.config.control_password)
            else:
                self.controller = Controller.from_port(
                    address=self.config.control_host,
                    port=self.config.control_port
                )
                self.controller.authenticate()
            
            self.logger.info("Stem Tor controller initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Stem initialization failed: {e}")
            return False
    
    async def create_connection(self, connection_id: str) -> Optional[TorConnection]:
        """Create a new Tor connection."""
        try:
            connection = TorConnection(
                connection_id=connection_id,
                method=self.config.method,
                socks_proxy=(self.config.socks_host, self.config.socks_port)
            )
            
            if self.config.method == TorMethod.PYSOCKS:
                success = await self._create_pysocks_connection(connection)
            elif self.config.method == TorMethod.TOR_PROXY:
                success = await self._create_tor_proxy_connection(connection)
            elif self.config.method == TorMethod.TORPY:
                success = await self._create_torpy_connection(connection)
            elif self.config.method == TorMethod.STEM:
                success = await self._create_stem_connection(connection)
            else:
                success = False
            
            if success:
                connection.is_active = True
                self.connections[connection_id] = connection
                self.logger.info(f"Tor connection {connection_id} created successfully")
                return connection
            else:
                self.logger.error(f"Failed to create Tor connection {connection_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating Tor connection {connection_id}: {e}")
            return None
    
    async def _create_pysocks_connection(self, connection: TorConnection) -> bool:
        """Create PySocks-based connection."""
        try:
            # Test the connection
            test_socket = socks.socksocket()
            test_socket.set_proxy(socks.SOCKS5, *connection.socks_proxy)
            test_socket.settimeout(10)
            test_socket.connect(("check.torproject.org", 80))
            test_socket.close()
            return True
            
        except Exception as e:
            self.logger.error(f"PySocks connection test failed: {e}")
            return False
    
    async def _create_tor_proxy_connection(self, connection: TorConnection) -> bool:
        """Create tor-proxy-based connection."""
        try:
            if self.tor_proxy_port is None:
                self.tor_proxy_port = tor_proxy()
            
            connection.socks_proxy = ("127.0.0.1", self.tor_proxy_port)
            return True
            
        except Exception as e:
            self.logger.error(f"tor-proxy connection creation failed: {e}")
            return False
    
    async def _create_torpy_connection(self, connection: TorConnection) -> bool:
        """Create Torpy-based connection."""
        try:
            if self.tor_client is None:
                self.tor_client = TorClient()
            
            # Create a circuit
            circuit = await self.tor_client.create_circuit()
            connection.circuit_id = circuit.id
            connection.exit_node = circuit.path[-1] if circuit.path else None
            return True
            
        except Exception as e:
            self.logger.error(f"Torpy connection creation failed: {e}")
            return False
    
    async def _create_stem_connection(self, connection: TorConnection) -> bool:
        """Create Stem-based connection."""
        try:
            if self.controller is None:
                return False
            
            # Get current circuit info
            circuits = self.controller.get_circuits()
            if circuits:
                circuit = circuits[0]
                connection.circuit_id = circuit.id
                connection.exit_node = circuit.path[-1] if circuit.path else None
            
            return True
            
        except Exception as e:
            self.logger.error(f"Stem connection creation failed: {e}")
            return False
    
    async def connect_through_tor(self, connection_id: str, host: str, port: int) -> Optional[socket.socket]:
        """Create a socket connection through Tor."""
        try:
            if connection_id not in self.connections:
                connection = await self.create_connection(connection_id)
                if connection is None:
                    return None
            else:
                connection = self.connections[connection_id]
            
            connection.last_used = int(time.time())
            
            if self.config.method == TorMethod.PYSOCKS:
                return await self._connect_pysocks(connection, host, port)
            elif self.config.method == TorMethod.TOR_PROXY:
                return await self._connect_tor_proxy(connection, host, port)
            elif self.config.method == TorMethod.TORPY:
                return await self._connect_torpy(connection, host, port)
            elif self.config.method == TorMethod.STEM:
                return await self._connect_stem(connection, host, port)
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to connect through Tor: {e}")
            return None
    
    async def _connect_pysocks(self, connection: TorConnection, host: str, port: int) -> socket.socket:
        """Connect using PySocks."""
        sock = socks.socksocket()
        sock.set_proxy(socks.SOCKS5, *connection.socks_proxy)
        sock.settimeout(self.config.circuit_timeout)
        sock.connect((host, port))
        return sock
    
    async def _connect_tor_proxy(self, connection: TorConnection, host: str, port: int) -> socket.socket:
        """Connect using tor-proxy."""
        sock = socks.socksocket()
        sock.set_proxy(socks.SOCKS5, *connection.socks_proxy)
        sock.settimeout(self.config.circuit_timeout)
        sock.connect((host, port))
        return sock
    
    async def _connect_torpy(self, connection: TorConnection, host: str, port: int) -> socket.socket:
        """Connect using Torpy."""
        if self.tor_client is None:
            raise Exception("Torpy client not initialized")
        
        # Create a new circuit if needed
        if connection.circuit_id is None:
            circuit = await self.tor_client.create_circuit()
            connection.circuit_id = circuit.id
            connection.exit_node = circuit.path[-1] if circuit.path else None
        
        # Create socket through Tor circuit
        sock = await self.tor_client.create_connection((host, port))
        return sock
    
    async def _connect_stem(self, connection: TorConnection, host: str, port: int) -> socket.socket:
        """Connect using Stem controller."""
        if self.controller is None:
            raise Exception("Stem controller not initialized")
        
        # Use SOCKS proxy through Tor
        sock = socks.socksocket()
        sock.set_proxy(socks.SOCKS5, *connection.socks_proxy)
        sock.settimeout(self.config.circuit_timeout)
        sock.connect((host, port))
        return sock
    
    async def rotate_ip(self, connection_id: str) -> bool:
        """Rotate IP address for a connection."""
        try:
            if self.config.method == TorMethod.STEM and self.controller:
                # Signal Tor to create new circuit
                self.controller.signal(Signal.NEWNYM)
                self.logger.info(f"Requested new Tor circuit for connection {connection_id}")
                return True
            elif self.config.method == TorMethod.TORPY and self.tor_client:
                # Create new circuit with Torpy
                if connection_id in self.connections:
                    connection = self.connections[connection_id]
                    circuit = await self.tor_client.create_circuit()
                    connection.circuit_id = circuit.id
                    connection.exit_node = circuit.path[-1] if circuit.path else None
                    self.logger.info(f"Created new Tor circuit for connection {connection_id}")
                    return True
            
            self.logger.warning(f"IP rotation not supported for method {self.config.method.value}")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to rotate IP for connection {connection_id}: {e}")
            return False
    
    async def get_exit_node(self, connection_id: str) -> Optional[str]:
        """Get the exit node for a connection."""
        if connection_id in self.connections:
            return self.connections[connection_id].exit_node
        return None
    
    async def verify_tor_connection(self, connection_id: str) -> bool:
        """Verify that a connection is actually using Tor."""
        try:
            if connection_id not in self.connections:
                return False
            
            # Connect to check.torproject.org to verify Tor usage
            sock = await self.connect_through_tor(connection_id, "check.torproject.org", 80)
            if sock is None:
                return False
            
            # Send HTTP request
            request = b"GET / HTTP/1.1\r\nHost: check.torproject.org\r\n\r\n"
            sock.send(request)
            
            # Read response
            response = sock.recv(4096)
            sock.close()
            
            # Check if response indicates Tor usage
            return b"Congratulations" in response or b"tor" in response.lower()
            
        except Exception as e:
            self.logger.error(f"Failed to verify Tor connection {connection_id}: {e}")
            return False
    
    async def close_connection(self, connection_id: str) -> bool:
        """Close a Tor connection."""
        try:
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                connection.is_active = False
                del self.connections[connection_id]
                self.logger.info(f"Closed Tor connection {connection_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error closing Tor connection {connection_id}: {e}")
            return False
    
    async def cleanup(self) -> None:
        """Cleanup Tor integration."""
        try:
            # Close all connections
            for connection_id in list(self.connections.keys()):
                await self.close_connection(connection_id)
            
            # Close controller
            if self.controller:
                self.controller.close()
                self.controller = None
            
            # Close Torpy client
            if self.tor_client:
                await self.tor_client.close()
                self.tor_client = None
            
            self.logger.info("Tor integration cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error during Tor cleanup: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get Tor integration status."""
        return {
            "method": self.config.method.value,
            "available_methods": [m.value for m in self.available_methods],
            "active_connections": len([c for c in self.connections.values() if c.is_active]),
            "total_connections": len(self.connections),
            "controller_connected": self.controller is not None,
            "torpy_available": self.tor_client is not None,
            "tor_proxy_port": self.tor_proxy_port,
            "connections": {
                conn_id: {
                    "method": conn.method.value,
                    "circuit_id": conn.circuit_id,
                    "exit_node": conn.exit_node,
                    "is_active": conn.is_active,
                    "created_at": conn.created_at,
                    "last_used": conn.last_used
                }
                for conn_id, conn in self.connections.items()
            }
        }
