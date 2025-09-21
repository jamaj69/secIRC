"""
secIRC Protocol Module

Anonymous, censorship-resistant messaging protocol using UDP.
Implements end-to-end encryption with relay servers that don't store metadata.
All entities are identified by cryptographic hashes for complete anonymity.
"""

from .anonymous_protocol import AnonymousProtocol
from .message_types import MessageType, Message, UserIdentity, HashIdentity
from .encryption import EndToEndEncryption
from .relay_discovery import RelayDiscovery
from .relay_sync import RelaySyncProtocol, GroupInfo
from .group_management import GroupManager, GroupMessage
from .hash_identity_system import HashIdentitySystem, IdentityRegistry
from .mesh_network import MeshNetwork, Challenge, ChallengeResponse, RelayNode
from .ring_management import FirstRingManager, RingMember, RingConsensus
from .ring_expansion import RingExpansionManager, ExpansionCandidate, ExpansionPlan
from .key_rotation import KeyRotationManager, KeyRotationMessage, KeyRotationSession
from .salt_protection import SaltProtectionSystem, SaltedMessage, SaltType
from .anti_mitm import AntiMITMProtection, SecurityEvent, AttackType, ThreatLevel
from .relay_authentication import RelayAuthenticationSystem, AuthenticationChallenge, AuthenticationResult
from .network_monitoring import NetworkMonitoringSystem, AnomalyDetection, AnomalyType
from .trust_system import TrustSystem, TrustScore, ReputationEvent, ConsensusVote
from .relay_verification import RelayVerificationSystem, VerificationTest, VerificationResult, RelayReliabilityScore
from .torrent_discovery import TorrentDiscoverySystem, RelayAnnouncement, DHTNode, TrackerResponse, DiscoveryResult
from .pubsub_server import PubSubServer, GroupKey, GroupMessage, GroupSubscription, PubSubEvent
from .group_encryption import GroupEncryptionSystem, GroupKeyMaterial, EncryptedGroupMessage, GroupKeyDistribution
from .decentralized_groups import DecentralizedGroupManager, DecentralizedGroup, GroupMember, GroupRole, GroupStatus
from .relay_connections import RelayConnectionManager, ConnectionConfig, ConnectionType, ConnectionStatus, RelayConnection
from .tor_integration import TorIntegration, TorConfig, TorMethod, TorConnection

__all__ = [
    "AnonymousProtocol",
    "MessageType", 
    "Message",
    "UserIdentity",
    "HashIdentity",
    "EndToEndEncryption",
    "RelayDiscovery",
    "RelaySyncProtocol",
    "GroupInfo",
    "GroupManager",
    "GroupMessage",
    "HashIdentitySystem",
    "IdentityRegistry",
    "MeshNetwork",
    "Challenge",
    "ChallengeResponse", 
    "RelayNode",
    "FirstRingManager",
    "RingMember",
    "RingConsensus",
    "RingExpansionManager",
    "ExpansionCandidate",
    "ExpansionPlan",
    "KeyRotationManager",
    "KeyRotationMessage",
    "KeyRotationSession",
    "SaltProtectionSystem",
    "SaltedMessage",
    "SaltType",
    "AntiMITMProtection",
    "SecurityEvent",
    "AttackType",
    "ThreatLevel",
    "RelayAuthenticationSystem",
    "AuthenticationChallenge",
    "AuthenticationResult",
    "NetworkMonitoringSystem",
    "AnomalyDetection",
    "AnomalyType",
    "TrustSystem",
    "TrustScore",
    "ReputationEvent",
    "ConsensusVote",
    "RelayVerificationSystem",
    "VerificationTest",
    "VerificationResult",
    "RelayReliabilityScore",
    "TorrentDiscoverySystem",
    "RelayAnnouncement",
    "DHTNode",
    "TrackerResponse",
    "DiscoveryResult",
    "PubSubServer",
    "GroupKey",
    "GroupMessage",
    "GroupSubscription",
    "PubSubEvent",
    "GroupEncryptionSystem",
    "GroupKeyMaterial",
    "EncryptedGroupMessage",
    "GroupKeyDistribution",
    "DecentralizedGroupManager",
    "DecentralizedGroup",
    "GroupMember",
    "GroupRole",
    "GroupStatus",
    "RelayConnectionManager",
    "ConnectionConfig",
    "ConnectionType",
    "ConnectionStatus",
    "RelayConnection",
    "TorIntegration",
    "TorConfig",
    "TorMethod",
    "TorConnection"
]