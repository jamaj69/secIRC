# secIRC Testing Guide

## Overview

This guide provides comprehensive instructions for testing the secIRC anonymous messaging system, including relay servers, clients, and the complete system integration.

## 🧪 **Test Environment Setup**

### **Prerequisites**

1. **Python 3.8+** installed
2. **Virtual environment** support
3. **Docker and Docker Compose** (for containerized testing)
4. **Network access** for relay discovery tests

### **Quick Setup**

```bash
# Clone and navigate to secIRC directory
cd secIRC

# Run the setup script
./scripts/setup.sh

# Activate virtual environment
source venv/bin/activate
```

## 🚀 **Running Tests**

### **1. Quick Test Run**

Run all tests with a single command:

```bash
./scripts/run_tests.sh
```

This will:
- Set up the test environment
- Run server tests
- Run client tests
- Run integration tests
- Run unit tests (if available)
- Provide a comprehensive test report

### **2. Individual Test Suites**

#### **Server Tests**
```bash
python scripts/test_server.py
```

Tests relay server functionality:
- Server startup and initialization
- Relay discovery and synchronization
- Message routing and delivery
- Group messaging
- Key rotation
- Network monitoring

#### **Client Tests**
```bash
python scripts/test_client.py
```

Tests client functionality:
- Client initialization and key management
- Contact management and public key exchange
- Group creation and management
- Message sending and receiving
- Key rotation
- Network connectivity

#### **Integration Tests**
```bash
python scripts/test_integration.py
```

Tests complete system integration:
- Multiple relay servers communication
- Client-server interaction
- End-to-end message delivery
- Group messaging across multiple clients
- Key rotation and synchronization
- Network resilience and failover

## 🐳 **Docker Testing**

### **Containerized Test Environment**

For isolated testing with multiple servers and clients:

```bash
# Run Docker tests
./scripts/test_docker.sh
```

This will:
- Build Docker images
- Start multiple relay servers
- Start test clients
- Run integration tests
- Collect logs
- Clean up containers

### **Manual Docker Testing**

```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# Check service status
docker-compose -f docker-compose.test.yml ps

# Run specific tests
docker-compose -f docker-compose.test.yml exec integration-tests python scripts/test_integration.py

# View logs
docker-compose -f docker-compose.test.yml logs

# Stop environment
docker-compose -f docker-compose.test.yml down
```

## 🔧 **Test Configuration**

### **Server Test Configuration**

File: `config/test_server.yaml`

```yaml
server:
  host: "127.0.0.1"
  port: 6667
  test_mode: true

network:
  udp_port: 6667
  max_packet_size: 1400
  test_timeout: 30

relay:
  discovery_interval: 10  # faster for testing
  sync_interval: 5
  max_relay_hops: 3

logging:
  level: "DEBUG"  # verbose for testing
  file: "logs/test_server.log"

test:
  enable_mock_data: true
  simulate_network_delay: false
  cleanup_after_tests: true
```

### **Client Test Configuration**

File: `config/test_client.yaml`

```yaml
client:
  test_mode: true
  auto_connect: false
  connection_timeout: 10

network:
  udp_port: 6667
  test_timeout: 30

relay:
  discovery_interval: 10
  max_relay_hops: 3

test:
  enable_mock_contacts: true
  enable_mock_groups: true
  log_all_operations: true
```

### **Security Test Configuration**

File: `config/test_security.yaml`

```yaml
encryption:
  algorithm: "AES-256-GCM"
  test_mode: true

password_hash:
  algorithm: "argon2"
  iterations: 1000  # reduced for testing

test:
  use_test_keys: true
  allow_weak_passwords: true
  test_key_rotation: true
```

## 📊 **Test Data**

### **Sample Test Data**

File: `test_data/sample_users.json`

Contains:
- Test users with nicknames and keys
- Test groups with members
- Sample messages for testing
- Mock data for various scenarios

### **Creating Custom Test Data**

```python
# Example: Create custom test users
test_users = [
    {
        "nickname": "TestUser1",
        "user_hash": "a1b2c3d4e5f6g7h8",
        "public_key": "test_public_key_data",
        "private_key": "test_private_key_data",
        "is_online": True,
        "key_rotation_count": 5
    }
]
```

## 🔍 **Test Scenarios**

### **1. Basic Functionality Tests**

- **Server Startup**: Verify servers start correctly
- **Client Connection**: Test client-server connections
- **Message Encryption**: Verify end-to-end encryption
- **Key Management**: Test key generation and rotation

### **2. Group Messaging Tests**

- **Group Creation**: Create groups with multiple members
- **Group Invitations**: Test invitation system
- **Group Messaging**: Send messages to groups
- **Member Management**: Add/remove group members

### **3. Network Tests**

- **Relay Discovery**: Find and connect to relay servers
- **Message Routing**: Route messages through relay chains
- **Network Resilience**: Test failover and recovery
- **Load Testing**: Test performance under load

### **4. Security Tests**

- **Encryption**: Verify message encryption/decryption
- **Key Rotation**: Test periodic key updates
- **Authentication**: Test relay authentication
- **Privacy**: Verify anonymous communication

## 📈 **Test Results and Reporting**

### **Test Output Format**

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

### **Log Files**

Test logs are stored in:
- `logs/test_server.log` - Server test logs
- `logs/test_client.log` - Client test logs
- `logs/integration_test.log` - Integration test logs
- `logs/docker_test_logs.txt` - Docker test logs

### **Debugging Failed Tests**

1. **Check Log Files**: Review detailed logs for error messages
2. **Verify Configuration**: Ensure test configs are correct
3. **Check Dependencies**: Verify all required packages are installed
4. **Network Issues**: Check firewall and network connectivity
5. **Resource Issues**: Ensure sufficient memory and disk space

## 🛠️ **Advanced Testing**

### **Performance Testing**

```bash
# Run performance tests
python scripts/test_performance.py

# Test with specific load
python scripts/test_load.py --users 100 --messages 1000
```

### **Security Testing**

```bash
# Run security tests
python scripts/test_security.py

# Test encryption strength
python scripts/test_encryption.py --key-size 2048
```

### **Network Testing**

```bash
# Test network connectivity
python scripts/test_network.py

# Test relay discovery
python scripts/test_discovery.py --timeout 30
```

## 🔧 **Troubleshooting**

### **Common Issues**

#### **1. Import Errors**
```
ModuleNotFoundError: No module named 'protocol'
```
**Solution**: Ensure you're running from the secIRC root directory and the virtual environment is activated.

#### **2. Port Conflicts**
```
OSError: [Errno 98] Address already in use
```
**Solution**: Stop existing servers or use different ports in test configuration.

#### **3. Permission Errors**
```
PermissionError: [Errno 13] Permission denied
```
**Solution**: Check file permissions and ensure the user has write access to logs and data directories.

#### **4. Network Timeouts**
```
TimeoutError: Connection timed out
```
**Solution**: Check network connectivity and firewall settings.

### **Debug Mode**

Enable debug mode for detailed logging:

```bash
# Set debug environment variable
export SECIRC_DEBUG=true
export SECIRC_LOG_LEVEL=DEBUG

# Run tests with debug output
python scripts/test_server.py
```

### **Verbose Output**

Get detailed test output:

```bash
# Run with verbose output
python scripts/run_tests.sh --verbose

# Run specific test with debug info
python scripts/test_integration.py --debug
```

## 📋 **Test Checklist**

### **Before Running Tests**

- [ ] Virtual environment is activated
- [ ] All dependencies are installed
- [ ] Test configuration files exist
- [ ] Log directories are writable
- [ ] Network connectivity is available
- [ ] Sufficient disk space available

### **After Running Tests**

- [ ] All test suites pass
- [ ] No critical errors in logs
- [ ] Test data is cleaned up
- [ ] Resources are released
- [ ] Test results are documented

## 🎯 **Continuous Integration**

### **GitHub Actions**

Example workflow for automated testing:

```yaml
name: secIRC Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run tests
        run: ./scripts/run_tests.sh
```

### **Local CI Setup**

```bash
# Set up pre-commit hooks
pip install pre-commit
pre-commit install

# Run tests before commit
git add .
git commit -m "Your commit message"
```

## 📚 **Additional Resources**

- [Test Configuration Reference](config/README.md)
- [API Testing Guide](docs/API_TESTING.md)
- [Performance Testing](docs/PERFORMANCE_TESTING.md)
- [Security Testing](docs/SECURITY_TESTING.md)
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md)

---

This comprehensive testing guide ensures that the secIRC system is thoroughly tested and ready for deployment! 🚀🔐
