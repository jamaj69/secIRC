#!/usr/bin/env python3
"""
Example: Using secIRC Relay Connection System

This example demonstrates how to set up and use the relay connection
system with multiple protocols (TCP, Tor, WebSocket).
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from protocol.relay_connections import (
    RelayConnectionManager, ConnectionConfig, ConnectionType
)
from protocol.encryption import EndToEndEncryption


async def example_relay_connections():
    """Example of setting up relay connections."""
    print("🔗 secIRC Relay Connection Example")
    print("=" * 40)
    
    # 1. Initialize encryption
    encryption = EndToEndEncryption()
    
    # 2. Configure connection parameters
    config = ConnectionConfig(
        max_connections=10,      # Maximum 10 relay connections
        min_connections=3,       # Maintain at least 3 connections
        connection_timeout=30,   # 30 second connection timeout
        heartbeat_interval=60,   # Send heartbeat every 60 seconds
        reconnect_interval=30,   # Try to reconnect every 30 seconds
        max_retry_attempts=3,    # Try 3 times before giving up
        retry_delay=30,          # Wait 30 seconds between retries
        
        # Protocol settings
        enable_tcp=True,         # Enable TCP connections
        enable_tor=True,         # Enable Tor connections
        enable_websocket=True,   # Enable WebSocket connections
        
        # Port configurations
        tcp_port=6667,           # Default TCP port
        websocket_port=8080,     # Default WebSocket port
        tor_port=9050,           # Tor SOCKS port
        
        # Security
        ssl_enabled=True,        # Enable SSL/TLS encryption
    )
    
    # 3. Create connection manager
    connection_manager = RelayConnectionManager(config, encryption)
    
    try:
        # 4. Start the connection manager
        print("🚀 Starting connection manager...")
        await connection_manager.start_connection_manager()
        
        # 5. Add relay connections
        print("\n📡 Adding relay connections...")
        
        # Add TCP connection
        await connection_manager.add_relay_connection(
            relay_id=b"relay_tcp_1",
            connection_type=ConnectionType.TCP,
            host="relay1.secirc.net",
            port=6667,
            priority=8  # High priority
        )
        print("   ✅ Added TCP relay connection")
        
        # Add WebSocket connection
        await connection_manager.add_relay_connection(
            relay_id=b"relay_ws_1",
            connection_type=ConnectionType.WEBSOCKET,
            host="relay2.secirc.net",
            port=8080,
            priority=7  # High priority
        )
        print("   ✅ Added WebSocket relay connection")
        
        # Add Tor connection
        await connection_manager.add_relay_connection(
            relay_id=b"relay_tor_1",
            connection_type=ConnectionType.TOR,
            host="relay3.onion",
            port=6667,
            priority=6  # Medium priority
        )
        print("   ✅ Added Tor relay connection")
        
        # 6. Monitor connections
        print("\n📊 Monitoring connections...")
        for i in range(5):
            status = connection_manager.get_connection_status()
            print(f"   Status {i+1}: {status['active_connections']} active, "
                  f"{status['failed_connections']} failed")
            await asyncio.sleep(2)
        
        # 7. Send test messages
        print("\n📤 Sending test messages...")
        test_message = {
            "type": "test",
            "content": "Hello from relay connection example",
            "timestamp": int(asyncio.get_event_loop().time())
        }
        
        sent_count = await connection_manager.broadcast_message(test_message)
        print(f"   📨 Sent {sent_count} test messages")
        
        # 8. Get available connections
        print("\n🔗 Available connections:")
        available = connection_manager.get_available_connections()
        for conn in available:
            print(f"   - {conn.relay_id.hex()}: {conn.connection_type.value}://{conn.host}:{conn.port}")
        
        print("\n✅ Example completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 9. Clean up
        print("\n🛑 Stopping connection manager...")
        await connection_manager.stop_connection_manager()
        print("✅ Connection manager stopped")


async def example_connection_configuration():
    """Example of different connection configurations."""
    print("\n⚙️ Connection Configuration Examples")
    print("=" * 40)
    
    # Example 1: High-performance configuration
    print("1. High-Performance Configuration:")
    perf_config = ConnectionConfig(
        max_connections=20,
        min_connections=10,
        connection_timeout=10,
        heartbeat_interval=30,
        enable_tcp=True,
        enable_websocket=True,
        enable_tor=False,  # Disable Tor for better performance
        ssl_enabled=True
    )
    print(f"   Max connections: {perf_config.max_connections}")
    print(f"   Min connections: {perf_config.min_connections}")
    print(f"   Tor enabled: {perf_config.enable_tor}")
    
    # Example 2: Privacy-focused configuration
    print("\n2. Privacy-Focused Configuration:")
    privacy_config = ConnectionConfig(
        max_connections=5,
        min_connections=2,
        connection_timeout=60,
        heartbeat_interval=120,
        enable_tcp=False,  # Disable direct TCP
        enable_websocket=False,  # Disable WebSocket
        enable_tor=True,  # Only use Tor
        ssl_enabled=True
    )
    print(f"   Max connections: {privacy_config.max_connections}")
    print(f"   TCP enabled: {privacy_config.enable_tcp}")
    print(f"   Tor enabled: {privacy_config.enable_tor}")
    
    # Example 3: Balanced configuration
    print("\n3. Balanced Configuration:")
    balanced_config = ConnectionConfig(
        max_connections=10,
        min_connections=3,
        connection_timeout=30,
        heartbeat_interval=60,
        enable_tcp=True,
        enable_websocket=True,
        enable_tor=True,
        ssl_enabled=True
    )
    print(f"   Max connections: {balanced_config.max_connections}")
    print(f"   All protocols enabled: {balanced_config.enable_tcp and balanced_config.enable_websocket and balanced_config.enable_tor}")


async def main():
    """Main example function."""
    print("🔗 secIRC Relay Connection Examples")
    print("=" * 50)
    
    try:
        # Show configuration examples
        await example_connection_configuration()
        
        # Run main example
        await example_relay_connections()
        
        print("\n🎉 All examples completed!")
        
    except Exception as e:
        print(f"\n❌ Examples failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
