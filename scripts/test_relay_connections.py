#!/usr/bin/env python3
"""
Test script for relay connection functionality

This script tests the multi-protocol relay connection system including
TCP, Tor, and WebSocket connections.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from protocol.relay_connections import (
    RelayConnectionManager, ConnectionConfig, ConnectionType, ConnectionStatus
)
from protocol.encryption import EndToEndEncryption


async def test_relay_connections():
    """Test relay connection functionality."""
    print("🧪 Testing secIRC Relay Connections")
    print("=" * 50)
    
    # Initialize encryption
    encryption = EndToEndEncryption()
    
    # Create connection configuration
    config = ConnectionConfig(
        max_connections=5,
        min_connections=2,
        connection_timeout=10,
        heartbeat_interval=30,
        reconnect_interval=15,
        enable_tcp=True,
        enable_tor=False,  # Disable Tor for testing (requires Tor daemon)
        enable_websocket=True,
        ssl_enabled=False  # Disable SSL for testing
    )
    
    # Create connection manager
    connection_manager = RelayConnectionManager(config, encryption)
    
    try:
        # Start connection manager
        print("🚀 Starting connection manager...")
        await connection_manager.start_connection_manager()
        
        # Test 1: Add TCP connection
        print("\n📡 Test 1: Adding TCP connection...")
        relay_id_1 = b"test_relay_1"
        success = await connection_manager.add_relay_connection(
            relay_id_1, ConnectionType.TCP, "127.0.0.1", 6667, priority=5
        )
        print(f"   TCP connection added: {success}")
        
        # Test 2: Add WebSocket connection
        print("\n🌐 Test 2: Adding WebSocket connection...")
        relay_id_2 = b"test_relay_2"
        success = await connection_manager.add_relay_connection(
            relay_id_2, ConnectionType.WEBSOCKET, "127.0.0.1", 8080, priority=7
        )
        print(f"   WebSocket connection added: {success}")
        
        # Test 3: Add Tor connection (will fail without Tor daemon)
        print("\n🧅 Test 3: Adding Tor connection...")
        relay_id_3 = b"test_relay_3"
        success = await connection_manager.add_relay_connection(
            relay_id_3, ConnectionType.TOR, "example.onion", 6667, priority=3
        )
        print(f"   Tor connection added: {success}")
        
        # Test 4: Check connection status
        print("\n📊 Test 4: Checking connection status...")
        status = connection_manager.get_connection_status()
        print(f"   Total connections: {status['total_connections']}")
        print(f"   Active connections: {status['active_connections']}")
        print(f"   Failed connections: {status['failed_connections']}")
        
        # Test 5: Wait for connection attempts
        print("\n⏳ Test 5: Waiting for connection attempts...")
        await asyncio.sleep(5)
        
        # Check status again
        status = connection_manager.get_connection_status()
        print(f"   After 5 seconds:")
        print(f"   - Total connections: {status['total_connections']}")
        print(f"   - Active connections: {status['active_connections']}")
        print(f"   - Failed connections: {status['failed_connections']}")
        
        # Test 6: Test message sending (to failed connections)
        print("\n📤 Test 6: Testing message sending...")
        test_message = {
            "type": "test",
            "content": "Hello from test script",
            "timestamp": int(time.time())
        }
        
        sent_count = await connection_manager.broadcast_message(test_message)
        print(f"   Messages sent: {sent_count}")
        
        # Test 7: Get available connections
        print("\n🔗 Test 7: Getting available connections...")
        available_connections = connection_manager.get_available_connections()
        print(f"   Available connections: {len(available_connections)}")
        
        for conn in available_connections:
            print(f"   - {conn.relay_id.hex()}: {conn.connection_type.value}://{conn.host}:{conn.port}")
        
        # Test 8: Remove a connection
        print("\n🗑️ Test 8: Removing a connection...")
        success = await connection_manager.remove_relay_connection(relay_id_1)
        print(f"   Connection removed: {success}")
        
        # Final status
        print("\n📈 Final Status:")
        final_status = connection_manager.get_connection_status()
        print(f"   Total connections: {final_status['total_connections']}")
        print(f"   Active connections: {final_status['active_connections']}")
        print(f"   Failed connections: {final_status['failed_connections']}")
        print(f"   Messages sent: {final_status['stats']['total_messages_sent']}")
        print(f"   Messages received: {final_status['stats']['total_messages_received']}")
        
        print("\n✅ Relay connection tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Stop connection manager
        print("\n🛑 Stopping connection manager...")
        await connection_manager.stop_connection_manager()
        print("✅ Connection manager stopped")


async def test_connection_configuration():
    """Test connection configuration loading."""
    print("\n🔧 Testing Connection Configuration")
    print("=" * 40)
    
    # Test default configuration
    config = ConnectionConfig()
    print(f"Default max connections: {config.max_connections}")
    print(f"Default min connections: {config.min_connections}")
    print(f"TCP enabled: {config.enable_tcp}")
    print(f"Tor enabled: {config.enable_tor}")
    print(f"WebSocket enabled: {config.enable_websocket}")
    print(f"SSL enabled: {config.ssl_enabled}")
    
    # Test custom configuration
    custom_config = ConnectionConfig(
        max_connections=15,
        min_connections=5,
        enable_tor=False,
        ssl_enabled=True
    )
    print(f"\nCustom max connections: {custom_config.max_connections}")
    print(f"Custom min connections: {custom_config.min_connections}")
    print(f"Custom Tor enabled: {custom_config.enable_tor}")
    print(f"Custom SSL enabled: {custom_config.ssl_enabled}")


async def main():
    """Main test function."""
    print("🧪 secIRC Relay Connection Test Suite")
    print("=" * 50)
    
    try:
        # Test configuration
        await test_connection_configuration()
        
        # Test relay connections
        await test_relay_connections()
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
