# secIRC Torrent-Inspired Relay Discovery System

## Overview

This document describes the torrent-inspired relay discovery system implemented in secIRC, which uses the proven BitTorrent protocol as a model for discovering new relay servers while maintaining a high level of security to avoid spy server infiltration.

## 🌐 Core Concept

### **BitTorrent Protocol Inspiration**
The system leverages the **proven BitTorrent protocol** for relay discovery:

- **DHT (Distributed Hash Table)**: Decentralized peer discovery
- **Tracker Protocol**: Centralized peer discovery
- **Peer Exchange (PEX)**: Peer-to-peer relay sharing
- **Bootstrap Nodes**: Initial network entry points
- **Security Measures**: Enhanced protection against spy servers

### **Why BitTorrent Protocol?**
- **Proven Decentralization**: Battle-tested decentralized network
- **Scalability**: Handles millions of peers efficiently
- **Resilience**: No single point of failure
- **Security**: Built-in protection mechanisms
- **Efficiency**: Optimized for peer discovery and communication

## 🔧 Discovery Methods

### **1. DHT (Distributed Hash Table) - 40% weight**

#### **How It Works**
```python
# Generate DHT node ID (20 bytes, like BitTorrent)
dht_node_id = os.urandom(20)

# Bootstrap with known DHT nodes
bootstrap_nodes = [
    ("router.bittorrent.com", 6881),
    ("dht.transmissionbt.com", 6881),
    ("router.utorrent.com", 6881)
]

# Find nodes closest to target ID
target_id = generate_random_node_id()
closest_nodes = get_closest_dht_nodes(target_id, k=20)

# Query nodes for relays
for node in closest_nodes:
    relays = await query_dht_node_for_relays(node.address, node.port, target_id)
```

#### **DHT Operations**
- **find_node**: Find nodes closest to target ID
- **get_peers**: Get peers for specific info hash
- **announce_peer**: Announce our relay to DHT network
- **ping/pong**: Keep-alive messages

#### **Security Features**
- **Node ID Validation**: Verify node ID format
- **Distance Calculation**: Use XOR distance for routing
- **Bucket Management**: Kademlia bucket system
- **Rate Limiting**: Prevent DHT flooding attacks

### **2. Tracker Protocol - 30% weight**

#### **HTTP Tracker**
```python
# HTTP tracker announcement
params = {
    "info_hash": relay_info_hash.hex(),
    "peer_id": dht_node_id.hex(),
    "port": dht_port,
    "uploaded": 0,
    "downloaded": 0,
    "left": 0,
    "compact": 1,
    "event": "started"
}

response = await http_get(tracker_url, params=params)
```

#### **UDP Tracker**
```python
# UDP tracker announcement
connect_request = struct.pack(">QII", 0x41727101980, 0, 0)  # Magic, action, transaction_id
sock.sendto(connect_request, (tracker_host, tracker_port))

# Receive connection ID
connect_response, addr = sock.recvfrom(16)
connection_id = struct.unpack(">Q", connect_response[8:16])[0]

# Send announce request
announce_request = struct.pack(
    ">QII20s20sQQQIIIH",
    connection_id,  # connection_id
    1,              # action (announce)
    0,              # transaction_id
    info_hash,      # info_hash
    peer_id,        # peer_id
    0,              # downloaded
    0,              # left
    0,              # uploaded
    2,              # event (started)
    0,              # IP address
    0,              # key
    -1,             # num_want
    dht_port        # port
)
```

#### **Tracker Features**
- **Multiple Trackers**: Redundancy and load distribution
- **Compact Format**: Efficient peer list encoding
- **Event Tracking**: started, completed, stopped events
- **Interval Management**: Dynamic announce intervals

### **3. Peer Exchange (PEX) - 20% weight**

#### **How It Works**
```python
# Exchange peer lists with known relays
known_relays = list(discovered_relays.values())

for relay in known_relays[:10]:  # Limit to 10 relays
    pex_relays = await exchange_peers_with_relay(relay)
    discovered_relays.extend(pex_relays)
```

#### **PEX Protocol**
- **Peer Lists**: Exchange lists of known peers
- **Incremental Updates**: Add/remove peers efficiently
- **Rate Limiting**: Prevent PEX flooding
- **Validation**: Verify peer information

### **4. Bootstrap Nodes - 10% weight**

#### **Standard BitTorrent Bootstrap Nodes**
```python
bootstrap_nodes = [
    ("router.bittorrent.com", 6881),
    ("dht.transmissionbt.com", 6881),
    ("router.utorrent.com", 6881),
    ("dht.aelitis.com", 6881),
    ("router.silotis.us", 6881)
]
```

#### **secIRC-Specific Bootstrap Nodes**
```python
secirc_bootstrap_nodes = [
    ("bootstrap1.secirc.net", 6881),
    ("bootstrap2.secirc.net", 6881),
    ("bootstrap3.secirc.net", 6881)
]
```

## 🛡️ Security Measures Against Spy Servers

### **1. Multi-Layer Verification**

#### **IP Address Validation**
```python
def validate_ip_address(address: str) -> bool:
    try:
        ip = ipaddress.ip_address(address)
        # Reject private IPs for public relays
        if ip.is_private:
            return False
        # Reject loopback
        if ip.is_loopback:
            return False
        # Reject multicast
        if ip.is_multicast:
            return False
        return True
    except ValueError:
        return False
```

#### **Port Validation**
```python
def validate_port(port: int) -> bool:
    return 1024 <= port <= 65535  # Valid port range
```

#### **Public Key Validation**
```python
def validate_public_key(public_key: bytes) -> bool:
    return len(public_key) == 32  # Ed25519 public key size
```

### **2. Response Time Analysis**

#### **Ping/Pong Testing**
```python
async def check_response_time(relay: RelayAnnouncement) -> bool:
    try:
        start_time = time.time()
        
        # Send ping request
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)
        
        ping_data = b"PING"
        sock.sendto(ping_data, (relay.address, relay.port))
        
        # Wait for pong response
        response, addr = sock.recvfrom(1024)
        sock.close()
        
        response_time = time.time() - start_time
        
        # Accept response times under 5 seconds
        return response_time < 5.0
        
    except Exception:
        return False
```

### **3. Protocol Compliance Testing**

#### **Handshake Verification**
```python
async def check_protocol_compliance(relay: RelayAnnouncement) -> bool:
    try:
        # Send protocol handshake
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)
        
        handshake_data = b"SECIRC_HANDSHAKE"
        sock.sendto(handshake_data, (relay.address, relay.port))
        
        # Wait for handshake response
        response, addr = sock.recvfrom(1024)
        sock.close()
        
        # Check if response contains expected protocol identifier
        return b"SECIRC_RESPONSE" in response
        
    except Exception:
        return False
```

### **4. Rate Limiting**

#### **Address-Based Rate Limiting**
```python
def check_rate_limit(address: str) -> bool:
    current_time = time.time()
    rate_limit_window = 60  # 1 minute
    max_requests = 10  # Maximum 10 requests per minute
    
    # Clean old entries
    while rate_limits[address] and current_time - rate_limits[address][0] > rate_limit_window:
        rate_limits[address].popleft()
    
    # Check if under limit
    if len(rate_limits[address]) >= max_requests:
        return False
    
    # Add current request
    rate_limits[address].append(current_time)
    return True
```

### **5. Spy Server Detection**

#### **Security Score Calculation**
```python
async def perform_security_checks(relay: RelayAnnouncement) -> float:
    security_score = 0.0
    
    # Check 1: IP address validation (20%)
    if validate_ip_address(relay.address):
        security_score += 0.2
    
    # Check 2: Port validation (20%)
    if validate_port(relay.port):
        security_score += 0.2
    
    # Check 3: Public key validation (20%)
    if validate_public_key(relay.public_key):
        security_score += 0.2
    
    # Check 4: Response time check (20%)
    if await check_response_time(relay):
        security_score += 0.2
    
    # Check 5: Protocol compliance (20%)
    if await check_protocol_compliance(relay):
        security_score += 0.2
    
    return security_score
```

#### **Spy Server Classification**
- **High Security** (≥ 0.8): Trusted relay
- **Medium Security** (0.5 - 0.8): Continue monitoring
- **Low Security** (0.3 - 0.5): Increase monitoring
- **Spy Server** (< 0.3): Block immediately

## 🔄 Discovery Process

### **Continuous Discovery Loop**

#### **1. DHT Discovery**
```python
async def discover_relays_dht() -> DiscoveryResult:
    start_time = time.time()
    
    # Generate random target ID
    target_id = generate_random_node_id()
    
    # Find nodes closest to target
    closest_nodes = get_closest_dht_nodes(target_id, k=20)
    
    # Query nodes for relays
    discovered_relays = []
    for node in closest_nodes:
        try:
            relays = await query_dht_node_for_relays(node.address, node.port, target_id)
            discovered_relays.extend(relays)
        except Exception as e:
            print(f"DHT query failed: {e}")
    
    return DiscoveryResult(
        method=DiscoveryMethod.DHT,
        relays_found=discovered_relays,
        discovery_time=time.time() - start_time,
        success=len(discovered_relays) > 0
    )
```

#### **2. Tracker Discovery**
```python
async def discover_relays_tracker() -> DiscoveryResult:
    start_time = time.time()
    discovered_relays = []
    
    # Query all trackers
    for tracker_url in tracker_servers:
        try:
            if tracker_url.startswith("http"):
                response = await announce_to_http_tracker(tracker_url)
            elif tracker_url.startswith("udp"):
                response = await announce_to_udp_tracker(tracker_url)
            
            if response and response.success:
                discovered_relays.extend(response.peers)
                
        except Exception as e:
            print(f"Tracker query failed: {e}")
    
    return DiscoveryResult(
        method=DiscoveryMethod.TRACKER,
        relays_found=discovered_relays,
        discovery_time=time.time() - start_time,
        success=len(discovered_relays) > 0
    )
```

#### **3. PEX Discovery**
```python
async def discover_relays_pex() -> DiscoveryResult:
    start_time = time.time()
    discovered_relays = []
    
    # Get known relays for PEX
    known_relays = list(discovered_relays.values())
    
    # Exchange peer lists with known relays
    for relay in known_relays[:10]:  # Limit to 10 relays
        try:
            pex_relays = await exchange_peers_with_relay(relay)
            discovered_relays.extend(pex_relays)
        except Exception as e:
            print(f"PEX failed: {e}")
    
    return DiscoveryResult(
        method=DiscoveryMethod.PEX,
        relays_found=discovered_relays,
        discovery_time=time.time() - start_time,
        success=len(discovered_relays) > 0
    )
```

### **Relay Processing**

#### **1. Security Verification**
```python
async def process_discovered_relay(relay: RelayAnnouncement) -> None:
    # Check if relay is already known
    if relay.relay_id in discovered_relays:
        return
    
    # Check if relay is a known spy server
    if relay.relay_id in known_spy_servers:
        print(f"Blocked known spy server: {relay.address}:{relay.port}")
        return
    
    # Check rate limits
    if not check_rate_limit(relay.address):
        print(f"Rate limited relay: {relay.address}:{relay.port}")
        return
    
    # Add to discovered relays
    discovered_relays[relay.relay_id] = relay
    
    # Queue for verification
    await queue_relay_for_verification(relay)
```

#### **2. Verification Process**
```python
async def verify_relay(relay: RelayAnnouncement) -> bool:
    # Perform security checks
    security_score = await perform_security_checks(relay)
    
    if security_score >= trust_threshold:
        # Relay is trusted
        verification_cache[relay.relay_id] = (True, int(time.time()))
        
        # Add to mesh network
        await add_relay_to_mesh(relay)
        
        return True
    else:
        # Relay is suspicious
        verification_cache[relay.relay_id] = (False, int(time.time()))
        
        if security_score < 0.3:
            # Relay is likely a spy server
            known_spy_servers.add(relay.relay_id)
            print(f"Detected spy server: {relay.address}:{relay.port}")
        
        return False
```

## 📊 Discovery Statistics

### **Key Metrics**

#### **Discovery Statistics**
```python
stats = {
    "discoveries_attempted": 0,
    "discoveries_successful": 0,
    "relays_discovered": 0,
    "dht_nodes_known": 0,
    "tracker_announcements": 0,
    "pex_exchanges": 0,
    "verification_attempts": 0,
    "verification_successes": 0,
    "spy_servers_detected": 0
}
```

#### **Real-Time Monitoring**
```python
# Get discovery status
status = torrent_discovery.get_discovery_status()
print(f"Discovered relays: {status['discovered_relays']}")
print(f"DHT nodes: {status['dht_nodes']}")
print(f"Verified relays: {status['verified_relays']}")
print(f"Spy servers detected: {status['spy_servers_detected']}")

# Get discovery statistics
stats = torrent_discovery.get_discovery_stats()
print(f"Discoveries attempted: {stats['discoveries_attempted']}")
print(f"Discoveries successful: {stats['discoveries_successful']}")
print(f"Success rate: {stats['discoveries_successful'] / stats['discoveries_attempted']:.2%}")
```

## 🔧 Configuration

### **Discovery Settings**

```yaml
# config/torrent_discovery.yaml
torrent_discovery:
  dht:
    port: 6881
    bucket_size: 8
    alpha: 3
    k: 20
    
  tracker:
    interval: 1800  # 30 minutes
    min_interval: 300  # 5 minutes
    timeout: 30  # 30 seconds
    
  security:
    verification_required: true
    trust_threshold: 0.7
    max_discovery_attempts: 3
    discovery_timeout: 60  # 60 seconds
    
  bootstrap_nodes:
    - "router.bittorrent.com:6881"
    - "dht.transmissionbt.com:6881"
    - "router.utorrent.com:6881"
    - "bootstrap1.secirc.net:6881"
    - "bootstrap2.secirc.net:6881"
    
  tracker_servers:
    - "http://tracker1.secirc.net:8080/announce"
    - "http://tracker2.secirc.net:8080/announce"
    - "udp://tracker1.secirc.net:8080/announce"
    - "udp://tracker2.secirc.net:8080/announce"
```

## 🚀 Usage Examples

### **Basic Discovery**

```python
# Start discovery service
await torrent_discovery.start_discovery_service()

# Get discovered relays
relays = torrent_discovery.get_discovered_relays()
for relay_id, relay in relays.items():
    print(f"Relay: {relay['address']}:{relay['port']}")
    print(f"Services: {relay['services']}")
    print(f"Uptime: {relay['uptime']} seconds")
```

### **Manual Discovery**

```python
# Manually discover relays using specific method
dht_result = await torrent_discovery.discover_relays_dht()
if dht_result.success:
    print(f"DHT discovery found {len(dht_result.relays_found)} relays")
    print(f"Discovery time: {dht_result.discovery_time:.2f} seconds")

tracker_result = await torrent_discovery.discover_relays_tracker()
if tracker_result.success:
    print(f"Tracker discovery found {len(tracker_result.relays_found)} relays")
```

### **Security Monitoring**

```python
# Monitor security statistics
stats = torrent_discovery.get_discovery_stats()
print(f"Verification attempts: {stats['verification_attempts']}")
print(f"Verification successes: {stats['verification_successes']}")
print(f"Spy servers detected: {stats['spy_servers_detected']}")

# Check verification cache
verification_cache = torrent_discovery.verification_cache
for relay_id, (is_verified, timestamp) in verification_cache.items():
    status = "Verified" if is_verified else "Suspicious"
    print(f"Relay {relay_id.hex()}: {status}")
```

## 🔮 Future Enhancements

### **Planned Improvements**

#### **1. Advanced DHT Features**
- **S/Kademlia**: Enhanced security for DHT
- **DHT Crawling**: Systematic DHT network exploration
- **DHT Metrics**: Advanced DHT performance metrics
- **DHT Routing**: Optimized DHT routing algorithms

#### **2. Enhanced Security**
- **Machine Learning**: ML-based spy server detection
- **Behavioral Analysis**: Advanced behavioral analysis
- **Reputation System**: Peer reputation tracking
- **Threat Intelligence**: Integration with threat intelligence feeds

#### **3. Performance Optimization**
- **Parallel Discovery**: Parallel discovery across methods
- **Caching**: Intelligent discovery result caching
- **Load Balancing**: Load balancing across discovery methods
- **Adaptive Intervals**: Dynamic discovery intervals

---

This torrent-inspired relay discovery system provides a robust, scalable, and secure way to discover new relay servers while maintaining protection against spy server infiltration. The system leverages the proven BitTorrent protocol while adding enhanced security measures specifically designed for the secIRC anonymous messaging system.
