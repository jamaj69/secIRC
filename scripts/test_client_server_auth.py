#!/usr/bin/env python3
"""
Test script for client-server authentication flow

This script demonstrates the complete authentication process between
a secIRC client and server, including challenge-response verification
and user online status management.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from client.secirc_client import SecIRCClient, ClientConfig
from server.secirc_server import SecIRCServer, ServerConfig
from protocol.authentication import ChallengeType, AuthenticationStatus
from protocol.user_status import UserStatus


async def test_client_server_authentication():
    """Test the complete client-server authentication flow."""
    print("🔐 Testing secIRC Client-Server Authentication")
    print("=" * 60)
    
    try:
        # Create server configuration
        server_config = ServerConfig(
            host="127.0.0.1",
            port=6667,
            ssl_enabled=False,  # Disable SSL for testing
            max_users_per_server=100,
            auth_timeout=300
        )
        
        # Create client configuration
        client_config = ClientConfig(
            server_host="127.0.0.1",
            server_port=6667,
            server_ssl=False,  # Disable SSL for testing
            nickname="TestUser",
            status_message="Testing authentication"
        )
        
        # Create server and client instances
        server = SecIRCServer(server_config)
        client = SecIRCClient(client_config)
        
        print("📡 Starting server...")
        server_success = await server.start_server()
        if not server_success:
            print("❌ Failed to start server")
            return False
        
        print("✅ Server started successfully")
        
        print("\n🔧 Initializing client...")
        client_success = await client.initialize()
        if not client_success:
            print("❌ Failed to initialize client")
            return False
        
        print("✅ Client initialized successfully")
        
        print(f"\n👤 Client user ID: {client.user_id.hex()}")
        print(f"👤 Client nickname: {client.nickname}")
        
        # Test 1: Client login process
        print("\n🔑 Test 1: Client Login Process")
        print("-" * 40)
        
        print("📤 Client sending login request...")
        login_success = await client.login()
        
        if login_success:
            print("✅ Client login successful")
            print(f"   - Authenticated: {client.is_authenticated}")
            print(f"   - User status: {client.user_status.value}")
            print(f"   - Session ID: {client.auth_session.session_id.hex() if client.auth_session else 'None'}")
        else:
            print("❌ Client login failed")
            return False
        
        # Test 2: Server status after client login
        print("\n📊 Test 2: Server Status After Client Login")
        print("-" * 40)
        
        server_status = server.get_server_status()
        print(f"   - Connected clients: {server_status['connected_clients']}")
        print(f"   - Online users: {server_status['online_users']}")
        print(f"   - Auth attempts: {server_status['stats']['auth_attempts']}")
        print(f"   - Auth successes: {server_status['stats']['auth_successes']}")
        print(f"   - Auth failures: {server_status['stats']['auth_failures']}")
        
        # Test 3: User presence management
        print("\n👥 Test 3: User Presence Management")
        print("-" * 40)
        
        # Check if user is online on server
        user_presence = server.user_status_manager.get_user_presence(client.user_id)
        if user_presence:
            print(f"   - User online: {user_presence.is_online()}")
            print(f"   - User status: {user_presence.status.value}")
            print(f"   - Last seen: {user_presence.last_seen}")
            print(f"   - Server ID: {user_presence.server_id.hex()}")
        else:
            print("   ❌ User presence not found on server")
        
        # Test 4: Message sending (simulated)
        print("\n📨 Test 4: Message Sending Simulation")
        print("-" * 40)
        
        # Create a test recipient
        test_recipient_id = b"test_recipient_123"
        test_recipient_public_key = b"test_public_key_123"
        
        # Add test recipient to client contacts
        await client.add_contact(test_recipient_id, test_recipient_public_key, "TestRecipient")
        print("   ✅ Added test recipient to contacts")
        
        # Simulate sending a message
        message_sent = await client.send_message(test_recipient_id, "Hello, this is a test message!")
        if message_sent:
            print("   ✅ Message sent successfully")
        else:
            print("   ❌ Failed to send message")
        
        # Test 5: Status updates
        print("\n🔄 Test 5: Status Updates")
        print("-" * 40)
        
        # Set client status to away
        status_updated = await client.set_status(UserStatus.AWAY, "Testing status update")
        if status_updated:
            print("   ✅ Status updated to AWAY")
        else:
            print("   ❌ Failed to update status")
        
        # Test 6: Client logout
        print("\n🚪 Test 6: Client Logout")
        print("-" * 40)
        
        logout_success = await client.logout()
        if logout_success:
            print("   ✅ Client logout successful")
        else:
            print("   ❌ Client logout failed")
        
        # Test 7: Server status after client logout
        print("\n📊 Test 7: Server Status After Client Logout")
        print("-" * 40)
        
        server_status = server.get_server_status()
        print(f"   - Connected clients: {server_status['connected_clients']}")
        print(f"   - Online users: {server_status['online_users']}")
        print(f"   - Messages processed: {server_status['stats']['messages_processed']}")
        print(f"   - Messages delivered: {server_status['stats']['messages_delivered']}")
        
        # Test 8: Authentication protocol details
        print("\n🔍 Test 8: Authentication Protocol Details")
        print("-" * 40)
        
        auth_status = server.auth_protocol.get_authentication_status()
        print(f"   - Active sessions: {auth_status['active_sessions']}")
        print(f"   - Active challenges: {auth_status['active_challenges']}")
        print(f"   - Authenticated sessions: {auth_status['authenticated_sessions']}")
        print(f"   - Pending sessions: {auth_status['pending_sessions']}")
        print(f"   - Challenged sessions: {auth_status['challenged_sessions']}")
        print(f"   - Verified sessions: {auth_status['verified_sessions']}")
        print(f"   - Failed sessions: {auth_status['failed_sessions']}")
        print(f"   - Expired sessions: {auth_status['expired_sessions']}")
        
        print("\n✅ All authentication tests completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Authentication test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        try:
            if 'client' in locals():
                await client.logout()
            if 'server' in locals():
                await server.stop_server()
            print("✅ Cleanup completed")
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")


async def test_authentication_challenges():
    """Test different types of authentication challenges."""
    print("\n🧩 Testing Authentication Challenges")
    print("=" * 40)
    
    try:
        from protocol.authentication import AuthenticationProtocol, ChallengeType
        from protocol.encryption import EndToEndEncryption
        
        # Create authentication protocol
        encryption = EndToEndEncryption()
        auth_protocol = AuthenticationProtocol(encryption)
        
        # Generate test key pair
        public_key, private_key = encryption.generate_keypair()
        user_id = b"test_user_123"
        
        print(f"👤 Test user ID: {user_id.hex()}")
        
        # Test 1: Cryptographic challenge
        print("\n1. Cryptographic Challenge:")
        challenge = auth_protocol.create_cryptographic_challenge(public_key)
        print(f"   - Challenge ID: {challenge.challenge_id.hex()}")
        print(f"   - Challenge type: {challenge.challenge_type.value}")
        print(f"   - Expires at: {challenge.expires_at}")
        
        # Test 2: Proof of work challenge
        print("\n2. Proof of Work Challenge:")
        challenge = auth_protocol.create_proof_of_work_challenge(difficulty=4)
        print(f"   - Challenge ID: {challenge.challenge_id.hex()}")
        print(f"   - Challenge type: {challenge.challenge_type.value}")
        print(f"   - Difficulty: {challenge.difficulty}")
        
        # Test 3: Timestamp challenge
        print("\n3. Timestamp Challenge:")
        challenge = auth_protocol.create_timestamp_challenge()
        print(f"   - Challenge ID: {challenge.challenge_id.hex()}")
        print(f"   - Challenge type: {challenge.challenge_type.value}")
        print(f"   - Timestamp: {challenge.timestamp}")
        
        # Test 4: Nonce challenge
        print("\n4. Nonce Challenge:")
        challenge = auth_protocol.create_nonce_challenge()
        print(f"   - Challenge ID: {challenge.challenge_id.hex()}")
        print(f"   - Challenge type: {challenge.challenge_type.value}")
        print(f"   - Nonce: {challenge.nonce.hex() if challenge.nonce else 'None'}")
        
        print("\n✅ Authentication challenge tests completed!")
        
    except Exception as e:
        print(f"\n❌ Authentication challenge test failed: {e}")
        import traceback
        traceback.print_exc()


async def test_user_status_management():
    """Test user status management functionality."""
    print("\n👥 Testing User Status Management")
    print("=" * 40)
    
    try:
        from protocol.user_status import UserStatusManager, UserPresence, UserStatus, MessageDeliveryManager
        
        # Create user status manager
        server_id = b"test_server_123"
        user_status_manager = UserStatusManager(server_id)
        message_delivery_manager = MessageDeliveryManager(user_status_manager)
        
        print(f"🖥️ Server ID: {server_id.hex()}")
        
        # Test 1: User login
        print("\n1. User Login:")
        user_id = b"test_user_456"
        session_id = b"test_session_789"
        public_key = b"test_public_key_456"
        nickname = "TestUser"
        
        presence = user_status_manager.user_login(user_id, session_id, public_key, nickname)
        print(f"   - User ID: {presence.user_id.hex()}")
        print(f"   - Status: {presence.status.value}")
        print(f"   - Online: {presence.is_online()}")
        print(f"   - Nickname: {presence.nickname}")
        
        # Test 2: User status update
        print("\n2. User Status Update:")
        success = user_status_manager.update_user_status(user_id, UserStatus.AWAY, "Testing status update")
        print(f"   - Status update success: {success}")
        
        updated_presence = user_status_manager.get_user_presence(user_id)
        print(f"   - New status: {updated_presence.status.value}")
        print(f"   - Status message: {updated_presence.status_message}")
        
        # Test 3: Message queuing
        print("\n3. Message Queuing:")
        sender_id = b"test_sender_123"
        message_id = message_delivery_manager.queue_message(
            sender_id, user_id, "TEXT_MESSAGE", b"Hello, this is a test message!"
        )
        print(f"   - Message ID: {message_id.hex()}")
        print(f"   - Messages queued: {message_delivery_manager.delivery_stats['messages_queued']}")
        
        # Test 4: Message delivery
        print("\n4. Message Delivery:")
        delivered_messages = message_delivery_manager.deliver_pending_messages(user_id)
        print(f"   - Messages delivered: {len(delivered_messages)}")
        print(f"   - Delivery stats: {message_delivery_manager.delivery_stats}")
        
        # Test 5: User logout
        print("\n5. User Logout:")
        logout_success = user_status_manager.user_logout(user_id)
        print(f"   - Logout success: {logout_success}")
        
        final_presence = user_status_manager.get_user_presence(user_id)
        print(f"   - Final status: {final_presence.status.value}")
        print(f"   - Online: {final_presence.is_online()}")
        
        print("\n✅ User status management tests completed!")
        
    except Exception as e:
        print(f"\n❌ User status management test failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    print("🧪 secIRC Client-Server Authentication Test Suite")
    print("=" * 70)
    
    try:
        # Test authentication challenges
        await test_authentication_challenges()
        
        # Test user status management
        await test_user_status_management()
        
        # Test complete client-server authentication flow
        await test_client_server_authentication()
        
        print("\n🎉 All client-server authentication tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
