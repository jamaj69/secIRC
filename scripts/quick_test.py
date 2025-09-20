#!/usr/bin/env python3
"""
secIRC Quick Test Script

This script provides a quick way to test basic secIRC functionality
without setting up the full test environment.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def print_header(title):
    """Print a formatted header."""
    print("\n" + "="*50)
    print(f" {title}")
    print("="*50)

def print_test_result(test_name, success, message=""):
    """Print test result with formatting."""
    status = "✅ PASSED" if success else "❌ FAILED"
    print(f"{test_name:<30} {status}")
    if message:
        print(f"  {message}")

async def quick_test():
    """Run a quick test of basic functionality."""
    print_header("secIRC Quick Test")
    
    results = []
    
    # Test 1: Basic imports
    try:
        from protocol.anonymous_protocol import AnonymousProtocol
        from protocol.message_types import MessageType, Message, UserIdentity
        from protocol.encryption import EndToEndEncryption
        print_test_result("Import Test", True, "All modules imported successfully")
        results.append(True)
    except Exception as e:
        print_test_result("Import Test", False, f"Import failed: {e}")
        results.append(False)
        return results
    
    # Test 2: Encryption initialization
    try:
        encryption = EndToEndEncryption()
        print_test_result("Encryption Init", True, "Encryption system initialized")
        results.append(True)
    except Exception as e:
        print_test_result("Encryption Init", False, f"Encryption failed: {e}")
        results.append(False)
    
    # Test 3: Protocol initialization
    try:
        protocol = AnonymousProtocol()
        await protocol.initialize()
        print_test_result("Protocol Init", True, "Protocol initialized")
        results.append(True)
    except Exception as e:
        print_test_result("Protocol Init", False, f"Protocol failed: {e}")
        results.append(False)
    
    # Test 4: User identity creation
    try:
        user = UserIdentity(
            user_hash=b"test_user_hash",
            public_key=b"test_public_key",
            private_key=b"test_private_key",
            nickname="TestUser"
        )
        print_test_result("User Identity", True, f"User created: {user.nickname}")
        results.append(True)
    except Exception as e:
        print_test_result("User Identity", False, f"User creation failed: {e}")
        results.append(False)
    
    # Test 5: Message creation
    try:
        message = Message(
            message_type=MessageType.TEXT_MESSAGE,
            content=b"Hello, secIRC!",
            sender_hash=b"sender_hash",
            recipient_hash=b"recipient_hash",
            timestamp=int(time.time())
        )
        print_test_result("Message Creation", True, f"Message created: {message.content.decode()}")
        results.append(True)
    except Exception as e:
        print_test_result("Message Creation", False, f"Message creation failed: {e}")
        results.append(False)
    
    # Test 6: Group manager initialization
    try:
        from protocol.decentralized_groups import DecentralizedGroupManager
        group_manager = DecentralizedGroupManager(encryption)
        print_test_result("Group Manager", True, "Group manager initialized")
        results.append(True)
    except Exception as e:
        print_test_result("Group Manager", False, f"Group manager failed: {e}")
        results.append(False)
    
    # Test 7: PubSub server initialization
    try:
        from protocol.pubsub_server import PubSubServer
        pubsub_server = PubSubServer(encryption)
        print_test_result("PubSub Server", True, "PubSub server initialized")
        results.append(True)
    except Exception as e:
        print_test_result("PubSub Server", False, f"PubSub server failed: {e}")
        results.append(False)
    
    return results

def main():
    """Main function."""
    print("🚀 secIRC Quick Test")
    print("This script tests basic functionality without full setup.")
    
    try:
        # Run quick test
        results = asyncio.run(quick_test())
        
        # Print summary
        print_header("Test Summary")
        passed = sum(results)
        total = len(results)
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        print(f"Tests passed: {passed}/{total}")
        print(f"Success rate: {success_rate:.1f}%")
        
        if passed == total:
            print("\n🎉 All quick tests passed!")
            print("The secIRC system is ready for more comprehensive testing.")
            print("\nNext steps:")
            print("- Run full tests: ./scripts/run_tests.sh")
            print("- Start test servers: ./scripts/start_test_servers.sh")
            print("- Run Docker tests: ./scripts/test_docker.sh")
            return 0
        else:
            print(f"\n⚠️ {total - passed} tests failed.")
            print("Please check the error messages above and fix any issues.")
            return 1
            
    except Exception as e:
        print(f"\n❌ Quick test failed with exception: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
