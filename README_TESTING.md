# secIRC Testing Overview

## 🧪 **Quick Start Testing**

### **1. Quick Test (Recommended First Step)**
```bash
# Test basic functionality
python scripts/quick_test.py
```

### **2. Full Test Suite**
```bash
# Run all tests
./scripts/run_tests.sh
```

### **3. Docker Testing**
```bash
# Test with Docker containers
./scripts/test_docker.sh
```

## 🚀 **Test Servers**

### **Start Test Servers**
```bash
# Start multiple test relay servers
./scripts/start_test_servers.sh
```

### **Stop Test Servers**
```bash
# Stop all test servers
./scripts/stop_test_servers.sh
```

## 📊 **Test Results**

After running tests, you'll see results like:

```
SECIRC RELAY SERVER TEST RESULTS
==================================================
Server Startup                ✅ PASSED
Relay Discovery               ✅ PASSED
Message Encryption            ✅ PASSED
Group Creation                ✅ PASSED
Group Messaging               ✅ PASSED
Key Rotation                  ✅ PASSED
Network Monitoring            ✅ PASSED
==================================================
Tests passed: 7/7
Success rate: 100.0%
🎉 All tests passed!
```

## 🔧 **Test Configuration**

Test configurations are in the `config/` directory:
- `test_server.yaml` - Server test configuration
- `test_client.yaml` - Client test configuration
- `test_security.yaml` - Security test configuration

## 📁 **Test Data**

Sample test data is in `test_data/`:
- `sample_users.json` - Test users, groups, and messages

## 📋 **Available Tests**

### **Individual Test Scripts**
- `scripts/test_server.py` - Relay server tests
- `scripts/test_client.py` - Client functionality tests
- `scripts/test_integration.py` - Complete system integration tests
- `scripts/quick_test.py` - Basic functionality test

### **Test Management Scripts**
- `scripts/run_tests.sh` - Run all test suites
- `scripts/test_docker.sh` - Docker-based testing
- `scripts/start_test_servers.sh` - Start test servers
- `scripts/stop_test_servers.sh` - Stop test servers

## 🐳 **Docker Testing**

The system includes Docker-based testing for isolated environments:

```bash
# Build and run Docker tests
docker-compose -f docker-compose.test.yml up --build

# Run specific tests
docker-compose -f docker-compose.test.yml exec integration-tests python scripts/test_integration.py

# View logs
docker-compose -f docker-compose.test.yml logs

# Clean up
docker-compose -f docker-compose.test.yml down
```

## 📚 **Documentation**

- [Complete Testing Guide](docs/TESTING_GUIDE.md) - Comprehensive testing documentation
- [API Documentation](docs/API.md) - API reference for testing
- [Architecture Guide](docs/ARCHITECTURE.md) - System architecture overview

## 🎯 **Testing Scenarios**

### **Basic Functionality**
- Server startup and initialization
- Client connection and authentication
- Message encryption and decryption
- Key generation and management

### **Group Messaging**
- Group creation and management
- Member invitations and management
- Group message encryption and delivery
- Key rotation for groups

### **Network Testing**
- Relay server discovery
- Message routing through relay chains
- Network resilience and failover
- Performance under load

### **Security Testing**
- End-to-end encryption
- Key rotation and synchronization
- Relay authentication
- Anonymous communication

## 🔍 **Troubleshooting**

### **Common Issues**

1. **Import Errors**: Ensure you're in the secIRC root directory and virtual environment is activated
2. **Port Conflicts**: Stop existing servers or use different ports
3. **Permission Errors**: Check file permissions for logs and data directories
4. **Network Timeouts**: Verify network connectivity and firewall settings

### **Debug Mode**

Enable debug mode for detailed logging:

```bash
export SECIRC_DEBUG=true
export SECIRC_LOG_LEVEL=DEBUG
python scripts/test_server.py
```

### **Log Files**

Test logs are stored in the `logs/` directory:
- `test_server.log` - Server test logs
- `test_client.log` - Client test logs
- `integration_test.log` - Integration test logs

## 🎉 **Success Criteria**

Tests are considered successful when:
- All test suites pass (100% success rate)
- No critical errors in logs
- System components initialize correctly
- Message encryption/decryption works
- Group messaging functions properly
- Network connectivity is established
- Key rotation operates correctly

---

**Ready to test? Start with the quick test:**

```bash
python scripts/quick_test.py
```

For comprehensive testing, see the [Complete Testing Guide](docs/TESTING_GUIDE.md).
