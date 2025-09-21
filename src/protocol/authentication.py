"""
Shared Authentication Protocol for secIRC

This module implements the challenge-response authentication system
used between clients and servers to verify identities and establish
secure communication channels.
"""

import asyncio
import hashlib
import hmac
import secrets
import time
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import struct

from .encryption import EndToEndEncryption
from .message_types import MessageType, Message, HashIdentity


class ChallengeType(Enum):
    """Types of authentication challenges."""
    CRYPTOGRAPHIC = "cryptographic"
    PROOF_OF_WORK = "proof_of_work"
    TIMESTAMP = "timestamp"
    NONCE = "nonce"
    SIGNATURE = "signature"


class AuthenticationStatus(Enum):
    """Authentication status states."""
    PENDING = "pending"
    CHALLENGED = "challenged"
    RESPONDED = "responded"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class AuthenticationChallenge:
    """Represents an authentication challenge."""
    
    challenge_id: bytes
    challenge_type: ChallengeType
    challenge_data: bytes
    timestamp: int
    expires_at: int
    difficulty: int = 1
    nonce: Optional[bytes] = None
    
    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = int(time.time())
        if self.expires_at == 0:
            self.expires_at = self.timestamp + 300  # 5 minutes default
    
    def is_expired(self) -> bool:
        """Check if challenge has expired."""
        return time.time() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "challenge_id": self.challenge_id.hex(),
            "challenge_type": self.challenge_type.value,
            "challenge_data": self.challenge_data.hex(),
            "timestamp": self.timestamp,
            "expires_at": self.expires_at,
            "difficulty": self.difficulty,
            "nonce": self.nonce.hex() if self.nonce else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuthenticationChallenge":
        """Create from dictionary."""
        return cls(
            challenge_id=bytes.fromhex(data["challenge_id"]),
            challenge_type=ChallengeType(data["challenge_type"]),
            challenge_data=bytes.fromhex(data["challenge_data"]),
            timestamp=data["timestamp"],
            expires_at=data["expires_at"],
            difficulty=data.get("difficulty", 1),
            nonce=bytes.fromhex(data["nonce"]) if data.get("nonce") else None
        )


@dataclass
class AuthenticationResponse:
    """Represents an authentication response."""
    
    challenge_id: bytes
    response_data: bytes
    timestamp: int
    signature: Optional[bytes] = None
    proof_of_work: Optional[bytes] = None
    
    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = int(time.time())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "challenge_id": self.challenge_id.hex(),
            "response_data": self.response_data.hex(),
            "timestamp": self.timestamp,
            "signature": self.signature.hex() if self.signature else None,
            "proof_of_work": self.proof_of_work.hex() if self.proof_of_work else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuthenticationResponse":
        """Create from dictionary."""
        return cls(
            challenge_id=bytes.fromhex(data["challenge_id"]),
            response_data=bytes.fromhex(data["response_data"]),
            timestamp=data["timestamp"],
            signature=bytes.fromhex(data["signature"]) if data.get("signature") else None,
            proof_of_work=bytes.fromhex(data["proof_of_work"]) if data.get("proof_of_work") else None
        )


@dataclass
class AuthenticationSession:
    """Represents an authentication session."""
    
    session_id: bytes
    user_id: bytes
    server_id: bytes
    status: AuthenticationStatus
    challenges: List[AuthenticationChallenge]
    responses: List[AuthenticationResponse]
    created_at: int
    last_activity: int
    is_authenticated: bool = False
    session_key: Optional[bytes] = None
    
    def __post_init__(self):
        if self.created_at == 0:
            self.created_at = int(time.time())
        if self.last_activity == 0:
            self.last_activity = self.created_at
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = int(time.time())
    
    def is_expired(self, timeout: int = 3600) -> bool:
        """Check if session has expired."""
        return time.time() - self.last_activity > timeout
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id.hex(),
            "user_id": self.user_id.hex(),
            "server_id": self.server_id.hex(),
            "status": self.status.value,
            "challenges": [c.to_dict() for c in self.challenges],
            "responses": [r.to_dict() for r in self.responses],
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "is_authenticated": self.is_authenticated,
            "session_key": self.session_key.hex() if self.session_key else None
        }


class AuthenticationProtocol:
    """Shared authentication protocol for clients and servers."""
    
    def __init__(self, encryption: EndToEndEncryption):
        self.encryption = encryption
        self.sessions: Dict[bytes, AuthenticationSession] = {}
        self.active_challenges: Dict[bytes, AuthenticationChallenge] = {}
        
        # Configuration
        self.challenge_timeout = 300  # 5 minutes
        self.session_timeout = 3600   # 1 hour
        self.max_challenges = 5
        self.proof_of_work_difficulty = 4
    
    def generate_challenge(self, challenge_type: ChallengeType, 
                          difficulty: int = 1) -> AuthenticationChallenge:
        """Generate a new authentication challenge."""
        challenge_id = secrets.token_bytes(16)
        challenge_data = secrets.token_bytes(32)
        nonce = secrets.token_bytes(16) if challenge_type == ChallengeType.NONCE else None
        
        challenge = AuthenticationChallenge(
            challenge_id=challenge_id,
            challenge_type=challenge_type,
            challenge_data=challenge_data,
            timestamp=int(time.time()),
            expires_at=int(time.time()) + self.challenge_timeout,
            difficulty=difficulty,
            nonce=nonce
        )
        
        self.active_challenges[challenge_id] = challenge
        return challenge
    
    def create_cryptographic_challenge(self, user_public_key: bytes) -> AuthenticationChallenge:
        """Create a cryptographic challenge."""
        challenge = self.generate_challenge(ChallengeType.CRYPTOGRAPHIC)
        
        # Create challenge data that requires the user's private key to solve
        challenge_data = hashlib.sha256(
            challenge.challenge_id + user_public_key + challenge.timestamp.to_bytes(8, 'big')
        ).digest()
        
        challenge.challenge_data = challenge_data
        return challenge
    
    def create_proof_of_work_challenge(self, difficulty: int = None) -> AuthenticationChallenge:
        """Create a proof of work challenge."""
        if difficulty is None:
            difficulty = self.proof_of_work_difficulty
        
        challenge = self.generate_challenge(ChallengeType.PROOF_OF_WORK, difficulty)
        
        # Create challenge data for proof of work
        challenge_data = hashlib.sha256(
            challenge.challenge_id + challenge.timestamp.to_bytes(8, 'big')
        ).digest()
        
        challenge.challenge_data = challenge_data
        return challenge
    
    def create_timestamp_challenge(self) -> AuthenticationChallenge:
        """Create a timestamp-based challenge."""
        challenge = self.generate_challenge(ChallengeType.TIMESTAMP)
        
        # Create challenge data with current timestamp
        current_time = int(time.time())
        challenge_data = current_time.to_bytes(8, 'big')
        
        challenge.challenge_data = challenge_data
        return challenge
    
    def create_nonce_challenge(self) -> AuthenticationChallenge:
        """Create a nonce-based challenge."""
        challenge = self.generate_challenge(ChallengeType.NONCE)
        
        # Nonce is already generated in the challenge
        challenge_data = challenge.nonce
        
        challenge.challenge_data = challenge_data
        return challenge
    
    def verify_cryptographic_response(self, challenge: AuthenticationChallenge,
                                    response: AuthenticationResponse,
                                    user_public_key: bytes) -> bool:
        """Verify a cryptographic challenge response."""
        try:
            # Verify the response was generated with the correct private key
            expected_data = hashlib.sha256(
                challenge.challenge_id + user_public_key + challenge.timestamp.to_bytes(8, 'big')
            ).digest()
            
            # The response should be a signature of the challenge data
            if response.signature:
                # Verify signature using public key
                return self.encryption.verify_signature(
                    challenge.challenge_data, response.signature, user_public_key
                )
            
            return False
            
        except Exception:
            return False
    
    def verify_proof_of_work_response(self, challenge: AuthenticationChallenge,
                                    response: AuthenticationResponse) -> bool:
        """Verify a proof of work challenge response."""
        try:
            # Verify the proof of work
            if not response.proof_of_work:
                return False
            
            # Check if the proof of work meets the difficulty requirement
            combined = challenge.challenge_data + response.proof_of_work
            hash_result = hashlib.sha256(combined).digest()
            
            # Count leading zeros
            leading_zeros = 0
            for byte in hash_result:
                if byte == 0:
                    leading_zeros += 8
                else:
                    leading_zeros += bin(byte)[2:].find('1')
                    break
            
            return leading_zeros >= challenge.difficulty
            
        except Exception:
            return False
    
    def verify_timestamp_response(self, challenge: AuthenticationChallenge,
                                response: AuthenticationResponse) -> bool:
        """Verify a timestamp challenge response."""
        try:
            # Check if response timestamp is within acceptable range
            time_diff = abs(response.timestamp - challenge.timestamp)
            return time_diff <= 30  # 30 seconds tolerance
            
        except Exception:
            return False
    
    def verify_nonce_response(self, challenge: AuthenticationChallenge,
                            response: AuthenticationResponse) -> bool:
        """Verify a nonce challenge response."""
        try:
            # Verify the nonce matches
            return response.response_data == challenge.nonce
            
        except Exception:
            return False
    
    def verify_challenge_response(self, challenge: AuthenticationChallenge,
                                response: AuthenticationResponse,
                                user_public_key: bytes) -> bool:
        """Verify a challenge response based on challenge type."""
        if challenge.is_expired():
            return False
        
        if challenge.challenge_type == ChallengeType.CRYPTOGRAPHIC:
            return self.verify_cryptographic_response(challenge, response, user_public_key)
        elif challenge.challenge_type == ChallengeType.PROOF_OF_WORK:
            return self.verify_proof_of_work_response(challenge, response)
        elif challenge.challenge_type == ChallengeType.TIMESTAMP:
            return self.verify_timestamp_response(challenge, response)
        elif challenge.challenge_type == ChallengeType.NONCE:
            return self.verify_nonce_response(challenge, response)
        else:
            return False
    
    def create_authentication_session(self, user_id: bytes, server_id: bytes) -> AuthenticationSession:
        """Create a new authentication session."""
        session_id = secrets.token_bytes(16)
        
        session = AuthenticationSession(
            session_id=session_id,
            user_id=user_id,
            server_id=server_id,
            status=AuthenticationStatus.PENDING,
            challenges=[],
            responses=[],
            created_at=int(time.time()),
            last_activity=int(time.time())
        )
        
        self.sessions[session_id] = session
        return session
    
    def add_challenge_to_session(self, session_id: bytes, challenge: AuthenticationChallenge) -> bool:
        """Add a challenge to an authentication session."""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        if len(session.challenges) >= self.max_challenges:
            return False
        
        session.challenges.append(challenge)
        session.status = AuthenticationStatus.CHALLENGED
        session.update_activity()
        return True
    
    def add_response_to_session(self, session_id: bytes, response: AuthenticationResponse) -> bool:
        """Add a response to an authentication session."""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        session.responses.append(response)
        session.status = AuthenticationStatus.RESPONDED
        session.update_activity()
        return True
    
    def verify_session(self, session_id: bytes, user_public_key: bytes) -> bool:
        """Verify an authentication session."""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        if session.is_expired(self.session_timeout):
            session.status = AuthenticationStatus.EXPIRED
            return False
        
        # Verify all challenge-response pairs
        if len(session.challenges) != len(session.responses):
            session.status = AuthenticationStatus.FAILED
            return False
        
        for challenge, response in zip(session.challenges, session.responses):
            if not self.verify_challenge_response(challenge, response, user_public_key):
                session.status = AuthenticationStatus.FAILED
                return False
        
        # Session is verified
        session.status = AuthenticationStatus.VERIFIED
        session.is_authenticated = True
        session.session_key = secrets.token_bytes(32)  # Generate session key
        session.update_activity()
        
        # Clean up challenges
        for challenge in session.challenges:
            if challenge.challenge_id in self.active_challenges:
                del self.active_challenges[challenge.challenge_id]
        
        return True
    
    def get_session(self, session_id: bytes) -> Optional[AuthenticationSession]:
        """Get an authentication session."""
        return self.sessions.get(session_id)
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions and challenges."""
        current_time = time.time()
        expired_sessions = []
        expired_challenges = []
        
        # Find expired sessions
        for session_id, session in self.sessions.items():
            if session.is_expired(self.session_timeout):
                expired_sessions.append(session_id)
        
        # Find expired challenges
        for challenge_id, challenge in self.active_challenges.items():
            if challenge.is_expired():
                expired_challenges.append(challenge_id)
        
        # Remove expired sessions
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        # Remove expired challenges
        for challenge_id in expired_challenges:
            del self.active_challenges[challenge_id]
        
        return len(expired_sessions) + len(expired_challenges)
    
    def get_authentication_status(self) -> Dict[str, Any]:
        """Get authentication system status."""
        return {
            "active_sessions": len(self.sessions),
            "active_challenges": len(self.active_challenges),
            "authenticated_sessions": len([s for s in self.sessions.values() if s.is_authenticated]),
            "pending_sessions": len([s for s in self.sessions.values() if s.status == AuthenticationStatus.PENDING]),
            "challenged_sessions": len([s for s in self.sessions.values() if s.status == AuthenticationStatus.CHALLENGED]),
            "verified_sessions": len([s for s in self.sessions.values() if s.status == AuthenticationStatus.VERIFIED]),
            "failed_sessions": len([s for s in self.sessions.values() if s.status == AuthenticationStatus.FAILED]),
            "expired_sessions": len([s for s in self.sessions.values() if s.status == AuthenticationStatus.EXPIRED])
        }
