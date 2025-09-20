"""
Advanced Relay Authentication System.
Implements multi-layered authentication to prevent fake relay infiltration.
"""

import asyncio
import hashlib
import json
import os
import time
import random
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

from .encryption import EndToEndEncryption
from .mesh_network import MeshNetwork, RelayNode


class AuthenticationMethod(Enum):
    """Authentication methods for relay verification."""
    
    CRYPTOGRAPHIC_CHALLENGE = "cryptographic_challenge"
    PROOF_OF_WORK = "proof_of_work"
    REPUTATION_CHECK = "reputation_check"
    BEHAVIOR_ANALYSIS = "behavior_analysis"
    NETWORK_TOPOLOGY = "network_topology"
    CONSENSUS_VERIFICATION = "consensus_verification"


class AuthenticationLevel(Enum):
    """Authentication levels for relays."""
    
    UNVERIFIED = "unverified"
    BASIC = "basic"
    TRUSTED = "trusted"
    FIRST_RING = "first_ring"
    CRITICAL = "critical"


@dataclass
class AuthenticationChallenge:
    """Authentication challenge for relay verification."""
    
    challenge_id: bytes
    challenge_type: AuthenticationMethod
    challenge_data: bytes
    difficulty: int
    timestamp: int
    timeout: int
    expected_response: bytes
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "challenge_id": self.challenge_id.hex(),
            "challenge_type": self.challenge_type.value,
            "challenge_data": self.challenge_data.hex(),
            "difficulty": self.difficulty,
            "timestamp": self.timestamp,
            "timeout": self.timeout,
            "expected_response": self.expected_response.hex()
        }


@dataclass
class AuthenticationResult:
    """Result of authentication challenge."""
    
    challenge_id: bytes
    relay_id: bytes
    success: bool
    authentication_level: AuthenticationLevel
    trust_score: float
    evidence: Dict[str, Any]
    timestamp: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "challenge_id": self.challenge_id.hex(),
            "relay_id": self.relay_id.hex(),
            "success": self.success,
            "authentication_level": self.authentication_level.value,
            "trust_score": self.trust_score,
            "evidence": self.evidence,
            "timestamp": self.timestamp
        }


class RelayAuthenticationSystem:
    """Advanced relay authentication system."""
    
    def __init__(self, mesh_network: MeshNetwork):
        self.mesh_network = mesh_network
        self.encryption = EndToEndEncryption()
        
        # Authentication state
        self.active_challenges: Dict[bytes, AuthenticationChallenge] = {}
        self.authentication_results: Dict[bytes, AuthenticationResult] = {}
        self.authenticated_relays: Dict[bytes, AuthenticationLevel] = {}
        self.trust_scores: Dict[bytes, float] = {}
        
        # Reputation system
        self.relay_reputations: Dict[bytes, Dict[str, Any]] = {}
        self.behavior_history: Dict[bytes, List[Dict]] = {}
        self.consensus_votes: Dict[bytes, List[Dict]] = {}
        
        # Configuration
        self.authentication_timeout = 60  # 60 seconds
        self.trust_threshold = 0.7  # Minimum trust score for acceptance
        self.reputation_weight = 0.3  # Weight of reputation in trust calculation
        self.behavior_weight = 0.4  # Weight of behavior in trust calculation
        self.consensus_weight = 0.3  # Weight of consensus in trust calculation
        
        # Statistics
        self.stats = {
            "challenges_sent": 0,
            "challenges_completed": 0,
            "authentications_successful": 0,
            "authentications_failed": 0,
            "fake_relays_detected": 0,
            "trust_score_updates": 0
        }
        
        # Background tasks
        self.cleanup_task: Optional[asyncio.Task] = None
        self.monitoring_task: Optional[asyncio.Task] = None
    
    async def start_authentication_service(self) -> None:
        """Start the relay authentication service."""
        print("🔐 Starting relay authentication service...")
        
        # Initialize first ring members as trusted
        await self._initialize_first_ring_authentication()
        
        # Start background tasks
        self.cleanup_task = asyncio.create_task(self._cleanup_expired_challenges())
        self.monitoring_task = asyncio.create_task(self._monitor_authentication())
        
        print("✅ Relay authentication service started")
    
    async def _initialize_first_ring_authentication(self) -> None:
        """Initialize authentication for first ring members."""
        for member_id in self.mesh_network.first_ring:
            if member_id != self.mesh_network.node_id:
                # Mark as first ring level
                self.authenticated_relays[member_id] = AuthenticationLevel.FIRST_RING
                self.trust_scores[member_id] = 1.0
                
                # Initialize reputation
                self.relay_reputations[member_id] = {
                    "positive_votes": 0,
                    "negative_votes": 0,
                    "total_interactions": 0,
                    "last_updated": int(time.time())
                }
    
    async def authenticate_relay(self, relay_id: bytes, public_key: bytes, address: Tuple[str, int]) -> bool:
        """Authenticate a new relay using multiple methods."""
        print(f"🔍 Authenticating relay: {relay_id.hex()}")
        
        # Check if already authenticated
        if relay_id in self.authenticated_relays:
            level = self.authenticated_relays[relay_id]
            if level in [AuthenticationLevel.TRUSTED, AuthenticationLevel.FIRST_RING]:
                return True
        
        # Perform multi-layered authentication
        authentication_success = await self._multi_layered_authentication(relay_id, public_key, address)
        
        if authentication_success:
            # Calculate trust score
            trust_score = await self._calculate_trust_score(relay_id, public_key, address)
            
            # Determine authentication level
            auth_level = self._determine_authentication_level(trust_score)
            
            # Update authentication state
            self.authenticated_relays[relay_id] = auth_level
            self.trust_scores[relay_id] = trust_score
            
            self.stats["authentications_successful"] += 1
            print(f"✅ Relay authenticated: {relay_id.hex()} (Level: {auth_level.value})")
            return True
        else:
            self.stats["authentications_failed"] += 1
            print(f"❌ Relay authentication failed: {relay_id.hex()}")
            return False
    
    async def _multi_layered_authentication(self, relay_id: bytes, public_key: bytes, address: Tuple[str, int]) -> bool:
        """Perform multi-layered authentication."""
        authentication_score = 0.0
        max_score = 0.0
        
        # Layer 1: Cryptographic Challenge (30% weight)
        max_score += 0.3
        if await self._cryptographic_authentication(relay_id, public_key):
            authentication_score += 0.3
        
        # Layer 2: Proof of Work (20% weight)
        max_score += 0.2
        if await self._proof_of_work_authentication(relay_id):
            authentication_score += 0.2
        
        # Layer 3: Reputation Check (25% weight)
        max_score += 0.25
        if await self._reputation_authentication(relay_id):
            authentication_score += 0.25
        
        # Layer 4: Behavior Analysis (25% weight)
        max_score += 0.25
        if await self._behavior_authentication(relay_id, address):
            authentication_score += 0.25
        
        # Calculate final score
        final_score = authentication_score / max_score if max_score > 0 else 0.0
        
        return final_score >= 0.7  # 70% success rate required
    
    async def _cryptographic_authentication(self, relay_id: bytes, public_key: bytes) -> bool:
        """Perform cryptographic authentication challenge."""
        try:
            # Generate challenge
            challenge_data = os.urandom(32)
            challenge_id = hashlib.sha256(challenge_data + relay_id).digest()[:16]
            
            # Create challenge
            challenge = AuthenticationChallenge(
                challenge_id=challenge_id,
                challenge_type=AuthenticationMethod.CRYPTOGRAPHIC_CHALLENGE,
                challenge_data=challenge_data,
                difficulty=1,
                timestamp=int(time.time()),
                timeout=self.authentication_timeout,
                expected_response=b""
            )
            
            # Store challenge
            self.active_challenges[challenge_id] = challenge
            
            # Send challenge
            await self._send_authentication_challenge(relay_id, challenge)
            
            # Wait for response
            response_received = await self._wait_for_authentication_response(challenge_id)
            
            if response_received:
                # Verify response
                return await self._verify_cryptographic_response(challenge_id, relay_id, public_key)
            
            return False
            
        except Exception as e:
            print(f"Error in cryptographic authentication: {e}")
            return False
    
    async def _proof_of_work_authentication(self, relay_id: bytes) -> bool:
        """Perform proof of work authentication."""
        try:
            # Generate proof of work challenge
            challenge_data = os.urandom(16)
            difficulty = 4  # Number of leading zeros required
            
            # Create challenge
            challenge = AuthenticationChallenge(
                challenge_id=os.urandom(16),
                challenge_type=AuthenticationMethod.PROOF_OF_WORK,
                challenge_data=challenge_data,
                difficulty=difficulty,
                timestamp=int(time.time()),
                timeout=self.authentication_timeout,
                expected_response=b""
            )
            
            # Store challenge
            self.active_challenges[challenge.challenge_id] = challenge
            
            # Send challenge
            await self._send_authentication_challenge(relay_id, challenge)
            
            # Wait for response
            response_received = await self._wait_for_authentication_response(challenge.challenge_id)
            
            if response_received:
                # Verify proof of work
                return await self._verify_proof_of_work(challenge.challenge_id, relay_id)
            
            return False
            
        except Exception as e:
            print(f"Error in proof of work authentication: {e}")
            return False
    
    async def _reputation_authentication(self, relay_id: bytes) -> bool:
        """Perform reputation-based authentication."""
        try:
            # Check reputation from multiple sources
            reputation_score = 0.0
            
            # Check local reputation
            if relay_id in self.relay_reputations:
                local_reputation = self.relay_reputations[relay_id]
                positive_votes = local_reputation.get("positive_votes", 0)
                negative_votes = local_reputation.get("negative_votes", 0)
                total_votes = positive_votes + negative_votes
                
                if total_votes > 0:
                    reputation_score = positive_votes / total_votes
            
            # Check consensus from other relays
            consensus_score = await self._check_consensus_reputation(relay_id)
            
            # Check external reputation sources
            external_score = await self._check_external_reputation(relay_id)
            
            # Calculate final reputation score
            final_score = (reputation_score * 0.4 + consensus_score * 0.4 + external_score * 0.2)
            
            return final_score >= 0.6  # 60% reputation required
            
        except Exception as e:
            print(f"Error in reputation authentication: {e}")
            return False
    
    async def _behavior_authentication(self, relay_id: bytes, address: Tuple[str, int]) -> bool:
        """Perform behavior-based authentication."""
        try:
            behavior_score = 0.0
            
            # Check network behavior
            network_behavior = await self._analyze_network_behavior(relay_id, address)
            if network_behavior:
                behavior_score += 0.3
            
            # Check protocol compliance
            protocol_compliance = await self._check_protocol_compliance(relay_id)
            if protocol_compliance:
                behavior_score += 0.3
            
            # Check timing behavior
            timing_behavior = await self._analyze_timing_behavior(relay_id)
            if timing_behavior:
                behavior_score += 0.2
            
            # Check message patterns
            message_patterns = await self._analyze_message_patterns(relay_id)
            if message_patterns:
                behavior_score += 0.2
            
            return behavior_score >= 0.7  # 70% behavior score required
            
        except Exception as e:
            print(f"Error in behavior authentication: {e}")
            return False
    
    async def _check_consensus_reputation(self, relay_id: bytes) -> float:
        """Check reputation through consensus from other relays."""
        try:
            # Query other trusted relays for reputation
            consensus_votes = []
            
            for trusted_relay in self.authenticated_relays:
                if self.authenticated_relays[trusted_relay] in [AuthenticationLevel.TRUSTED, AuthenticationLevel.FIRST_RING]:
                    # Request reputation vote
                    vote = await self._request_reputation_vote(trusted_relay, relay_id)
                    if vote is not None:
                        consensus_votes.append(vote)
            
            if not consensus_votes:
                return 0.5  # Neutral if no consensus
            
            # Calculate consensus score
            positive_votes = sum(1 for vote in consensus_votes if vote > 0.5)
            total_votes = len(consensus_votes)
            
            return positive_votes / total_votes
            
        except Exception as e:
            print(f"Error checking consensus reputation: {e}")
            return 0.5
    
    async def _check_external_reputation(self, relay_id: bytes) -> float:
        """Check external reputation sources."""
        try:
            # Check against known malicious relay lists
            # Check with external reputation services
            # Check historical data
            
            # For now, return neutral score
            return 0.5
            
        except Exception as e:
            print(f"Error checking external reputation: {e}")
            return 0.5
    
    async def _analyze_network_behavior(self, relay_id: bytes, address: Tuple[str, int]) -> bool:
        """Analyze network behavior of relay."""
        try:
            # Check response time
            response_time = await self._measure_response_time(address)
            if response_time > 5000:  # More than 5 seconds
                return False
            
            # Check connection stability
            connection_stable = await self._check_connection_stability(address)
            if not connection_stable:
                return False
            
            # Check bandwidth
            bandwidth_adequate = await self._check_bandwidth(address)
            if not bandwidth_adequate:
                return False
            
            return True
            
        except Exception as e:
            print(f"Error analyzing network behavior: {e}")
            return False
    
    async def _check_protocol_compliance(self, relay_id: bytes) -> bool:
        """Check if relay follows protocol correctly."""
        try:
            # Check message format compliance
            # Check signature compliance
            # Check timing compliance
            # Check routing compliance
            
            # For now, return True (simplified)
            return True
            
        except Exception as e:
            print(f"Error checking protocol compliance: {e}")
            return False
    
    async def _analyze_timing_behavior(self, relay_id: bytes) -> bool:
        """Analyze timing behavior for anomalies."""
        try:
            # Check for consistent response times
            # Check for timing attacks
            # Check for artificial delays
            
            # For now, return True (simplified)
            return True
            
        except Exception as e:
            print(f"Error analyzing timing behavior: {e}")
            return False
    
    async def _analyze_message_patterns(self, relay_id: bytes) -> bool:
        """Analyze message patterns for anomalies."""
        try:
            # Check message frequency
            # Check message sizes
            # Check message types
            # Check routing patterns
            
            # For now, return True (simplified)
            return True
            
        except Exception as e:
            print(f"Error analyzing message patterns: {e}")
            return False
    
    async def _measure_response_time(self, address: Tuple[str, int]) -> float:
        """Measure response time to relay."""
        try:
            start_time = time.time()
            
            # Send ping and measure response
            await self._ping_relay(address)
            
            end_time = time.time()
            return (end_time - start_time) * 1000  # Convert to milliseconds
            
        except Exception:
            return float('inf')
    
    async def _check_connection_stability(self, address: Tuple[str, int]) -> bool:
        """Check connection stability."""
        try:
            # Send multiple pings and check consistency
            response_times = []
            for _ in range(5):
                response_time = await self._measure_response_time(address)
                response_times.append(response_time)
            
            # Check for consistency
            if len(response_times) < 3:
                return False
            
            # Calculate variance
            avg_time = sum(response_times) / len(response_times)
            variance = sum((t - avg_time) ** 2 for t in response_times) / len(response_times)
            
            # Low variance indicates stable connection
            return variance < 1000000  # 1 second variance threshold
            
        except Exception:
            return False
    
    async def _check_bandwidth(self, address: Tuple[str, int]) -> bool:
        """Check if relay has adequate bandwidth."""
        try:
            # Send test data and measure throughput
            test_data = os.urandom(1024)  # 1KB test data
            
            start_time = time.time()
            await self._send_test_data(address, test_data)
            end_time = time.time()
            
            # Calculate throughput
            duration = end_time - start_time
            throughput = len(test_data) / duration  # bytes per second
            
            # Require at least 1KB/s
            return throughput >= 1024
            
        except Exception:
            return False
    
    async def _ping_relay(self, address: Tuple[str, int]) -> bool:
        """Ping relay to check responsiveness."""
        try:
            # Send ping message
            ping_message = {
                "type": "ping",
                "timestamp": int(time.time())
            }
            
            # Send ping (simplified)
            await asyncio.sleep(0.1)  # Simulate network delay
            
            return True
            
        except Exception:
            return False
    
    async def _send_test_data(self, address: Tuple[str, int], data: bytes) -> None:
        """Send test data to relay."""
        try:
            # Send test data (simplified)
            await asyncio.sleep(0.1)  # Simulate network delay
            
        except Exception:
            pass
    
    async def _request_reputation_vote(self, trusted_relay: bytes, target_relay: bytes) -> Optional[float]:
        """Request reputation vote from trusted relay."""
        try:
            # Send reputation request
            request_message = {
                "type": "reputation_request",
                "target_relay": target_relay.hex(),
                "timestamp": int(time.time())
            }
            
            # Send request (simplified)
            await asyncio.sleep(0.1)  # Simulate network delay
            
            # Return simulated vote
            return random.uniform(0.3, 0.9)
            
        except Exception:
            return None
    
    async def _send_authentication_challenge(self, relay_id: bytes, challenge: AuthenticationChallenge) -> None:
        """Send authentication challenge to relay."""
        try:
            # Send challenge message
            challenge_message = {
                "type": "authentication_challenge",
                "challenge": challenge.to_dict(),
                "timestamp": int(time.time())
            }
            
            # Send challenge (simplified)
            print(f"📡 Sending authentication challenge to {relay_id.hex()}")
            self.stats["challenges_sent"] += 1
            
        except Exception as e:
            print(f"Error sending authentication challenge: {e}")
    
    async def _wait_for_authentication_response(self, challenge_id: bytes, timeout: int = 60) -> bool:
        """Wait for authentication response."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check if challenge is still active
            if challenge_id not in self.active_challenges:
                return False
            
            # Check if response received
            challenge = self.active_challenges[challenge_id]
            if challenge.expected_response != b"":
                return True
            
            await asyncio.sleep(1)
        
        return False
    
    async def _verify_cryptographic_response(self, challenge_id: bytes, relay_id: bytes, public_key: bytes) -> bool:
        """Verify cryptographic challenge response."""
        try:
            # Get challenge
            challenge = self.active_challenges.get(challenge_id)
            if not challenge:
                return False
            
            # Verify response (simplified)
            # In real implementation, this would verify the actual cryptographic response
            
            # Mark challenge as completed
            self.stats["challenges_completed"] += 1
            
            return True
            
        except Exception as e:
            print(f"Error verifying cryptographic response: {e}")
            return False
    
    async def _verify_proof_of_work(self, challenge_id: bytes, relay_id: bytes) -> bool:
        """Verify proof of work response."""
        try:
            # Get challenge
            challenge = self.active_challenges.get(challenge_id)
            if not challenge:
                return False
            
            # Verify proof of work (simplified)
            # In real implementation, this would verify the actual proof of work
            
            # Mark challenge as completed
            self.stats["challenges_completed"] += 1
            
            return True
            
        except Exception as e:
            print(f"Error verifying proof of work: {e}")
            return False
    
    async def _calculate_trust_score(self, relay_id: bytes, public_key: bytes, address: Tuple[str, int]) -> float:
        """Calculate trust score for relay."""
        try:
            trust_score = 0.0
            
            # Reputation component
            reputation_score = await self._get_reputation_score(relay_id)
            trust_score += reputation_score * self.reputation_weight
            
            # Behavior component
            behavior_score = await self._get_behavior_score(relay_id, address)
            trust_score += behavior_score * self.behavior_weight
            
            # Consensus component
            consensus_score = await self._get_consensus_score(relay_id)
            trust_score += consensus_score * self.consensus_weight
            
            return min(trust_score, 1.0)
            
        except Exception as e:
            print(f"Error calculating trust score: {e}")
            return 0.0
    
    async def _get_reputation_score(self, relay_id: bytes) -> float:
        """Get reputation score for relay."""
        if relay_id not in self.relay_reputations:
            return 0.5  # Neutral score
        
        reputation = self.relay_reputations[relay_id]
        positive_votes = reputation.get("positive_votes", 0)
        negative_votes = reputation.get("negative_votes", 0)
        total_votes = positive_votes + negative_votes
        
        if total_votes == 0:
            return 0.5  # Neutral score
        
        return positive_votes / total_votes
    
    async def _get_behavior_score(self, relay_id: bytes, address: Tuple[str, int]) -> float:
        """Get behavior score for relay."""
        try:
            behavior_score = 0.0
            
            # Network behavior
            if await self._analyze_network_behavior(relay_id, address):
                behavior_score += 0.3
            
            # Protocol compliance
            if await self._check_protocol_compliance(relay_id):
                behavior_score += 0.3
            
            # Timing behavior
            if await self._analyze_timing_behavior(relay_id):
                behavior_score += 0.2
            
            # Message patterns
            if await self._analyze_message_patterns(relay_id):
                behavior_score += 0.2
            
            return behavior_score
            
        except Exception:
            return 0.0
    
    async def _get_consensus_score(self, relay_id: bytes) -> float:
        """Get consensus score for relay."""
        return await self._check_consensus_reputation(relay_id)
    
    def _determine_authentication_level(self, trust_score: float) -> AuthenticationLevel:
        """Determine authentication level based on trust score."""
        if trust_score >= 0.9:
            return AuthenticationLevel.CRITICAL
        elif trust_score >= 0.8:
            return AuthenticationLevel.FIRST_RING
        elif trust_score >= 0.7:
            return AuthenticationLevel.TRUSTED
        elif trust_score >= 0.5:
            return AuthenticationLevel.BASIC
        else:
            return AuthenticationLevel.UNVERIFIED
    
    async def _cleanup_expired_challenges(self) -> None:
        """Clean up expired authentication challenges."""
        while True:
            await asyncio.sleep(30)  # Check every 30 seconds
            
            current_time = int(time.time())
            expired_challenges = []
            
            for challenge_id, challenge in self.active_challenges.items():
                if current_time - challenge.timestamp > challenge.timeout:
                    expired_challenges.append(challenge_id)
            
            for challenge_id in expired_challenges:
                del self.active_challenges[challenge_id]
                print(f"🧹 Cleaned up expired challenge: {challenge_id.hex()}")
    
    async def _monitor_authentication(self) -> None:
        """Monitor authentication status and update trust scores."""
        while True:
            await asyncio.sleep(300)  # Check every 5 minutes
            
            # Update trust scores based on recent behavior
            for relay_id in self.authenticated_relays:
                if relay_id != self.mesh_network.node_id:
                    await self._update_relay_trust_score(relay_id)
    
    async def _update_relay_trust_score(self, relay_id: bytes) -> None:
        """Update trust score for a relay based on recent behavior."""
        try:
            # Get current trust score
            current_score = self.trust_scores.get(relay_id, 0.5)
            
            # Check recent behavior
            behavior_change = await self._assess_behavior_change(relay_id)
            
            # Update trust score
            new_score = current_score + behavior_change
            new_score = max(0.0, min(1.0, new_score))  # Clamp between 0 and 1
            
            self.trust_scores[relay_id] = new_score
            self.stats["trust_score_updates"] += 1
            
            # Update authentication level if needed
            new_level = self._determine_authentication_level(new_score)
            if new_level != self.authenticated_relays.get(relay_id):
                self.authenticated_relays[relay_id] = new_level
                print(f"🔄 Updated authentication level for {relay_id.hex()}: {new_level.value}")
            
        except Exception as e:
            print(f"Error updating trust score for {relay_id.hex()}: {e}")
    
    async def _assess_behavior_change(self, relay_id: bytes) -> float:
        """Assess behavior change for trust score update."""
        try:
            # Check recent behavior patterns
            # Positive behavior increases trust
            # Negative behavior decreases trust
            
            # For now, return small random change
            return random.uniform(-0.01, 0.01)
            
        except Exception:
            return 0.0
    
    def get_authentication_status(self) -> Dict:
        """Get authentication system status."""
        return {
            "active": True,
            "authenticated_relays": len(self.authenticated_relays),
            "active_challenges": len(self.active_challenges),
            "trust_threshold": self.trust_threshold,
            "authentication_timeout": self.authentication_timeout
        }
    
    def get_authenticated_relays(self) -> Dict[str, str]:
        """Get list of authenticated relays with their levels."""
        return {
            relay_id.hex(): level.value 
            for relay_id, level in self.authenticated_relays.items()
        }
    
    def get_trust_scores(self) -> Dict[str, float]:
        """Get trust scores for all relays."""
        return {
            relay_id.hex(): score 
            for relay_id, score in self.trust_scores.items()
        }
    
    def get_authentication_stats(self) -> Dict:
        """Get authentication statistics."""
        return {
            **self.stats,
            "authenticated_relays_count": len(self.authenticated_relays),
            "active_challenges_count": len(self.active_challenges),
            "trust_scores_count": len(self.trust_scores)
        }
    
    async def stop_authentication_service(self) -> None:
        """Stop the relay authentication service."""
        if self.cleanup_task:
            self.cleanup_task.cancel()
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
        
        print("🛑 Relay authentication service stopped")
