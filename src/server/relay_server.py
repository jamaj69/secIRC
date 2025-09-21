"""
secIRC Relay Server Implementation

This module implements a relay server that can connect to other relay servers
using multiple protocols (TCP, Tor, WebSocket) and maintain a configurable
number of connections.
"""

import asyncio
import yaml
import logging
import signal
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..protocol.relay_connections import (
    RelayConnectionManager, ConnectionConfig, ConnectionType
)
from ..protocol.encryption import EndToEndEncryption
from ..protocol.message_types import MessageType, Message
from ..protocol.pubsub_server import PubSubServer


class RelayServer:
    """Main relay server implementation."""
    
    def __init__(self, config_path: str = "config/relay_connections.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize components
        self.encryption = EndToEndEncryption()
        self.connection_manager = RelayConnectionManager(
            ConnectionConfig(**self.config["connection_manager"]),
            self.encryption
        )
        self.pubsub_server = PubSubServer(self.encryption)
        
        # Server state
        self.is_running = False
        self.server_tasks: List[asyncio.Task] = []
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            return config
            
        except Exception as e:
            print(f"Error loading configuration: {e}")
            # Return default configuration
            return {
                "connection_manager": {
                    "max_connections": 10,
                    "min_connections": 3,
                    "connection_timeout": 30,
                    "heartbeat_interval": 60,
                    "reconnect_interval": 30,
                    "max_retry_attempts": 3,
                    "retry_delay": 30,
                    "enable_tcp": True,
                    "enable_tor": True,
                    "enable_websocket": True,
                    "tcp_port": 6667,
                    "websocket_port": 8080,
                    "tor_port": 9050,
                    "ssl_enabled": True
                }
            }
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        log_level = self.config.get("monitoring", {}).get("log_level", "INFO")
        
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('logs/relay_server.log')
            ]
        )
    
    async def start_server(self) -> None:
        """Start the relay server."""
        try:
            self.logger.info("Starting secIRC Relay Server...")
            
            # Start connection manager
            await self.connection_manager.start_connection_manager()
            
            # Start pubsub server
            await self.pubsub_server.start_pubsub_service()
            
            # Add bootstrap relay connections
            await self._add_bootstrap_connections()
            
            # Start server tasks
            self.server_tasks = [
                asyncio.create_task(self._server_main_loop()),
                asyncio.create_task(self._connection_monitor_loop()),
                asyncio.create_task(self._message_processing_loop())
            ]
            
            self.is_running = True
            self.logger.info("Relay server started successfully")
            
            # Wait for all tasks
            await asyncio.gather(*self.server_tasks, return_exceptions=True)
            
        except Exception as e:
            self.logger.error(f"Error starting relay server: {e}")
            await self.stop_server()
    
    async def stop_server(self) -> None:
        """Stop the relay server."""
        try:
            self.logger.info("Stopping relay server...")
            self.is_running = False
            
            # Cancel server tasks
            for task in self.server_tasks:
                task.cancel()
            
            # Stop components
            await self.connection_manager.stop_connection_manager()
            await self.pubsub_server.stop_pubsub_service()
            
            self.logger.info("Relay server stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping relay server: {e}")
    
    async def _add_bootstrap_connections(self) -> None:
        """Add bootstrap relay connections from configuration."""
        try:
            bootstrap_relays = self.config.get("discovery", {}).get("bootstrap_relays", [])
            
            for relay_config in bootstrap_relays:
                relay_id = relay_config["relay_id"].encode()
                connection_type = ConnectionType(relay_config["connection_type"])
                host = relay_config["host"]
                port = relay_config["port"]
                priority = relay_config.get("priority", 5)
                
                success = await self.connection_manager.add_relay_connection(
                    relay_id, connection_type, host, port, priority
                )
                
                if success:
                    self.logger.info(f"Added bootstrap relay: {relay_config['relay_id']}")
                else:
                    self.logger.warning(f"Failed to add bootstrap relay: {relay_config['relay_id']}")
            
        except Exception as e:
            self.logger.error(f"Error adding bootstrap connections: {e}")
    
    async def _server_main_loop(self) -> None:
        """Main server loop."""
        while self.is_running:
            try:
                # Check connection status
                status = self.connection_manager.get_connection_status()
                active_connections = status["active_connections"]
                min_connections = self.config["connection_manager"]["min_connections"]
                
                if active_connections < min_connections:
                    self.logger.warning(
                        f"Low connection count: {active_connections}/{min_connections}"
                    )
                    # TODO: Trigger connection discovery
                
                # Log server status periodically
                if hasattr(self, '_last_status_log'):
                    if asyncio.get_event_loop().time() - self._last_status_log > 300:  # 5 minutes
                        self._log_server_status()
                        self._last_status_log = asyncio.get_event_loop().time()
                else:
                    self._last_status_log = asyncio.get_event_loop().time()
                
                await asyncio.sleep(10)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in server main loop: {e}")
                await asyncio.sleep(5)
    
    async def _connection_monitor_loop(self) -> None:
        """Monitor connection health and performance."""
        while self.is_running:
            try:
                # Get connection status
                status = self.connection_manager.get_connection_status()
                
                # Log connection statistics
                self.logger.debug(f"Connection status: {status}")
                
                # Check for failed connections
                failed_connections = status["failed_connections"]
                if failed_connections > 0:
                    self.logger.warning(f"Failed connections: {failed_connections}")
                
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in connection monitor loop: {e}")
                await asyncio.sleep(10)
    
    async def _message_processing_loop(self) -> None:
        """Process incoming messages from relay connections."""
        while self.is_running:
            try:
                # Get available connections
                connections = self.connection_manager.get_available_connections()
                
                # Process messages from each connection
                for connection in connections:
                    try:
                        # TODO: Implement message receiving and processing
                        # This would involve receiving messages from connections
                        # and routing them appropriately
                        pass
                        
                    except Exception as e:
                        self.logger.error(f"Error processing messages from {connection.relay_id.hex()}: {e}")
                
                await asyncio.sleep(0.1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in message processing loop: {e}")
                await asyncio.sleep(1)
    
    def _log_server_status(self) -> None:
        """Log current server status."""
        try:
            status = self.connection_manager.get_connection_status()
            pubsub_status = self.pubsub_server.get_pubsub_status()
            
            self.logger.info("=== Relay Server Status ===")
            self.logger.info(f"Active connections: {status['active_connections']}")
            self.logger.info(f"Total connections: {status['total_connections']}")
            self.logger.info(f"Failed connections: {status['failed_connections']}")
            self.logger.info(f"Messages sent: {status['stats']['total_messages_sent']}")
            self.logger.info(f"Messages received: {status['stats']['total_messages_received']}")
            self.logger.info(f"PubSub active: {pubsub_status['active']}")
            self.logger.info(f"Pending messages: {pubsub_status['pending_messages']}")
            self.logger.info("==========================")
            
        except Exception as e:
            self.logger.error(f"Error logging server status: {e}")
    
    def get_server_status(self) -> Dict[str, Any]:
        """Get comprehensive server status."""
        try:
            connection_status = self.connection_manager.get_connection_status()
            pubsub_status = self.pubsub_server.get_pubsub_status()
            
            return {
                "server_running": self.is_running,
                "connections": connection_status,
                "pubsub": pubsub_status,
                "config": {
                    "max_connections": self.config["connection_manager"]["max_connections"],
                    "min_connections": self.config["connection_manager"]["min_connections"],
                    "protocols_enabled": {
                        "tcp": self.config["connection_manager"]["enable_tcp"],
                        "tor": self.config["connection_manager"]["enable_tor"],
                        "websocket": self.config["connection_manager"]["enable_websocket"]
                    }
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting server status: {e}")
            return {"error": str(e)}


async def main():
    """Main entry point for the relay server."""
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Create relay server instance
    server = RelayServer()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}, shutting down...")
        asyncio.create_task(server.stop_server())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start the server
        await server.start_server()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        await server.stop_server()


if __name__ == "__main__":
    asyncio.run(main())