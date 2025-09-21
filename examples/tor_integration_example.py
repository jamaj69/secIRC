#!/usr/bin/env python3
"""
Example: Using secIRC Transparent Tor Integration

This example demonstrates how to use the transparent Tor proxy integration
with different Tor packages for anonymous relay connections.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from protocol.tor_integration import TorIntegration, TorConfig, TorMethod
from protocol.relay_connections import RelayConnectionManager, ConnectionConfig, ConnectionType
from protocol.encryption import EndToEndEncryption


async def example_tor_methods():
    """Example of different Tor connection methods."""
    print("🧅 Tor Integration Methods Example")
    print("=" * 40)
    
    # Example 1: PySocks (most common)
    print("1. PySocks Method (SOCKS5 proxy):")
    pysocks_config = TorConfig(
        method=TorMethod.PYSOCKS,
        socks_host="127.0.0.1",
        socks_port=9050,
        enable_circuit_verification=True
    )
    
    tor_integration = TorIntegration(pysocks_config)
    if TorMethod.PYSOCKS in tor_integration.available_methods:
        print("   ✅ PySocks available")
        success = await tor_integration.initialize()
        print(f"   Initialization: {'✅ Success' if success else '❌ Failed'}")
        if success:
            await tor_integration.cleanup()
    else:
        print("   ❌ PySocks not available (install PySocks)")
    
    # Example 2: tor-proxy package
    print("\n2. tor-proxy Package:")
    tor_proxy_config = TorConfig(
        method=TorMethod.TOR_PROXY,
        enable_ip_rotation=True,
        ip_rotation_interval=300
    )
    
    tor_integration = TorIntegration(tor_proxy_config)
    if TorMethod.TOR_PROXY in tor_integration.available_methods:
        print("   ✅ tor-proxy available")
        success = await tor_integration.initialize()
        print(f"   Initialization: {'✅ Success' if success else '❌ Failed'}")
        if success:
            await tor_integration.cleanup()
    else:
        print("   ❌ tor-proxy not available (install tor-proxy)")
    
    # Example 3: Torpy (pure Python)
    print("\n3. Torpy Method (pure Python):")
    torpy_config = TorConfig(
        method=TorMethod.TORPY,
        enable_circuit_verification=True,
        circuit_timeout=60
    )
    
    tor_integration = TorIntegration(torpy_config)
    if TorMethod.TORPY in tor_integration.available_methods:
        print("   ✅ Torpy available")
        success = await tor_integration.initialize()
        print(f"   Initialization: {'✅ Success' if success else '❌ Failed'}")
        if success:
            await tor_integration.cleanup()
    else:
        print("   ❌ Torpy not available (install torpy)")
    
    # Example 4: Stem (Tor controller)
    print("\n4. Stem Method (Tor controller):")
    stem_config = TorConfig(
        method=TorMethod.STEM,
        control_host="127.0.0.1",
        control_port=9051,
        enable_ip_rotation=True,
        ip_rotation_interval=300
    )
    
    tor_integration = TorIntegration(stem_config)
    if TorMethod.STEM in tor_integration.available_methods:
        print("   ✅ Stem available")
        success = await tor_integration.initialize()
        print(f"   Initialization: {'✅ Success' if success else '❌ Failed'}")
        if success:
            await tor_integration.cleanup()
    else:
        print("   ❌ Stem not available (install stem)")


async def example_transparent_tor_usage():
    """Example of transparent Tor usage in relay connections."""
    print("\n🔗 Transparent Tor Usage Example")
    print("=" * 40)
    
    try:
        # Initialize encryption
        encryption = EndToEndEncryption()
        
        # Configure relay connections with Tor support
        config = ConnectionConfig(
            max_connections=5,
            min_connections=2,
            enable_tcp=True,
            enable_tor=True,  # Enable Tor support
            enable_websocket=True,
            tor_port=9050,    # Tor SOCKS port
            ssl_enabled=False  # Disable SSL for testing
        )
        
        # Create connection manager
        connection_manager = RelayConnectionManager(config, encryption)
        
        # Start connection manager (this initializes Tor integration)
        await connection_manager.start_connection_manager()
        print("✅ Connection manager started with Tor support")
        
        # Add a Tor connection to a relay
        await connection_manager.add_relay_connection(
            relay_id=b"tor_relay_1",
            connection_type=ConnectionType.TOR,
            host="example.onion",  # Example .onion address
            port=6667,
            priority=8
        )
        print("✅ Added Tor relay connection")
        
        # Add a regular TCP connection for comparison
        await connection_manager.add_relay_connection(
            relay_id=b"tcp_relay_1",
            connection_type=ConnectionType.TCP,
            host="relay.example.com",
            port=6667,
            priority=7
        )
        print("✅ Added TCP relay connection")
        
        # Monitor connections
        print("\n📊 Connection Status:")
        status = connection_manager.get_connection_status()
        print(f"   Total connections: {status['total_connections']}")
        print(f"   Active connections: {status['active_connections']}")
        print(f"   Failed connections: {status['failed_connections']}")
        
        # Wait a bit for connection attempts
        print("\n⏳ Waiting for connection attempts...")
        await asyncio.sleep(5)
        
        # Check status again
        status = connection_manager.get_connection_status()
        print(f"   After 5 seconds:")
        print(f"   - Total connections: {status['total_connections']}")
        print(f"   - Active connections: {status['active_connections']}")
        print(f"   - Failed connections: {status['failed_connections']}")
        
        # Get available connections
        available = connection_manager.get_available_connections()
        print(f"\n🔗 Available connections: {len(available)}")
        for conn in available:
            print(f"   - {conn.relay_id.hex()}: {conn.connection_type.value}://{conn.host}:{conn.port}")
        
        # Cleanup
        await connection_manager.stop_connection_manager()
        print("🧹 Connection manager stopped")
        
    except Exception as e:
        print(f"❌ Example failed: {e}")
        import traceback
        traceback.print_exc()


async def example_tor_verification():
    """Example of Tor connection verification."""
    print("\n🔍 Tor Verification Example")
    print("=" * 30)
    
    try:
        # Create Tor integration with verification enabled
        config = TorConfig(
            method=TorMethod.PYSOCKS,
            socks_host="127.0.0.1",
            socks_port=9050,
            enable_circuit_verification=True,
            circuit_timeout=30
        )
        
        tor_integration = TorIntegration(config)
        
        if TorMethod.PYSOCKS not in tor_integration.available_methods:
            print("❌ PySocks not available, skipping verification example")
            return
        
        # Initialize
        success = await tor_integration.initialize()
        if not success:
            print("❌ Tor integration initialization failed")
            return
        
        print("✅ Tor integration initialized")
        
        # Create connection
        connection_id = "verification_test"
        connection = await tor_integration.create_connection(connection_id)
        if not connection:
            print("❌ Failed to create Tor connection")
            return
        
        print("✅ Tor connection created")
        
        # Verify Tor connection
        print("🔍 Verifying Tor connection...")
        is_tor = await tor_integration.verify_tor_connection(connection_id)
        
        if is_tor:
            print("✅ Tor verification successful - using Tor network")
            
            # Get exit node information
            exit_node = await tor_integration.get_exit_node(connection_id)
            if exit_node:
                print(f"🌐 Exit node: {exit_node}")
        else:
            print("❌ Tor verification failed - not using Tor network")
        
        # Test IP rotation if supported
        if TorMethod.STEM in tor_integration.available_methods:
            print("🔄 Testing IP rotation...")
            rotation_success = await tor_integration.rotate_ip(connection_id)
            if rotation_success:
                print("✅ IP rotation successful")
            else:
                print("⚠️ IP rotation not supported with current method")
        
        # Get detailed status
        status = tor_integration.get_status()
        print(f"\n📊 Tor Integration Status:")
        print(f"   Method: {status['method']}")
        print(f"   Active connections: {status['active_connections']}")
        print(f"   Controller connected: {status['controller_connected']}")
        
        # Cleanup
        await tor_integration.close_connection(connection_id)
        await tor_integration.cleanup()
        print("🧹 Tor integration cleaned up")
        
    except Exception as e:
        print(f"❌ Verification example failed: {e}")
        import traceback
        traceback.print_exc()


async def example_tor_configuration_options():
    """Example of different Tor configuration options."""
    print("\n⚙️ Tor Configuration Options Example")
    print("=" * 40)
    
    # Example 1: Basic configuration
    print("1. Basic Configuration:")
    basic_config = TorConfig(
        method=TorMethod.PYSOCKS,
        socks_host="127.0.0.1",
        socks_port=9050
    )
    print(f"   Method: {basic_config.method.value}")
    print(f"   SOCKS: {basic_config.socks_host}:{basic_config.socks_port}")
    print(f"   Circuit timeout: {basic_config.circuit_timeout}s")
    
    # Example 2: Advanced configuration with IP rotation
    print("\n2. Advanced Configuration with IP Rotation:")
    advanced_config = TorConfig(
        method=TorMethod.STEM,
        socks_host="127.0.0.1",
        socks_port=9050,
        control_host="127.0.0.1",
        control_port=9051,
        enable_ip_rotation=True,
        ip_rotation_interval=300,  # 5 minutes
        enable_circuit_verification=True,
        circuit_timeout=60,
        max_circuit_dirtiness=600
    )
    print(f"   Method: {advanced_config.method.value}")
    print(f"   SOCKS: {advanced_config.socks_host}:{advanced_config.socks_port}")
    print(f"   Control: {advanced_config.control_host}:{advanced_config.control_port}")
    print(f"   IP rotation: {advanced_config.enable_ip_rotation}")
    print(f"   Rotation interval: {advanced_config.ip_rotation_interval}s")
    print(f"   Circuit verification: {advanced_config.enable_circuit_verification}")
    
    # Example 3: Privacy-focused configuration
    print("\n3. Privacy-Focused Configuration:")
    privacy_config = TorConfig(
        method=TorMethod.TORPY,  # Pure Python, no external dependencies
        enable_ip_rotation=True,
        ip_rotation_interval=180,  # 3 minutes
        enable_circuit_verification=True,
        circuit_timeout=120,  # Longer timeout for better privacy
        max_circuit_dirtiness=300  # Shorter circuit lifetime
    )
    print(f"   Method: {privacy_config.method.value}")
    print(f"   IP rotation: {privacy_config.enable_ip_rotation}")
    print(f"   Rotation interval: {privacy_config.ip_rotation_interval}s")
    print(f"   Circuit timeout: {privacy_config.circuit_timeout}s")
    print(f"   Max circuit dirtiness: {privacy_config.max_circuit_dirtiness}s")


async def main():
    """Main example function."""
    print("🧅 secIRC Transparent Tor Integration Examples")
    print("=" * 60)
    
    try:
        # Show different Tor methods
        await example_tor_methods()
        
        # Show transparent usage in relay connections
        await example_transparent_tor_usage()
        
        # Show Tor verification
        await example_tor_verification()
        
        # Show configuration options
        await example_tor_configuration_options()
        
        print("\n🎉 All Tor integration examples completed!")
        
    except Exception as e:
        print(f"\n❌ Examples failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
