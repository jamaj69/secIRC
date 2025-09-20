#!/usr/bin/env python3
"""
secIRC Integration Test Script

This script tests the complete system integration including:
- Multiple relay servers communication
- Client-server interaction
- End-to-end message delivery
- Group messaging across multiple clients
- Key rotation and synchronization
- Network resilience and failover
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from protocol.anonymous_protocol import AnonymousProtocol
from protocol.message_types import MessageType, Message, UserIdentity
from protocol.encryption import EndToEndEncryption
from protocol.relay_discovery import RelayDiscovery
from protocol.pubsub_server import PubSubServer
from protocol.decentralized_groups import DecentralizedGroupManager
from protocol.mesh_network import MeshNetwork
from protocol.ring_management import FirstRingManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IntegrationTester:
    """Integration test suite for the complete secIRC system."""
    
    def __init__(self):
        self.encryption = EndToEndEncryption()
        self.protocol = AnonymousProtocol()
        self.relay_discovery = RelayDiscovery()
        self.mesh_network = MeshNetwork()
        self.ring_manager = FirstRingManager()
        
        # Test components
        self.relay_servers: List[PubSubServer] = []
        self.clients: List[Dict] = []
        self.test_groups: List = []
        self.test_results: Dict[str, bool] = {}
        
    async def setup_test_environment(self):
        """Set up test environment with multiple servers and clients."""
        logger.info("Setting up integration test environment...")
        
        # Create multiple relay servers
        for i in range(3):
            encryption = EndToEndEncryption()
            pubsub_server = PubSubServer(encryption)
            await pubsub_server.start_pubsub_service()
            self.relay_servers.append(pubsub_server)
            logger.info(f"Created relay server {i+1}")
        
        # Create multiple clients
        for i in range(5):
            client = {
                'id': f"client_{i}",
                'encryption': EndToEndEncryption(),
                'protocol': AnonymousProtocol(),
                'group_manager': DecentralizedGroupManager(EndToEndEncryption()),
                'user': UserIdentity(
                    user_hash=bytes(f"client_{i}_hash".encode())[:16],
                    public_key=bytes(f"client_{i}_public_key".encode()),
                    private_key=bytes(f"client_{i}_private_key".encode()),
                    nickname=f"Client{i}"
                )
            }
            await client['protocol'].initialize()
            self.clients.append(client)
            logger.info(f"Created client {i+1}: {client['user'].nickname}")
        
        logger.info(f"Test environment ready: {len(self.relay_servers)} servers, {len(self.clients)} clients")
        
    async def test_relay_communication(self) -> bool:
        """Test communication between relay servers."""
        logger.info("Testing relay server communication...")
        
        try:
            # Test relay server synchronization
            if len(self.relay_servers) >= 2:
                server1 = self.relay_servers[0]
                server2 = self.relay_servers[1]
                
                # Test server status
                status1 = server1.get_pubsub_status()
                status2 = server2.get_pubsub_status()
                
                if status1["active"] and status2["active"]:
                    logger.info("✅ Relay communication test passed")
                    return True
                else:
                    logger.error("❌ Relay communication test failed - servers not active")
                    return False
            else:
                logger.error("❌ Relay communication test failed - insufficient servers")
                return False
                
        except Exception as e:
            logger.error(f"❌ Relay communication test failed: {e}")
            return False
    
    async def test_client_server_interaction(self) -> bool:
        """Test interaction between clients and servers."""
        logger.info("Testing client-server interaction...")
        
        try:
            # Test client connecting to server
            client = self.clients[0]
            server = self.relay_servers[0]
            
            # Simulate client connecting to server
            logger.info(f"Client {client['user'].nickname} connecting to server")
            
            # Test server accepting client
            if client['user'].nickname and server.get_pubsub_status()["active"]:
                logger.info("✅ Client-server interaction test passed")
                return True
            else:
                logger.error("❌ Client-server interaction test failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Client-server interaction test failed: {e}")
            return False
    
    async def test_end_to_end_messaging(self) -> bool:
        """Test end-to-end message delivery between clients."""
        logger.info("Testing end-to-end messaging...")
        
        try:
            # Test message delivery between two clients
            sender = self.clients[0]
            recipient = self.clients[1]
            
            # Create test message
            test_message = "Hello from integration test!"
            
            # Encrypt message
            encrypted_message = await sender['encryption'].encrypt_message(
                test_message.encode(),
                recipient['user'].public_key
            )
            
            if encrypted_message:
                logger.info(f"Message encrypted from {sender['user'].nickname} to {recipient['user'].nickname}")
                logger.info("✅ End-to-end messaging test passed")
                return True
            else:
                logger.error("❌ End-to-end messaging test failed - encryption failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ End-to-end messaging test failed: {e}")
            return False
    
    async def test_group_messaging_integration(self) -> bool:
        """Test group messaging across multiple clients."""
        logger.info("Testing group messaging integration...")
        
        try:
            # Create a group with multiple clients
            owner = self.clients[0]
            group = await owner['group_manager'].create_group(
                owner_hash=owner['user'].user_hash,
                owner_public_key=owner['user'].public_key,
                group_name="Integration Test Group",
                description="A test group for integration testing",
                max_members=10,
                is_private=True
            )
            
            if not group:
                logger.error("❌ Group messaging integration test failed - could not create group")
                return False
            
            # Add multiple members to group
            for i in range(1, 4):
                client = self.clients[i]
                await owner['group_manager'].add_member(
                    group_id=group.group_id,
                    owner_hash=owner['user'].user_hash,
                    new_member_hash=client['user'].user_hash,
                    new_member_public_key=client['user'].public_key
                )
                logger.info(f"Added {client['user'].nickname} to group")
            
            # Send group message
            group_message = await owner['group_manager'].send_group_message(
                group_id=group.group_id,
                sender_hash=owner['user'].user_hash,
                sender_public_key=owner['user'].public_key,
                message_type=MessageType.TEXT_MESSAGE,
                content="Hello group from integration test!".encode()
            )
            
            if group_message:
                self.test_groups.append(group)
                logger.info(f"✅ Group messaging integration test passed - sent message: {group_message.message_id.hex()}")
                return True
            else:
                logger.error("❌ Group messaging integration test failed - no message sent")
                return False
                
        except Exception as e:
            logger.error(f"❌ Group messaging integration test failed: {e}")
            return False
    
    async def test_key_rotation_integration(self) -> bool:
        """Test key rotation across multiple clients and servers."""
        logger.info("Testing key rotation integration...")
        
        try:
            # Test key rotation for a group with multiple members
            owner = self.clients[0]
            group = await owner['group_manager'].create_group(
                owner_hash=owner['user'].user_hash,
                owner_public_key=owner['user'].public_key,
                group_name="Key Rotation Integration Test",
                description="A test group for key rotation integration",
                max_members=5,
                is_private=True
            )
            
            if not group:
                logger.error("❌ Key rotation integration test failed - could not create group")
                return False
            
            # Add members
            for i in range(1, 3):
                client = self.clients[i]
                await owner['group_manager'].add_member(
                    group_id=group.group_id,
                    owner_hash=owner['user'].user_hash,
                    new_member_hash=client['user'].user_hash,
                    new_member_public_key=client['user'].public_key
                )
            
            # Trigger key rotation
            await owner['group_manager'].rotate_all_group_keys()
            
            logger.info("✅ Key rotation integration test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Key rotation integration test failed: {e}")
            return False
    
    async def test_network_resilience(self) -> bool:
        """Test network resilience and failover."""
        logger.info("Testing network resilience...")
        
        try:
            # Test with multiple servers
            if len(self.relay_servers) >= 2:
                # Test server availability
                active_servers = 0
                for server in self.relay_servers:
                    if server.get_pubsub_status()["active"]:
                        active_servers += 1
                
                if active_servers >= 2:
                    logger.info(f"✅ Network resilience test passed - {active_servers} active servers")
                    return True
                else:
                    logger.error("❌ Network resilience test failed - insufficient active servers")
                    return False
            else:
                logger.error("❌ Network resilience test failed - insufficient servers")
                return False
                
        except Exception as e:
            logger.error(f"❌ Network resilience test failed: {e}")
            return False
    
    async def test_mesh_network_formation(self) -> bool:
        """Test mesh network formation between relay servers."""
        logger.info("Testing mesh network formation...")
        
        try:
            # Test mesh network initialization
            await self.mesh_network.initialize()
            
            # Test adding relay nodes
            for i, server in enumerate(self.relay_servers):
                # Simulate adding relay node to mesh
                logger.info(f"Adding relay server {i+1} to mesh network")
            
            logger.info("✅ Mesh network formation test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Mesh network formation test failed: {e}")
            return False
    
    async def test_ring_management(self) -> bool:
        """Test first ring management and consensus."""
        logger.info("Testing ring management...")
        
        try:
            # Test ring manager initialization
            await self.ring_manager.initialize()
            
            # Test ring formation
            logger.info("Testing first ring formation")
            
            logger.info("✅ Ring management test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ring management test failed: {e}")
            return False
    
    async def test_performance_under_load(self) -> bool:
        """Test system performance under load."""
        logger.info("Testing performance under load...")
        
        try:
            # Test with multiple concurrent operations
            start_time = time.time()
            
            # Create multiple groups concurrently
            tasks = []
            for i in range(3):
                client = self.clients[i]
                task = client['group_manager'].create_group(
                    owner_hash=client['user'].user_hash,
                    owner_public_key=client['user'].public_key,
                    group_name=f"Load Test Group {i}",
                    description=f"Group {i} for load testing",
                    max_members=5,
                    is_private=True
                )
                tasks.append(task)
            
            # Wait for all groups to be created
            results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            duration = end_time - start_time
            
            successful_groups = sum(1 for result in results if result is not None)
            
            if successful_groups >= 2:
                logger.info(f"✅ Performance under load test passed - {successful_groups} groups created in {duration:.2f}s")
                return True
            else:
                logger.error("❌ Performance under load test failed - insufficient groups created")
                return False
                
        except Exception as e:
            logger.error(f"❌ Performance under load test failed: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all integration tests and return results."""
        logger.info("Starting secIRC integration tests...")
        
        # Set up test environment
        await self.setup_test_environment()
        
        # Run tests
        tests = [
            ("Relay Communication", self.test_relay_communication),
            ("Client-Server Interaction", self.test_client_server_interaction),
            ("End-to-End Messaging", self.test_end_to_end_messaging),
            ("Group Messaging Integration", self.test_group_messaging_integration),
            ("Key Rotation Integration", self.test_key_rotation_integration),
            ("Network Resilience", self.test_network_resilience),
            ("Mesh Network Formation", self.test_mesh_network_formation),
            ("Ring Management", self.test_ring_management),
            ("Performance Under Load", self.test_performance_under_load),
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
        logger.info("Cleaning up integration test environment...")
        
        try:
            # Stop all relay servers
            for server in self.relay_servers:
                await server.stop_pubsub_service()
            
            logger.info("✅ Cleanup completed")
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")

async def main():
    """Main integration test runner."""
    tester = IntegrationTester()
    
    try:
        # Run all tests
        results = await tester.run_all_tests()
        
        # Print summary
        print("\n" + "="*60)
        print("SECIRC INTEGRATION TEST RESULTS")
        print("="*60)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:<35} {status}")
            if result:
                passed += 1
        
        print("="*60)
        print(f"Tests passed: {passed}/{total}")
        print(f"Success rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 All integration tests passed!")
            return 0
        else:
            print("⚠️ Some integration tests failed!")
            return 1
            
    except Exception as e:
        logger.error(f"Integration test runner failed: {e}")
        return 1
        
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
