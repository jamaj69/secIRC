"""
Torrent-Inspired Relay Discovery System.
Implements a decentralized relay discovery system based on BitTorrent protocol
with enhanced security measures to prevent spy server infiltration.
"""

import asyncio
import hashlib
import json
import os
import random
import socket
import struct
import time
from typing import Dict, List, Set, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import ipaddress

from .encryption import EndToEndEncryption
from .mesh_network import MeshNetwork, RelayNode


class DiscoveryMethod(Enum):
    """Methods for discovering relay servers."""
    
    DHT = "dht"                    # Distributed Hash Table
    TRACKER = "tracker"            # Tracker protocol
    PEX = "pex"                    # Peer Exchange
    BOOTSTRAP = "bootstrap"        # Bootstrap nodes
    DNS = "dns"                    # DNS-based discovery
    WEB = "web"                    # Web-based discovery


class RelayInfo(Enum):
    """Types of relay information."""
    
    BASIC = "basic"                # Basic relay info
    DETAILED = "detailed"          # Detailed relay info
    VERIFIED = "verified"          # Verified relay info
    TRUSTED = "trusted"            # Trusted relay info


@dataclass
class RelayAnnouncement:
    """Announcement of a relay server."""
    
    relay_id: bytes                # 20-byte relay ID (like torrent peer ID)
    public_key: bytes              # Relay's public key
    address: str                   # IP address
    port: int                      # Port number
    services: List[str]            # Services offered
    capabilities: List[str]        # Capabilities
    uptime: int                    # Uptime in seconds
    last_seen: int                 # Last seen timestamp
    version: str                   # Protocol version
    country: Optional[str] = None  # Country code
    bandwidth: Optional[int] = None # Available bandwidth
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "relay_id": self.relay_id.hex(),
            "public_key": self.public_key.hex(),
            "address": self.address,
            "port": self.port,
            "services": self.services,
            "capabilities": self.capabilities,
            "uptime": self.uptime,
            "last_seen": self.last_seen,
            "version": self.version,
            "country": self.country,
            "bandwidth": self.bandwidth
        }


@dataclass
class DHTNode:
    """DHT node for relay discovery."""
    
    node_id: bytes                 # 20-byte node ID
    address: str                   # IP address
    port: int                      # Port number
    last_seen: int                 # Last seen timestamp
    distance: int                  # Distance from our node ID
    is_verified: bool = False      # Whether node is verified
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "node_id": self.node_id.hex(),
            "address": self.address,
            "port": self.port,
            "last_seen": self.last_seen,
            "distance": self.distance,
            "is_verified": self.is_verified
        }


@dataclass
class TrackerResponse:
    """Response from tracker server."""
    
    interval: int                  # Announce interval
    min_interval: int              # Minimum announce interval
    complete: int                  # Number of complete relays
    incomplete: int                # Number of incomplete relays
    peers: List[RelayAnnouncement] # List of relay announcements
    failure_reason: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "interval": self.interval,
            "min_interval": self.min_interval,
            "complete": self.complete,
            "incomplete": self.incomplete,
            "peers": [peer.to_dict() for peer in self.peers],
            "failure_reason": self.failure_reason
        }


@dataclass
class DiscoveryResult:
    """Result of relay discovery."""
    
    method: DiscoveryMethod
    relays_found: List[RelayAnnouncement]
    discovery_time: float
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "method": self.method.value,
            "relays_found": [relay.to_dict() for relay in self.relays_found],
            "discovery_time": self.discovery_time,
            "success": self.success,
            "error_message": self.error_message
        }


class TorrentDiscoverySystem:
    """Torrent-inspired relay discovery system with enhanced security."""
    
    def __init__(self, mesh_network: MeshNetwork):
        self.mesh_network = mesh_network
        self.encryption = EndToEndEncryption()
        
        # Discovery state
        self.discovered_relays: Dict[bytes, RelayAnnouncement] = {}
        self.dht_nodes: Dict[bytes, DHTNode] = {}
        self.tracker_servers: List[str] = []
        self.bootstrap_nodes: List[Tuple[str, int]] = []
        
        # DHT configuration
        self.dht_port = 6881  # Standard DHT port
        self.dht_bucket_size = 8  # Kademlia bucket size
        self.dht_alpha = 3  # Kademlia alpha parameter
        self.dht_k = 20  # Kademlia k parameter
        
        # Tracker configuration
        self.tracker_interval = 1800  # 30 minutes
        self.tracker_min_interval = 300  # 5 minutes
        self.tracker_timeout = 30  # 30 seconds
        
        # Security configuration
        self.verification_required = True
        self.trust_threshold = 0.7
        self.max_discovery_attempts = 3
        self.discovery_timeout = 60  # 60 seconds
        
        # Statistics
        self.stats = {
            "discoveries_attempted": 0,
            "discoveries_successful": 0,
            "relays_discovered": 0,
            "dht_nodes_known": 0,
            "tracker_announcements": 0,
            "pex_exchanges": 0,
            "verification_attempts": 0,
            "verification_successes": 0,
            "spy_servers_detected": 0
        }
        
        # Background tasks
        self.discovery_task: Optional[asyncio.Task] = None
        self.dht_task: Optional[asyncio.Task] = None
        self.tracker_task: Optional[asyncio.Task] = None
        self.verification_task: Optional[asyncio.Task] = None
        
        # Security measures
        self.known_spy_servers: Set[bytes] = set()
        self.verification_cache: Dict[bytes, Tuple[bool, int]] = {}
        self.rate_limits: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
    
    async def start_discovery_service(self) -> None:
        """Start the torrent-inspired discovery service."""
        print("🌐 Starting torrent-inspired relay discovery service...")
        
        # Initialize bootstrap nodes
        await self._initialize_bootstrap_nodes()
        
        # Start DHT service
        await self._start_dht_service()
        
        # Start tracker service
        await self._start_tracker_service()
        
        # Start discovery service
        await self._start_discovery_service()
        
        # Start verification service
        await self._start_verification_service()
        
        print("✅ Torrent-inspired discovery service started")
        print(f"   DHT Port: {self.dht_port}")
        print(f"   Bootstrap Nodes: {len(self.bootstrap_nodes)}")
        print(f"   Tracker Servers: {len(self.tracker_servers)}")
    
    async def _initialize_bootstrap_nodes(self) -> None:
        """Initialize bootstrap nodes for discovery."""
        # Standard BitTorrent bootstrap nodes
        self.bootstrap_nodes = [
            ("router.bittorrent.com", 6881),
            ("dht.transmissionbt.com", 6881),
            ("router.utorrent.com", 6881),
            ("dht.aelitis.com", 6881),
            ("router.silotis.us", 6881)
        ]
        
        # secIRC-specific bootstrap nodes
        self.bootstrap_nodes.extend([
            ("bootstrap1.secirc.net", 6881),
            ("bootstrap2.secirc.net", 6881),
            ("bootstrap3.secirc.net", 6881)
        ])
        
        print(f"📡 Initialized {len(self.bootstrap_nodes)} bootstrap nodes")
    
    async def _start_dht_service(self) -> None:
        """Start DHT service for decentralized discovery."""
        print("🔍 Starting DHT service...")
        
        # Create DHT node ID
        self.dht_node_id = self._generate_dht_node_id()
        
        # Start DHT background task
        self.dht_task = asyncio.create_task(self._dht_service_loop())
        
        print(f"✅ DHT service started with node ID: {self.dht_node_id.hex()}")
    
    async def _start_tracker_service(self) -> None:
        """Start tracker service for centralized discovery."""
        print("📡 Starting tracker service...")
        
        # Initialize tracker servers
        self.tracker_servers = [
            "http://tracker1.secirc.net:8080/announce",
            "http://tracker2.secirc.net:8080/announce",
            "http://tracker3.secirc.net:8080/announce",
            "udp://tracker1.secirc.net:8080/announce",
            "udp://tracker2.secirc.net:8080/announce"
        ]
        
        # Start tracker background task
        self.tracker_task = asyncio.create_task(self._tracker_service_loop())
        
        print(f"✅ Tracker service started with {len(self.tracker_servers)} trackers")
    
    async def _start_discovery_service(self) -> None:
        """Start main discovery service."""
        print("🔍 Starting discovery service...")
        
        # Start discovery background task
        self.discovery_task = asyncio.create_task(self._discovery_service_loop())
        
        print("✅ Discovery service started")
    
    async def _start_verification_service(self) -> None:
        """Start verification service for security."""
        print("🛡️ Starting verification service...")
        
        # Start verification background task
        self.verification_task = asyncio.create_task(self._verification_service_loop())
        
        print("✅ Verification service started")
    
    # DHT Implementation
    
    async def _dht_service_loop(self) -> None:
        """Main DHT service loop."""
        while True:
            try:
                # Perform DHT operations
                await self._dht_bootstrap()
                await self._dht_find_nodes()
                await self._dht_announce_peer()
                
                # Wait before next iteration
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                print(f"❌ DHT service error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def _dht_bootstrap(self) -> None:
        """Bootstrap DHT network."""
        for address, port in self.bootstrap_nodes:
            try:
                # Send find_node request to bootstrap node
                await self._dht_find_node(address, port, self.dht_node_id)
                
            except Exception as e:
                print(f"❌ DHT bootstrap failed for {address}:{port}: {e}")
    
    async def _dht_find_nodes(self) -> None:
        """Find nodes in DHT network."""
        # Find nodes closest to our node ID
        target_id = self._generate_random_node_id()
        
        # Query closest known nodes
        closest_nodes = self._get_closest_dht_nodes(target_id, self.dht_k)
        
        for node in closest_nodes:
            try:
                await self._dht_find_node(node.address, node.port, target_id)
            except Exception as e:
                print(f"❌ DHT find_node failed for {node.address}:{node.port}: {e}")
    
    async def _dht_announce_peer(self) -> None:
        """Announce our peer to DHT network."""
        # Generate info hash for our relay
        info_hash = self._generate_relay_info_hash()
        
        # Find nodes closest to info hash
        closest_nodes = self._get_closest_dht_nodes(info_hash, self.dht_k)
        
        for node in closest_nodes:
            try:
                await self._dht_announce_peer_to_node(node.address, node.port, info_hash)
            except Exception as e:
                print(f"❌ DHT announce_peer failed for {node.address}:{node.port}: {e}")
    
    async def _dht_find_node(self, address: str, port: int, target_id: bytes) -> None:
        """Send find_node request to DHT node."""
        # Create find_node request
        request = {
            "t": self._generate_transaction_id(),
            "y": "q",
            "q": "find_node",
            "a": {
                "id": self.dht_node_id.hex(),
                "target": target_id.hex()
            }
        }
        
        # Send request
        response = await self._send_dht_request(address, port, request)
        
        if response and response.get("y") == "r":
            # Process response
            nodes = response.get("r", {}).get("nodes", "")
            await self._process_dht_nodes(nodes)
    
    async def _dht_announce_peer_to_node(self, address: str, port: int, info_hash: bytes) -> None:
        """Announce peer to DHT node."""
        # Create announce_peer request
        request = {
            "t": self._generate_transaction_id(),
            "y": "q",
            "q": "announce_peer",
            "a": {
                "id": self.dht_node_id.hex(),
                "info_hash": info_hash.hex(),
                "port": self.dht_port,
                "token": self._generate_dht_token()
            }
        }
        
        # Send request
        response = await self._send_dht_request(address, port, request)
        
        if response and response.get("y") == "r":
            self.stats["tracker_announcements"] += 1
    
    async def _send_dht_request(self, address: str, port: int, request: Dict) -> Optional[Dict]:
        """Send DHT request and wait for response."""
        try:
            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(10)  # 10 second timeout
            
            # Send request
            request_data = json.dumps(request).encode()
            sock.sendto(request_data, (address, port))
            
            # Wait for response
            response_data, addr = sock.recvfrom(1024)
            response = json.loads(response_data.decode())
            
            sock.close()
            return response
            
        except Exception as e:
            print(f"❌ DHT request failed to {address}:{port}: {e}")
            return None
    
    async def _process_dht_nodes(self, nodes_data: str) -> None:
        """Process DHT nodes from response."""
        if not nodes_data:
            return
        
        # Parse nodes data (compact format)
        nodes = []
        for i in range(0, len(nodes_data), 26):  # 20 bytes ID + 4 bytes IP + 2 bytes port
            if i + 26 <= len(nodes_data):
                node_id = nodes_data[i:i+20]
                ip_bytes = nodes_data[i+20:i+24]
                port_bytes = nodes_data[i+24:i+26]
                
                ip = socket.inet_ntoa(ip_bytes)
                port = struct.unpack(">H", port_bytes)[0]
                
                # Create DHT node
                dht_node = DHTNode(
                    node_id=node_id,
                    address=ip,
                    port=port,
                    last_seen=int(time.time()),
                    distance=self._calculate_dht_distance(self.dht_node_id, node_id)
                )
                
                nodes.append(dht_node)
        
        # Add nodes to DHT network
        for node in nodes:
            self.dht_nodes[node.node_id] = node
        
        self.stats["dht_nodes_known"] = len(self.dht_nodes)
    
    # Tracker Implementation
    
    async def _tracker_service_loop(self) -> None:
        """Main tracker service loop."""
        while True:
            try:
                # Announce to all trackers
                for tracker_url in self.tracker_servers:
                    await self._announce_to_tracker(tracker_url)
                
                # Wait before next announcement
                await asyncio.sleep(self.tracker_interval)
                
            except Exception as e:
                print(f"❌ Tracker service error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def _announce_to_tracker(self, tracker_url: str) -> None:
        """Announce to tracker server."""
        try:
            if tracker_url.startswith("http"):
                response = await self._announce_to_http_tracker(tracker_url)
            elif tracker_url.startswith("udp"):
                response = await self._announce_to_udp_tracker(tracker_url)
            else:
                print(f"❌ Unsupported tracker protocol: {tracker_url}")
                return
            
            if response and response.success:
                # Process discovered relays
                for relay in response.peers:
                    await self._process_discovered_relay(relay)
                
                self.stats["tracker_announcements"] += 1
                
        except Exception as e:
            print(f"❌ Tracker announcement failed for {tracker_url}: {e}")
    
    async def _announce_to_http_tracker(self, tracker_url: str) -> Optional[TrackerResponse]:
        """Announce to HTTP tracker."""
        try:
            import aiohttp
            
            # Prepare announce parameters
            params = {
                "info_hash": self._generate_relay_info_hash().hex(),
                "peer_id": self.dht_node_id.hex(),
                "port": self.dht_port,
                "uploaded": 0,
                "downloaded": 0,
                "left": 0,
                "compact": 1,
                "event": "started"
            }
            
            # Send HTTP request
            async with aiohttp.ClientSession() as session:
                async with session.get(tracker_url, params=params, timeout=30) as response:
                    if response.status == 200:
                        data = await response.read()
                        return await self._parse_tracker_response(data)
                    else:
                        print(f"❌ HTTP tracker error: {response.status}")
                        return None
                        
        except Exception as e:
            print(f"❌ HTTP tracker announcement failed: {e}")
            return None
    
    async def _announce_to_udp_tracker(self, tracker_url: str) -> Optional[TrackerResponse]:
        """Announce to UDP tracker."""
        try:
            # Parse tracker URL
            url_parts = tracker_url.replace("udp://", "").split("/")
            host_port = url_parts[0].split(":")
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 80
            
            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(30)
            
            # Send connect request
            connect_request = struct.pack(">QII", 0x41727101980, 0, 0)  # Magic, action, transaction_id
            sock.sendto(connect_request, (host, port))
            
            # Receive connect response
            connect_response, addr = sock.recvfrom(16)
            if len(connect_response) >= 16:
                action, transaction_id, connection_id = struct.unpack(">IIQ", connect_response)
                
                if action == 0:  # Connect response
                    # Send announce request
                    info_hash = self._generate_relay_info_hash()
                    peer_id = self.dht_node_id
                    
                    announce_request = struct.pack(
                        ">QII20s20sQQQIIIH",
                        connection_id,  # connection_id
                        1,              # action (announce)
                        0,              # transaction_id
                        info_hash,      # info_hash
                        peer_id,        # peer_id
                        0,              # downloaded
                        0,              # left
                        0,              # uploaded
                        2,              # event (started)
                        0,              # IP address
                        0,              # key
                        -1,             # num_want
                        self.dht_port   # port
                    )
                    
                    sock.sendto(announce_request, (host, port))
                    
                    # Receive announce response
                    announce_response, addr = sock.recvfrom(1024)
                    if len(announce_response) >= 20:
                        action, transaction_id, interval, leechers, seeders = struct.unpack(">IIIII", announce_response[:20])
                        
                        if action == 1:  # Announce response
                            # Parse peers
                            peers_data = announce_response[20:]
                            peers = []
                            
                            for i in range(0, len(peers_data), 6):  # 4 bytes IP + 2 bytes port
                                if i + 6 <= len(peers_data):
                                    ip_bytes = peers_data[i:i+4]
                                    port_bytes = peers_data[i+4:i+6]
                                    
                                    ip = socket.inet_ntoa(ip_bytes)
                                    port = struct.unpack(">H", port_bytes)[0]
                                    
                                    # Create relay announcement
                                    relay = RelayAnnouncement(
                                        relay_id=os.urandom(20),
                                        public_key=os.urandom(32),
                                        address=ip,
                                        port=port,
                                        services=["relay"],
                                        capabilities=["udp", "encryption"],
                                        uptime=0,
                                        last_seen=int(time.time()),
                                        version="1.0.0"
                                    )
                                    
                                    peers.append(relay)
                            
                            sock.close()
                            return TrackerResponse(
                                interval=interval,
                                min_interval=300,
                                complete=seeders,
                                incomplete=leechers,
                                peers=peers
                            )
            
            sock.close()
            return None
            
        except Exception as e:
            print(f"❌ UDP tracker announcement failed: {e}")
            return None
    
    async def _parse_tracker_response(self, data: bytes) -> Optional[TrackerResponse]:
        """Parse tracker response data."""
        try:
            import bencodepy
            
            # Decode bencoded response
            response_data = bencodepy.decode(data)
            
            if b"failure reason" in response_data:
                return TrackerResponse(
                    interval=0,
                    min_interval=0,
                    complete=0,
                    incomplete=0,
                    peers=[],
                    failure_reason=response_data[b"failure reason"].decode()
                )
            
            # Parse peers
            peers = []
            if b"peers" in response_data:
                peers_data = response_data[b"peers"]
                
                if isinstance(peers_data, bytes):
                    # Compact format
                    for i in range(0, len(peers_data), 6):  # 4 bytes IP + 2 bytes port
                        if i + 6 <= len(peers_data):
                            ip_bytes = peers_data[i:i+4]
                            port_bytes = peers_data[i+4:i+6]
                            
                            ip = socket.inet_ntoa(ip_bytes)
                            port = struct.unpack(">H", port_bytes)[0]
                            
                            # Create relay announcement
                            relay = RelayAnnouncement(
                                relay_id=os.urandom(20),
                                public_key=os.urandom(32),
                                address=ip,
                                port=port,
                                services=["relay"],
                                capabilities=["udp", "encryption"],
                                uptime=0,
                                last_seen=int(time.time()),
                                version="1.0.0"
                            )
                            
                            peers.append(relay)
            
            return TrackerResponse(
                interval=response_data.get(b"interval", 1800),
                min_interval=response_data.get(b"min interval", 300),
                complete=response_data.get(b"complete", 0),
                incomplete=response_data.get(b"incomplete", 0),
                peers=peers
            )
            
        except Exception as e:
            print(f"❌ Failed to parse tracker response: {e}")
            return None
    
    # Discovery Service
    
    async def _discovery_service_loop(self) -> None:
        """Main discovery service loop."""
        while True:
            try:
                # Perform discovery using multiple methods
                discovery_results = []
                
                # DHT discovery
                dht_result = await self._discover_relays_dht()
                if dht_result:
                    discovery_results.append(dht_result)
                
                # Tracker discovery
                tracker_result = await self._discover_relays_tracker()
                if tracker_result:
                    discovery_results.append(tracker_result)
                
                # PEX discovery
                pex_result = await self._discover_relays_pex()
                if pex_result:
                    discovery_results.append(pex_result)
                
                # Process discovery results
                await self._process_discovery_results(discovery_results)
                
                # Wait before next discovery
                await asyncio.sleep(600)  # 10 minutes
                
            except Exception as e:
                print(f"❌ Discovery service error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def _discover_relays_dht(self) -> Optional[DiscoveryResult]:
        """Discover relays using DHT."""
        start_time = time.time()
        
        try:
            # Generate random target ID
            target_id = self._generate_random_node_id()
            
            # Find nodes closest to target
            closest_nodes = self._get_closest_dht_nodes(target_id, self.dht_k)
            
            # Query nodes for relays
            discovered_relays = []
            for node in closest_nodes:
                try:
                    relays = await self._query_dht_node_for_relays(node.address, node.port, target_id)
                    discovered_relays.extend(relays)
                except Exception as e:
                    print(f"❌ DHT query failed for {node.address}:{node.port}: {e}")
            
            discovery_time = time.time() - start_time
            
            return DiscoveryResult(
                method=DiscoveryMethod.DHT,
                relays_found=discovered_relays,
                discovery_time=discovery_time,
                success=len(discovered_relays) > 0
            )
            
        except Exception as e:
            discovery_time = time.time() - start_time
            return DiscoveryResult(
                method=DiscoveryMethod.DHT,
                relays_found=[],
                discovery_time=discovery_time,
                success=False,
                error_message=str(e)
            )
    
    async def _discover_relays_tracker(self) -> Optional[DiscoveryResult]:
        """Discover relays using tracker."""
        start_time = time.time()
        
        try:
            discovered_relays = []
            
            # Query all trackers
            for tracker_url in self.tracker_servers:
                try:
                    if tracker_url.startswith("http"):
                        response = await self._announce_to_http_tracker(tracker_url)
                    elif tracker_url.startswith("udp"):
                        response = await self._announce_to_udp_tracker(tracker_url)
                    else:
                        continue
                    
                    if response and response.success:
                        discovered_relays.extend(response.peers)
                        
                except Exception as e:
                    print(f"❌ Tracker query failed for {tracker_url}: {e}")
            
            discovery_time = time.time() - start_time
            
            return DiscoveryResult(
                method=DiscoveryMethod.TRACKER,
                relays_found=discovered_relays,
                discovery_time=discovery_time,
                success=len(discovered_relays) > 0
            )
            
        except Exception as e:
            discovery_time = time.time() - start_time
            return DiscoveryResult(
                method=DiscoveryMethod.TRACKER,
                relays_found=[],
                discovery_time=discovery_time,
                success=False,
                error_message=str(e)
            )
    
    async def _discover_relays_pex(self) -> Optional[DiscoveryResult]:
        """Discover relays using Peer Exchange (PEX)."""
        start_time = time.time()
        
        try:
            discovered_relays = []
            
            # Get known relays for PEX
            known_relays = list(self.discovered_relays.values())
            
            # Exchange peer lists with known relays
            for relay in known_relays[:10]:  # Limit to 10 relays
                try:
                    pex_relays = await self._exchange_peers_with_relay(relay)
                    discovered_relays.extend(pex_relays)
                except Exception as e:
                    print(f"❌ PEX failed for {relay.address}:{relay.port}: {e}")
            
            discovery_time = time.time() - start_time
            
            return DiscoveryResult(
                method=DiscoveryMethod.PEX,
                relays_found=discovered_relays,
                discovery_time=discovery_time,
                success=len(discovered_relays) > 0
            )
            
        except Exception as e:
            discovery_time = time.time() - start_time
            return DiscoveryResult(
                method=DiscoveryMethod.PEX,
                relays_found=[],
                discovery_time=discovery_time,
                success=False,
                error_message=str(e)
            )
    
    async def _process_discovery_results(self, results: List[DiscoveryResult]) -> None:
        """Process discovery results."""
        for result in results:
            self.stats["discoveries_attempted"] += 1
            
            if result.success:
                self.stats["discoveries_successful"] += 1
                self.stats["relays_discovered"] += len(result.relays_found)
                
                # Process each discovered relay
                for relay in result.relays_found:
                    await self._process_discovered_relay(relay)
    
    async def _process_discovered_relay(self, relay: RelayAnnouncement) -> None:
        """Process a discovered relay."""
        # Check if relay is already known
        if relay.relay_id in self.discovered_relays:
            # Update existing relay
            existing_relay = self.discovered_relays[relay.relay_id]
            existing_relay.last_seen = relay.last_seen
            existing_relay.uptime = relay.uptime
            return
        
        # Check if relay is a known spy server
        if relay.relay_id in self.known_spy_servers:
            print(f"🚫 Blocked known spy server: {relay.address}:{relay.port}")
            return
        
        # Check rate limits
        if not self._check_rate_limit(relay.address):
            print(f"🚫 Rate limited relay: {relay.address}:{relay.port}")
            return
        
        # Add to discovered relays
        self.discovered_relays[relay.relay_id] = relay
        
        # Queue for verification
        await self._queue_relay_for_verification(relay)
    
    # Security and Verification
    
    async def _verification_service_loop(self) -> None:
        """Main verification service loop."""
        while True:
            try:
                # Verify discovered relays
                await self._verify_discovered_relays()
                
                # Clean up old verification cache
                await self._cleanup_verification_cache()
                
                # Wait before next verification
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                print(f"❌ Verification service error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def _queue_relay_for_verification(self, relay: RelayAnnouncement) -> None:
        """Queue relay for verification."""
        # Check if relay is already in verification cache
        if relay.relay_id in self.verification_cache:
            is_verified, timestamp = self.verification_cache[relay.relay_id]
            if time.time() - timestamp < 3600:  # Cache for 1 hour
                return
        
        # Queue for verification
        await self._verify_relay(relay)
    
    async def _verify_relay(self, relay: RelayAnnouncement) -> bool:
        """Verify a relay for security."""
        self.stats["verification_attempts"] += 1
        
        try:
            # Perform security checks
            security_score = await self._perform_security_checks(relay)
            
            if security_score >= self.trust_threshold:
                # Relay is trusted
                self.verification_cache[relay.relay_id] = (True, int(time.time()))
                self.stats["verification_successes"] += 1
                
                # Add to mesh network
                await self._add_relay_to_mesh(relay)
                
                return True
            else:
                # Relay is suspicious
                self.verification_cache[relay.relay_id] = (False, int(time.time()))
                
                if security_score < 0.3:
                    # Relay is likely a spy server
                    self.known_spy_servers.add(relay.relay_id)
                    self.stats["spy_servers_detected"] += 1
                    print(f"🚫 Detected spy server: {relay.address}:{relay.port}")
                
                return False
                
        except Exception as e:
            print(f"❌ Verification failed for {relay.address}:{relay.port}: {e}")
            return False
    
    async def _perform_security_checks(self, relay: RelayAnnouncement) -> float:
        """Perform security checks on relay."""
        security_score = 0.0
        
        # Check 1: IP address validation
        if self._validate_ip_address(relay.address):
            security_score += 0.2
        
        # Check 2: Port validation
        if self._validate_port(relay.port):
            security_score += 0.2
        
        # Check 3: Public key validation
        if self._validate_public_key(relay.public_key):
            security_score += 0.2
        
        # Check 4: Response time check
        if await self._check_response_time(relay):
            security_score += 0.2
        
        # Check 5: Protocol compliance
        if await self._check_protocol_compliance(relay):
            security_score += 0.2
        
        return security_score
    
    def _validate_ip_address(self, address: str) -> bool:
        """Validate IP address."""
        try:
            ip = ipaddress.ip_address(address)
            # Reject private IPs for public relays
            if ip.is_private:
                return False
            # Reject loopback
            if ip.is_loopback:
                return False
            # Reject multicast
            if ip.is_multicast:
                return False
            return True
        except ValueError:
            return False
    
    def _validate_port(self, port: int) -> bool:
        """Validate port number."""
        return 1024 <= port <= 65535
    
    def _validate_public_key(self, public_key: bytes) -> bool:
        """Validate public key."""
        return len(public_key) == 32  # Ed25519 public key size
    
    async def _check_response_time(self, relay: RelayAnnouncement) -> bool:
        """Check relay response time."""
        try:
            start_time = time.time()
            
            # Send ping request
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)
            
            ping_data = b"PING"
            sock.sendto(ping_data, (relay.address, relay.port))
            
            # Wait for pong response
            response, addr = sock.recvfrom(1024)
            sock.close()
            
            response_time = time.time() - start_time
            
            # Accept response times under 5 seconds
            return response_time < 5.0
            
        except Exception:
            return False
    
    async def _check_protocol_compliance(self, relay: RelayAnnouncement) -> bool:
        """Check protocol compliance."""
        try:
            # Send protocol handshake
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)
            
            handshake_data = b"SECIRC_HANDSHAKE"
            sock.sendto(handshake_data, (relay.address, relay.port))
            
            # Wait for handshake response
            response, addr = sock.recvfrom(1024)
            sock.close()
            
            # Check if response contains expected protocol identifier
            return b"SECIRC_RESPONSE" in response
            
        except Exception:
            return False
    
    async def _add_relay_to_mesh(self, relay: RelayAnnouncement) -> None:
        """Add verified relay to mesh network."""
        try:
            # Create relay node
            relay_node = RelayNode(
                node_id=relay.relay_id,
                public_key=relay.public_key,
                address=relay.address,
                port=relay.port,
                last_seen=relay.last_seen,
                is_verified=True
            )
            
            # Add to mesh network
            self.mesh_network.known_nodes[relay.relay_id] = relay_node
            
            print(f"✅ Added verified relay to mesh: {relay.address}:{relay.port}")
            
        except Exception as e:
            print(f"❌ Failed to add relay to mesh: {e}")
    
    # Helper Methods
    
    def _generate_dht_node_id(self) -> bytes:
        """Generate DHT node ID."""
        return os.urandom(20)
    
    def _generate_random_node_id(self) -> bytes:
        """Generate random node ID."""
        return os.urandom(20)
    
    def _generate_relay_info_hash(self) -> bytes:
        """Generate relay info hash."""
        info = {
            "relay_id": self.mesh_network.node_id.hex(),
            "public_key": self.mesh_network.public_key.hex(),
            "services": ["relay", "dht", "tracker"],
            "version": "1.0.0"
        }
        
        info_str = json.dumps(info, sort_keys=True)
        return hashlib.sha1(info_str.encode()).digest()
    
    def _generate_transaction_id(self) -> str:
        """Generate transaction ID."""
        return os.urandom(2).hex()
    
    def _generate_dht_token(self) -> str:
        """Generate DHT token."""
        return os.urandom(4).hex()
    
    def _calculate_dht_distance(self, node_id1: bytes, node_id2: bytes) -> int:
        """Calculate DHT distance between two node IDs."""
        return int.from_bytes(node_id1, 'big') ^ int.from_bytes(node_id2, 'big')
    
    def _get_closest_dht_nodes(self, target_id: bytes, k: int) -> List[DHTNode]:
        """Get k closest DHT nodes to target ID."""
        nodes = list(self.dht_nodes.values())
        nodes.sort(key=lambda node: self._calculate_dht_distance(target_id, node.node_id))
        return nodes[:k]
    
    def _check_rate_limit(self, address: str) -> bool:
        """Check rate limit for address."""
        current_time = time.time()
        rate_limit_window = 60  # 1 minute
        max_requests = 10  # Maximum 10 requests per minute
        
        # Clean old entries
        while self.rate_limits[address] and current_time - self.rate_limits[address][0] > rate_limit_window:
            self.rate_limits[address].popleft()
        
        # Check if under limit
        if len(self.rate_limits[address]) >= max_requests:
            return False
        
        # Add current request
        self.rate_limits[address].append(current_time)
        return True
    
    async def _verify_discovered_relays(self) -> None:
        """Verify discovered relays."""
        for relay_id, relay in list(self.discovered_relays.items()):
            # Check if relay needs verification
            if relay_id not in self.verification_cache:
                await self._verify_relay(relay)
            else:
                is_verified, timestamp = self.verification_cache[relay_id]
                if time.time() - timestamp > 3600:  # Reverify after 1 hour
                    await self._verify_relay(relay)
    
    async def _cleanup_verification_cache(self) -> None:
        """Clean up old verification cache entries."""
        current_time = time.time()
        cutoff_time = current_time - (24 * 3600)  # 24 hours
        
        # Remove old entries
        old_entries = [
            relay_id for relay_id, (_, timestamp) in self.verification_cache.items()
            if timestamp < cutoff_time
        ]
        
        for relay_id in old_entries:
            del self.verification_cache[relay_id]
    
    async def _query_dht_node_for_relays(self, address: str, port: int, target_id: bytes) -> List[RelayAnnouncement]:
        """Query DHT node for relays."""
        # Simplified implementation
        return []
    
    async def _exchange_peers_with_relay(self, relay: RelayAnnouncement) -> List[RelayAnnouncement]:
        """Exchange peer lists with relay using PEX."""
        # Simplified implementation
        return []
    
    # Public API
    
    def get_discovery_status(self) -> Dict:
        """Get discovery system status."""
        return {
            "active": True,
            "discovered_relays": len(self.discovered_relays),
            "dht_nodes": len(self.dht_nodes),
            "tracker_servers": len(self.tracker_servers),
            "bootstrap_nodes": len(self.bootstrap_nodes),
            "verified_relays": len([r for r in self.verification_cache.values() if r[0]]),
            "spy_servers_detected": len(self.known_spy_servers)
        }
    
    def get_discovered_relays(self) -> Dict[str, Dict]:
        """Get discovered relays."""
        return {
            relay_id.hex(): relay.to_dict()
            for relay_id, relay in self.discovered_relays.items()
        }
    
    def get_discovery_stats(self) -> Dict:
        """Get discovery statistics."""
        return {
            **self.stats,
            "discovered_relays_count": len(self.discovered_relays),
            "dht_nodes_count": len(self.dht_nodes),
            "verification_cache_size": len(self.verification_cache),
            "known_spy_servers_count": len(self.known_spy_servers)
        }
    
    async def stop_discovery_service(self) -> None:
        """Stop the discovery service."""
        if self.discovery_task:
            self.discovery_task.cancel()
        
        if self.dht_task:
            self.dht_task.cancel()
        
        if self.tracker_task:
            self.tracker_task.cancel()
        
        if self.verification_task:
            self.verification_task.cancel()
        
        print("🛑 Torrent-inspired discovery service stopped")
