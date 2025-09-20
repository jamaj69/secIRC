#!/usr/bin/env python3
"""
secIRC Relay Server Main Entry Point

Anonymous, censorship-resistant relay server for messaging.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from server.relay_server import RelayServer


async def main():
    """Main entry point."""
    print("🌐 secIRC Anonymous Relay Server")
    print("=" * 50)
    
    # Check if config file exists
    config_path = "config/server.yaml"
    if not os.path.exists(config_path):
        print(f"⚠️  Configuration file not found: {config_path}")
        print("   Using default configuration...")
    
    # Create and start server
    server = RelayServer(config_path)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
