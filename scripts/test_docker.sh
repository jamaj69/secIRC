#!/bin/bash

# secIRC Docker Test Script
# This script runs tests using Docker containers

set -e

echo "🐳 secIRC Docker Test Runner"
echo "============================"

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

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_status "ERROR" "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_status "ERROR" "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "docker-compose.test.yml" ]; then
    print_status "ERROR" "Please run this script from the secIRC root directory"
    exit 1
fi

# Create necessary directories
print_status "INFO" "Creating necessary directories..."
mkdir -p logs test_data data temp uploads

# Build Docker images
print_status "INFO" "Building Docker images..."
if docker-compose -f docker-compose.test.yml build; then
    print_status "SUCCESS" "Docker images built successfully"
else
    print_status "ERROR" "Failed to build Docker images"
    exit 1
fi

# Start test environment
print_status "INFO" "Starting test environment..."
if docker-compose -f docker-compose.test.yml up -d; then
    print_status "SUCCESS" "Test environment started"
else
    print_status "ERROR" "Failed to start test environment"
    exit 1
fi

# Wait for services to be ready
print_status "INFO" "Waiting for services to be ready..."
sleep 10

# Check service status
print_status "INFO" "Checking service status..."
docker-compose -f docker-compose.test.yml ps

# Run integration tests
print_status "INFO" "Running integration tests..."
if docker-compose -f docker-compose.test.yml exec integration-tests python scripts/test_integration.py; then
    print_status "SUCCESS" "Integration tests passed"
    INTEGRATION_RESULT=0
else
    print_status "ERROR" "Integration tests failed"
    INTEGRATION_RESULT=1
fi

# Run client tests
print_status "INFO" "Running client tests..."
if docker-compose -f docker-compose.test.yml exec test-client-1 python scripts/test_client.py; then
    print_status "SUCCESS" "Client tests passed"
    CLIENT_RESULT=0
else
    print_status "ERROR" "Client tests failed"
    CLIENT_RESULT=1
fi

# Collect logs
print_status "INFO" "Collecting logs..."
docker-compose -f docker-compose.test.yml logs > logs/docker_test_logs.txt

# Stop test environment
print_status "INFO" "Stopping test environment..."
docker-compose -f docker-compose.test.yml down

# Print results
echo ""
echo "📊 Docker Test Results"
echo "======================"

if [ $INTEGRATION_RESULT -eq 0 ] && [ $CLIENT_RESULT -eq 0 ]; then
    print_status "SUCCESS" "All Docker tests passed! 🎉"
    echo ""
    echo "The secIRC system is ready for deployment!"
    exit 0
else
    print_status "ERROR" "Some Docker tests failed."
    echo ""
    echo "Check the logs in logs/docker_test_logs.txt for details."
    exit 1
fi
