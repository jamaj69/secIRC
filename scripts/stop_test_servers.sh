#!/bin/bash

# secIRC Test Server Stopper Script
# This script stops all test relay servers

set -e

echo "🛑 secIRC Test Server Stopper"
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

# Function to stop a test server
stop_test_server() {
    local server_id=$1
    
    if [ -f "logs/test_server_${server_id}.pid" ]; then
        pid=$(cat "logs/test_server_${server_id}.pid")
        if ps -p $pid > /dev/null 2>&1; then
            print_status "INFO" "Stopping test server $server_id (PID: $pid)..."
            kill $pid
            sleep 2
            
            # Check if process is still running
            if ps -p $pid > /dev/null 2>&1; then
                print_status "WARNING" "Test server $server_id did not stop gracefully, forcing..."
                kill -9 $pid
            fi
            
            print_status "SUCCESS" "Test server $server_id stopped"
        else
            print_status "WARNING" "Test server $server_id is not running"
        fi
        
        # Remove PID file
        rm -f "logs/test_server_${server_id}.pid"
    else
        print_status "WARNING" "Test server $server_id PID file not found"
    fi
}

# Stop all test servers
print_status "INFO" "Stopping all test servers..."
stop_test_server 1
stop_test_server 2
stop_test_server 3

# Clean up any remaining processes
print_status "INFO" "Cleaning up any remaining processes..."
pkill -f "test_server" || true

# Clean up temporary files
print_status "INFO" "Cleaning up temporary files..."
rm -f config/test_server_*.yaml

echo ""
print_status "SUCCESS" "All test servers stopped! 🎉"
