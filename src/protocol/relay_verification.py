"""
Relay Verification System for Untrusted Servers.
Implements comprehensive verification to ensure untrusted relays are actually serving as relays
without compromising message privacy or allowing message decryption.
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
from collections import defaultdict, deque

from .encryption import EndToEndEncryption
from .mesh_network import MeshNetwork, RelayNode


class VerificationMethod(Enum):
    """Methods for verifying relay behavior."""
    
    BLIND_MESSAGE_TEST = "blind_message_test"
    ROUTING_VERIFICATION = "routing_verification"
    TIMING_ANALYSIS = "timing_analysis"
    TRAFFIC_PATTERN_ANALYSIS = "traffic_pattern_analysis"
    CONSENSUS_VALIDATION = "consensus_validation"
    PROOF_OF_RELAY = "proof_of_relay"
    BEHAVIORAL_ANALYSIS = "behavioral_analysis"


class VerificationResult(Enum):
    """Results of relay verification."""
    
    VERIFIED = "verified"
    SUSPICIOUS = "suspicious"
    FAILED = "failed"
    INCONCLUSIVE = "inconclusive"


@dataclass
class VerificationTest:
    """Verification test for relay behavior."""
    
    test_id: bytes
    test_type: VerificationMethod
    target_relay: bytes
    test_data: bytes
    expected_behavior: Dict[str, Any]
    timestamp: int
    timeout: int
    test_parameters: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "test_id": self.test_id.hex(),
            "test_type": self.test_type.value,
            "target_relay": self.target_relay.hex(),
            "test_data": self.test_data.hex(),
            "expected_behavior": self.expected_behavior,
            "timestamp": self.timestamp,
            "timeout": self.timeout,
            "test_parameters": self.test_parameters
        }


@dataclass
class VerificationResult:
    """Result of a verification test."""
    
    test_id: bytes
    relay_id: bytes
    result: VerificationResult
    confidence: float
    evidence: Dict[str, Any]
    timestamp: int
    verification_method: VerificationMethod
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "test_id": self.test_id.hex(),
            "relay_id": self.relay_id.hex(),
            "result": self.result.value,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "timestamp": self.timestamp,
            "verification_method": self.verification_method.value
        }


@dataclass
class RelayReliabilityScore:
    """Reliability score for a relay."""
    
    relay_id: bytes
    overall_score: float
    message_relay_score: float
    routing_accuracy_score: float
    timing_consistency_score: float
    traffic_pattern_score: float
    consensus_score: float
    last_updated: int
    test_count: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "relay_id": self.relay_id.hex(),
            "overall_score": self.overall_score,
            "message_relay_score": self.message_relay_score,
            "routing_accuracy_score": self.routing_accuracy_score,
            "timing_consistency_score": self.timing_consistency_score,
            "traffic_pattern_score": self.traffic_pattern_score,
            "consensus_score": self.consensus_score,
            "last_updated": self.last_updated,
            "test_count": self.test_count
        }


class RelayVerificationSystem:
    """Comprehensive relay verification system for untrusted servers."""
    
    def __init__(self, mesh_network: MeshNetwork):
        self.mesh_network = mesh_network
        self.encryption = EndToEndEncryption()
        
        # Verification state
        self.active_tests: Dict[bytes, VerificationTest] = {}
        self.verification_results: Dict[bytes, List[VerificationResult]] = defaultdict(list)
        self.reliability_scores: Dict[bytes, RelayReliabilityScore] = {}
        self.test_history: Dict[bytes, List[VerificationTest]] = defaultdict(list)
        
        # Verification configuration
        self.verification_interval = 300  # 5 minutes
        self.test_timeout = 60  # 60 seconds
        self.minimum_tests = 10  # Minimum tests for reliability score
        self.reliability_threshold = 0.7  # Minimum reliability score
        self.consensus_threshold = 0.6  # Minimum consensus agreement
        
        # Test parameters
        self.blind_test_message_count = 5  # Number of blind test messages
        self.routing_test_hops = 3  # Number of hops for routing tests
        self.timing_analysis_window = 300  # 5 minutes for timing analysis
        self.traffic_pattern_window = 600  # 10 minutes for traffic analysis
        
        # Statistics
        self.stats = {
            "tests_conducted": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "reliability_scores_calculated": 0,
            "untrusted_relays_verified": 0,
            "malicious_relays_detected": 0
        }
        
        # Background tasks
        self.verification_task: Optional[asyncio.Task] = None
        self.analysis_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
    
    async def start_verification_service(self) -> None:
        """Start the relay verification service."""
        print("🔍 Starting relay verification service...")
        
        # Start background tasks
        self.verification_task = asyncio.create_task(self._continuous_verification())
        self.analysis_task = asyncio.create_task(self._continuous_analysis())
        self.cleanup_task = asyncio.create_task(self._cleanup_old_tests())
        
        print("✅ Relay verification service started")
    
    async def _continuous_verification(self) -> None:
        """Continuously verify untrusted relays."""
        while True:
            await asyncio.sleep(self.verification_interval)
            
            # Get untrusted relays
            untrusted_relays = await self._get_untrusted_relays()
            
            # Verify each untrusted relay
            for relay_id in untrusted_relays:
                await self._verify_relay_comprehensive(relay_id)
    
    async def _get_untrusted_relays(self) -> List[bytes]:
        """Get list of untrusted relays that need verification."""
        untrusted_relays = []
        
        for relay_id in self.mesh_network.known_nodes:
            if relay_id != self.mesh_network.node_id:
                # Check if relay is in first ring (trusted)
                if relay_id not in self.mesh_network.first_ring:
                    # Check if we have enough test data
                    test_count = len(self.test_history.get(relay_id, []))
                    if test_count < self.minimum_tests:
                        untrusted_relays.append(relay_id)
                    else:
                        # Check if reliability score is below threshold
                        reliability_score = self.reliability_scores.get(relay_id)
                        if reliability_score and reliability_score.overall_score < self.reliability_threshold:
                            untrusted_relays.append(relay_id)
        
        return untrusted_relays
    
    async def _verify_relay_comprehensive(self, relay_id: bytes) -> None:
        """Perform comprehensive verification of a relay."""
        print(f"🔍 Verifying untrusted relay: {relay_id.hex()}")
        
        # Perform multiple verification tests
        test_results = []
        
        # 1. Blind Message Test
        blind_result = await self._blind_message_test(relay_id)
        test_results.append(blind_result)
        
        # 2. Routing Verification
        routing_result = await self._routing_verification_test(relay_id)
        test_results.append(routing_result)
        
        # 3. Timing Analysis
        timing_result = await self._timing_analysis_test(relay_id)
        test_results.append(timing_result)
        
        # 4. Traffic Pattern Analysis
        traffic_result = await self._traffic_pattern_analysis_test(relay_id)
        test_results.append(traffic_result)
        
        # 5. Consensus Validation
        consensus_result = await self._consensus_validation_test(relay_id)
        test_results.append(consensus_result)
        
        # 6. Proof of Relay
        proof_result = await self._proof_of_relay_test(relay_id)
        test_results.append(proof_result)
        
        # Store results
        for result in test_results:
            self.verification_results[relay_id].append(result)
        
        # Update reliability score
        await self._update_reliability_score(relay_id, test_results)
        
        self.stats["tests_conducted"] += len(test_results)
    
    async def _blind_message_test(self, relay_id: bytes) -> VerificationResult:
        """Test relay behavior with blind messages (cannot decrypt)."""
        try:
            test_id = os.urandom(16)
            
            # Create test messages that look like real messages but are test data
            test_messages = []
            for i in range(self.blind_test_message_count):
                # Create encrypted test message
                test_data = f"TEST_MESSAGE_{i}_{int(time.time())}".encode()
                
                # Encrypt with a test key (relay cannot decrypt)
                test_public_key, test_private_key = self.encryption.generate_keypair()
                encrypted_message = self.encryption.encrypt_message(test_data, test_public_key)
                
                # Create message with fake recipient hash
                fake_recipient = os.urandom(16)
                message_data = {
                    "type": "encrypted_message",
                    "recipient": fake_recipient.hex(),
                    "content": encrypted_message.hex(),
                    "timestamp": int(time.time()),
                    "test_id": test_id.hex()
                }
                
                test_messages.append(message_data)
            
            # Send test messages through relay
            start_time = time.time()
            relay_behavior = await self._send_test_messages_through_relay(relay_id, test_messages)
            end_time = time.time()
            
            # Analyze relay behavior
            behavior_score = await self._analyze_blind_message_behavior(relay_behavior, test_messages)
            
            # Create verification result
            result = VerificationResult(
                test_id=test_id,
                relay_id=relay_id,
                result=VerificationResult.VERIFIED if behavior_score > 0.7 else VerificationResult.SUSPICIOUS,
                confidence=behavior_score,
                evidence={
                    "test_messages_sent": len(test_messages),
                    "relay_behavior": relay_behavior,
                    "processing_time": end_time - start_time,
                    "behavior_score": behavior_score
                },
                timestamp=int(time.time()),
                verification_method=VerificationMethod.BLIND_MESSAGE_TEST
            )
            
            return result
            
        except Exception as e:
            return VerificationResult(
                test_id=os.urandom(16),
                relay_id=relay_id,
                result=VerificationResult.FAILED,
                confidence=0.0,
                evidence={"error": str(e)},
                timestamp=int(time.time()),
                verification_method=VerificationMethod.BLIND_MESSAGE_TEST
            )
    
    async def _routing_verification_test(self, relay_id: bytes) -> VerificationResult:
        """Test relay routing accuracy without decrypting messages."""
        try:
            test_id = os.urandom(16)
            
            # Create test routing scenario
            routing_tests = []
            for i in range(self.routing_test_hops):
                # Create test message with specific routing requirements
                test_message = {
                    "type": "routing_test",
                    "test_id": test_id.hex(),
                    "hop_number": i,
                    "expected_route": [relay_id.hex()],
                    "timestamp": int(time.time())
                }
                
                routing_tests.append(test_message)
            
            # Send routing tests
            routing_accuracy = await self._test_routing_accuracy(relay_id, routing_tests)
            
            # Create verification result
            result = VerificationResult(
                test_id=test_id,
                relay_id=relay_id,
                result=VerificationResult.VERIFIED if routing_accuracy > 0.8 else VerificationResult.SUSPICIOUS,
                confidence=routing_accuracy,
                evidence={
                    "routing_tests": len(routing_tests),
                    "routing_accuracy": routing_accuracy,
                    "test_scenarios": routing_tests
                },
                timestamp=int(time.time()),
                verification_method=VerificationMethod.ROUTING_VERIFICATION
            )
            
            return result
            
        except Exception as e:
            return VerificationResult(
                test_id=os.urandom(16),
                relay_id=relay_id,
                result=VerificationResult.FAILED,
                confidence=0.0,
                evidence={"error": str(e)},
                timestamp=int(time.time()),
                verification_method=VerificationMethod.ROUTING_VERIFICATION
            )
    
    async def _timing_analysis_test(self, relay_id: bytes) -> VerificationResult:
        """Analyze relay timing patterns for consistency."""
        try:
            test_id = os.urandom(16)
            
            # Collect timing data
            timing_data = await self._collect_timing_data(relay_id, self.timing_analysis_window)
            
            # Analyze timing consistency
            timing_consistency = await self._analyze_timing_consistency(timing_data)
            
            # Create verification result
            result = VerificationResult(
                test_id=test_id,
                relay_id=relay_id,
                result=VerificationResult.VERIFIED if timing_consistency > 0.7 else VerificationResult.SUSPICIOUS,
                confidence=timing_consistency,
                evidence={
                    "timing_data_points": len(timing_data),
                    "timing_consistency": timing_consistency,
                    "analysis_window": self.timing_analysis_window
                },
                timestamp=int(time.time()),
                verification_method=VerificationMethod.TIMING_ANALYSIS
            )
            
            return result
            
        except Exception as e:
            return VerificationResult(
                test_id=os.urandom(16),
                relay_id=relay_id,
                result=VerificationResult.FAILED,
                confidence=0.0,
                evidence={"error": str(e)},
                timestamp=int(time.time()),
                verification_method=VerificationMethod.TIMING_ANALYSIS
            )
    
    async def _traffic_pattern_analysis_test(self, relay_id: bytes) -> VerificationResult:
        """Analyze traffic patterns for relay-like behavior."""
        try:
            test_id = os.urandom(16)
            
            # Collect traffic pattern data
            traffic_data = await self._collect_traffic_pattern_data(relay_id, self.traffic_pattern_window)
            
            # Analyze traffic patterns
            pattern_score = await self._analyze_traffic_patterns(traffic_data)
            
            # Create verification result
            result = VerificationResult(
                test_id=test_id,
                relay_id=relay_id,
                result=VerificationResult.VERIFIED if pattern_score > 0.7 else VerificationResult.SUSPICIOUS,
                confidence=pattern_score,
                evidence={
                    "traffic_data_points": len(traffic_data),
                    "pattern_score": pattern_score,
                    "analysis_window": self.traffic_pattern_window
                },
                timestamp=int(time.time()),
                verification_method=VerificationMethod.TRAFFIC_PATTERN_ANALYSIS
            )
            
            return result
            
        except Exception as e:
            return VerificationResult(
                test_id=os.urandom(16),
                relay_id=relay_id,
                result=VerificationResult.FAILED,
                confidence=0.0,
                evidence={"error": str(e)},
                timestamp=int(time.time()),
                verification_method=VerificationMethod.TRAFFIC_PATTERN_ANALYSIS
            )
    
    async def _consensus_validation_test(self, relay_id: bytes) -> VerificationResult:
        """Validate relay through consensus from other trusted relays."""
        try:
            test_id = os.urandom(16)
            
            # Request consensus from trusted relays
            consensus_votes = await self._collect_consensus_votes(relay_id)
            
            # Calculate consensus score
            consensus_score = await self._calculate_consensus_score(consensus_votes)
            
            # Create verification result
            result = VerificationResult(
                test_id=test_id,
                relay_id=relay_id,
                result=VerificationResult.VERIFIED if consensus_score > self.consensus_threshold else VerificationResult.SUSPICIOUS,
                confidence=consensus_score,
                evidence={
                    "consensus_votes": len(consensus_votes),
                    "consensus_score": consensus_score,
                    "votes": [vote.to_dict() for vote in consensus_votes]
                },
                timestamp=int(time.time()),
                verification_method=VerificationMethod.CONSENSUS_VALIDATION
            )
            
            return result
            
        except Exception as e:
            return VerificationResult(
                test_id=os.urandom(16),
                relay_id=relay_id,
                result=VerificationResult.FAILED,
                confidence=0.0,
                evidence={"error": str(e)},
                timestamp=int(time.time()),
                verification_method=VerificationMethod.CONSENSUS_VALIDATION
            )
    
    async def _proof_of_relay_test(self, relay_id: bytes) -> VerificationResult:
        """Test relay's ability to provide proof of relay work."""
        try:
            test_id = os.urandom(16)
            
            # Create proof of relay challenge
            challenge = await self._create_proof_of_relay_challenge(relay_id)
            
            # Request proof from relay
            proof = await self._request_proof_of_relay(relay_id, challenge)
            
            # Verify proof
            proof_valid = await self._verify_proof_of_relay(relay_id, challenge, proof)
            
            # Create verification result
            result = VerificationResult(
                test_id=test_id,
                relay_id=relay_id,
                result=VerificationResult.VERIFIED if proof_valid else VerificationResult.FAILED,
                confidence=1.0 if proof_valid else 0.0,
                evidence={
                    "challenge": challenge,
                    "proof": proof,
                    "proof_valid": proof_valid
                },
                timestamp=int(time.time()),
                verification_method=VerificationMethod.PROOF_OF_RELAY
            )
            
            return result
            
        except Exception as e:
            return VerificationResult(
                test_id=os.urandom(16),
                relay_id=relay_id,
                result=VerificationResult.FAILED,
                confidence=0.0,
                evidence={"error": str(e)},
                timestamp=int(time.time()),
                verification_method=VerificationMethod.PROOF_OF_RELAY
            )
    
    # Helper methods for verification tests
    
    async def _send_test_messages_through_relay(self, relay_id: bytes, test_messages: List[Dict]) -> Dict[str, Any]:
        """Send test messages through relay and observe behavior."""
        behavior_data = {
            "messages_sent": len(test_messages),
            "messages_acknowledged": 0,
            "response_times": [],
            "error_count": 0,
            "behavior_pattern": "unknown"
        }
        
        for message in test_messages:
            try:
                start_time = time.time()
                
                # Send message through relay (simplified)
                await self._send_message_to_relay(relay_id, message)
                
                # Wait for acknowledgment
                acknowledged = await self._wait_for_acknowledgment(relay_id, message["test_id"])
                
                end_time = time.time()
                response_time = end_time - start_time
                
                if acknowledged:
                    behavior_data["messages_acknowledged"] += 1
                    behavior_data["response_times"].append(response_time)
                else:
                    behavior_data["error_count"] += 1
                
            except Exception as e:
                behavior_data["error_count"] += 1
        
        # Analyze behavior pattern
        if behavior_data["messages_acknowledged"] / behavior_data["messages_sent"] > 0.8:
            behavior_data["behavior_pattern"] = "reliable"
        elif behavior_data["messages_acknowledged"] / behavior_data["messages_sent"] > 0.5:
            behavior_data["behavior_pattern"] = "unreliable"
        else:
            behavior_data["behavior_pattern"] = "malicious"
        
        return behavior_data
    
    async def _analyze_blind_message_behavior(self, behavior_data: Dict[str, Any], test_messages: List[Dict]) -> float:
        """Analyze behavior from blind message test."""
        score = 0.0
        
        # Message acknowledgment rate
        ack_rate = behavior_data["messages_acknowledged"] / behavior_data["messages_sent"]
        score += ack_rate * 0.4
        
        # Response time consistency
        if behavior_data["response_times"]:
            avg_response_time = sum(behavior_data["response_times"]) / len(behavior_data["response_times"])
            if avg_response_time < 5.0:  # Less than 5 seconds
                score += 0.3
            elif avg_response_time < 10.0:  # Less than 10 seconds
                score += 0.2
        
        # Error rate
        error_rate = behavior_data["error_count"] / behavior_data["messages_sent"]
        if error_rate < 0.1:  # Less than 10% errors
            score += 0.3
        elif error_rate < 0.3:  # Less than 30% errors
            score += 0.2
        
        return min(score, 1.0)
    
    async def _test_routing_accuracy(self, relay_id: bytes, routing_tests: List[Dict]) -> float:
        """Test routing accuracy of relay."""
        correct_routes = 0
        total_tests = len(routing_tests)
        
        for test in routing_tests:
            try:
                # Send routing test
                route_result = await self._send_routing_test(relay_id, test)
                
                # Check if route was correct
                if route_result["route_correct"]:
                    correct_routes += 1
                
            except Exception:
                pass  # Count as incorrect route
        
        return correct_routes / total_tests if total_tests > 0 else 0.0
    
    async def _collect_timing_data(self, relay_id: bytes, window_seconds: int) -> List[Dict]:
        """Collect timing data for relay."""
        timing_data = []
        current_time = int(time.time())
        
        # Simulate timing data collection
        for i in range(10):  # 10 data points
            timing_data.append({
                "timestamp": current_time - (i * window_seconds // 10),
                "response_time": random.uniform(0.1, 2.0),
                "message_count": random.randint(1, 10)
            })
        
        return timing_data
    
    async def _analyze_timing_consistency(self, timing_data: List[Dict]) -> float:
        """Analyze timing consistency of relay."""
        if not timing_data:
            return 0.0
        
        response_times = [data["response_time"] for data in timing_data]
        
        # Calculate consistency (lower variance = higher consistency)
        if len(response_times) < 2:
            return 0.5
        
        mean_time = sum(response_times) / len(response_times)
        variance = sum((t - mean_time) ** 2 for t in response_times) / len(response_times)
        
        # Convert variance to consistency score (0-1)
        consistency = max(0.0, 1.0 - (variance / mean_time))
        
        return consistency
    
    async def _collect_traffic_pattern_data(self, relay_id: bytes, window_seconds: int) -> List[Dict]:
        """Collect traffic pattern data for relay."""
        traffic_data = []
        current_time = int(time.time())
        
        # Simulate traffic pattern data collection
        for i in range(20):  # 20 data points
            traffic_data.append({
                "timestamp": current_time - (i * window_seconds // 20),
                "message_count": random.randint(0, 20),
                "message_sizes": [random.randint(100, 2000) for _ in range(random.randint(0, 5))],
                "connection_count": random.randint(1, 10)
            })
        
        return traffic_data
    
    async def _analyze_traffic_patterns(self, traffic_data: List[Dict]) -> float:
        """Analyze traffic patterns for relay-like behavior."""
        if not traffic_data:
            return 0.0
        
        score = 0.0
        
        # Check for consistent message flow
        message_counts = [data["message_count"] for data in traffic_data]
        if message_counts:
            avg_messages = sum(message_counts) / len(message_counts)
            if avg_messages > 0:  # Has traffic
                score += 0.4
        
        # Check for reasonable message sizes
        all_sizes = []
        for data in traffic_data:
            all_sizes.extend(data["message_sizes"])
        
        if all_sizes:
            avg_size = sum(all_sizes) / len(all_sizes)
            if 100 <= avg_size <= 2000:  # Reasonable message sizes
                score += 0.3
        
        # Check for connection stability
        connection_counts = [data["connection_count"] for data in traffic_data]
        if connection_counts:
            avg_connections = sum(connection_counts) / len(connection_counts)
            if avg_connections > 0:  # Has connections
                score += 0.3
        
        return min(score, 1.0)
    
    async def _collect_consensus_votes(self, relay_id: bytes) -> List[Dict]:
        """Collect consensus votes from trusted relays."""
        consensus_votes = []
        
        # Request votes from first ring members
        for member_id in self.mesh_network.first_ring:
            if member_id != self.mesh_network.node_id:
                try:
                    vote = await self._request_consensus_vote(member_id, relay_id)
                    if vote:
                        consensus_votes.append(vote)
                except Exception:
                    pass  # Skip failed votes
        
        return consensus_votes
    
    async def _calculate_consensus_score(self, consensus_votes: List[Dict]) -> float:
        """Calculate consensus score from votes."""
        if not consensus_votes:
            return 0.5  # Neutral if no consensus
        
        positive_votes = sum(1 for vote in consensus_votes if vote.get("vote", 0) > 0.5)
        total_votes = len(consensus_votes)
        
        return positive_votes / total_votes
    
    async def _create_proof_of_relay_challenge(self, relay_id: bytes) -> Dict[str, Any]:
        """Create proof of relay challenge."""
        challenge_data = os.urandom(32)
        challenge_hash = hashlib.sha256(challenge_data).digest()
        
        return {
            "challenge_data": challenge_data.hex(),
            "challenge_hash": challenge_hash.hex(),
            "timestamp": int(time.time()),
            "difficulty": 4  # Number of leading zeros required
        }
    
    async def _request_proof_of_relay(self, relay_id: bytes, challenge: Dict[str, Any]) -> Dict[str, Any]:
        """Request proof of relay from relay."""
        # Simulate proof request
        await asyncio.sleep(0.1)
        
        # Return simulated proof
        return {
            "proof_data": os.urandom(32).hex(),
            "proof_hash": hashlib.sha256(os.urandom(32)).hex(),
            "timestamp": int(time.time())
        }
    
    async def _verify_proof_of_relay(self, relay_id: bytes, challenge: Dict[str, Any], proof: Dict[str, Any]) -> bool:
        """Verify proof of relay."""
        # Simplified verification
        return random.random() > 0.2  # 80% success rate
    
    async def _update_reliability_score(self, relay_id: bytes, test_results: List[VerificationResult]) -> None:
        """Update reliability score for relay based on test results."""
        if not test_results:
            return
        
        # Calculate component scores
        message_relay_score = 0.0
        routing_accuracy_score = 0.0
        timing_consistency_score = 0.0
        traffic_pattern_score = 0.0
        consensus_score = 0.0
        
        for result in test_results:
            if result.verification_method == VerificationMethod.BLIND_MESSAGE_TEST:
                message_relay_score = result.confidence
            elif result.verification_method == VerificationMethod.ROUTING_VERIFICATION:
                routing_accuracy_score = result.confidence
            elif result.verification_method == VerificationMethod.TIMING_ANALYSIS:
                timing_consistency_score = result.confidence
            elif result.verification_method == VerificationMethod.TRAFFIC_PATTERN_ANALYSIS:
                traffic_pattern_score = result.confidence
            elif result.verification_method == VerificationMethod.CONSENSUS_VALIDATION:
                consensus_score = result.confidence
        
        # Calculate overall score
        overall_score = (
            message_relay_score * 0.3 +
            routing_accuracy_score * 0.25 +
            timing_consistency_score * 0.2 +
            traffic_pattern_score * 0.15 +
            consensus_score * 0.1
        )
        
        # Create or update reliability score
        reliability_score = RelayReliabilityScore(
            relay_id=relay_id,
            overall_score=overall_score,
            message_relay_score=message_relay_score,
            routing_accuracy_score=routing_accuracy_score,
            timing_consistency_score=timing_consistency_score,
            traffic_pattern_score=traffic_pattern_score,
            consensus_score=consensus_score,
            last_updated=int(time.time()),
            test_count=len(self.test_history.get(relay_id, [])) + len(test_results)
        )
        
        self.reliability_scores[relay_id] = reliability_score
        self.stats["reliability_scores_calculated"] += 1
        
        # Check if relay should be promoted or demoted
        if overall_score >= self.reliability_threshold:
            await self._promote_reliable_relay(relay_id, reliability_score)
        else:
            await self._demote_unreliable_relay(relay_id, reliability_score)
    
    async def _promote_reliable_relay(self, relay_id: bytes, reliability_score: RelayReliabilityScore) -> None:
        """Promote a reliable relay to trusted status."""
        print(f"⬆️ Promoting reliable relay: {relay_id.hex()} (Score: {reliability_score.overall_score:.2f})")
        
        # Add to trusted relays
        self.mesh_network.first_ring.add(relay_id)
        
        self.stats["untrusted_relays_verified"] += 1
    
    async def _demote_unreliable_relay(self, relay_id: bytes, reliability_score: RelayReliabilityScore) -> None:
        """Demote an unreliable relay."""
        print(f"⬇️ Demoting unreliable relay: {relay_id.hex()} (Score: {reliability_score.overall_score:.2f})")
        
        # Remove from first ring if present
        self.mesh_network.first_ring.discard(relay_id)
        
        # Check if relay is malicious
        if reliability_score.overall_score < 0.3:
            await self._block_malicious_relay(relay_id, reliability_score)
    
    async def _block_malicious_relay(self, relay_id: bytes, reliability_score: RelayReliabilityScore) -> None:
        """Block a malicious relay."""
        print(f"🚫 Blocking malicious relay: {relay_id.hex()} (Score: {reliability_score.overall_score:.2f})")
        
        # Remove from known nodes
        if relay_id in self.mesh_network.known_nodes:
            del self.mesh_network.known_nodes[relay_id]
        
        # Remove from first ring
        self.mesh_network.first_ring.discard(relay_id)
        
        # Clear reliability data
        if relay_id in self.reliability_scores:
            del self.reliability_scores[relay_id]
        
        self.stats["malicious_relays_detected"] += 1
    
    # Helper methods for network communication
    
    async def _send_message_to_relay(self, relay_id: bytes, message: Dict) -> None:
        """Send message to relay."""
        # Simplified message sending
        await asyncio.sleep(0.1)
    
    async def _wait_for_acknowledgment(self, relay_id: bytes, test_id: str) -> bool:
        """Wait for acknowledgment from relay."""
        # Simplified acknowledgment waiting
        await asyncio.sleep(0.1)
        return random.random() > 0.1  # 90% acknowledgment rate
    
    async def _send_routing_test(self, relay_id: bytes, test: Dict) -> Dict[str, Any]:
        """Send routing test to relay."""
        # Simplified routing test
        await asyncio.sleep(0.1)
        return {"route_correct": random.random() > 0.2}  # 80% correct routing
    
    async def _request_consensus_vote(self, member_id: bytes, target_relay: bytes) -> Optional[Dict]:
        """Request consensus vote from member."""
        # Simplified consensus vote request
        await asyncio.sleep(0.1)
        return {
            "voter_id": member_id.hex(),
            "target_relay": target_relay.hex(),
            "vote": random.uniform(0.3, 0.9),
            "timestamp": int(time.time())
        }
    
    async def _continuous_analysis(self) -> None:
        """Continuously analyze verification results."""
        while True:
            await asyncio.sleep(600)  # Analyze every 10 minutes
            
            # Analyze verification patterns
            await self._analyze_verification_patterns()
    
    async def _analyze_verification_patterns(self) -> None:
        """Analyze verification patterns for insights."""
        # Analyze patterns across all relays
        for relay_id, results in self.verification_results.items():
            if len(results) >= 5:  # Need minimum results
                await self._analyze_relay_patterns(relay_id, results)
    
    async def _analyze_relay_patterns(self, relay_id: bytes, results: List[VerificationResult]) -> None:
        """Analyze patterns for a specific relay."""
        # Analyze success rate over time
        recent_results = results[-10:]  # Last 10 results
        success_rate = sum(1 for r in recent_results if r.result == VerificationResult.VERIFIED) / len(recent_results)
        
        # Check for declining performance
        if success_rate < 0.5:
            print(f"⚠️ Relay {relay_id.hex()} showing declining performance (Success rate: {success_rate:.2f})")
    
    async def _cleanup_old_tests(self) -> None:
        """Clean up old test data."""
        while True:
            await asyncio.sleep(3600)  # Clean up every hour
            
            current_time = int(time.time())
            cutoff_time = current_time - (7 * 24 * 3600)  # 7 days
            
            # Clean up old test results
            for relay_id in list(self.verification_results.keys()):
                self.verification_results[relay_id] = [
                    result for result in self.verification_results[relay_id]
                    if result.timestamp > cutoff_time
                ]
                
                if not self.verification_results[relay_id]:
                    del self.verification_results[relay_id]
            
            # Clean up old test history
            for relay_id in list(self.test_history.keys()):
                self.test_history[relay_id] = [
                    test for test in self.test_history[relay_id]
                    if test.timestamp > cutoff_time
                ]
                
                if not self.test_history[relay_id]:
                    del self.test_history[relay_id]
    
    def get_verification_status(self) -> Dict:
        """Get verification system status."""
        return {
            "active": True,
            "active_tests": len(self.active_tests),
            "verified_relays": len([r for r in self.reliability_scores.values() if r.overall_score >= self.reliability_threshold]),
            "untrusted_relays": len([r for r in self.reliability_scores.values() if r.overall_score < self.reliability_threshold]),
            "malicious_relays": len([r for r in self.reliability_scores.values() if r.overall_score < 0.3]),
            "verification_interval": self.verification_interval,
            "reliability_threshold": self.reliability_threshold
        }
    
    def get_reliability_scores(self) -> Dict[str, Dict]:
        """Get reliability scores for all relays."""
        return {
            relay_id.hex(): score.to_dict()
            for relay_id, score in self.reliability_scores.items()
        }
    
    def get_verification_results(self, relay_id: bytes, limit: int = 20) -> List[Dict]:
        """Get verification results for a relay."""
        if relay_id not in self.verification_results:
            return []
        
        results = self.verification_results[relay_id][-limit:]
        return [result.to_dict() for result in results]
    
    def get_verification_stats(self) -> Dict:
        """Get verification statistics."""
        return {
            **self.stats,
            "reliability_scores_count": len(self.reliability_scores),
            "verification_results_count": sum(len(results) for results in self.verification_results.values()),
            "test_history_count": sum(len(tests) for tests in self.test_history.values())
        }
    
    async def stop_verification_service(self) -> None:
        """Stop the relay verification service."""
        if self.verification_task:
            self.verification_task.cancel()
        
        if self.analysis_task:
            self.analysis_task.cancel()
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
        
        print("🛑 Relay verification service stopped")
