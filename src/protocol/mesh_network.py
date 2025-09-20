"""
Mesh network implementation for relay servers.
Forms a first ring of trusted relays that authenticate each other through challenges.
"""

import asyncio
import hashlib
import json
import os
import time
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from .encryption import EndToEndEncryption
from .message_types import MessageType


class ChallengeType(Enum):
    """Types of cryptographic challenges."""
    
    # Authentication challenges
    PROOF_OF_WORK = "proof_of_work"
    SIGNATURE_CHALLENGE = "signature_challenge"
    KEY_EXCHANGE = "key_exchange"
    
    # Ring membership challenges
    RING_JOIN_REQUEST = "ring_join_request"
    RING_VERIFICATION = "ring_verification"
    RING_CONSENSUS = "ring_consensus"
    
    # Network challenges
    NETWORK_PROOF = "network_proof"
    RELAY_VERIFICATION = "relay_verification"


@dataclass
class Challenge:
    """Cryptographic challenge for relay authentication."""
    
    challenge_id: bytes
    challenge_type: ChallengeType
    challenge_data: bytes
    timestamp: int
    nonce: bytes
    difficulty: int = 1
    
    def to_bytes(self) -> bytes:
        """Serialize challenge to bytes."""
        return (self.challenge_id + 
                self.challenge_type.value.encode('utf-8') +
                self.challenge_data +
                self.timestamp.to_bytes(8, 'big') +
                self.nonce +
                self.difficulty.to_bytes(4, 'big'))
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "Challenge":
        """Deserialize challenge from bytes."""
        offset = 0
        
        challenge_id = data[offset:offset+16]
        offset += 16
        
        type_length = data[offset:offset+1][0]
        offset += 1
        challenge_type = ChallengeType(data[offset:offset+type_length].decode('utf-8'))
        offset += type_length
        
        data_length = int.from_bytes(data[offset:offset+4], 'big')
        offset += 4
        challenge_data = data[offset:offset+data_length]
        offset += data_length
        
        timestamp = int.from_bytes(data[offset:offset+8], 'big')
        offset += 8
        
        nonce = data[offset:offset+16]
        offset += 16
        
        difficulty = int.from_bytes(data[offset:offset+4], 'big')
        
        return cls(
            challenge_id=challenge_id,
            challenge_type=challenge_type,
            challenge_data=challenge_data,
            timestamp=timestamp,
            nonce=nonce,
            difficulty=difficulty
        )


@dataclass
class ChallengeResponse:
    """Response to a cryptographic challenge."""
    
    challenge_id: bytes
    response_data: bytes
    proof: bytes
    timestamp: int
    signature: bytes
    
    def to_bytes(self) -> bytes:
        """Serialize response to bytes."""
        return (self.challenge_id +
                len(self.response_data).to_bytes(4, 'big') +
                self.response_data +
                len(self.proof).to_bytes(4, 'big') +
                self.proof +
                self.timestamp.to_bytes(8, 'big') +
                self.signature)
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "ChallengeResponse":
        """Deserialize response from bytes."""
        offset = 0
        
        challenge_id = data[offset:offset+16]
        offset += 16
        
        response_length = int.from_bytes(data[offset:offset+4], 'big')
        offset += 4
        response_data = data[offset:offset+response_length]
        offset += response_length
        
        proof_length = int.from_bytes(data[offset:offset+4], 'big')
        offset += 4
        proof = data[offset:offset+proof_length]
        offset += proof_length
        
        timestamp = int.from_bytes(data[offset:offset+8], 'big')
        offset += 8
        
        signature = data[offset:]
        
        return cls(
            challenge_id=challenge_id,
            response_data=response_data,
            proof=proof,
            timestamp=timestamp,
            signature=signature
        )


@dataclass
class RelayNode:
    """A relay node in the mesh network."""
    
    node_id: bytes
    public_key: bytes
    address: str
    port: int
    is_first_ring: bool
    reputation: float
    last_seen: int
    challenges_passed: int
    challenges_failed: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "node_id": self.node_id.hex(),
            "public_key": self.public_key.hex(),
            "address": self.address,
            "port": self.port,
            "is_first_ring": self.is_first_ring,
            "reputation": self.reputation,
            "last_seen": self.last_seen,
            "challenges_passed": self.challenges_passed,
            "challenges_failed": self.challenges_failed
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "RelayNode":
        """Create from dictionary."""
        return cls(
            node_id=bytes.fromhex(data["node_id"]),
            public_key=bytes.fromhex(data["public_key"]),
            address=data["address"],
            port=data["port"],
            is_first_ring=data["is_first_ring"],
            reputation=data["reputation"],
            last_seen=data["last_seen"],
            challenges_passed=data["challenges_passed"],
            challenges_failed=data["challenges_failed"]
        )


class MeshNetwork:
    """Mesh network manager for relay servers."""
    
    def __init__(self, node_id: bytes, private_key: bytes, public_key: bytes):
        self.node_id = node_id
        self.private_key = private_key
        self.public_key = public_key
        self.encryption = EndToEndEncryption()
        
        # Network topology
        self.first_ring: Set[bytes] = set()  # Set of first ring node IDs
        self.known_nodes: Dict[bytes, RelayNode] = {}  # All known nodes
        self.connections: Dict[bytes, asyncio.StreamWriter] = {}  # Active connections
        
        # Challenge system
        self.active_challenges: Dict[bytes, Challenge] = {}
        self.challenge_responses: Dict[bytes, ChallengeResponse] = {}
        
        # Network configuration
        self.max_first_ring_size = 12  # Maximum nodes in first ring
        self.challenge_timeout = 30  # Challenge timeout in seconds
        self.heartbeat_interval = 60  # Heartbeat interval in seconds
        self.consensus_threshold = 0.75  # Consensus threshold for decisions
        
        # Network state
        self.is_first_ring_member = False
        self.network_consensus = {}  # Consensus data
        self.last_consensus_time = 0
        
        # Statistics
        self.stats = {
            "challenges_sent": 0,
            "challenges_received": 0,
            "challenges_passed": 0,
            "challenges_failed": 0,
            "first_ring_connections": 0,
            "total_connections": 0
        }
    
    async def start_mesh_network(self, bootstrap_nodes: List[Tuple[str, int]]) -> None:
        """Start the mesh network."""
        print(f"🌐 Starting mesh network for node {self.node_id.hex()}")
        
        # Try to join existing first ring
        await self._attempt_first_ring_join(bootstrap_nodes)
        
        # Start network services
        asyncio.create_task(self._start_challenge_server())
        asyncio.create_task(self._start_heartbeat_service())
        asyncio.create_task(self._start_consensus_service())
        asyncio.create_task(self._start_network_monitor())
        
        print(f"✅ Mesh network started")
        print(f"   First ring member: {self.is_first_ring_member}")
        print(f"   Known nodes: {len(self.known_nodes)}")
        print(f"   First ring size: {len(self.first_ring)}")
    
    async def _attempt_first_ring_join(self, bootstrap_nodes: List[Tuple[str, int]]) -> None:
        """Attempt to join the first ring through bootstrap nodes."""
        for address, port in bootstrap_nodes:
            try:
                # Connect to bootstrap node
                reader, writer = await asyncio.open_connection(address, port)
                
                # Send first ring join request
                join_request = await self._create_ring_join_request()
                writer.write(join_request)
                await writer.drain()
                
                # Read response
                response_data = await reader.read(4096)
                if response_data:
                    await self._process_ring_join_response(response_data, address, port)
                
                writer.close()
                await writer.wait_closed()
                
                # If we successfully joined, break
                if self.is_first_ring_member:
                    break
                    
            except Exception as e:
                print(f"Failed to connect to bootstrap node {address}:{port}: {e}")
                continue
        
        # If no bootstrap nodes worked, initialize as first ring member
        if not self.is_first_ring_member and len(self.first_ring) == 0:
            await self._initialize_first_ring()
    
    async def _create_ring_join_request(self) -> bytes:
        """Create a first ring join request."""
        # Create challenge for authentication
        challenge = await self._create_authentication_challenge()
        
        request_data = {
            "node_id": self.node_id.hex(),
            "public_key": self.public_key.hex(),
            "challenge": challenge.to_bytes().hex(),
            "timestamp": int(time.time()),
            "request_type": "first_ring_join"
        }
        
        # Sign the request
        request_json = json.dumps(request_data).encode('utf-8')
        signature = self.encryption._sign_message(request_json, self.private_key)
        
        # Combine request and signature
        return request_json + signature
    
    async def _process_ring_join_response(self, response_data: bytes, address: str, port: int) -> None:
        """Process response to ring join request."""
        try:
            # Split response and signature
            signature = response_data[-256:]  # Last 256 bytes are signature
            response_json = response_data[:-256]
            
            # Verify signature (would need the bootstrap node's public key)
            # For now, assume it's valid
            
            response = json.loads(response_json.decode('utf-8'))
            
            if response.get("status") == "accepted":
                # We're accepted into the first ring
                self.is_first_ring_member = True
                self.first_ring.add(self.node_id)
                
                # Add bootstrap node to our known nodes
                bootstrap_node_id = bytes.fromhex(response["bootstrap_node_id"])
                bootstrap_public_key = bytes.fromhex(response["bootstrap_public_key"])
                
                bootstrap_node = RelayNode(
                    node_id=bootstrap_node_id,
                    public_key=bootstrap_public_key,
                    address=address,
                    port=port,
                    is_first_ring=True,
                    reputation=1.0,
                    last_seen=int(time.time()),
                    challenges_passed=0,
                    challenges_failed=0
                )
                
                self.known_nodes[bootstrap_node_id] = bootstrap_node
                self.first_ring.add(bootstrap_node_id)
                
                # Get list of other first ring members
                for member_data in response.get("first_ring_members", []):
                    member_id = bytes.fromhex(member_data["node_id"])
                    member_public_key = bytes.fromhex(member_data["public_key"])
                    member_address = member_data["address"]
                    member_port = member_data["port"]
                    
                    member_node = RelayNode(
                        node_id=member_id,
                        public_key=member_public_key,
                        address=member_address,
                        port=member_port,
                        is_first_ring=True,
                        reputation=1.0,
                        last_seen=int(time.time()),
                        challenges_passed=0,
                        challenges_failed=0
                    )
                    
                    self.known_nodes[member_id] = member_node
                    self.first_ring.add(member_id)
                
                print(f"✅ Successfully joined first ring!")
                print(f"   First ring members: {len(self.first_ring)}")
                
            elif response.get("status") == "challenge_required":
                # We need to solve a challenge
                challenge_data = bytes.fromhex(response["challenge"])
                challenge = Challenge.from_bytes(challenge_data)
                
                # Solve the challenge
                response = await self._solve_challenge(challenge)
                
                # Send challenge response
                # This would be implemented with actual network communication
                
        except Exception as e:
            print(f"Error processing ring join response: {e}")
    
    async def _initialize_first_ring(self) -> None:
        """Initialize as the first member of a new first ring."""
        print("🆕 Initializing new first ring")
        
        self.is_first_ring_member = True
        self.first_ring.add(self.node_id)
        
        # Create our own node entry
        our_node = RelayNode(
            node_id=self.node_id,
            public_key=self.public_key,
            address="0.0.0.0",  # Will be updated with actual address
            port=6667,  # Will be updated with actual port
            is_first_ring=True,
            reputation=1.0,
            last_seen=int(time.time()),
            challenges_passed=0,
            challenges_failed=0
        )
        
        self.known_nodes[self.node_id] = our_node
        
        print("✅ Initialized as first ring member")
    
    async def _create_authentication_challenge(self) -> Challenge:
        """Create an authentication challenge."""
        challenge_id = os.urandom(16)
        challenge_data = os.urandom(32)
        nonce = os.urandom(16)
        timestamp = int(time.time())
        
        challenge = Challenge(
            challenge_id=challenge_id,
            challenge_type=ChallengeType.SIGNATURE_CHALLENGE,
            challenge_data=challenge_data,
            timestamp=timestamp,
            nonce=nonce,
            difficulty=1
        )
        
        self.active_challenges[challenge_id] = challenge
        return challenge
    
    async def _solve_challenge(self, challenge: Challenge) -> ChallengeResponse:
        """Solve a cryptographic challenge."""
        if challenge.challenge_type == ChallengeType.SIGNATURE_CHALLENGE:
            # Sign the challenge data
            challenge_bytes = challenge.to_bytes()
            signature = self.encryption._sign_message(challenge_bytes, self.private_key)
            
            response = ChallengeResponse(
                challenge_id=challenge.challenge_id,
                response_data=challenge_bytes,
                proof=signature,
                timestamp=int(time.time()),
                signature=signature
            )
            
            return response
        
        elif challenge.challenge_type == ChallengeType.PROOF_OF_WORK:
            # Solve proof of work challenge
            return await self._solve_proof_of_work(challenge)
        
        else:
            raise ValueError(f"Unknown challenge type: {challenge.challenge_type}")
    
    async def _solve_proof_of_work(self, challenge: Challenge) -> ChallengeResponse:
        """Solve a proof of work challenge."""
        target = (2 ** (256 - challenge.difficulty)) - 1
        nonce = 0
        
        while True:
            # Create proof data
            proof_data = challenge.challenge_data + nonce.to_bytes(8, 'big')
            proof_hash = hashlib.sha256(proof_data).digest()
            proof_int = int.from_bytes(proof_hash, 'big')
            
            if proof_int <= target:
                # Found valid proof
                response = ChallengeResponse(
                    challenge_id=challenge.challenge_id,
                    response_data=challenge.challenge_data,
                    proof=nonce.to_bytes(8, 'big'),
                    timestamp=int(time.time()),
                    signature=b"proof_of_work_signature"
                )
                
                return response
            
            nonce += 1
            
            # Prevent infinite loop
            if nonce > 1000000:
                raise ValueError("Proof of work challenge too difficult")
    
    async def _start_challenge_server(self) -> None:
        """Start server for handling challenges."""
        # This would implement a TCP server for challenge handling
        # For now, it's a placeholder
        while True:
            await asyncio.sleep(1)
    
    async def _start_heartbeat_service(self) -> None:
        """Start heartbeat service for first ring members."""
        while True:
            await asyncio.sleep(self.heartbeat_interval)
            
            if self.is_first_ring_member:
                await self._send_heartbeats()
    
    async def _send_heartbeats(self) -> None:
        """Send heartbeats to other first ring members."""
        for node_id in self.first_ring:
            if node_id == self.node_id:
                continue
            
            node = self.known_nodes.get(node_id)
            if not node:
                continue
            
            try:
                # Send heartbeat
                heartbeat_data = {
                    "node_id": self.node_id.hex(),
                    "timestamp": int(time.time()),
                    "type": "heartbeat"
                }
                
                # This would implement actual network communication
                # For now, just update last seen
                node.last_seen = int(time.time())
                
            except Exception as e:
                print(f"Failed to send heartbeat to {node_id.hex()}: {e}")
    
    async def _start_consensus_service(self) -> None:
        """Start consensus service for first ring decisions."""
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            
            if self.is_first_ring_member:
                await self._run_consensus_round()
    
    async def _run_consensus_round(self) -> None:
        """Run a consensus round for network decisions."""
        # Collect consensus data from all first ring members
        consensus_data = {
            "timestamp": int(time.time()),
            "node_id": self.node_id.hex(),
            "known_nodes": len(self.known_nodes),
            "first_ring_size": len(self.first_ring),
            "network_health": self._calculate_network_health()
        }
        
        # This would implement actual consensus protocol
        # For now, just store our consensus data
        self.network_consensus[self.node_id] = consensus_data
        self.last_consensus_time = int(time.time())
    
    def _calculate_network_health(self) -> float:
        """Calculate network health score."""
        if not self.known_nodes:
            return 0.0
        
        total_reputation = sum(node.reputation for node in self.known_nodes.values())
        avg_reputation = total_reputation / len(self.known_nodes)
        
        # Factor in connectivity
        connectivity_score = len(self.connections) / max(len(self.known_nodes), 1)
        
        return (avg_reputation + connectivity_score) / 2
    
    async def _start_network_monitor(self) -> None:
        """Start network monitoring service."""
        while True:
            await asyncio.sleep(60)  # Every minute
            
            # Clean up stale nodes
            current_time = int(time.time())
            stale_nodes = []
            
            for node_id, node in self.known_nodes.items():
                if current_time - node.last_seen > 3600:  # 1 hour
                    stale_nodes.append(node_id)
            
            for node_id in stale_nodes:
                self._remove_node(node_id)
            
            # Update statistics
            self.stats["first_ring_connections"] = len(self.first_ring)
            self.stats["total_connections"] = len(self.known_nodes)
    
    def _remove_node(self, node_id: bytes) -> None:
        """Remove a node from the network."""
        if node_id in self.known_nodes:
            del self.known_nodes[node_id]
        
        if node_id in self.first_ring:
            self.first_ring.remove(node_id)
        
        if node_id in self.connections:
            self.connections[node_id].close()
            del self.connections[node_id]
    
    def add_node(self, node: RelayNode) -> None:
        """Add a new node to the network."""
        self.known_nodes[node.node_id] = node
        
        if node.is_first_ring:
            self.first_ring.add(node.node_id)
    
    def get_first_ring_members(self) -> List[RelayNode]:
        """Get all first ring members."""
        return [node for node in self.known_nodes.values() if node.is_first_ring]
    
    def get_network_stats(self) -> Dict:
        """Get network statistics."""
        return {
            **self.stats,
            "is_first_ring_member": self.is_first_ring_member,
            "first_ring_size": len(self.first_ring),
            "total_nodes": len(self.known_nodes),
            "network_health": self._calculate_network_health(),
            "last_consensus": self.last_consensus_time
        }
    
    def export_network_state(self) -> Dict:
        """Export network state for persistence."""
        return {
            "node_id": self.node_id.hex(),
            "is_first_ring_member": self.is_first_ring_member,
            "first_ring": [node_id.hex() for node_id in self.first_ring],
            "known_nodes": {
                node_id.hex(): node.to_dict()
                for node_id, node in self.known_nodes.items()
            },
            "stats": self.stats
        }
    
    def import_network_state(self, state_data: Dict) -> None:
        """Import network state from persistence."""
        self.is_first_ring_member = state_data.get("is_first_ring_member", False)
        
        # Import first ring
        self.first_ring = {
            bytes.fromhex(node_id_hex)
            for node_id_hex in state_data.get("first_ring", [])
        }
        
        # Import known nodes
        for node_id_hex, node_data in state_data.get("known_nodes", {}).items():
            node = RelayNode.from_dict(node_data)
            self.known_nodes[node.node_id] = node
        
        # Import stats
        self.stats.update(state_data.get("stats", {}))
