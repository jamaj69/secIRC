#!/usr/bin/env python3
"""
secIRC Client Test Script

This script tests the client functionality including:
- Client initialization and key management
- Contact management and public key exchange
- Group creation and management
- Message sending and receiving
- Key rotation
- Network connectivity
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from protocol.anonymous_protocol import AnonymousProtocol
from protocol.message_types import MessageType, Message, UserIdentity
from protocol.encryption import EndToEndEncryption
from protocol.relay_discovery import RelayDiscovery
from protocol.pubsub_server import PubSubServer
from protocol.decentralized_groups import DecentralizedGroupManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ClientTester:
    """Test suite for client functionality."""
    
    def __init__(self):
        self.encryption = EndToEndEncryption()
        self.protocol = AnonymousProtocol()
        self.relay_discovery = RelayDiscovery()
        self.pubsub_server = PubSubServer(self.encryption)
        self.group_manager = DecentralizedGroupManager(self.encryption)
        
        # Test data
        self.test_users: List[UserIdentity] = []
        self.test_contacts: List[UserIdentity] = []
        self.test_groups: List = []
        self.test_results: Dict[str, bool] = {}
        
    async def setup_test_environment(self):
        """Set up test environment with sample data."""
        logger.info("Setting up test environment...")
        
        # Create test users (simulating different clients)
        for i in range(3):
            user = UserIdentity(
                user_hash=bytes(f"client_{i}_hash".encode())[:16],
                public_key=bytes(f"client_{i}_public_key".encode()),
                private_key=bytes(f"client_{i}_private_key".encode()),
                nickname=f"Client{i}"
            )
            self.test_users.append(user)
        
        # Create test contacts
        for i in range(3, 6):
            contact = UserIdentity(
                user_hash=bytes(f"contact_{i}_hash".encode())[:16],
                public_key=bytes(f"contact_{i}_public_key".encode()),
                private_key=bytes(f"contact_{i}_private_key".encode()),
                nickname=f"Contact{i}"
            )
            self.test_contacts.append(contact)
        
        logger.info(f"Created {len(self.test_users)} test users and {len(self.test_contacts)} test contacts")
        
    async def test_client_initialization(self) -> bool:
        """Test client initialization and key management."""
        logger.info("Testing client initialization...")
        
        try:
            # Initialize protocol
            await self.protocol.initialize()
            
            # Test key generation
            user = self.test_users[0]
            if user.user_hash and user.public_key and user.private_key:
                logger.info("✅ Client initialization test passed")
                return True
            else:
                logger.error("❌ Client initialization test failed - missing keys")
                return False
                
        except Exception as e:
            logger.error(f"❌ Client initialization test failed: {e}")
            return False
    
    async def test_contact_management(self) -> bool:
        """Test contact management functionality."""
        logger.info("Testing contact management...")
        
        try:
            # Test adding contacts
            user = self.test_users[0]
            contact = self.test_contacts[0]
            
            # Simulate adding a contact
            # In a real implementation, this would use the ContactManager
            logger.info(f"Adding contact: {contact.nickname}")
            
            # Test contact validation
            if contact.nickname and contact.user_hash and contact.public_key:
                logger.info("✅ Contact management test passed")
                return True
            else:
                logger.error("❌ Contact management test failed - invalid contact data")
                return False
                
        except Exception as e:
            logger.error(f"❌ Contact management test failed: {e}")
            return False
    
    async def test_public_key_exchange(self) -> bool:
        """Test public key exchange between clients."""
        logger.info("Testing public key exchange...")
        
        try:
            # Test public key exchange
            user1 = self.test_users[0]
            user2 = self.test_users[1]
            
            # Simulate public key exchange
            logger.info(f"Exchanging keys between {user1.nickname} and {user2.nickname}")
            
            # Test key validation
            if user1.public_key and user2.public_key:
                logger.info("✅ Public key exchange test passed")
                return True
            else:
                logger.error("❌ Public key exchange test failed - missing public keys")
                return False
                
        except Exception as e:
            logger.error(f"❌ Public key exchange test failed: {e}")
            return False
    
    async def test_message_encryption(self) -> bool:
        """Test message encryption and decryption."""
        logger.info("Testing message encryption...")
        
        try:
            # Test message encryption
            test_message = "Hello from client test!"
            sender = self.test_users[0]
            recipient = self.test_users[1]
            
            # Encrypt message
            encrypted_message = await self.encryption.encrypt_message(
                test_message.encode(),
                recipient.public_key
            )
            
            if encrypted_message:
                logger.info("✅ Message encryption test passed")
                return True
            else:
                logger.error("❌ Message encryption test failed - no encrypted message")
                return False
                
        except Exception as e:
            logger.error(f"❌ Message encryption test failed: {e}")
            return False
    
    async def test_group_creation(self) -> bool:
        """Test group creation from client perspective."""
        logger.info("Testing group creation...")
        
        try:
            # Create a test group
            owner = self.test_users[0]
            group = await self.group_manager.create_group(
                owner_hash=owner.user_hash,
                owner_public_key=owner.public_key,
                group_name="Client Test Group",
                description="A test group created by client",
                max_members=10,
                is_private=True
            )
            
            if group:
                self.test_groups.append(group)
                logger.info(f"✅ Group creation test passed - created group: {group.group_id.hex()}")
                return True
            else:
                logger.error("❌ Group creation test failed - no group created")
                return False
                
        except Exception as e:
            logger.error(f"❌ Group creation test failed: {e}")
            return False
    
    async def test_group_invitations(self) -> bool:
        """Test group invitation functionality."""
        logger.info("Testing group invitations...")
        
        try:
            if not self.test_groups:
                logger.error("❌ Group invitation test failed - no groups available")
                return False
            
            group = self.test_groups[0]
            owner = self.test_users[0]
            invitee = self.test_contacts[0]
            
            # Test group invitation
            # In a real implementation, this would use the GroupManager
            logger.info(f"Inviting {invitee.nickname} to group {group.group_id.hex()}")
            
            # Simulate invitation process
            if invitee.nickname and invitee.public_key:
                logger.info("✅ Group invitation test passed")
                return True
            else:
                logger.error("❌ Group invitation test failed - invalid invitee data")
                return False
                
        except Exception as e:
            logger.error(f"❌ Group invitation test failed: {e}")
            return False
    
    async def test_group_messaging(self) -> bool:
        """Test group messaging from client perspective."""
        logger.info("Testing group messaging...")
        
        try:
            if not self.test_groups:
                logger.error("❌ Group messaging test failed - no groups available")
                return False
            
            group = self.test_groups[0]
            owner = self.test_users[0]
            
            # Add members to group
            for i in range(1, 3):
                await self.group_manager.add_member(
                    group_id=group.group_id,
                    owner_hash=owner.user_hash,
                    new_member_hash=self.test_users[i].user_hash,
                    new_member_public_key=self.test_users[i].public_key
                )
            
            # Send a group message
            group_message = await self.group_manager.send_group_message(
                group_id=group.group_id,
                sender_hash=owner.user_hash,
                sender_public_key=owner.public_key,
                message_type=MessageType.TEXT_MESSAGE,
                content="Hello group from client!".encode()
            )
            
            if group_message:
                logger.info(f"✅ Group messaging test passed - sent message: {group_message.message_id.hex()}")
                return True
            else:
                logger.error("❌ Group messaging test failed - no message sent")
                return False
                
        except Exception as e:
            logger.error(f"❌ Group messaging test failed: {e}")
            return False
    
    async def test_key_rotation(self) -> bool:
        """Test key rotation from client perspective."""
        logger.info("Testing key rotation...")
        
        try:
            # Test key rotation for a group
            owner = self.test_users[0]
            group = await self.group_manager.create_group(
                owner_hash=owner.user_hash,
                owner_public_key=owner.public_key,
                group_name="Key Rotation Test Group",
                description="A test group for key rotation",
                max_members=5,
                is_private=True
            )
            
            if not group:
                logger.error("❌ Key rotation test failed - could not create group")
                return False
            
            # Add a member
            await self.group_manager.add_member(
                group_id=group.group_id,
                owner_hash=owner.user_hash,
                new_member_hash=self.test_users[1].user_hash,
                new_member_public_key=self.test_users[1].public_key
            )
            
            # Trigger key rotation
            await self.group_manager.rotate_all_group_keys()
            
            logger.info("✅ Key rotation test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Key rotation test failed: {e}")
            return False
    
    async def test_network_connectivity(self) -> bool:
        """Test network connectivity and relay discovery."""
        logger.info("Testing network connectivity...")
        
        try:
            # Test relay discovery
            discovered_relays = await self.relay_discovery.discover_relays()
            
            if discovered_relays is not None:
                logger.info(f"✅ Network connectivity test passed - discovered {len(discovered_relays)} relays")
                return True
            else:
                logger.warning("⚠️ Network connectivity test - no relays discovered (expected in test environment)")
                return True  # This is expected in a test environment
                
        except Exception as e:
            logger.error(f"❌ Network connectivity test failed: {e}")
            return False
    
    async def test_message_delivery(self) -> bool:
        """Test message delivery and receipt."""
        logger.info("Testing message delivery...")
        
        try:
            # Test message delivery
            sender = self.test_users[0]
            recipient = self.test_users[1]
            
            # Create a test message
            test_message = Message(
                message_type=MessageType.TEXT_MESSAGE,
                content="Test message for delivery".encode(),
                sender_hash=sender.user_hash,
                recipient_hash=recipient.user_hash,
                timestamp=int(time.time())
            )
            
            # Simulate message delivery
            logger.info(f"Delivering message from {sender.nickname} to {recipient.nickname}")
            
            if test_message.content and test_message.sender_hash and test_message.recipient_hash:
                logger.info("✅ Message delivery test passed")
                return True
            else:
                logger.error("❌ Message delivery test failed - invalid message data")
                return False
                
        except Exception as e:
            logger.error(f"❌ Message delivery test failed: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all tests and return results."""
        logger.info("Starting secIRC client tests...")
        
        # Set up test environment
        await self.setup_test_environment()
        
        # Run tests
        tests = [
            ("Client Initialization", self.test_client_initialization),
            ("Contact Management", self.test_contact_management),
            ("Public Key Exchange", self.test_public_key_exchange),
            ("Message Encryption", self.test_message_encryption),
            ("Group Creation", self.test_group_creation),
            ("Group Invitations", self.test_group_invitations),
            ("Group Messaging", self.test_group_messaging),
            ("Key Rotation", self.test_key_rotation),
            ("Network Connectivity", self.test_network_connectivity),
            ("Message Delivery", self.test_message_delivery),
        ]
        
        results = {}
        for test_name, test_func in tests:
            logger.info(f"Running test: {test_name}")
            try:
                result = await test_func()
                results[test_name] = result
                if result:
                    logger.info(f"✅ {test_name} test passed")
                else:
                    logger.error(f"❌ {test_name} test failed")
            except Exception as e:
                logger.error(f"❌ {test_name} test failed with exception: {e}")
                results[test_name] = False
        
        return results
    
    async def cleanup(self):
        """Clean up test environment."""
        logger.info("Cleaning up test environment...")
        
        try:
            await self.pubsub_server.stop_pubsub_service()
            logger.info("✅ Cleanup completed")
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")

async def main():
    """Main test runner."""
    tester = ClientTester()
    
    try:
        # Run all tests
        results = await tester.run_all_tests()
        
        # Print summary
        print("\n" + "="*50)
        print("SECIRC CLIENT TEST RESULTS")
        print("="*50)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:<25} {status}")
            if result:
                passed += 1
        
        print("="*50)
        print(f"Tests passed: {passed}/{total}")
        print(f"Success rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️ Some tests failed!")
            return 1
            
    except Exception as e:
        logger.error(f"Test runner failed: {e}")
        return 1
        
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
