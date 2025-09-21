"""
secIRC Server Implementation

This module implements the secIRC relay server that handles client authentication,
user status management, and message delivery across the relay network.
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
class ServerConfig:
    """Configuration for secIRC server."""
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 6667
    ssl_enabled: bool = True
    ssl_cert_path: str = "config/ssl/server.crt"
    ssl_key_path: str = "config/ssl/server.key"
    
    # Authentication
    max_auth_attempts: int = 3
    auth_timeout: int = 300
    session_timeout: int = 3600
    
    # User management
    max_users_per_server: int = 1000
    user_presence_timeout: int = 300
    
    # Message delivery
    max_pending_messages: int = 100
    message_ttl: int = 3600
    delivery_retry_attempts: int = 3
    
    # Relay connections
    max_relay_connections: int = 10
    min_relay_connections: int = 3
    relay_heartbeat_interval: int = 60
    
    # Storage
    data_dir: str = "data/server"
    users_file: str = "users.json"
    messages_file: str = "messages.json"
    relay_config_file: str = "relay_connections.yaml"


class SecIRCServer:
    """Main secIRC server implementation."""
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self.server_id = hashlib.sha256(f"server_{config.host}_{config.port}".encode()).digest()[:16]
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.encryption = EndToEndEncryption()
        self.auth_protocol = AuthenticationProtocol(self.encryption)
        self.user_status_manager = UserStatusManager(self.server_id)
        self.message_delivery_manager = MessageDeliveryManager(self.user_status_manager)
        self.relay_connection_manager = None
        
        # Server state
        self.is_running = False
        self.connected_clients: Dict[bytes, Dict[str, Any]] = {}  # user_id -> client_info
        self.server_tasks: List[asyncio.Task] = []
        
        # Statistics
        self.stats = {
            "clients_connected": 0,
            "clients_authenticated": 0,
            "messages_processed": 0,
            "messages_delivered": 0,
            "messages_failed": 0,
            "auth_attempts": 0,
            "auth_successes": 0,
            "auth_failures": 0
        }
        
        # Create data directory
        Path(self.config.data_dir).mkdir(parents=True, exist_ok=True)
    
    async def start_server(self) -> bool:
        """Start the secIRC server."""
        try:
            self.logger.info(f"Starting secIRC server on {self.config.host}:{self.config.port}")
            
            # Initialize relay connections
            if not await self._initialize_relay_connections():
                return False
            
            # Start server tasks
            await self._start_server_tasks()
            
            # Start message delivery processing
            await self._start_message_delivery()
            
            self.is_running = True
            self.logger.info("secIRC server started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            return False
    
    async def _initialize_relay_connections(self) -> bool:
        """Initialize relay connections to other servers."""
        try:
            # Create relay connection configuration
            relay_config = ConnectionConfig(
                max_connections=self.config.max_relay_connections,
                min_connections=self.config.min_relay_connections,
                enable_tcp=True,
                enable_tor=True,
                enable_websocket=True,
                ssl_enabled=self.config.ssl_enabled,
                heartbeat_interval=self.config.relay_heartbeat_interval
            )
            
            # Create relay connection manager
            self.relay_connection_manager = RelayConnectionManager(relay_config, self.encryption)
            await self.relay_connection_manager.start_connection_manager()
            
            # Load relay configuration
            await self._load_relay_configuration()
            
            self.logger.info("Relay connections initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize relay connections: {e}")
            return False
    
    async def _load_relay_configuration(self) -> None:
        """Load relay configuration from file."""
        try:
            config_file = Path(self.config.data_dir) / self.config.relay_config_file
            if not config_file.exists():
                self.logger.warning("Relay configuration file not found, using defaults")
                return
            
            import yaml
            with open(config_file, 'r') as f:
                relay_config = yaml.safe_load(f)
            
            # Add configured relay connections
            bootstrap_relays = relay_config.get("discovery", {}).get("bootstrap_relays", [])
            for relay_config_item in bootstrap_relays:
                relay_id = relay_config_item["relay_id"].encode()
                connection_type = ConnectionType(relay_config_item["connection_type"])
                host = relay_config_item["host"]
                port = relay_config_item["port"]
                priority = relay_config_item.get("priority", 5)
                
                await self.relay_connection_manager.add_relay_connection(
                    relay_id, connection_type, host, port, priority
                )
            
            self.logger.info(f"Loaded {len(bootstrap_relays)} relay connections")
            
        except Exception as e:
            self.logger.error(f"Failed to load relay configuration: {e}")
    
    async def _start_server_tasks(self) -> None:
        """Start server background tasks."""
        try:
            # Authentication cleanup task
            self.server_tasks.append(
                asyncio.create_task(self._authentication_cleanup_loop())
            )
            
            # User presence monitoring task
            self.server_tasks.append(
                asyncio.create_task(self._user_presence_monitoring_loop())
            )
            
            # Message delivery processing task
            self.server_tasks.append(
                asyncio.create_task(self._message_delivery_loop())
            )
            
            # Statistics reporting task
            self.server_tasks.append(
                asyncio.create_task(self._statistics_reporting_loop())
            )
            
            # Relay network synchronization task
            self.server_tasks.append(
                asyncio.create_task(self._relay_sync_loop())
            )
            
            self.logger.info("Started server background tasks")
            
        except Exception as e:
            self.logger.error(f"Failed to start server tasks: {e}")
    
    async def _start_message_delivery(self) -> None:
        """Start message delivery system."""
        try:
            # Start message delivery manager
            self.logger.info("Started message delivery system")
            
        except Exception as e:
            self.logger.error(f"Failed to start message delivery: {e}")
    
    async def handle_client_connection(self, client_info: Dict[str, Any]) -> bool:
        """Handle a new client connection."""
        try:
            user_id = bytes.fromhex(client_info["user_id"])
            self.logger.info(f"Handling client connection for user {user_id.hex()}")
            
            # Store client connection info
            self.connected_clients[user_id] = client_info
            self.stats["clients_connected"] += 1
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to handle client connection: {e}")
            return False
    
    async def handle_authentication_request(self, auth_request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle client authentication request."""
        try:
            user_id = bytes.fromhex(auth_request["user_id"])
            public_key = bytes.fromhex(auth_request["public_key"])
            nickname = auth_request.get("nickname", "")
            session_id = bytes.fromhex(auth_request["session_id"])
            
            self.logger.info(f"Handling authentication request for user {user_id.hex()}")
            self.stats["auth_attempts"] += 1
            
            # Create authentication session
            auth_session = self.auth_protocol.create_authentication_session(
                user_id, self.server_id
            )
            
            # Generate authentication challenges
            challenges = await self._generate_authentication_challenges(public_key)
            
            # Add challenges to session
            for challenge in challenges:
                self.auth_protocol.add_challenge_to_session(
                    auth_session.session_id, challenge
                )
            
            # Prepare response
            response = {
                "type": "auth_challenges",
                "session_id": auth_session.session_id.hex(),
                "challenges": [challenge.to_dict() for challenge in challenges],
                "timestamp": int(time.time())
            }
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to handle authentication request: {e}")
            self.stats["auth_failures"] += 1
            return {
                "type": "auth_error",
                "error": "Authentication request failed",
                "timestamp": int(time.time())
            }
    
    async def _generate_authentication_challenges(self, public_key: bytes) -> List[AuthenticationChallenge]:
        """Generate authentication challenges for a client."""
        challenges = []
        
        # Cryptographic challenge
        challenges.append(
            self.auth_protocol.create_cryptographic_challenge(public_key)
        )
        
        # Proof of work challenge
        challenges.append(
            self.auth_protocol.create_proof_of_work_challenge(difficulty=4)
        )
        
        # Timestamp challenge
        challenges.append(
            self.auth_protocol.create_timestamp_challenge()
        )
        
        # Nonce challenge
        challenges.append(
            self.auth_protocol.create_nonce_challenge()
        )
        
        return challenges
    
    async def handle_authentication_response(self, auth_response: Dict[str, Any]) -> Dict[str, Any]:
        """Handle client authentication response."""
        try:
            session_id = bytes.fromhex(auth_response["session_id"])
            responses_data = auth_response["responses"]
            
            # Get authentication session
            auth_session = self.auth_protocol.get_session(session_id)
            if not auth_session:
                return {
                    "type": "auth_error",
                    "error": "Invalid session",
                    "timestamp": int(time.time())
                }
            
            # Parse responses
            responses = []
            for response_data in responses_data:
                response = AuthenticationResponse.from_dict(response_data)
                responses.append(response)
                self.auth_protocol.add_response_to_session(session_id, response)
            
            # Verify authentication
            success = self.auth_protocol.verify_session(
                session_id, auth_session.user_id
            )
            
            if success:
                # Authentication successful
                auth_session = self.auth_protocol.get_session(session_id)
                
                # Set user online
                await self._set_user_online(auth_session)
                
                # Broadcast user online status to relay network
                await self._broadcast_user_online(auth_session.user_id)
                
                self.stats["auth_successes"] += 1
                
                response = {
                    "type": "auth_success",
                    "session_id": session_id.hex(),
                    "session_key": auth_session.session_key.hex(),
                    "timestamp": int(time.time())
                }
            else:
                # Authentication failed
                self.stats["auth_failures"] += 1
                response = {
                    "type": "auth_failure",
                    "error": "Authentication verification failed",
                    "timestamp": int(time.time())
                }
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to handle authentication response: {e}")
            self.stats["auth_failures"] += 1
            return {
                "type": "auth_error",
                "error": "Authentication response processing failed",
                "timestamp": int(time.time())
            }
    
    async def _set_user_online(self, auth_session: AuthenticationSession) -> None:
        """Set user online status."""
        try:
            # Get user presence from session
            user_presence = self.user_status_manager.get_user_presence(auth_session.user_id)
            if not user_presence:
                # Create new user presence
                user_presence = UserPresence(
                    user_id=auth_session.user_id,
                    status=UserStatus.ONLINE,
                    last_seen=int(time.time()),
                    server_id=self.server_id,
                    session_id=auth_session.session_id,
                    public_key=None,  # Will be set from client info
                    nickname="",  # Will be set from client info
                    status_message=""
                )
            
            # Update user presence
            user_presence.status = UserStatus.ONLINE
            user_presence.update_presence()
            user_presence.session_id = auth_session.session_id
            
            # Store in user status manager
            self.user_status_manager.user_presences[auth_session.user_id] = user_presence
            self.user_status_manager.user_sessions[auth_session.user_id] = auth_session.session_id
            self.user_status_manager.server_users[self.server_id].add(auth_session.user_id)
            
            self.stats["clients_authenticated"] += 1
            
            self.logger.info(f"User {auth_session.user_id.hex()} is now online")
            
        except Exception as e:
            self.logger.error(f"Failed to set user online: {e}")
    
    async def _broadcast_user_online(self, user_id: bytes) -> None:
        """Broadcast user online status to relay network."""
        try:
            user_presence = self.user_status_manager.get_user_presence(user_id)
            if not user_presence:
                return
            
            # Create broadcast message
            broadcast_message = self.user_status_manager.broadcast_user_online(user_id, user_presence)
            
            # Send to all connected relay servers
            if self.relay_connection_manager:
                sent_count = await self.relay_connection_manager.broadcast_message(broadcast_message)
                self.logger.info(f"Broadcasted user online status to {sent_count} relay servers")
            
        except Exception as e:
            self.logger.error(f"Failed to broadcast user online status: {e}")
    
    async def handle_user_logout(self, user_id: bytes) -> bool:
        """Handle user logout."""
        try:
            self.logger.info(f"Handling user logout for {user_id.hex()}")
            
            # Set user offline
            success = self.user_status_manager.user_logout(user_id)
            if success:
                # Remove from connected clients
                if user_id in self.connected_clients:
                    del self.connected_clients[user_id]
                
                # Broadcast user offline status
                await self._broadcast_user_offline(user_id)
                
                # Deliver any pending messages
                pending_messages = self.message_delivery_manager.deliver_pending_messages(user_id)
                if pending_messages:
                    self.logger.info(f"Delivered {len(pending_messages)} pending messages to {user_id.hex()}")
                
                self.stats["clients_connected"] -= 1
                self.stats["clients_authenticated"] -= 1
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to handle user logout: {e}")
            return False
    
    async def _broadcast_user_offline(self, user_id: bytes) -> None:
        """Broadcast user offline status to relay network."""
        try:
            # Create broadcast message
            broadcast_message = self.user_status_manager.broadcast_user_offline(user_id)
            
            # Send to all connected relay servers
            if self.relay_connection_manager:
                sent_count = await self.relay_connection_manager.broadcast_message(broadcast_message)
                self.logger.info(f"Broadcasted user offline status to {sent_count} relay servers")
            
        except Exception as e:
            self.logger.error(f"Failed to broadcast user offline status: {e}")
    
    async def handle_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming message."""
        try:
            sender_id = bytes.fromhex(message_data["sender_id"])
            recipient_id = bytes.fromhex(message_data["recipient_id"])
            message_type = MessageType(message_data["message_type"])
            encrypted_content = bytes.fromhex(message_data["encrypted_content"])
            
            self.logger.info(f"Handling message from {sender_id.hex()} to {recipient_id.hex()}")
            self.stats["messages_processed"] += 1
            
            # Check if recipient is online
            if self.user_status_manager.is_user_online(recipient_id):
                # Deliver message immediately
                success = await self._deliver_message_to_user(
                    recipient_id, sender_id, message_type, encrypted_content
                )
                
                if success:
                    self.stats["messages_delivered"] += 1
                    return {
                        "type": "message_delivered",
                        "message_id": message_data.get("message_id", ""),
                        "timestamp": int(time.time())
                    }
                else:
                    self.stats["messages_failed"] += 1
                    return {
                        "type": "message_failed",
                        "error": "Message delivery failed",
                        "timestamp": int(time.time())
                    }
            else:
                # Queue message for later delivery
                message_id = self.message_delivery_manager.queue_message(
                    sender_id, recipient_id, message_type, encrypted_content
                )
                
                return {
                    "type": "message_queued",
                    "message_id": message_id.hex(),
                    "timestamp": int(time.time())
                }
            
        except Exception as e:
            self.logger.error(f"Failed to handle message: {e}")
            self.stats["messages_failed"] += 1
            return {
                "type": "message_error",
                "error": "Message processing failed",
                "timestamp": int(time.time())
            }
    
    async def _deliver_message_to_user(self, recipient_id: bytes, sender_id: bytes,
                                     message_type: MessageType, encrypted_content: bytes) -> bool:
        """Deliver a message to an online user."""
        try:
            # Get user session
            if recipient_id not in self.user_status_manager.user_sessions:
                return False
            
            session_id = self.user_status_manager.user_sessions[recipient_id]
            
            # Create delivery message
            delivery_message = {
                "type": "message_delivery",
                "sender_id": sender_id.hex(),
                "message_type": message_type.value,
                "encrypted_content": encrypted_content.hex(),
                "timestamp": int(time.time())
            }
            
            # Send message to user (simplified - in real implementation, this would
            # send through the user's connection)
            self.logger.info(f"Delivered message to user {recipient_id.hex()}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to deliver message to user: {e}")
            return False
    
    async def _authentication_cleanup_loop(self) -> None:
        """Clean up expired authentication sessions."""
        while self.is_running:
            try:
                cleaned = self.auth_protocol.cleanup_expired_sessions()
                if cleaned > 0:
                    self.logger.debug(f"Cleaned up {cleaned} expired authentication sessions")
                
                await asyncio.sleep(60)  # Clean up every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in authentication cleanup loop: {e}")
                await asyncio.sleep(60)
    
    async def _user_presence_monitoring_loop(self) -> None:
        """Monitor user presence and handle timeouts."""
        while self.is_running:
            try:
                # Check for users who haven't been active
                current_time = time.time()
                timeout_users = []
                
                for user_id, presence in self.user_status_manager.user_presences.items():
                    if (presence.is_online() and 
                        current_time - presence.last_seen > self.config.user_presence_timeout):
                        timeout_users.append(user_id)
                
                # Set timeout users as offline
                for user_id in timeout_users:
                    await self.handle_user_logout(user_id)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in user presence monitoring loop: {e}")
                await asyncio.sleep(30)
    
    async def _message_delivery_loop(self) -> None:
        """Process message delivery queue."""
        while self.is_running:
            try:
                # Process delivery queue
                delivered = self.message_delivery_manager.process_delivery_queue()
                
                if delivered:
                    self.logger.info(f"Delivered {len(delivered)} messages")
                
                # Clean up expired messages
                cleaned = self.message_delivery_manager.cleanup_expired_messages()
                if cleaned > 0:
                    self.logger.debug(f"Cleaned up {cleaned} expired messages")
                
                await asyncio.sleep(1)  # Process every second
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in message delivery loop: {e}")
                await asyncio.sleep(5)
    
    async def _statistics_reporting_loop(self) -> None:
        """Report server statistics periodically."""
        while self.is_running:
            try:
                # Log statistics
                self.logger.info("=== Server Statistics ===")
                self.logger.info(f"Connected clients: {self.stats['clients_connected']}")
                self.logger.info(f"Authenticated clients: {self.stats['clients_authenticated']}")
                self.logger.info(f"Messages processed: {self.stats['messages_processed']}")
                self.logger.info(f"Messages delivered: {self.stats['messages_delivered']}")
                self.logger.info(f"Messages failed: {self.stats['messages_failed']}")
                self.logger.info(f"Auth attempts: {self.stats['auth_attempts']}")
                self.logger.info(f"Auth successes: {self.stats['auth_successes']}")
                self.logger.info(f"Auth failures: {self.stats['auth_failures']}")
                
                # Relay connection status
                if self.relay_connection_manager:
                    relay_status = self.relay_connection_manager.get_connection_status()
                    self.logger.info(f"Relay connections: {relay_status['active_connections']}")
                
                await asyncio.sleep(300)  # Report every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in statistics reporting loop: {e}")
                await asyncio.sleep(300)
    
    async def _relay_sync_loop(self) -> None:
        """Synchronize with relay network."""
        while self.is_running:
            try:
                # Sync user status with relay network
                online_users = self.user_status_manager.get_online_users()
                
                # Send periodic heartbeat to relay network
                heartbeat_message = {
                    "type": "heartbeat",
                    "server_id": self.server_id.hex(),
                    "online_users": len(online_users),
                    "timestamp": int(time.time())
                }
                
                if self.relay_connection_manager:
                    sent_count = await self.relay_connection_manager.broadcast_message(heartbeat_message)
                    if sent_count > 0:
                        self.logger.debug(f"Sent heartbeat to {sent_count} relay servers")
                
                await asyncio.sleep(self.config.relay_heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in relay sync loop: {e}")
                await asyncio.sleep(60)
    
    async def stop_server(self) -> bool:
        """Stop the secIRC server."""
        try:
            self.logger.info("Stopping secIRC server...")
            
            self.is_running = False
            
            # Cancel server tasks
            for task in self.server_tasks:
                task.cancel()
            
            # Stop relay connections
            if self.relay_connection_manager:
                await self.relay_connection_manager.stop_connection_manager()
            
            # Set all users offline
            for user_id in list(self.connected_clients.keys()):
                await self.handle_user_logout(user_id)
            
            self.logger.info("secIRC server stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop server: {e}")
            return False
    
    def get_server_status(self) -> Dict[str, Any]:
        """Get server status information."""
        return {
            "is_running": self.is_running,
            "server_id": self.server_id.hex(),
            "host": self.config.host,
            "port": self.config.port,
            "stats": self.stats,
            "connected_clients": len(self.connected_clients),
            "online_users": len(self.user_status_manager.get_online_users()),
            "relay_connections": self.relay_connection_manager.get_connection_status() if self.relay_connection_manager else None,
            "auth_status": self.auth_protocol.get_authentication_status(),
            "delivery_stats": self.message_delivery_manager.get_delivery_stats()
        }
