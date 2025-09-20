#!/bin/bash

# secIRC Test Server Starter Script
# This script starts multiple test relay servers for testing

set -e

echo "🚀 secIRC Test Server Starter"
echo "============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "SUCCESS")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️ $message${NC}"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️ $message${NC}"
            ;;
    esac
}

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    print_status "ERROR" "Please run this script from the secIRC root directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_status "WARNING" "Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
print_status "INFO" "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
print_status "INFO" "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
print_status "INFO" "Creating necessary directories..."
mkdir -p logs test_data data temp uploads

# Function to start a test server
start_test_server() {
    local server_id=$1
    local port=$2
    local ssl_port=$3
    
    print_status "INFO" "Starting test server $server_id on port $port..."
    
    # Create server-specific config
    cat > "config/test_server_${server_id}.yaml" << EOF
server:
  host: "127.0.0.1"
  port: $port
  ssl_port: $ssl_port
  test_mode: true

network:
  udp_port: $port
  max_packet_size: 1400
  test_timeout: 30

relay:
  discovery_interval: 10
  sync_interval: 5
  max_relay_hops: 3
  bootstrap_relays:
    - host: "127.0.0.1"
      port: 6668
    - host: "127.0.0.1"
      port: 6669
    - host: "127.0.0.1"
      port: 6670

first_ring:
  members: []
  consensus_threshold: 0.5
  challenge_interval: 60

ring_expansion:
  interval: 30
  candidates: 3
  consensus_threshold: 0.5

logging:
  level: "DEBUG"
  file: "logs/test_server_${server_id}.log"
  anonymize_ips: false

test:
  enable_mock_data: true
  simulate_network_delay: false
  test_data_path: "test_data/"
  cleanup_after_tests: true
EOF

    # Start server in background
    python3 -c "
import asyncio
import sys
import os
sys.path.insert(0, 'src')

from protocol.pubsub_server import PubSubServer
from protocol.encryption import EndToEndEncryption

async def start_server():
    encryption = EndToEndEncryption()
    server = PubSubServer(encryption)
    await server.start_pubsub_service()
    print(f'Test server $server_id started on port $port')
    
    # Keep server running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await server.stop_pubsub_service()
        print(f'Test server $server_id stopped')

if __name__ == '__main__':
    asyncio.run(start_server())
" > "logs/test_server_${server_id}.log" 2>&1 &
    
    echo $! > "logs/test_server_${server_id}.pid"
    print_status "SUCCESS" "Test server $server_id started (PID: $(cat logs/test_server_${server_id}.pid))"
}

# Start test servers
start_test_server 1 6668 6698
start_test_server 2 6669 6699
start_test_server 3 6670 6700

# Wait a moment for servers to start
sleep 3

# Check if servers are running
print_status "INFO" "Checking server status..."
for i in 1 2 3; do
    if [ -f "logs/test_server_${i}.pid" ]; then
        pid=$(cat "logs/test_server_${i}.pid")
        if ps -p $pid > /dev/null 2>&1; then
            print_status "SUCCESS" "Test server $i is running (PID: $pid)"
        else
            print_status "ERROR" "Test server $i is not running"
        fi
    else
        print_status "ERROR" "Test server $i PID file not found"
    fi
done

echo ""
echo "🎉 Test servers started!"
echo "========================"
echo "Server 1: 127.0.0.1:6668 (SSL: 6698)"
echo "Server 2: 127.0.0.1:6669 (SSL: 6699)"
echo "Server 3: 127.0.0.1:6670 (SSL: 6700)"
echo ""
echo "Logs are available in:"
echo "- logs/test_server_1.log"
echo "- logs/test_server_2.log"
echo "- logs/test_server_3.log"
echo ""
echo "To stop the servers, run: ./scripts/stop_test_servers.sh"
echo "To run tests, run: ./scripts/run_tests.sh"
