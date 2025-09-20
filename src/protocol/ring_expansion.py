"""
Ring expansion system for adding new relay servers to the first ring.
Handles the process of expanding the trusted core network.
"""

import asyncio
import hashlib
import json
import time
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .mesh_network import MeshNetwork, RelayNode
from .ring_management import FirstRingManager, RingMember
from .encryption import EndToEndEncryption


class ExpansionPhase(Enum):
    """Phases of ring expansion."""
    
    DISCOVERY = "discovery"  # Discovering potential new members
    EVALUATION = "evaluation"  # Evaluating candidates
    CHALLENGE = "challenge"  # Issuing challenges to candidates
    CONSENSUS = "consensus"  # Ring consensus on new members
    INTEGRATION = "integration"  # Integrating new members
    COMPLETE = "complete"  # Expansion complete


@dataclass
class ExpansionCandidate:
    """A candidate for ring expansion."""
    
    node_id: bytes
    public_key: bytes
    address: str
    port: int
    discovery_time: int
    reputation_score: float
    network_connectivity: float
    uptime_score: float
    challenge_results: List[bool]
    consensus_votes: Dict[bytes, bool]  # ring_member_id -> vote
    status: str  # "discovered", "evaluated", "challenged", "voted", "accepted", "rejected"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "node_id": self.node_id.hex(),
            "public_key": self.public_key.hex(),
            "address": self.address,
            "port": self.port,
            "discovery_time": self.discovery_time,
            "reputation_score": self.reputation_score,
            "network_connectivity": self.network_connectivity,
            "uptime_score": self.uptime_score,
            "challenge_results": self.challenge_results,
            "consensus_votes": {node_id.hex(): vote for node_id, vote in self.consensus_votes.items()},
            "status": self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ExpansionCandidate":
        """Create from dictionary."""
        return cls(
            node_id=bytes.fromhex(data["node_id"]),
            public_key=bytes.fromhex(data["public_key"]),
            address=data["address"],
            port=data["port"],
            discovery_time=data["discovery_time"],
            reputation_score=data["reputation_score"],
            network_connectivity=data["network_connectivity"],
            uptime_score=data["uptime_score"],
            challenge_results=data["challenge_results"],
            consensus_votes={bytes.fromhex(node_id_hex): vote for node_id_hex, vote in data["consensus_votes"].items()},
            status=data["status"]
        )


@dataclass
class ExpansionPlan:
    """Plan for ring expansion."""
    
    plan_id: bytes
    target_size: int
    current_size: int
    expansion_phase: ExpansionPhase
    candidates: List[ExpansionCandidate]
    start_time: int
    estimated_completion: int
    proposer_id: bytes
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "plan_id": self.plan_id.hex(),
            "target_size": self.target_size,
            "current_size": self.current_size,
            "expansion_phase": self.expansion_phase.value,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "start_time": self.start_time,
            "estimated_completion": self.estimated_completion,
            "proposer_id": self.proposer_id.hex()
        }


class RingExpansionManager:
    """Manages the expansion of the first ring."""
    
    def __init__(self, mesh_network: MeshNetwork, ring_manager: FirstRingManager):
        self.mesh_network = mesh_network
        self.ring_manager = ring_manager
        self.encryption = EndToEndEncryption()
        
        # Expansion state
        self.active_expansion: Optional[ExpansionPlan] = None
        self.expansion_history: List[ExpansionPlan] = []
        self.candidate_pool: Dict[bytes, ExpansionCandidate] = {}
        
        # Expansion configuration
        self.min_candidates_for_expansion = 3
        self.max_expansion_batch = 4
        self.evaluation_period = 3600  # 1 hour
        self.challenge_timeout = 1800  # 30 minutes
        self.consensus_timeout = 600  # 10 minutes
        
        # Discovery sources
        self.discovery_sources = [
            "dns_discovery",
            "web_discovery", 
            "peer_recommendation",
            "network_scan"
        ]
        
        # Statistics
        self.stats = {
            "expansions_initiated": 0,
            "expansions_completed": 0,
            "candidates_discovered": 0,
            "candidates_evaluated": 0,
            "candidates_accepted": 0,
            "candidates_rejected": 0,
            "challenges_issued": 0,
            "challenges_passed": 0
        }
    
    async def start_expansion_services(self) -> None:
        """Start ring expansion services."""
        asyncio.create_task(self._candidate_discovery())
        asyncio.create_task(self._expansion_monitor())
        asyncio.create_task(self._candidate_evaluation())
    
    async def initiate_expansion(self, target_size: int) -> bool:
        """Initiate a ring expansion to target size."""
        if self.active_expansion:
            print("⚠️ Expansion already in progress")
            return False
        
        current_size = len(self.ring_manager.ring_members)
        if target_size <= current_size:
            print(f"⚠️ Target size {target_size} not larger than current size {current_size}")
            return False
        
        if target_size > self.ring_manager.max_ring_size:
            print(f"⚠️ Target size {target_size} exceeds maximum {self.ring_manager.max_ring_size}")
            return False
        
        print(f"🚀 Initiating ring expansion from {current_size} to {target_size} members")
        
        # Create expansion plan
        import os
        plan_id = os.urandom(16)
        
        self.active_expansion = ExpansionPlan(
            plan_id=plan_id,
            target_size=target_size,
            current_size=current_size,
            expansion_phase=ExpansionPhase.DISCOVERY,
            candidates=[],
            start_time=int(time.time()),
            estimated_completion=int(time.time()) + 3600,  # 1 hour estimate
            proposer_id=self.mesh_network.node_id
        )
        
        self.stats["expansions_initiated"] += 1
        
        # Start discovery phase
        await self._start_discovery_phase()
        
        return True
    
    async def _start_discovery_phase(self) -> None:
        """Start the discovery phase of expansion."""
        if not self.active_expansion:
            return
        
        print("🔍 Starting candidate discovery phase")
        self.active_expansion.expansion_phase = ExpansionPhase.DISCOVERY
        
        # Discover candidates from multiple sources
        for source in self.discovery_sources:
            try:
                if source == "dns_discovery":
                    await self._discover_candidates_dns()
                elif source == "web_discovery":
                    await self._discover_candidates_web()
                elif source == "peer_recommendation":
                    await self._discover_candidates_peer()
                elif source == "network_scan":
                    await self._discover_candidates_scan()
            except Exception as e:
                print(f"Discovery source {source} failed: {e}")
        
        # Check if we have enough candidates
        if len(self.candidate_pool) >= self.min_candidates_for_expansion:
            await self._transition_to_evaluation_phase()
        else:
            print(f"⚠️ Insufficient candidates found: {len(self.candidate_pool)}")
            await self._cancel_expansion("insufficient_candidates")
    
    async def _discover_candidates_dns(self) -> None:
        """Discover candidates via DNS."""
        # This would implement DNS-based discovery
        # For now, add some mock candidates
        mock_candidates = [
            ("relay1.example.com", 6667),
            ("relay2.example.com", 6667),
            ("relay3.example.com", 6667)
        ]
        
        for address, port in mock_candidates:
            try:
                # Create mock candidate
                import os
                public_key = os.urandom(256)  # Mock public key
                node_id = hashlib.sha256(public_key).digest()[:16]
                
                candidate = ExpansionCandidate(
                    node_id=node_id,
                    public_key=public_key,
                    address=address,
                    port=port,
                    discovery_time=int(time.time()),
                    reputation_score=0.5,  # Initial score
                    network_connectivity=0.0,  # Will be evaluated
                    uptime_score=0.0,  # Will be evaluated
                    challenge_results=[],
                    consensus_votes={},
                    status="discovered"
                )
                
                self.candidate_pool[node_id] = candidate
                self.stats["candidates_discovered"] += 1
                
            except Exception as e:
                print(f"Failed to discover candidate {address}:{port}: {e}")
    
    async def _discover_candidates_web(self) -> None:
        """Discover candidates via web APIs."""
        # This would implement web-based discovery
        # For now, it's a placeholder
        pass
    
    async def _discover_candidates_peer(self) -> None:
        """Discover candidates via peer recommendations."""
        # This would implement peer recommendation system
        # For now, it's a placeholder
        pass
    
    async def _discover_candidates_scan(self) -> None:
        """Discover candidates via network scanning."""
        # This would implement network scanning
        # For now, it's a placeholder
        pass
    
    async def _transition_to_evaluation_phase(self) -> None:
        """Transition to evaluation phase."""
        if not self.active_expansion:
            return
        
        print("📊 Starting candidate evaluation phase")
        self.active_expansion.expansion_phase = ExpansionPhase.EVALUATION
        
        # Select top candidates for evaluation
        candidates = list(self.candidate_pool.values())
        candidates.sort(key=lambda c: c.reputation_score, reverse=True)
        
        # Take top candidates up to max expansion batch
        selected_candidates = candidates[:self.max_expansion_batch]
        
        # Add selected candidates to expansion plan
        self.active_expansion.candidates = selected_candidates
        
        # Start evaluation
        await self._evaluate_candidates(selected_candidates)
    
    async def _evaluate_candidates(self, candidates: List[ExpansionCandidate]) -> None:
        """Evaluate expansion candidates."""
        for candidate in candidates:
            try:
                # Test network connectivity
                connectivity_score = await self._test_connectivity(candidate)
                candidate.network_connectivity = connectivity_score
                
                # Test uptime and reliability
                uptime_score = await self._test_uptime(candidate)
                candidate.uptime_score = uptime_score
                
                # Update reputation score
                candidate.reputation_score = (
                    candidate.network_connectivity * 0.4 +
                    candidate.uptime_score * 0.3 +
                    candidate.reputation_score * 0.3
                )
                
                candidate.status = "evaluated"
                self.stats["candidates_evaluated"] += 1
                
            except Exception as e:
                print(f"Failed to evaluate candidate {candidate.node_id.hex()}: {e}")
                candidate.status = "evaluation_failed"
    
    async def _test_connectivity(self, candidate: ExpansionCandidate) -> float:
        """Test network connectivity to a candidate."""
        try:
            # Attempt to connect to candidate
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(candidate.address, candidate.port),
                timeout=10
            )
            
            # Send ping
            ping_data = {
                "type": "ping",
                "timestamp": int(time.time())
            }
            
            writer.write(json.dumps(ping_data).encode('utf-8'))
            await writer.drain()
            
            # Wait for pong
            response_data = await asyncio.wait_for(reader.read(1024), timeout=5)
            response = json.loads(response_data.decode('utf-8'))
            
            writer.close()
            await writer.wait_closed()
            
            if response.get("type") == "pong":
                return 1.0  # Perfect connectivity
            else:
                return 0.5  # Partial connectivity
                
        except asyncio.TimeoutError:
            return 0.0  # No connectivity
        except Exception:
            return 0.0  # No connectivity
    
    async def _test_uptime(self, candidate: ExpansionCandidate) -> float:
        """Test uptime and reliability of a candidate."""
        # This would implement uptime testing
        # For now, return a mock score
        return 0.8
    
    async def _transition_to_challenge_phase(self) -> None:
        """Transition to challenge phase."""
        if not self.active_expansion:
            return
        
        print("🔐 Starting challenge phase")
        self.active_expansion.expansion_phase = ExpansionPhase.CHALLENGE
        
        # Issue challenges to evaluated candidates
        for candidate in self.active_expansion.candidates:
            if candidate.status == "evaluated":
                await self._issue_challenge(candidate)
    
    async def _issue_challenge(self, candidate: ExpansionCandidate) -> None:
        """Issue a challenge to a candidate."""
        try:
            # Create challenge
            import os
            challenge_id = os.urandom(16)
            challenge_data = os.urandom(32)
            
            challenge = {
                "challenge_id": challenge_id.hex(),
                "challenge_data": challenge_data.hex(),
                "challenge_type": "signature_challenge",
                "timestamp": int(time.time()),
                "timeout": self.challenge_timeout
            }
            
            # Send challenge to candidate
            # This would implement actual network communication
            print(f"📤 Issued challenge to {candidate.node_id.hex()}")
            
            candidate.status = "challenged"
            self.stats["challenges_issued"] += 1
            
        except Exception as e:
            print(f"Failed to issue challenge to {candidate.node_id.hex()}: {e}")
            candidate.status = "challenge_failed"
    
    async def process_challenge_response(self, candidate_id: bytes, 
                                       response_data: Dict) -> bool:
        """Process a challenge response from a candidate."""
        if not self.active_expansion:
            return False
        
        # Find candidate
        candidate = None
        for c in self.active_expansion.candidates:
            if c.node_id == candidate_id:
                candidate = c
                break
        
        if not candidate:
            return False
        
        try:
            # Verify challenge response
            is_valid = await self._verify_challenge_response(candidate, response_data)
            
            if is_valid:
                candidate.challenge_results.append(True)
                candidate.status = "challenge_passed"
                self.stats["challenges_passed"] += 1
                
                # Check if all candidates have been challenged
                if all(c.status in ["challenge_passed", "challenge_failed"] 
                       for c in self.active_expansion.candidates):
                    await self._transition_to_consensus_phase()
                
                return True
            else:
                candidate.challenge_results.append(False)
                candidate.status = "challenge_failed"
                return False
                
        except Exception as e:
            print(f"Error processing challenge response: {e}")
            candidate.status = "challenge_failed"
            return False
    
    async def _verify_challenge_response(self, candidate: ExpansionCandidate, 
                                       response_data: Dict) -> bool:
        """Verify a challenge response."""
        # This would implement actual challenge verification
        # For now, return True as placeholder
        return True
    
    async def _transition_to_consensus_phase(self) -> None:
        """Transition to consensus phase."""
        if not self.active_expansion:
            return
        
        print("🗳️ Starting consensus phase")
        self.active_expansion.expansion_phase = ExpansionPhase.CONSENSUS
        
        # Create consensus proposals for each candidate
        for candidate in self.active_expansion.candidates:
            if candidate.status == "challenge_passed":
                await self._create_membership_consensus(candidate)
    
    async def _create_membership_consensus(self, candidate: ExpansionCandidate) -> None:
        """Create consensus proposal for candidate membership."""
        # This would create actual consensus proposals
        # For now, simulate consensus voting
        for member_id in self.ring_manager.ring_members:
            # Simulate vote based on candidate's reputation
            vote = candidate.reputation_score > 0.7
            candidate.consensus_votes[member_id] = vote
        
        # Check if consensus is reached
        total_votes = len(candidate.consensus_votes)
        yes_votes = sum(1 for vote in candidate.consensus_votes.values() if vote)
        
        if yes_votes > (total_votes * 0.75):  # 75% threshold
            candidate.status = "accepted"
            self.stats["candidates_accepted"] += 1
        else:
            candidate.status = "rejected"
            self.stats["candidates_rejected"] += 1
    
    async def _transition_to_integration_phase(self) -> None:
        """Transition to integration phase."""
        if not self.active_expansion:
            return
        
        print("🔗 Starting integration phase")
        self.active_expansion.expansion_phase = ExpansionPhase.INTEGRATION
        
        # Integrate accepted candidates
        accepted_candidates = [c for c in self.active_expansion.candidates 
                             if c.status == "accepted"]
        
        for candidate in accepted_candidates:
            await self._integrate_candidate(candidate)
        
        # Complete expansion
        await self._complete_expansion()
    
    async def _integrate_candidate(self, candidate: ExpansionCandidate) -> None:
        """Integrate an accepted candidate into the ring."""
        try:
            # Create ring member
            new_member = RingMember(
                node_id=candidate.node_id,
                public_key=candidate.public_key,
                address=candidate.address,
                port=candidate.port,
                join_timestamp=int(time.time()),
                last_heartbeat=int(time.time()),
                reputation=candidate.reputation_score,
                is_active=True,
                consensus_votes=0,
                challenges_solved=len([r for r in candidate.challenge_results if r])
            )
            
            # Add to ring
            self.ring_manager.ring_members[candidate.node_id] = new_member
            
            # Add to mesh network
            relay_node = RelayNode(
                node_id=candidate.node_id,
                public_key=candidate.public_key,
                address=candidate.address,
                port=candidate.port,
                is_first_ring=True,
                reputation=candidate.reputation_score,
                last_seen=int(time.time()),
                challenges_passed=len([r for r in candidate.challenge_results if r]),
                challenges_failed=len([r for r in candidate.challenge_results if not r])
            )
            
            self.mesh_network.add_node(relay_node)
            
            print(f"✅ Integrated candidate {candidate.node_id.hex()} into ring")
            
        except Exception as e:
            print(f"Failed to integrate candidate {candidate.node_id.hex()}: {e}")
    
    async def _complete_expansion(self) -> None:
        """Complete the expansion process."""
        if not self.active_expansion:
            return
        
        print("🎉 Ring expansion completed")
        self.active_expansion.expansion_phase = ExpansionPhase.COMPLETE
        
        # Move to history
        self.expansion_history.append(self.active_expansion)
        self.stats["expansions_completed"] += 1
        
        # Clear active expansion
        self.active_expansion = None
        
        # Clear candidate pool
        self.candidate_pool.clear()
        
        # Broadcast ring update
        await self.ring_manager._broadcast_ring_update()
    
    async def _cancel_expansion(self, reason: str) -> None:
        """Cancel the current expansion."""
        if not self.active_expansion:
            return
        
        print(f"❌ Ring expansion cancelled: {reason}")
        
        # Move to history with cancelled status
        self.active_expansion.expansion_phase = ExpansionPhase.COMPLETE
        self.expansion_history.append(self.active_expansion)
        
        # Clear active expansion
        self.active_expansion = None
        
        # Clear candidate pool
        self.candidate_pool.clear()
    
    async def _candidate_discovery(self) -> None:
        """Continuous candidate discovery service."""
        while True:
            await asyncio.sleep(3600)  # Every hour
            
            # Only discover if no active expansion
            if not self.active_expansion:
                await self._discover_candidates_dns()
    
    async def _expansion_monitor(self) -> None:
        """Monitor active expansion progress."""
        while True:
            await asyncio.sleep(60)  # Every minute
            
            if not self.active_expansion:
                continue
            
            current_time = int(time.time())
            
            # Check for timeouts
            if current_time - self.active_expansion.start_time > 7200:  # 2 hours
                await self._cancel_expansion("timeout")
                continue
            
            # Check phase transitions
            if self.active_expansion.expansion_phase == ExpansionPhase.CONSENSUS:
                # Check if all candidates have been voted on
                all_voted = all(c.status in ["accepted", "rejected"] 
                              for c in self.active_expansion.candidates)
                
                if all_voted:
                    await self._transition_to_integration_phase()
    
    async def _candidate_evaluation(self) -> None:
        """Continuous candidate evaluation service."""
        while True:
            await asyncio.sleep(1800)  # Every 30 minutes
            
            # Re-evaluate candidates in pool
            for candidate in self.candidate_pool.values():
                if candidate.status == "discovered":
                    await self._evaluate_candidates([candidate])
    
    def get_expansion_status(self) -> Dict:
        """Get current expansion status."""
        if not self.active_expansion:
            return {
                "active": False,
                "phase": None,
                "candidates": 0,
                "target_size": 0,
                "current_size": len(self.ring_manager.ring_members)
            }
        
        return {
            "active": True,
            "phase": self.active_expansion.expansion_phase.value,
            "candidates": len(self.active_expansion.candidates),
            "target_size": self.active_expansion.target_size,
            "current_size": self.active_expansion.current_size,
            "start_time": self.active_expansion.start_time,
            "estimated_completion": self.active_expansion.estimated_completion
        }
    
    def get_expansion_history(self) -> List[Dict]:
        """Get expansion history."""
        return [plan.to_dict() for plan in self.expansion_history]
    
    def get_candidate_pool(self) -> List[Dict]:
        """Get current candidate pool."""
        return [candidate.to_dict() for candidate in self.candidate_pool.values()]
    
    def get_expansion_stats(self) -> Dict:
        """Get expansion statistics."""
        return {
            **self.stats,
            "active_expansion": self.active_expansion is not None,
            "candidate_pool_size": len(self.candidate_pool),
            "expansion_history_count": len(self.expansion_history)
        }
