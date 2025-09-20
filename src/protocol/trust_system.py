"""
Trust and Reputation System.
Implements comprehensive trust mechanisms to prevent malicious relay infiltration.
"""

import asyncio
import hashlib
import json
import os
import time
import statistics
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque

from .encryption import EndToEndEncryption
from .mesh_network import MeshNetwork, RelayNode


class TrustLevel(Enum):
    """Trust levels for relays."""
    
    UNTRUSTED = "untrusted"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReputationEvent(Enum):
    """Types of reputation events."""
    
    MESSAGE_RELAYED = "message_relayed"
    MESSAGE_FAILED = "message_failed"
    AUTHENTICATION_SUCCESS = "authentication_success"
    AUTHENTICATION_FAILED = "authentication_failed"
    ANOMALY_DETECTED = "anomaly_detected"
    GOOD_BEHAVIOR = "good_behavior"
    BAD_BEHAVIOR = "bad_behavior"
    CONSENSUS_VOTE = "consensus_vote"


@dataclass
class TrustScore:
    """Trust score for a relay."""
    
    relay_id: bytes
    overall_score: float
    reputation_score: float
    behavior_score: float
    consensus_score: float
    recency_score: float
    last_updated: int
    confidence: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "relay_id": self.relay_id.hex(),
            "overall_score": self.overall_score,
            "reputation_score": self.reputation_score,
            "behavior_score": self.behavior_score,
            "consensus_score": self.consensus_score,
            "recency_score": self.recency_score,
            "last_updated": self.last_updated,
            "confidence": self.confidence
        }


@dataclass
class ReputationEvent:
    """Reputation event for trust calculation."""
    
    event_id: bytes
    relay_id: bytes
    event_type: ReputationEvent
    score_change: float
    timestamp: int
    source_id: bytes
    evidence: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "event_id": self.event_id.hex(),
            "relay_id": self.relay_id.hex(),
            "event_type": self.event_type.value,
            "score_change": self.score_change,
            "timestamp": self.timestamp,
            "source_id": self.source_id.hex(),
            "evidence": self.evidence
        }


@dataclass
class ConsensusVote:
    """Consensus vote for relay reputation."""
    
    voter_id: bytes
    target_relay_id: bytes
    vote: float  # -1.0 to 1.0
    timestamp: int
    reason: str
    evidence: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "voter_id": self.voter_id.hex(),
            "target_relay_id": self.target_relay_id.hex(),
            "vote": self.vote,
            "timestamp": self.timestamp,
            "reason": self.reason,
            "evidence": self.evidence
        }


class TrustSystem:
    """Comprehensive trust and reputation system."""
    
    def __init__(self, mesh_network: MeshNetwork):
        self.mesh_network = mesh_network
        self.encryption = EndToEndEncryption()
        
        # Trust data
        self.trust_scores: Dict[bytes, TrustScore] = {}
        self.reputation_events: Dict[bytes, List[ReputationEvent]] = defaultdict(list)
        self.consensus_votes: Dict[bytes, List[ConsensusVote]] = defaultdict(list)
        self.behavior_history: Dict[bytes, List[Dict]] = defaultdict(list)
        
        # Trust configuration
        self.reputation_weight = 0.3  # Weight of reputation in trust calculation
        self.behavior_weight = 0.4    # Weight of behavior in trust calculation
        self.consensus_weight = 0.2   # Weight of consensus in trust calculation
        self.recency_weight = 0.1     # Weight of recency in trust calculation
        
        # Trust thresholds
        self.trust_thresholds = {
            TrustLevel.UNTRUSTED: 0.0,
            TrustLevel.LOW: 0.2,
            TrustLevel.MEDIUM: 0.4,
            TrustLevel.HIGH: 0.7,
            TrustLevel.CRITICAL: 0.9
        }
        
        # Event weights
        self.event_weights = {
            ReputationEvent.MESSAGE_RELAYED: 0.1,
            ReputationEvent.MESSAGE_FAILED: -0.2,
            ReputationEvent.AUTHENTICATION_SUCCESS: 0.3,
            ReputationEvent.AUTHENTICATION_FAILED: -0.5,
            ReputationEvent.ANOMALY_DETECTED: -0.4,
            ReputationEvent.GOOD_BEHAVIOR: 0.2,
            ReputationEvent.BAD_BEHAVIOR: -0.3,
            ReputationEvent.CONSENSUS_VOTE: 0.1
        }
        
        # Decay parameters
        self.reputation_decay_rate = 0.01  # Per day
        self.behavior_decay_rate = 0.02    # Per day
        self.consensus_decay_rate = 0.005  # Per day
        
        # Statistics
        self.stats = {
            "trust_scores_calculated": 0,
            "reputation_events_processed": 0,
            "consensus_votes_collected": 0,
            "trust_level_changes": 0,
            "malicious_relays_detected": 0
        }
        
        # Background tasks
        self.trust_calculation_task: Optional[asyncio.Task] = None
        self.consensus_task: Optional[asyncio.Task] = None
        self.decay_task: Optional[asyncio.Task] = None
    
    async def start_trust_service(self) -> None:
        """Start the trust and reputation service."""
        print("🤝 Starting trust and reputation service...")
        
        # Initialize trust scores for first ring members
        await self._initialize_first_ring_trust()
        
        # Start background tasks
        self.trust_calculation_task = asyncio.create_task(self._continuous_trust_calculation())
        self.consensus_task = asyncio.create_task(self._collect_consensus_votes())
        self.decay_task = asyncio.create_task(self._apply_trust_decay())
        
        print("✅ Trust and reputation service started")
    
    async def _initialize_first_ring_trust(self) -> None:
        """Initialize trust scores for first ring members."""
        for member_id in self.mesh_network.first_ring:
            if member_id != self.mesh_network.node_id:
                # Create high trust score for first ring members
                trust_score = TrustScore(
                    relay_id=member_id,
                    overall_score=1.0,
                    reputation_score=1.0,
                    behavior_score=1.0,
                    consensus_score=1.0,
                    recency_score=1.0,
                    last_updated=int(time.time()),
                    confidence=1.0
                )
                self.trust_scores[member_id] = trust_score
    
    async def _continuous_trust_calculation(self) -> None:
        """Continuously calculate and update trust scores."""
        while True:
            await asyncio.sleep(60)  # Calculate every minute
            
            # Update trust scores for all known relays
            for relay_id in self.mesh_network.known_nodes:
                if relay_id != self.mesh_network.node_id:
                    await self._calculate_trust_score(relay_id)
            
            self.stats["trust_scores_calculated"] += 1
    
    async def _collect_consensus_votes(self) -> None:
        """Collect consensus votes from other trusted relays."""
        while True:
            await asyncio.sleep(300)  # Collect every 5 minutes
            
            # Request consensus votes from first ring members
            for member_id in self.mesh_network.first_ring:
                if member_id != self.mesh_network.node_id:
                    await self._request_consensus_votes(member_id)
    
    async def _apply_trust_decay(self) -> None:
        """Apply trust decay over time."""
        while True:
            await asyncio.sleep(3600)  # Apply decay every hour
            
            current_time = int(time.time())
            
            for relay_id, trust_score in self.trust_scores.items():
                # Apply decay based on time since last update
                time_since_update = current_time - trust_score.last_updated
                decay_factor = 1.0 - (self.reputation_decay_rate * time_since_update / 86400)  # Per day
                
                # Apply decay to scores
                trust_score.reputation_score *= decay_factor
                trust_score.behavior_score *= decay_factor
                trust_score.consensus_score *= decay_factor
                trust_score.recency_score *= decay_factor
                
                # Recalculate overall score
                trust_score.overall_score = await self._calculate_overall_trust_score(trust_score)
                trust_score.last_updated = current_time
    
    async def record_reputation_event(self, relay_id: bytes, event_type: ReputationEvent, 
                                    evidence: Dict[str, Any], source_id: Optional[bytes] = None) -> None:
        """Record a reputation event for a relay."""
        if source_id is None:
            source_id = self.mesh_network.node_id
        
        # Create reputation event
        event = ReputationEvent(
            event_id=os.urandom(16),
            relay_id=relay_id,
            event_type=event_type,
            score_change=self.event_weights.get(event_type, 0.0),
            timestamp=int(time.time()),
            source_id=source_id,
            evidence=evidence
        )
        
        # Store event
        self.reputation_events[relay_id].append(event)
        
        # Keep only recent events (last 30 days)
        cutoff_time = int(time.time()) - (30 * 24 * 3600)
        self.reputation_events[relay_id] = [
            e for e in self.reputation_events[relay_id]
            if e.timestamp > cutoff_time
        ]
        
        self.stats["reputation_events_processed"] += 1
        
        # Immediately update trust score
        await self._calculate_trust_score(relay_id)
        
        print(f"📊 Recorded reputation event: {event_type.value} for {relay_id.hex()}")
    
    async def submit_consensus_vote(self, target_relay_id: bytes, vote: float, 
                                  reason: str, evidence: Dict[str, Any]) -> None:
        """Submit a consensus vote for a relay."""
        # Create consensus vote
        consensus_vote = ConsensusVote(
            voter_id=self.mesh_network.node_id,
            target_relay_id=target_relay_id,
            vote=max(-1.0, min(1.0, vote)),  # Clamp between -1 and 1
            timestamp=int(time.time()),
            reason=reason,
            evidence=evidence
        )
        
        # Store vote
        self.consensus_votes[target_relay_id].append(consensus_vote)
        
        # Keep only recent votes (last 7 days)
        cutoff_time = int(time.time()) - (7 * 24 * 3600)
        self.consensus_votes[target_relay_id] = [
            v for v in self.consensus_votes[target_relay_id]
            if v.timestamp > cutoff_time
        ]
        
        self.stats["consensus_votes_collected"] += 1
        
        # Update trust score
        await self._calculate_trust_score(target_relay_id)
        
        print(f"🗳️ Submitted consensus vote: {vote:.2f} for {target_relay_id.hex()}")
    
    async def _calculate_trust_score(self, relay_id: bytes) -> None:
        """Calculate comprehensive trust score for a relay."""
        try:
            # Calculate component scores
            reputation_score = await self._calculate_reputation_score(relay_id)
            behavior_score = await self._calculate_behavior_score(relay_id)
            consensus_score = await self._calculate_consensus_score(relay_id)
            recency_score = await self._calculate_recency_score(relay_id)
            
            # Calculate overall score
            overall_score = (
                reputation_score * self.reputation_weight +
                behavior_score * self.behavior_weight +
                consensus_score * self.consensus_weight +
                recency_score * self.recency_weight
            )
            
            # Calculate confidence
            confidence = await self._calculate_confidence(relay_id)
            
            # Create or update trust score
            trust_score = TrustScore(
                relay_id=relay_id,
                overall_score=max(0.0, min(1.0, overall_score)),
                reputation_score=max(0.0, min(1.0, reputation_score)),
                behavior_score=max(0.0, min(1.0, behavior_score)),
                consensus_score=max(0.0, min(1.0, consensus_score)),
                recency_score=max(0.0, min(1.0, recency_score)),
                last_updated=int(time.time()),
                confidence=max(0.0, min(1.0, confidence))
            )
            
            # Check for trust level change
            old_level = self._get_trust_level(relay_id)
            self.trust_scores[relay_id] = trust_score
            new_level = self._get_trust_level(relay_id)
            
            if old_level != new_level:
                self.stats["trust_level_changes"] += 1
                print(f"🔄 Trust level changed for {relay_id.hex()}: {old_level.value} -> {new_level.value}")
                
                # Handle trust level change
                await self._handle_trust_level_change(relay_id, old_level, new_level)
            
        except Exception as e:
            print(f"Error calculating trust score for {relay_id.hex()}: {e}")
    
    async def _calculate_reputation_score(self, relay_id: bytes) -> float:
        """Calculate reputation score based on events."""
        if relay_id not in self.reputation_events:
            return 0.5  # Neutral score
        
        events = self.reputation_events[relay_id]
        if not events:
            return 0.5  # Neutral score
        
        # Calculate weighted score
        total_score = 0.0
        total_weight = 0.0
        
        current_time = int(time.time())
        
        for event in events:
            # Weight by recency (more recent events have higher weight)
            age_days = (current_time - event.timestamp) / 86400
            recency_weight = max(0.1, 1.0 - (age_days / 30))  # Decay over 30 days
            
            total_score += event.score_change * recency_weight
            total_weight += recency_weight
        
        if total_weight == 0:
            return 0.5
        
        # Normalize to 0-1 range
        normalized_score = (total_score / total_weight + 1.0) / 2.0
        return max(0.0, min(1.0, normalized_score))
    
    async def _calculate_behavior_score(self, relay_id: bytes) -> float:
        """Calculate behavior score based on network behavior."""
        if relay_id not in self.behavior_history:
            return 0.5  # Neutral score
        
        behaviors = self.behavior_history[relay_id]
        if not behaviors:
            return 0.5  # Neutral score
        
        # Analyze recent behaviors
        current_time = int(time.time())
        recent_behaviors = [
            b for b in behaviors
            if current_time - b["timestamp"] < 86400  # Last 24 hours
        ]
        
        if not recent_behaviors:
            return 0.5
        
        # Calculate behavior score based on various metrics
        behavior_score = 0.0
        
        # Response time score
        response_times = [b.get("response_time", 1000) for b in recent_behaviors]
        avg_response_time = statistics.mean(response_times)
        response_score = max(0.0, 1.0 - (avg_response_time / 5000))  # 5 second threshold
        behavior_score += response_score * 0.3
        
        # Success rate score
        success_count = sum(1 for b in recent_behaviors if b.get("success", False))
        success_rate = success_count / len(recent_behaviors)
        behavior_score += success_rate * 0.4
        
        # Protocol compliance score
        compliance_count = sum(1 for b in recent_behaviors if b.get("protocol_compliant", True))
        compliance_rate = compliance_count / len(recent_behaviors)
        behavior_score += compliance_rate * 0.3
        
        return max(0.0, min(1.0, behavior_score))
    
    async def _calculate_consensus_score(self, relay_id: bytes) -> float:
        """Calculate consensus score based on votes from other relays."""
        if relay_id not in self.consensus_votes:
            return 0.5  # Neutral score
        
        votes = self.consensus_votes[relay_id]
        if not votes:
            return 0.5  # Neutral score
        
        # Calculate weighted average vote
        total_vote = 0.0
        total_weight = 0.0
        
        current_time = int(time.time())
        
        for vote in votes:
            # Weight by voter trust and recency
            voter_trust = self.trust_scores.get(vote.voter_id, TrustScore(
                relay_id=vote.voter_id,
                overall_score=0.5,
                reputation_score=0.5,
                behavior_score=0.5,
                consensus_score=0.5,
                recency_score=0.5,
                last_updated=current_time,
                confidence=0.5
            )).overall_score
            
            age_days = (current_time - vote.timestamp) / 86400
            recency_weight = max(0.1, 1.0 - (age_days / 7))  # Decay over 7 days
            
            weight = voter_trust * recency_weight
            
            total_vote += vote.vote * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.5
        
        # Normalize to 0-1 range
        normalized_score = (total_vote / total_weight + 1.0) / 2.0
        return max(0.0, min(1.0, normalized_score))
    
    async def _calculate_recency_score(self, relay_id: bytes) -> float:
        """Calculate recency score based on recent activity."""
        if relay_id not in self.reputation_events:
            return 0.0  # No activity
        
        events = self.reputation_events[relay_id]
        if not events:
            return 0.0
        
        # Get most recent event
        most_recent_event = max(events, key=lambda e: e.timestamp)
        current_time = int(time.time())
        
        # Calculate recency score (higher for more recent activity)
        age_hours = (current_time - most_recent_event.timestamp) / 3600
        
        if age_hours < 1:
            return 1.0
        elif age_hours < 24:
            return 0.8
        elif age_hours < 168:  # 1 week
            return 0.6
        elif age_hours < 720:  # 1 month
            return 0.4
        else:
            return 0.2
    
    async def _calculate_confidence(self, relay_id: bytes) -> float:
        """Calculate confidence in trust score."""
        confidence = 0.0
        
        # Base confidence on amount of data
        event_count = len(self.reputation_events.get(relay_id, []))
        vote_count = len(self.consensus_votes.get(relay_id, []))
        behavior_count = len(self.behavior_history.get(relay_id, []))
        
        # More data = higher confidence
        data_confidence = min(1.0, (event_count + vote_count + behavior_count) / 100)
        confidence += data_confidence * 0.4
        
        # Consensus agreement = higher confidence
        if relay_id in self.consensus_votes and self.consensus_votes[relay_id]:
            votes = [v.vote for v in self.consensus_votes[relay_id]]
            if len(votes) > 1:
                vote_variance = statistics.variance(votes)
                agreement_confidence = max(0.0, 1.0 - vote_variance)
                confidence += agreement_confidence * 0.3
        
        # Consistency = higher confidence
        if relay_id in self.reputation_events and len(self.reputation_events[relay_id]) > 5:
            recent_events = self.reputation_events[relay_id][-10:]
            positive_events = sum(1 for e in recent_events if e.score_change > 0)
            consistency = abs(positive_events / len(recent_events) - 0.5) * 2  # 0-1 scale
            confidence += consistency * 0.3
        
        return max(0.0, min(1.0, confidence))
    
    async def _calculate_overall_trust_score(self, trust_score: TrustScore) -> float:
        """Calculate overall trust score from components."""
        return (
            trust_score.reputation_score * self.reputation_weight +
            trust_score.behavior_score * self.behavior_weight +
            trust_score.consensus_score * self.consensus_weight +
            trust_score.recency_score * self.recency_weight
        )
    
    def _get_trust_level(self, relay_id: bytes) -> TrustLevel:
        """Get trust level for a relay."""
        if relay_id not in self.trust_scores:
            return TrustLevel.UNTRUSTED
        
        score = self.trust_scores[relay_id].overall_score
        
        if score >= self.trust_thresholds[TrustLevel.CRITICAL]:
            return TrustLevel.CRITICAL
        elif score >= self.trust_thresholds[TrustLevel.HIGH]:
            return TrustLevel.HIGH
        elif score >= self.trust_thresholds[TrustLevel.MEDIUM]:
            return TrustLevel.MEDIUM
        elif score >= self.trust_thresholds[TrustLevel.LOW]:
            return TrustLevel.LOW
        else:
            return TrustLevel.UNTRUSTED
    
    async def _handle_trust_level_change(self, relay_id: bytes, old_level: TrustLevel, new_level: TrustLevel) -> None:
        """Handle trust level change."""
        if new_level == TrustLevel.UNTRUSTED:
            # Block untrusted relay
            await self._block_untrusted_relay(relay_id)
        elif new_level in [TrustLevel.CRITICAL, TrustLevel.HIGH]:
            # Promote to trusted status
            await self._promote_trusted_relay(relay_id)
        elif old_level in [TrustLevel.CRITICAL, TrustLevel.HIGH] and new_level in [TrustLevel.MEDIUM, TrustLevel.LOW]:
            # Demote from trusted status
            await self._demote_trusted_relay(relay_id)
    
    async def _block_untrusted_relay(self, relay_id: bytes) -> None:
        """Block an untrusted relay."""
        # Remove from known nodes
        if relay_id in self.mesh_network.known_nodes:
            del self.mesh_network.known_nodes[relay_id]
        
        # Remove from first ring if present
        self.mesh_network.first_ring.discard(relay_id)
        
        # Clear trust data
        if relay_id in self.trust_scores:
            del self.trust_scores[relay_id]
        
        self.stats["malicious_relays_detected"] += 1
        
        print(f"🚫 Blocked untrusted relay: {relay_id.hex()}")
    
    async def _promote_trusted_relay(self, relay_id: bytes) -> None:
        """Promote a relay to trusted status."""
        print(f"⬆️ Promoted relay to trusted: {relay_id.hex()}")
        # Implementation would add to trusted relay list
    
    async def _demote_trusted_relay(self, relay_id: bytes) -> None:
        """Demote a relay from trusted status."""
        print(f"⬇️ Demoted relay from trusted: {relay_id.hex()}")
        # Implementation would remove from trusted relay list
    
    async def _request_consensus_votes(self, member_id: bytes) -> None:
        """Request consensus votes from a first ring member."""
        try:
            # Send consensus request
            request_message = {
                "type": "consensus_request",
                "timestamp": int(time.time())
            }
            
            # Send request (simplified)
            await asyncio.sleep(0.1)  # Simulate network delay
            
        except Exception as e:
            print(f"Error requesting consensus votes from {member_id.hex()}: {e}")
    
    def get_trust_score(self, relay_id: bytes) -> Optional[TrustScore]:
        """Get trust score for a relay."""
        return self.trust_scores.get(relay_id)
    
    def get_trust_level(self, relay_id: bytes) -> TrustLevel:
        """Get trust level for a relay."""
        return self._get_trust_level(relay_id)
    
    def get_trusted_relays(self) -> List[bytes]:
        """Get list of trusted relays."""
        return [
            relay_id for relay_id, trust_score in self.trust_scores.items()
            if trust_score.overall_score >= self.trust_thresholds[TrustLevel.HIGH]
        ]
    
    def get_untrusted_relays(self) -> List[bytes]:
        """Get list of untrusted relays."""
        return [
            relay_id for relay_id, trust_score in self.trust_scores.items()
            if trust_score.overall_score < self.trust_thresholds[TrustLevel.LOW]
        ]
    
    def get_trust_status(self) -> Dict:
        """Get trust system status."""
        return {
            "active": True,
            "trusted_relays": len(self.get_trusted_relays()),
            "untrusted_relays": len(self.get_untrusted_relays()),
            "total_relays": len(self.trust_scores),
            "reputation_events": sum(len(events) for events in self.reputation_events.values()),
            "consensus_votes": sum(len(votes) for votes in self.consensus_votes.values())
        }
    
    def get_trust_scores(self) -> Dict[str, Dict]:
        """Get all trust scores."""
        return {
            relay_id.hex(): trust_score.to_dict()
            for relay_id, trust_score in self.trust_scores.items()
        }
    
    def get_reputation_events(self, relay_id: bytes, limit: int = 50) -> List[Dict]:
        """Get reputation events for a relay."""
        if relay_id not in self.reputation_events:
            return []
        
        events = self.reputation_events[relay_id][-limit:]
        return [event.to_dict() for event in events]
    
    def get_consensus_votes(self, relay_id: bytes, limit: int = 20) -> List[Dict]:
        """Get consensus votes for a relay."""
        if relay_id not in self.consensus_votes:
            return []
        
        votes = self.consensus_votes[relay_id][-limit:]
        return [vote.to_dict() for vote in votes]
    
    def get_trust_stats(self) -> Dict:
        """Get trust system statistics."""
        return {
            **self.stats,
            "trust_scores_count": len(self.trust_scores),
            "reputation_events_count": sum(len(events) for events in self.reputation_events.values()),
            "consensus_votes_count": sum(len(votes) for votes in self.consensus_votes.values()),
            "behavior_history_count": sum(len(behaviors) for behaviors in self.behavior_history.values())
        }
    
    async def stop_trust_service(self) -> None:
        """Stop the trust and reputation service."""
        if self.trust_calculation_task:
            self.trust_calculation_task.cancel()
        
        if self.consensus_task:
            self.consensus_task.cancel()
        
        if self.decay_task:
            self.decay_task.cancel()
        
        print("🛑 Trust and reputation service stopped")
