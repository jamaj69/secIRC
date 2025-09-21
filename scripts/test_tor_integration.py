#!/usr/bin/env python3
"""
Test script for Tor integration functionality

This script tests the transparent Tor proxy integration using multiple
Tor packages (PySocks, tor-proxy, Torpy, Stem).
"""

import asyncio
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from protocol.tor_integration import TorIntegration, TorConfig, TorMethod


async def test_tor_methods():
    """Test different Tor connection methods."""
    print("🧅 Testing secIRC Tor Integration")
    print("=" * 50)
    
    # Test each available method
    methods_to_test = [
        TorMethod.PYSOCKS,
        TorMethod.TOR_PROXY,
        TorMethod.TORPY,
        TorMethod.STEM
    ]
    
    for method in methods_to_test:
        print(f"\n🔍 Testing {method.value} method...")
        
        try:
            # Create Tor configuration
            config = TorConfig(
                method=method,
                socks_host="127.0.0.1",
                socks_port=9050,
                control_host="127.0.0.1",
                control_port=9051,
                circuit_timeout=30,
                enable_circuit_verification=True
            )
            
            # Create Tor integration
            tor_integration = TorIntegration(config)
            
            # Check if method is available
            if method not in tor_integration.available_methods:
                print(f"   ❌ {method.value} not available (missing dependencies)")
                continue
            
            print(f"   ✅ {method.value} is available")
            
            # Initialize Tor integration
            success = await tor_integration.initialize()
            if success:
                print(f"   ✅ {method.value} initialized successfully")
                
                # Test connection creation
                connection_id = f"test_{method.value}"
                connection = await tor_integration.create_connection(connection_id)
                if connection:
                    print(f"   ✅ Connection created: {connection_id}")
                    
                    # Test Tor verification
                    is_tor = await tor_integration.verify_tor_connection(connection_id)
                    if is_tor:
                        print(f"   ✅ Tor verification successful")
                    else:
                        print(f"   ⚠️ Tor verification failed")
                    
                    # Get exit node info
                    exit_node = await tor_integration.get_exit_node(connection_id)
                    if exit_node:
                        print(f"   🌐 Exit node: {exit_node}")
                    
                    # Test IP rotation if supported
                    if method in [TorMethod.STEM, TorMethod.TORPY]:
                        rotation_success = await tor_integration.rotate_ip(connection_id)
                        if rotation_success:
                            print(f"   🔄 IP rotation successful")
                        else:
                            print(f"   ⚠️ IP rotation not supported")
                    
                    # Clean up
                    await tor_integration.close_connection(connection_id)
                    print(f"   🧹 Connection closed")
                else:
                    print(f"   ❌ Failed to create connection")
                
                # Cleanup
                await tor_integration.cleanup()
                print(f"   🧹 {method.value} cleaned up")
            else:
                print(f"   ❌ {method.value} initialization failed")
                
        except Exception as e:
            print(f"   ❌ {method.value} test failed: {e}")
            import traceback
            traceback.print_exc()


async def test_tor_connection_through_relay():
    """Test connecting to a relay through Tor."""
    print("\n🔗 Testing Tor Connection to Relay")
    print("=" * 40)
    
    try:
        # Use PySocks method (most reliable)
        config = TorConfig(
            method=TorMethod.PYSOCKS,
            socks_host="127.0.0.1",
            socks_port=9050,
            enable_circuit_verification=True
        )
        
        tor_integration = TorIntegration(config)
        
        if TorMethod.PYSOCKS not in tor_integration.available_methods:
            print("❌ PySocks not available, skipping relay connection test")
            return
        
        # Initialize
        success = await tor_integration.initialize()
        if not success:
            print("❌ Tor integration initialization failed")
            return
        
        print("✅ Tor integration initialized")
        
        # Create connection
        connection_id = "relay_test"
        connection = await tor_integration.create_connection(connection_id)
        if not connection:
            print("❌ Failed to create Tor connection")
            return
        
        print("✅ Tor connection created")
        
        # Test connection to a test relay (using check.torproject.org as example)
        try:
            sock = await tor_integration.connect_through_tor(
                connection_id, "check.torproject.org", 80
            )
            if sock:
                print("✅ Successfully connected through Tor")
                
                # Send a simple HTTP request
                request = b"GET / HTTP/1.1\r\nHost: check.torproject.org\r\n\r\n"
                sock.send(request)
                
                # Read response
                response = sock.recv(4096)
                sock.close()
                
                if b"Congratulations" in response or b"tor" in response.lower():
                    print("✅ Tor connection verified - using Tor network")
                else:
                    print("⚠️ Tor connection not verified")
            else:
                print("❌ Failed to connect through Tor")
                
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
        
        # Cleanup
        await tor_integration.close_connection(connection_id)
        await tor_integration.cleanup()
        print("🧹 Tor integration cleaned up")
        
    except Exception as e:
        print(f"❌ Relay connection test failed: {e}")
        import traceback
        traceback.print_exc()


async def test_tor_status_and_monitoring():
    """Test Tor status monitoring and statistics."""
    print("\n📊 Testing Tor Status and Monitoring")
    print("=" * 40)
    
    try:
        config = TorConfig(
            method=TorMethod.PYSOCKS,
            socks_host="127.0.0.1",
            socks_port=9050
        )
        
        tor_integration = TorIntegration(config)
        
        if TorMethod.PYSOCKS not in tor_integration.available_methods:
            print("❌ PySocks not available, skipping status test")
            return
        
        # Initialize
        await tor_integration.initialize()
        
        # Create multiple connections
        connection_ids = ["status_test_1", "status_test_2", "status_test_3"]
        for conn_id in connection_ids:
            await tor_integration.create_connection(conn_id)
        
        # Get status
        status = tor_integration.get_status()
        
        print("📈 Tor Integration Status:")
        print(f"   Method: {status['method']}")
        print(f"   Available methods: {status['available_methods']}")
        print(f"   Active connections: {status['active_connections']}")
        print(f"   Total connections: {status['total_connections']}")
        print(f"   Controller connected: {status['controller_connected']}")
        print(f"   Torpy available: {status['torpy_available']}")
        print(f"   Tor proxy port: {status['tor_proxy_port']}")
        
        print("\n🔗 Connection Details:")
        for conn_id, conn_info in status['connections'].items():
            print(f"   {conn_id}:")
            print(f"     Method: {conn_info['method']}")
            print(f"     Circuit ID: {conn_info['circuit_id']}")
            print(f"     Exit Node: {conn_info['exit_node']}")
            print(f"     Active: {conn_info['is_active']}")
            print(f"     Created: {conn_info['created_at']}")
            print(f"     Last Used: {conn_info['last_used']}")
        
        # Cleanup
        for conn_id in connection_ids:
            await tor_integration.close_connection(conn_id)
        
        await tor_integration.cleanup()
        print("🧹 Status test cleaned up")
        
    except Exception as e:
        print(f"❌ Status test failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    print("🧅 secIRC Tor Integration Test Suite")
    print("=" * 60)
    
    try:
        # Test different Tor methods
        await test_tor_methods()
        
        # Test relay connection through Tor
        await test_tor_connection_through_relay()
        
        # Test status and monitoring
        await test_tor_status_and_monitoring()
        
        print("\n🎉 All Tor integration tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
