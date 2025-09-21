"""
secIRC Client Implementation

This module implements the secIRC client that handles user authentication,
message sending/receiving, and communication with relay servers.
"""

import asyncio
import hashlib
import json
import logging
import time
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from pathlib import Path

from ..protocol.authentication import (
    AuthenticationProtocol, AuthenticationSession, AuthenticationStatus,
    ChallengeType, AuthenticationChallenge, AuthenticationResponse
)
from ..protocol.user_status import (
    UserStatusManager, UserPresence, UserStatus, MessageDeliveryManager,
    PendingMessage, MessageDeliveryStatus
)
from ..protocol.encryption import EndToEndEncryption
from ..protocol.message_types import MessageType, Message, HashIdentity
from ..protocol.relay_connections import RelayConnectionManager, ConnectionConfig, ConnectionType


@dataclass
class ClientConfig:
    """Configuration for secIRC client."""
    
    # Server connection
    server_host: str = "127.0.0.1"
    server_port: int = 6667
    server_ssl: bool = True
    
    # Authentication
    max_auth_attempts: int = 3
    auth_timeout: int = 30
    
    # Message handling
    message_retry_attempts: int = 3
    message_timeout: int = 30
    
    # User settings
    nickname: str = ""
    status_message: str = ""
    auto_away_timeout: int = 900  # 15 minutes
    
    # Storage
    data_dir: str = "data/client"
    keys_file: str = "user_keys.json"
    contacts_file: str = "contacts.json"
    messages_file: str = "messages.json"


class SecIRCClient:
    """Main secIRC client implementation."""
    
    def __init__(self, config: ClientConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.encryption = EndToEndEncryption()
        self.auth_protocol = AuthenticationProtocol(self.encryption)
        self.connection_manager = None
        
        # User identity
        self.user_id: Optional[bytes] = None
        self.public_key: Optional[bytes] = None
        self.private_key: Optional[bytes] = None
        self.nickname: str = config.nickname
        
        # Authentication state
        self.auth_session: Optional[AuthenticationSession] = None
        self.is_authenticated: bool = False
        self.server_connection = None
        
        # User status
        self.user_status = UserStatus.OFFLINE
        self.status_message = config.status_message
        self.last_activity = 0
        
        # Message handling
        self.received_messages: List[Message] = []
        self.sent_messages: List[Message] = []
        self.contacts: Dict[bytes, Dict[str, Any]] = {}
        
        # Background tasks
        self.background_tasks: List[asyncio.Task] = []
        
        # Create data directory
        Path(self.config.data_dir).mkdir(parents=True, exist_ok=True)
    
    async def initialize(self) -> bool:
        """Initialize the client."""
        try:
            self.logger.info("Initializing secIRC client...")
            
            # Load or generate user keys
            if not await self._load_user_keys():
                if not await self._generate_user_keys():
                    return False
            
            # Load contacts
            await self._load_contacts()
            
            # Initialize connection manager
            connection_config = ConnectionConfig(
                max_connections=5,
                min_connections=1,
                enable_tcp=True,
                enable_tor=True,
                enable_websocket=True,
                ssl_enabled=self.config.server_ssl
            )
            
            self.connection_manager = RelayConnectionManager(connection_config, self.encryption)
            await self.connection_manager.start_connection_manager()
            
            self.logger.info("secIRC client initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize client: {e}")
            return False
    
    async def _load_user_keys(self) -> bool:
        """Load user keys from storage."""
        try:
            keys_file = Path(self.config.data_dir) / self.config.keys_file
            if not keys_file.exists():
                return False
            
            with open(keys_file, 'r') as f:
                keys_data = json.load(f)
            
            self.user_id = bytes.fromhex(keys_data["user_id"])
            self.public_key = bytes.fromhex(keys_data["public_key"])
            self.private_key = bytes.fromhex(keys_data["private_key"])
            self.nickname = keys_data.get("nickname", self.nickname)
            
            self.logger.info(f"Loaded user keys for {self.nickname}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load user keys: {e}")
            return False
    
    async def _generate_user_keys(self) -> bool:
        """Generate new user keys."""
        try:
            # Generate key pair
            self.public_key, self.private_key = self.encryption.generate_keypair()
            
            # Generate user ID from public key
            self.user_id = hashlib.sha256(self.public_key).digest()[:16]
            
            # Save keys
            keys_data = {
                "user_id": self.user_id.hex(),
                "public_key": self.public_key.hex(),
                "private_key": self.private_key.hex(),
                "nickname": self.nickname,
                "created_at": int(time.time())
            }
            
            keys_file = Path(self.config.data_dir) / self.config.keys_file
            with open(keys_file, 'w') as f:
                json.dump(keys_data, f, indent=2)
            
            self.logger.info(f"Generated new user keys for {self.nickname}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate user keys: {e}")
            return False
    
    async def _load_contacts(self) -> None:
        """Load contacts from storage."""
        try:
            contacts_file = Path(self.config.data_dir) / self.config.contacts_file
            if not contacts_file.exists():
                return
            
            with open(contacts_file, 'r') as f:
                self.contacts = json.load(f)
            
            # Convert hex strings back to bytes
            for user_id_hex, contact_data in self.contacts.items():
                if "public_key" in contact_data:
                    contact_data["public_key"] = bytes.fromhex(contact_data["public_key"])
            
            self.logger.info(f"Loaded {len(self.contacts)} contacts")
            
        except Exception as e:
            self.logger.error(f"Failed to load contacts: {e}")
    
    async def _save_contacts(self) -> None:
        """Save contacts to storage."""
        try:
            # Convert bytes to hex strings for JSON serialization
            contacts_data = {}
            for user_id_hex, contact_data in self.contacts.items():
                contact_copy = contact_data.copy()
                if "public_key" in contact_copy:
                    contact_copy["public_key"] = contact_copy["public_key"].hex()
                contacts_data[user_id_hex] = contact_copy
            
            contacts_file = Path(self.config.data_dir) / self.config.contacts_file
            with open(contacts_file, 'w') as f:
                json.dump(contacts_data, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Failed to save contacts: {e}")
    
    async def login(self, password: str = None) -> bool:
        """Login to the secIRC network."""
        try:
            self.logger.info(f"Logging in user {self.nickname}...")
            
            # Connect to server
            if not await self._connect_to_server():
                return False
            
            # Start authentication process
            if not await self._start_authentication():
                return False
            
            # Handle authentication challenges
            if not await self._handle_authentication_challenges():
                return False
            
            # Complete authentication
            if not await self._complete_authentication():
                return False
            
            # Set user online
            await self._set_user_online()
            
            # Start background tasks
            await self._start_background_tasks()
            
            self.is_authenticated = True
            self.user_status = UserStatus.ONLINE
            self.last_activity = int(time.time())
            
            self.logger.info(f"Successfully logged in as {self.nickname}")
            return True
            
        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            return False
    
    async def _connect_to_server(self) -> bool:
        """Connect to the relay server."""
        try:
            # Add server connection
            server_id = b"main_server"  # In real implementation, this would be the actual server ID
            success = await self.connection_manager.add_relay_connection(
                server_id, ConnectionType.TCP, self.config.server_host, self.config.server_port
            )
            
            if not success:
                self.logger.error("Failed to add server connection")
                return False
            
            # Wait for connection to be established
            await asyncio.sleep(1)
            
            # Check if connection is active
            status = self.connection_manager.get_connection_status()
            if status["active_connections"] == 0:
                self.logger.error("Server connection not established")
                return False
            
            self.logger.info("Connected to server")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to server: {e}")
            return False
    
    async def _start_authentication(self) -> bool:
        """Start the authentication process."""
        try:
            # Create authentication session
            server_id = b"main_server"
            self.auth_session = self.auth_protocol.create_authentication_session(
                self.user_id, server_id
            )
            
            # Send authentication request
            auth_request = {
                "type": "auth_request",
                "user_id": self.user_id.hex(),
                "public_key": self.public_key.hex(),
                "nickname": self.nickname,
                "session_id": self.auth_session.session_id.hex(),
                "timestamp": int(time.time())
            }
            
            # Send to server (simplified)
            self.logger.info("Sent authentication request")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start authentication: {e}")
            return False
    
    async def _handle_authentication_challenges(self) -> bool:
        """Handle authentication challenges from server."""
        try:
            # Simulate receiving challenges from server
            challenges = [
                self.auth_protocol.create_cryptographic_challenge(self.public_key),
                self.auth_protocol.create_proof_of_work_challenge(),
                self.auth_protocol.create_timestamp_challenge()
            ]
            
            # Add challenges to session
            for challenge in challenges:
                self.auth_protocol.add_challenge_to_session(
                    self.auth_session.session_id, challenge
                )
            
            # Generate responses
            for challenge in challenges:
                response = await self._generate_challenge_response(challenge)
                if response:
                    self.auth_protocol.add_response_to_session(
                        self.auth_session.session_id, response
                    )
                else:
                    self.logger.error(f"Failed to generate response for challenge {challenge.challenge_id.hex()}")
                    return False
            
            self.logger.info("Handled authentication challenges")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to handle authentication challenges: {e}")
            return False
    
    async def _generate_challenge_response(self, challenge: AuthenticationChallenge) -> Optional[AuthenticationResponse]:
        """Generate a response to an authentication challenge."""
        try:
            if challenge.challenge_type == ChallengeType.CRYPTOGRAPHIC:
                # Sign the challenge data with private key
                signature = self.encryption.sign_message(challenge.challenge_data, self.private_key)
                response_data = challenge.challenge_data
                
            elif challenge.challenge_type == ChallengeType.PROOF_OF_WORK:
                # Solve proof of work challenge
                response_data = await self._solve_proof_of_work(challenge)
                if not response_data:
                    return None
                
            elif challenge.challenge_type == ChallengeType.TIMESTAMP:
                # Return current timestamp
                response_data = int(time.time()).to_bytes(8, 'big')
                
            elif challenge.challenge_type == ChallengeType.NONCE:
                # Return the nonce
                response_data = challenge.nonce
                
            else:
                self.logger.error(f"Unknown challenge type: {challenge.challenge_type}")
                return None
            
            response = AuthenticationResponse(
                challenge_id=challenge.challenge_id,
                response_data=response_data,
                timestamp=int(time.time())
            )
            
            # Add signature for cryptographic challenges
            if challenge.challenge_type == ChallengeType.CRYPTOGRAPHIC:
                response.signature = self.encryption.sign_message(challenge.challenge_data, self.private_key)
            
            # Add proof of work for PoW challenges
            if challenge.challenge_type == ChallengeType.PROOF_OF_WORK:
                response.proof_of_work = response_data
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to generate challenge response: {e}")
            return None
    
    async def _solve_proof_of_work(self, challenge: AuthenticationChallenge) -> Optional[bytes]:
        """Solve a proof of work challenge."""
        try:
            import random
            
            # Simple proof of work solver
            for _ in range(100000):  # Limit attempts
                nonce = random.randint(0, 2**32).to_bytes(4, 'big')
                combined = challenge.challenge_data + nonce
                hash_result = hashlib.sha256(combined).digest()
                
                # Check if it meets difficulty requirement
                leading_zeros = 0
                for byte in hash_result:
                    if byte == 0:
                        leading_zeros += 8
                    else:
                        leading_zeros += bin(byte)[2:].find('1')
                        break
                
                if leading_zeros >= challenge.difficulty:
                    return nonce
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to solve proof of work: {e}")
            return None
    
    async def _complete_authentication(self) -> bool:
        """Complete the authentication process."""
        try:
            # Verify session
            success = self.auth_protocol.verify_session(
                self.auth_session.session_id, self.public_key
            )
            
            if not success:
                self.logger.error("Authentication verification failed")
                return False
            
            # Update session
            self.auth_session = self.auth_protocol.get_session(self.auth_session.session_id)
            if not self.auth_session or not self.auth_session.is_authenticated:
                self.logger.error("Authentication session not verified")
                return False
            
            self.logger.info("Authentication completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to complete authentication: {e}")
            return False
    
    async def _set_user_online(self) -> None:
        """Set user online status."""
        try:
            # Create user presence
            presence = UserPresence(
                user_id=self.user_id,
                status=UserStatus.ONLINE,
                last_seen=int(time.time()),
                server_id=b"main_server",
                session_id=self.auth_session.session_id,
                public_key=self.public_key,
                nickname=self.nickname,
                status_message=self.status_message
            )
            
            # Broadcast user online status
            online_message = {
                "type": "user_online",
                "user_id": self.user_id.hex(),
                "presence": presence.to_dict(),
                "timestamp": int(time.time())
            }
            
            # Send to server (simplified)
            self.logger.info("Broadcasted user online status")
            
        except Exception as e:
            self.logger.error(f"Failed to set user online: {e}")
    
    async def _start_background_tasks(self) -> None:
        """Start background tasks."""
        try:
            # Message processing task
            self.background_tasks.append(
                asyncio.create_task(self._message_processing_loop())
            )
            
            # Presence update task
            self.background_tasks.append(
                asyncio.create_task(self._presence_update_loop())
            )
            
            # Auto-away task
            self.background_tasks.append(
                asyncio.create_task(self._auto_away_loop())
            )
            
            self.logger.info("Started background tasks")
            
        except Exception as e:
            self.logger.error(f"Failed to start background tasks: {e}")
    
    async def _message_processing_loop(self) -> None:
        """Process incoming messages."""
        while self.is_authenticated:
            try:
                # Check for new messages (simplified)
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in message processing loop: {e}")
                await asyncio.sleep(5)
    
    async def _presence_update_loop(self) -> None:
        """Update user presence periodically."""
        while self.is_authenticated:
            try:
                # Update last activity
                self.last_activity = int(time.time())
                
                # Send presence update if needed
                await asyncio.sleep(60)  # Update every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in presence update loop: {e}")
                await asyncio.sleep(60)
    
    async def _auto_away_loop(self) -> None:
        """Handle auto-away functionality."""
        while self.is_authenticated:
            try:
                # Check if user has been inactive
                if (self.user_status == UserStatus.ONLINE and 
                    time.time() - self.last_activity > self.config.auto_away_timeout):
                    
                    await self.set_status(UserStatus.AWAY, "Auto-away")
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in auto-away loop: {e}")
                await asyncio.sleep(60)
    
    async def send_message(self, recipient_id: bytes, content: str, 
                          message_type: MessageType = MessageType.TEXT_MESSAGE) -> bool:
        """Send a message to another user."""
        try:
            if not self.is_authenticated:
                self.logger.error("Not authenticated")
                return False
            
            # Create message
            message = Message(
                message_type=message_type,
                content=content.encode('utf-8'),
                sender_id=self.user_id,
                recipient_id=recipient_id,
                timestamp=int(time.time())
            )
            
            # Encrypt message for recipient
            if recipient_id in self.contacts:
                recipient_public_key = self.contacts[recipient_id.hex()]["public_key"]
                encrypted_content = self.encryption.encrypt_message(message.content, recipient_public_key)
            else:
                self.logger.error(f"Recipient {recipient_id.hex()} not in contacts")
                return False
            
            # Send message (simplified)
            message_data = {
                "type": "message",
                "message_id": message.message_id.hex(),
                "sender_id": message.sender_id.hex(),
                "recipient_id": message.recipient_id.hex(),
                "message_type": message.message_type.value,
                "encrypted_content": encrypted_content.hex(),
                "timestamp": message.timestamp
            }
            
            # Add to sent messages
            self.sent_messages.append(message)
            
            self.logger.info(f"Sent message to {recipient_id.hex()}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return False
    
    async def set_status(self, status: UserStatus, status_message: str = None) -> bool:
        """Set user status."""
        try:
            if not self.is_authenticated:
                return False
            
            self.user_status = status
            if status_message is not None:
                self.status_message = status_message
            
            # Broadcast status update
            status_message_data = {
                "type": "status_update",
                "user_id": self.user_id.hex(),
                "status": status.value,
                "status_message": status_message,
                "timestamp": int(time.time())
            }
            
            self.logger.info(f"Status updated to {status.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set status: {e}")
            return False
    
    async def add_contact(self, user_id: bytes, public_key: bytes, nickname: str) -> bool:
        """Add a contact."""
        try:
            self.contacts[user_id.hex()] = {
                "user_id": user_id.hex(),
                "public_key": public_key,
                "nickname": nickname,
                "added_at": int(time.time())
            }
            
            await self._save_contacts()
            self.logger.info(f"Added contact {nickname}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add contact: {e}")
            return False
    
    async def logout(self) -> bool:
        """Logout from the secIRC network."""
        try:
            self.logger.info("Logging out...")
            
            # Cancel background tasks
            for task in self.background_tasks:
                task.cancel()
            
            # Set user offline
            if self.is_authenticated:
                offline_message = {
                    "type": "user_offline",
                    "user_id": self.user_id.hex(),
                    "timestamp": int(time.time())
                }
            
            # Close server connection
            if self.connection_manager:
                await self.connection_manager.stop_connection_manager()
            
            # Reset state
            self.is_authenticated = False
            self.user_status = UserStatus.OFFLINE
            self.auth_session = None
            
            self.logger.info("Logged out successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Logout failed: {e}")
            return False
    
    def get_client_status(self) -> Dict[str, Any]:
        """Get client status information."""
        return {
            "is_authenticated": self.is_authenticated,
            "user_id": self.user_id.hex() if self.user_id else None,
            "nickname": self.nickname,
            "user_status": self.user_status.value,
            "status_message": self.status_message,
            "contacts_count": len(self.contacts),
            "sent_messages": len(self.sent_messages),
            "received_messages": len(self.received_messages),
            "last_activity": self.last_activity,
            "auth_session": self.auth_session.to_dict() if self.auth_session else None
        }
