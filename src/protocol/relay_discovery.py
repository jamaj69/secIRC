"""
Relay server discovery mechanisms for anonymous messaging.
Implements multiple strategies to find and maintain relay servers.
"""

import asyncio
import json
import time
import random
from typing import List, Dict, Set, Optional
from dataclasses import asdict
import aiohttp
import dns.resolver
from .message_types import RelayInfo


class RelayDiscovery:
    """Handles discovery and management of relay servers."""
    
    def __init__(self):
        self.known_relays: Dict[bytes, RelayInfo] = {}
        self.discovery_methods = [
            self._dns_discovery,
            self._web_discovery,
            self._peer_discovery,
            self._bootstrap_discovery
        ]
        self.bootstrap_servers = [
            "relay1.secirc.net",
            "relay2.secirc.net", 
            "relay3.secirc.net"
        ]
    
    async def discover_relays(self, max_relays: int = 10) -> List[RelayInfo]:
        """Discover relay servers using multiple methods."""
        discovered_relays = set()
        
        # Try each discovery method
        for method in self.discovery_methods:
            try:
                relays = await method()
                for relay in relays:
                    if len(discovered_relays) >= max_relays:
                        break
                    discovered_relays.add(relay)
            except Exception as e:
                print(f"Discovery method failed: {e}")
                continue
        
        return list(discovered_relays)
    
    async def _dns_discovery(self) -> List[RelayInfo]:
        """Discover relays using DNS SRV records."""
        relays = []
        
        try:
            # Query for SRV records
            resolver = dns.resolver.Resolver()
            resolver.timeout = 5
            resolver.lifetime = 5
            
            # Try different DNS queries
            dns_queries = [
                "_secirc._udp.secirc.net",
                "_relay._udp.secirc.net",
                "relays.secirc.net"
            ]
            
            for query in dns_queries:
                try:
                    answers = resolver.resolve(query, 'SRV')
                    for answer in answers:
                        # Extract relay info from SRV record
                        hostname = str(answer.target).rstrip('.')
                        port = answer.port
                        
                        # Get public key from TXT record
                        try:
                            txt_answers = resolver.resolve(hostname, 'TXT')
                            public_key = None
                            for txt in txt_answers:
                                txt_data = str(txt).strip('"')
                                if txt_data.startswith('pubkey='):
                                    public_key = txt_data[7:]
                                    break
                            
                            if public_key:
                                relay = RelayInfo(
                                    server_id=self._generate_server_id(hostname),
                                    address=hostname,
                                    port=port,
                                    public_key=bytes.fromhex(public_key),
                                    last_seen=int(time.time())
                                )
                                relays.append(relay)
                        except:
                            continue
                            
                except dns.resolver.NXDOMAIN:
                    continue
                except Exception as e:
                    print(f"DNS query failed for {query}: {e}")
                    continue
                    
        except Exception as e:
            print(f"DNS discovery failed: {e}")
        
        return relays
    
    async def _web_discovery(self) -> List[RelayInfo]:
        """Discover relays using web-based discovery."""
        relays = []
        
        discovery_urls = [
            "https://relays.secirc.net/discovery.json",
            "https://api.secirc.net/relays",
            "https://discovery.secirc.net/relays.json"
        ]
        
        async with aiohttp.ClientSession() as session:
            for url in discovery_urls:
                try:
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            for relay_data in data.get('relays', []):
                                relay = RelayInfo(
                                    server_id=bytes.fromhex(relay_data['id']),
                                    address=relay_data['address'],
                                    port=relay_data['port'],
                                    public_key=bytes.fromhex(relay_data['public_key']),
                                    last_seen=int(time.time()),
                                    reputation=relay_data.get('reputation', 1.0)
                                )
                                relays.append(relay)
                except Exception as e:
                    print(f"Web discovery failed for {url}: {e}")
                    continue
        
        return relays
    
    async def _peer_discovery(self) -> List[RelayInfo]:
        """Discover relays through peer-to-peer gossip."""
        relays = []
        
        # This would implement a gossip protocol where peers
        # share known relay servers with each other
        # For now, return empty list as this requires network implementation
        
        return relays
    
    async def _bootstrap_discovery(self) -> List[RelayInfo]:
        """Use hardcoded bootstrap servers for initial discovery."""
        relays = []
        
        for bootstrap_server in self.bootstrap_servers:
            try:
                # Try to connect to bootstrap server
                relay = await self._query_bootstrap_server(bootstrap_server)
                if relay:
                    relays.append(relay)
            except Exception as e:
                print(f"Bootstrap discovery failed for {bootstrap_server}: {e}")
                continue
        
        return relays
    
    async def _query_bootstrap_server(self, address: str) -> Optional[RelayInfo]:
        """Query a bootstrap server for relay information."""
        try:
            # This would implement actual UDP communication
            # For now, return a mock relay
            return RelayInfo(
                server_id=self._generate_server_id(address),
                address=address,
                port=6667,
                public_key=b"mock_public_key_32_bytes_long",
                last_seen=int(time.time())
            )
        except Exception:
            return None
    
    def add_relay(self, relay: RelayInfo) -> None:
        """Add a relay to the known relays list."""
        self.known_relays[relay.server_id] = relay
    
    def remove_relay(self, server_id: bytes) -> None:
        """Remove a relay from the known relays list."""
        if server_id in self.known_relays:
            del self.known_relays[server_id]
    
    def get_best_relays(self, count: int = 3) -> List[RelayInfo]:
        """Get the best relay servers based on reputation and activity."""
        # Filter active relays
        active_relays = [
            relay for relay in self.known_relays.values()
            if relay.is_active and (time.time() - relay.last_seen) < 3600
        ]
        
        # Sort by reputation (descending)
        active_relays.sort(key=lambda x: x.reputation, reverse=True)
        
        return active_relays[:count]
    
    def update_relay_reputation(self, server_id: bytes, success: bool) -> None:
        """Update relay reputation based on success/failure."""
        if server_id in self.known_relays:
            relay = self.known_relays[server_id]
            if success:
                relay.reputation = min(1.0, relay.reputation + 0.1)
            else:
                relay.reputation = max(0.0, relay.reputation - 0.2)
            
            relay.last_seen = int(time.time())
    
    def get_relay_chain(self, target_relays: int = 3) -> List[RelayInfo]:
        """Get a random chain of relays for message routing."""
        available_relays = list(self.known_relays.values())
        
        if len(available_relays) < target_relays:
            return available_relays
        
        # Select random relays for the chain
        return random.sample(available_relays, target_relays)
    
    def _generate_server_id(self, address: str) -> bytes:
        """Generate a unique server ID from address."""
        import hashlib
        return hashlib.sha256(address.encode()).digest()[:16]
    
    def save_relays(self, filename: str) -> None:
        """Save known relays to file."""
        relays_data = {
            server_id.hex(): asdict(relay) for server_id, relay in self.known_relays.items()
        }
        
        with open(filename, 'w') as f:
            json.dump(relays_data, f, indent=2)
    
    def load_relays(self, filename: str) -> None:
        """Load known relays from file."""
        try:
            with open(filename, 'r') as f:
                relays_data = json.load(f)
            
            for server_id_hex, relay_data in relays_data.items():
                server_id = bytes.fromhex(server_id_hex)
                relay = RelayInfo.from_dict(relay_data)
                self.known_relays[server_id] = relay
        except FileNotFoundError:
            pass  # File doesn't exist yet
        except Exception as e:
            print(f"Failed to load relays: {e}")
