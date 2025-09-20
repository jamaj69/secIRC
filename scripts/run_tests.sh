#!/bin/bash

# secIRC Test Runner Script
# This script runs all test suites for the secIRC system

set -e

echo "🚀 secIRC Test Runner"
echo "===================="

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

# Function to run a test script
run_test() {
    local test_name=$1
    local test_script=$2
    local description=$3
    
    echo ""
    echo "Running $test_name..."
    echo "Description: $description"
    echo "----------------------------------------"
    
    if [ -f "$test_script" ]; then
        if python3 "$test_script"; then
            print_status "SUCCESS" "$test_name completed successfully"
            return 0
        else
            print_status "ERROR" "$test_name failed"
            return 1
        fi
    else
        print_status "ERROR" "Test script not found: $test_script"
        return 1
    fi
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

# Install/upgrade dependencies
print_status "INFO" "Installing dependencies..."
pip install -r requirements.txt

# Make test scripts executable
chmod +x scripts/test_*.py

# Initialize test results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Run individual test suites
echo ""
echo "🧪 Running Test Suites"
echo "======================"

# 1. Server Tests
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if run_test "Relay Server Tests" "scripts/test_server.py" "Tests relay server functionality including startup, discovery, messaging, and key rotation"; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# 2. Client Tests
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if run_test "Client Tests" "scripts/test_client.py" "Tests client functionality including initialization, contact management, group creation, and messaging"; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# 3. Integration Tests
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if run_test "Integration Tests" "scripts/test_integration.py" "Tests complete system integration including multi-server communication, end-to-end messaging, and network resilience"; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Run unit tests if available
if [ -d "tests" ] && [ -f "tests/__init__.py" ]; then
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo ""
    echo "Running Unit Tests..."
    echo "Description: Tests individual components and functions"
    echo "----------------------------------------"
    
    if python -m pytest tests/ -v; then
        print_status "SUCCESS" "Unit tests completed successfully"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        print_status "ERROR" "Unit tests failed"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
fi

# Print final results
echo ""
echo "📊 Test Results Summary"
echo "======================="
echo "Total test suites: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo "Success rate: $(( (PASSED_TESTS * 100) / TOTAL_TESTS ))%"

if [ $FAILED_TESTS -eq 0 ]; then
    print_status "SUCCESS" "All tests passed! 🎉"
    echo ""
    echo "The secIRC system is ready for deployment!"
    exit 0
else
    print_status "ERROR" "Some tests failed. Please check the logs above."
    echo ""
    echo "Common issues and solutions:"
    echo "- Check that all dependencies are installed"
    echo "- Verify that the virtual environment is activated"
    echo "- Ensure all required configuration files exist"
    echo "- Check network connectivity for relay discovery tests"
    exit 1
fi
