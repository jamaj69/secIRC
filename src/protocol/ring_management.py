"""
First ring management system for relay servers.
Handles ring formation, expansion, and member authentication.
"""

import asyncio
import hashlib
import json
import time
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .mesh_network import MeshNetwork, Challenge, ChallengeResponse, RelayNode
from .encryption import EndToEndEncryption


class RingStatus(Enum):
    """Status of the first ring."""
    
    FORMING = "forming"  # Ring is being formed
    ACTIVE = "active"    # Ring is active and operational
    EXPANDING = "expanding"  # Ring is accepting new members
    MAINTENANCE = "maintenance"  # Ring is in maintenance mode
    DEGRADED = "degraded"  # Ring has lost some members


@dataclass
class RingMember:
    """A member of the first ring."""
    
    node_id: bytes
    public_key: bytes
    address: str
    port: int
    join_timestamp: int
    last_heartbeat: int
    reputation: float
    is_active: bool
    consensus_votes: int
    challenges_solved: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "node_id": self.node_id.hex(),
            "public_key": self.public_key.hex(),
            "address": self.address,
            "port": self.port,
            "join_timestamp": self.join_timestamp,
            "last_heartbeat": self.last_heartbeat,
            "reputation": self.reputation,
            "is_active": self.is_active,
            "consensus_votes": self.consensus_votes,
            "challenges_solved": self.challenges_solved
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "RingMember":
        """Create from dictionary."""
        return cls(
            node_id=bytes.fromhex(data["node_id"]),
            public_key=bytes.fromhex(data["public_key"]),
            address=data["address"],
            port=data["port"],
            join_timestamp=data["join_timestamp"],
            last_heartbeat=data["last_heartbeat"],
            reputation=data["reputation"],
            is_active=data["is_active"],
            consensus_votes=data["consensus_votes"],
            challenges_solved=data["challenges_solved"]
        )


@dataclass
class RingConsensus:
    """Consensus data for ring decisions."""
    
    consensus_id: bytes
    proposal_type: str
    proposal_data: Dict
    proposer_id: bytes
    timestamp: int
    votes: Dict[bytes, bool]  # node_id -> vote
    threshold_reached: bool
    result: Optional[bool] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "consensus_id": self.consensus_id.hex(),
            "proposal_type": self.proposal_type,
            "proposal_data": self.proposal_data,
            "proposer_id": self.proposer_id.hex(),
            "timestamp": self.timestamp,
            "votes": {node_id.hex(): vote for node_id, vote in self.votes.items()},
            "threshold_reached": self.threshold_reached,
            "result": self.result
        }


class FirstRingManager:
    """Manages the first ring of trusted relay servers."""
    
    def __init__(self, mesh_network: MeshNetwork):
        self.mesh_network = mesh_network
        self.encryption = EndToEndEncryption()
        
        # Ring state
        self.ring_status = RingStatus.FORMING
        self.ring_members: Dict[bytes, RingMember] = {}
        self.ring_leader: Optional[bytes] = None
        self.ring_formation_time = 0
        
        # Ring configuration
        self.max_ring_size = 12
        self.min_ring_size = 3
        self.consensus_threshold = 0.75
        self.heartbeat_timeout = 300  # 5 minutes
        self.challenge_interval = 3600  # 1 hour
        
        # Consensus system
        self.active_consensus: Dict[bytes, RingConsensus] = {}
        self.consensus_history: List[RingConsensus] = []
        
        # Ring expansion
        self.pending_join_requests: Dict[bytes, Dict] = {}
        self.expansion_candidates: Set[bytes] = set()
        
        # Statistics
        self.stats = {
            "ring_formed_at": 0,
            "members_added": 0,
            "members_removed": 0,
            "consensus_rounds": 0,
            "challenges_issued": 0,
            "challenges_passed": 0,
            "challenges_failed": 0
        }
    
    async def initialize_ring(self) -> None:
        """Initialize the first ring."""
        print("🔗 Initializing first ring...")
        
        # Add ourselves as the first member
        our_member = RingMember(
            node_id=self.mesh_network.node_id,
            public_key=self.mesh_network.public_key,
            address="0.0.0.0",  # Will be updated
            port=6667,  # Will be updated
            join_timestamp=int(time.time()),
            last_heartbeat=int(time.time()),
            reputation=1.0,
            is_active=True,
            consensus_votes=0,
            challenges_solved=0
        )
        
        self.ring_members[self.mesh_network.node_id] = our_member
        self.ring_leader = self.mesh_network.node_id
        self.ring_status = RingStatus.ACTIVE
        self.ring_formation_time = int(time.time())
        self.stats["ring_formed_at"] = int(time.time())
        
        print(f"✅ First ring initialized with {len(self.ring_members)} members")
        print(f"   Ring leader: {self.ring_leader.hex()}")
        print(f"   Status: {self.ring_status.value}")
    
    async def process_join_request(self, request_data: Dict, 
                                 requester_address: str, requester_port: int) -> Dict:
        """Process a request to join the first ring."""
        try:
            requester_id = bytes.fromhex(request_data["node_id"])
            requester_public_key = bytes.fromhex(request_data["public_key"])
            
            print(f"📥 Processing join request from {requester_id.hex()}")
            
            # Check if ring is accepting new members
            if self.ring_status not in [RingStatus.ACTIVE, RingStatus.EXPANDING]:
                return {
                    "status": "rejected",
                    "reason": "ring_not_accepting_members",
                    "ring_status": self.ring_status.value
                }
            
            # Check ring capacity
            if len(self.ring_members) >= self.max_ring_size:
                return {
                    "status": "rejected",
                    "reason": "ring_at_capacity",
                    "current_size": len(self.ring_members),
                    "max_size": self.max_ring_size
                }
            
            # Verify requester's identity
            if not self._verify_node_identity(requester_id, requester_public_key):
                return {
                    "status": "rejected",
                    "reason": "invalid_identity"
                }
            
            # Create authentication challenge
            challenge = await self._create_join_challenge(requester_id)
            
            # Store pending request
            self.pending_join_requests[requester_id] = {
                "request_data": request_data,
                "address": requester_address,
                "port": requester_port,
                "challenge": challenge,
                "timestamp": int(time.time())
            }
            
            return {
                "status": "challenge_required",
                "challenge": challenge.to_bytes().hex(),
                "challenge_id": challenge.challenge_id.hex(),
                "timeout": self.challenge_interval
            }
            
        except Exception as e:
            print(f"Error processing join request: {e}")
            return {
                "status": "error",
                "reason": str(e)
            }
    
    async def process_challenge_response(self, response_data: Dict) -> Dict:
        """Process a challenge response from a potential ring member."""
        try:
            challenge_id = bytes.fromhex(response_data["challenge_id"])
            response_bytes = bytes.fromhex(response_data["response"])
            
            # Find the pending request
            requester_id = None
            for node_id, request in self.pending_join_requests.items():
                if request["challenge"].challenge_id == challenge_id:
                    requester_id = node_id
                    break
            
            if not requester_id:
                return {
                    "status": "rejected",
                    "reason": "challenge_not_found"
                }
            
            # Verify challenge response
            challenge_response = ChallengeResponse.from_bytes(response_bytes)
            is_valid = await self._verify_challenge_response(
                self.pending_join_requests[requester_id]["challenge"],
                challenge_response
            )
            
            if not is_valid:
                self.stats["challenges_failed"] += 1
                del self.pending_join_requests[requester_id]
                return {
                    "status": "rejected",
                    "reason": "challenge_failed"
                }
            
            # Challenge passed - initiate consensus for membership
            self.stats["challenges_passed"] += 1
            
            # Create consensus proposal
            consensus_id = await self._create_membership_consensus(requester_id)
            
            return {
                "status": "consensus_required",
                "consensus_id": consensus_id.hex(),
                "estimated_time": 300  # 5 minutes
            }
            
        except Exception as e:
            print(f"Error processing challenge response: {e}")
            return {
                "status": "error",
                "reason": str(e)
            }
    
    async def _create_join_challenge(self, requester_id: bytes) -> Challenge:
        """Create a challenge for ring join request."""
        import os
        
        challenge_id = os.urandom(16)
        challenge_data = os.urandom(32)
        nonce = os.urandom(16)
        timestamp = int(time.time())
        
        # Create a signature challenge
        challenge = Challenge(
            challenge_id=challenge_id,
            challenge_type="signature_challenge",
            challenge_data=challenge_data,
            timestamp=timestamp,
            nonce=nonce,
            difficulty=1
        )
        
        self.stats["challenges_issued"] += 1
        return challenge
    
    async def _verify_challenge_response(self, challenge: Challenge, 
                                       response: ChallengeResponse) -> bool:
        """Verify a challenge response."""
        try:
            # Verify challenge ID matches
            if challenge.challenge_id != response.challenge_id:
                return False
            
            # Verify timestamp is recent
            current_time = int(time.time())
            if current_time - response.timestamp > self.challenge_interval:
                return False
            
            # Verify signature (this would use the requester's public key)
            # For now, assume it's valid if the response data matches
            return challenge.challenge_data == response.response_data
            
        except Exception:
            return False
    
    async def _create_membership_consensus(self, candidate_id: bytes) -> bytes:
        """Create a consensus proposal for ring membership."""
        import os
        
        consensus_id = os.urandom(16)
        
        # Get candidate data
        candidate_request = self.pending_join_requests[candidate_id]
        
        consensus = RingConsensus(
            consensus_id=consensus_id,
            proposal_type="add_member",
            proposal_data={
                "candidate_id": candidate_id.hex(),
                "candidate_public_key": candidate_request["request_data"]["public_key"],
                "candidate_address": candidate_request["address"],
                "candidate_port": candidate_request["port"]
            },
            proposer_id=self.mesh_network.node_id,
            timestamp=int(time.time()),
            votes={},
            threshold_reached=False
        )
        
        # Add our vote
        consensus.votes[self.mesh_network.node_id] = True
        
        self.active_consensus[consensus_id] = consensus
        
        # Broadcast consensus to other ring members
        await self._broadcast_consensus(consensus)
        
        return consensus_id
    
    async def _broadcast_consensus(self, consensus: RingConsensus) -> None:
        """Broadcast consensus proposal to ring members."""
        for member_id in self.ring_members:
            if member_id == self.mesh_network.node_id:
                continue
            
            try:
                # Send consensus proposal
                consensus_data = {
                    "type": "consensus_proposal",
                    "consensus": consensus.to_dict()
                }
                
                # This would implement actual network communication
                # For now, just simulate
                print(f"📡 Broadcasting consensus to {member_id.hex()}")
                
            except Exception as e:
                print(f"Failed to broadcast to {member_id.hex()}: {e}")
    
    async def process_consensus_vote(self, vote_data: Dict) -> Dict:
        """Process a consensus vote from a ring member."""
        try:
            consensus_id = bytes.fromhex(vote_data["consensus_id"])
            voter_id = bytes.fromhex(vote_data["voter_id"])
            vote = vote_data["vote"]
            signature = bytes.fromhex(vote_data["signature"])
            
            # Verify voter is a ring member
            if voter_id not in self.ring_members:
                return {
                    "status": "rejected",
                    "reason": "not_ring_member"
                }
            
            # Verify consensus exists
            if consensus_id not in self.active_consensus:
                return {
                    "status": "rejected",
                    "reason": "consensus_not_found"
                }
            
            consensus = self.active_consensus[consensus_id]
            
            # Verify signature (would use voter's public key)
            # For now, assume it's valid
            
            # Record vote
            consensus.votes[voter_id] = vote
            
            # Check if threshold is reached
            total_members = len(self.ring_members)
            votes_received = len(consensus.votes)
            yes_votes = sum(1 for v in consensus.votes.values() if v)
            
            if votes_received >= total_members * self.consensus_threshold:
                consensus.threshold_reached = True
                consensus.result = yes_votes > (votes_received / 2)
                
                # Execute consensus result
                await self._execute_consensus_result(consensus)
                
                # Move to history
                self.consensus_history.append(consensus)
                del self.active_consensus[consensus_id]
                
                return {
                    "status": "consensus_completed",
                    "result": consensus.result,
                    "yes_votes": yes_votes,
                    "total_votes": votes_received
                }
            
            return {
                "status": "vote_recorded",
                "votes_received": votes_received,
                "total_members": total_members,
                "yes_votes": yes_votes
            }
            
        except Exception as e:
            print(f"Error processing consensus vote: {e}")
            return {
                "status": "error",
                "reason": str(e)
            }
    
    async def _execute_consensus_result(self, consensus: RingConsensus) -> None:
        """Execute the result of a consensus."""
        if consensus.proposal_type == "add_member" and consensus.result:
            # Add new member to ring
            candidate_id = bytes.fromhex(consensus.proposal_data["candidate_id"])
            candidate_public_key = bytes.fromhex(consensus.proposal_data["candidate_public_key"])
            candidate_address = consensus.proposal_data["candidate_address"]
            candidate_port = consensus.proposal_data["candidate_port"]
            
            new_member = RingMember(
                node_id=candidate_id,
                public_key=candidate_public_key,
                address=candidate_address,
                port=candidate_port,
                join_timestamp=int(time.time()),
                last_heartbeat=int(time.time()),
                reputation=1.0,
                is_active=True,
                consensus_votes=0,
                challenges_solved=1  # They solved the join challenge
            )
            
            self.ring_members[candidate_id] = new_member
            self.stats["members_added"] += 1
            
            # Remove from pending requests
            if candidate_id in self.pending_join_requests:
                del self.pending_join_requests[candidate_id]
            
            print(f"✅ Added new ring member: {candidate_id.hex()}")
            print(f"   Ring size: {len(self.ring_members)}")
            
            # Broadcast ring update
            await self._broadcast_ring_update()
    
    async def _broadcast_ring_update(self) -> None:
        """Broadcast ring membership update to all members."""
        ring_data = {
            "type": "ring_update",
            "ring_members": [member.to_dict() for member in self.ring_members.values()],
            "ring_status": self.ring_status.value,
            "timestamp": int(time.time())
        }
        
        for member_id in self.ring_members:
            if member_id == self.mesh_network.node_id:
                continue
            
            try:
                # Send ring update
                print(f"📡 Broadcasting ring update to {member_id.hex()}")
                # This would implement actual network communication
                
            except Exception as e:
                print(f"Failed to broadcast ring update to {member_id.hex()}: {e}")
    
    async def start_ring_services(self) -> None:
        """Start ring management services."""
        asyncio.create_task(self._heartbeat_monitor())
        asyncio.create_task(self._consensus_monitor())
        asyncio.create_task(self._ring_health_monitor())
    
    async def _heartbeat_monitor(self) -> None:
        """Monitor heartbeats from ring members."""
        while True:
            await asyncio.sleep(60)  # Check every minute
            
            current_time = int(time.time())
            inactive_members = []
            
            for member_id, member in self.ring_members.items():
                if current_time - member.last_heartbeat > self.heartbeat_timeout:
                    inactive_members.append(member_id)
            
            # Remove inactive members
            for member_id in inactive_members:
                await self._remove_ring_member(member_id, "heartbeat_timeout")
    
    async def _consensus_monitor(self) -> None:
        """Monitor active consensus proposals."""
        while True:
            await asyncio.sleep(30)  # Check every 30 seconds
            
            current_time = int(time.time())
            expired_consensus = []
            
            for consensus_id, consensus in self.active_consensus.items():
                if current_time - consensus.timestamp > 600:  # 10 minutes timeout
                    expired_consensus.append(consensus_id)
            
            # Remove expired consensus
            for consensus_id in expired_consensus:
                consensus = self.active_consensus[consensus_id]
                consensus.result = False  # Reject by timeout
                self.consensus_history.append(consensus)
                del self.active_consensus[consensus_id]
                
                print(f"⏰ Consensus {consensus_id.hex()} expired")
    
    async def _ring_health_monitor(self) -> None:
        """Monitor overall ring health."""
        while True:
            await asyncio.sleep(300)  # Check every 5 minutes
            
            active_members = sum(1 for member in self.ring_members.values() if member.is_active)
            total_members = len(self.ring_members)
            
            # Update ring status based on health
            if active_members < self.min_ring_size:
                self.ring_status = RingStatus.DEGRADED
                print(f"⚠️ Ring degraded: {active_members}/{total_members} active members")
            elif active_members == total_members:
                self.ring_status = RingStatus.ACTIVE
            else:
                self.ring_status = RingStatus.MAINTENANCE
    
    async def _remove_ring_member(self, member_id: bytes, reason: str) -> None:
        """Remove a member from the ring."""
        if member_id in self.ring_members:
            del self.ring_members[member_id]
            self.stats["members_removed"] += 1
            
            print(f"❌ Removed ring member {member_id.hex()}: {reason}")
            print(f"   Ring size: {len(self.ring_members)}")
            
            # Broadcast ring update
            await self._broadcast_ring_update()
    
    def _verify_node_identity(self, node_id: bytes, public_key: bytes) -> bool:
        """Verify a node's identity."""
        # Verify that the node_id is a hash of the public_key
        expected_hash = hashlib.sha256(public_key).digest()[:16]
        return node_id == expected_hash
    
    def get_ring_info(self) -> Dict:
        """Get information about the first ring."""
        return {
            "status": self.ring_status.value,
            "size": len(self.ring_members),
            "max_size": self.max_ring_size,
            "min_size": self.min_ring_size,
            "leader": self.ring_leader.hex() if self.ring_leader else None,
            "formation_time": self.ring_formation_time,
            "active_consensus": len(self.active_consensus),
            "pending_requests": len(self.pending_join_requests),
            "stats": self.stats
        }
    
    def get_ring_members(self) -> List[Dict]:
        """Get list of ring members."""
        return [member.to_dict() for member in self.ring_members.values()]
    
    def export_ring_state(self) -> Dict:
        """Export ring state for persistence."""
        return {
            "ring_status": self.ring_status.value,
            "ring_leader": self.ring_leader.hex() if self.ring_leader else None,
            "ring_formation_time": self.ring_formation_time,
            "ring_members": {
                member_id.hex(): member.to_dict()
                for member_id, member in self.ring_members.items()
            },
            "active_consensus": {
                consensus_id.hex(): consensus.to_dict()
                for consensus_id, consensus in self.active_consensus.items()
            },
            "stats": self.stats
        }
