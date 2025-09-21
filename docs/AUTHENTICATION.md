# secIRC Authentication System

## Overview

secIRC implements a robust multi-challenge authentication system that ensures secure client-server communication. The system uses multiple independent challenges to verify user identity and prevent various types of attacks.

## Authentication Flow

### Step-by-Step Process

1. **Client Login Request**: Client sends authentication request with user ID and public key
2. **Server Challenge Generation**: Server generates multiple authentication challenges
3. **Client Response**: Client solves challenges and sends responses
4. **Server Verification**: Server verifies all challenge responses
5. **Session Creation**: Successful authentication creates secure session
6. **User Status Update**: User is marked as online and status is broadcast

### Authentication Diagram

```
Client                    Server
  |                         |
  |---- Auth Request ------>|
  |<--- Auth Challenges ----|
  |---- Auth Responses ---->|
  |<--- Auth Success -------|
  |                         |
  |---- User Online ------->|
  |<--- Status Confirmed ---|
```

## Challenge Types

### 1. Cryptographic Challenge

**Purpose**: Verify user's private key ownership

**Process**:
1. Server generates random challenge data
2. Client signs challenge data with private key
3. Server verifies signature using client's public key

**Security Benefits**:
- Proves possession of private key
- Prevents impersonation attacks
- Ensures message authenticity

**Implementation**:
```python
# Server generates challenge
challenge = auth_protocol.create_cryptographic_challenge(public_key)

# Client signs challenge
signature = encryption.sign_message(challenge.challenge_data, private_key)

# Server verifies signature
is_valid = encryption.verify_signature(challenge.challenge_data, signature, public_key)
```

### 2. Proof of Work Challenge

**Purpose**: Prevent brute force attacks and resource exhaustion

**Process**:
1. Server generates challenge with difficulty level
2. Client performs computational work to solve challenge
3. Server verifies proof of work meets difficulty requirement

**Security Benefits**:
- Prevents automated attacks
- Requires computational resources
- Configurable difficulty levels

**Implementation**:
```python
# Server generates PoW challenge
challenge = auth_protocol.create_proof_of_work_challenge(difficulty=4)

# Client solves challenge
nonce = solve_proof_of_work(challenge.challenge_data, challenge.difficulty)

# Server verifies solution
is_valid = verify_proof_of_work(challenge.challenge_data, nonce, challenge.difficulty)
```

### 3. Timestamp Challenge

**Purpose**: Prevent replay attacks

**Process**:
1. Server sends current timestamp
2. Client responds with current timestamp
3. Server verifies timestamp is within acceptable range

**Security Benefits**:
- Prevents replay attacks
- Ensures freshness of authentication
- Time-based validation

**Implementation**:
```python
# Server generates timestamp challenge
challenge = auth_protocol.create_timestamp_challenge()

# Client responds with current timestamp
response_timestamp = int(time.time())

# Server verifies timestamp
time_diff = abs(response_timestamp - challenge.timestamp)
is_valid = time_diff <= 30  # 30 seconds tolerance
```

### 4. Nonce Challenge

**Purpose**: Ensure session uniqueness

**Process**:
1. Server generates random nonce
2. Client returns the same nonce
3. Server verifies nonce matches

**Security Benefits**:
- Prevents session replay
- Ensures session uniqueness
- Random value validation

**Implementation**:
```python
# Server generates nonce challenge
challenge = auth_protocol.create_nonce_challenge()

# Client returns nonce
response_nonce = challenge.nonce

# Server verifies nonce
is_valid = response_nonce == challenge.nonce
```

## Session Management

### Session Lifecycle

1. **Creation**: Session created after successful authentication
2. **Active**: Session remains active while user is connected
3. **Expiration**: Session expires after timeout period
4. **Cleanup**: Expired sessions are automatically cleaned up

### Session Properties

```python
@dataclass
class AuthenticationSession:
    session_id: bytes           # Unique session identifier
    user_id: bytes             # User identifier
    server_id: bytes           # Server identifier
    status: AuthenticationStatus # Current session status
    challenges: List[AuthenticationChallenge] # Authentication challenges
    responses: List[AuthenticationResponse]   # Challenge responses
    created_at: int            # Session creation timestamp
    last_activity: int         # Last activity timestamp
    is_authenticated: bool     # Authentication status
    session_key: Optional[bytes] # Session encryption key
```

### Session Status

- **PENDING**: Session created, awaiting challenges
- **CHALLENGED**: Challenges sent, awaiting responses
- **RESPONDED**: Responses received, awaiting verification
- **VERIFIED**: Authentication successful
- **FAILED**: Authentication failed
- **EXPIRED**: Session expired

## Security Features

### Multi-Layer Protection

The authentication system provides multiple layers of security:

1. **Cryptographic Security**: Digital signature verification
2. **Computational Security**: Proof of work requirements
3. **Temporal Security**: Timestamp validation
4. **Uniqueness Security**: Nonce validation

### Attack Prevention

#### Brute Force Attacks
- Proof of work challenges require computational resources
- Configurable difficulty levels
- Rate limiting on authentication attempts

#### Replay Attacks
- Timestamp challenges prevent old authentication reuse
- Nonce challenges ensure session uniqueness
- Session expiration limits attack window

#### Impersonation Attacks
- Cryptographic challenges verify private key ownership
- Public key verification prevents key substitution
- Session binding prevents session hijacking

#### Man-in-the-Middle Attacks
- End-to-end encryption protects communication
- Public key verification prevents key substitution
- Session key generation after authentication

## Configuration

### Authentication Settings

```yaml
# Authentication configuration
authentication:
  max_attempts: 3              # Maximum authentication attempts
  timeout: 300                 # Authentication timeout (seconds)
  session_timeout: 3600        # Session timeout (seconds)
  challenge_timeout: 300       # Challenge timeout (seconds)
  max_challenges: 5            # Maximum challenges per session
  
  # Challenge-specific settings
  proof_of_work:
    difficulty: 4              # Proof of work difficulty
    max_attempts: 100000       # Maximum PoW attempts
    
  timestamp:
    tolerance: 30              # Timestamp tolerance (seconds)
    
  nonce:
    length: 16                 # Nonce length (bytes)
```

### Security Parameters

```python
# Default security parameters
DEFAULT_CHALLENGE_TIMEOUT = 300      # 5 minutes
DEFAULT_SESSION_TIMEOUT = 3600       # 1 hour
DEFAULT_POW_DIFFICULTY = 4           # 4 leading zeros
DEFAULT_TIMESTAMP_TOLERANCE = 30     # 30 seconds
DEFAULT_NONCE_LENGTH = 16            # 16 bytes
```

## Usage Examples

### Client Authentication

```python
from client.secirc_client import SecIRCClient, ClientConfig

# Create client
config = ClientConfig(nickname="MyUser")
client = SecIRCClient(config)

# Initialize client
await client.initialize()

# Login with authentication
success = await client.login()
if success:
    print("Authentication successful!")
    print(f"Session ID: {client.auth_session.session_id.hex()}")
    print(f"User status: {client.user_status.value}")
else:
    print("Authentication failed!")
```

### Server Authentication Handling

```python
from server.secirc_server import SecIRCServer, ServerConfig

# Create server
config = ServerConfig(host="0.0.0.0", port=6667)
server = SecIRCServer(config)

# Start server
await server.start_server()

# Server automatically handles:
# - Authentication requests
# - Challenge generation
# - Response verification
# - Session management
# - User status updates
```

### Manual Authentication Testing

```python
from protocol.authentication import AuthenticationProtocol, ChallengeType
from protocol.encryption import EndToEndEncryption

# Create authentication protocol
encryption = EndToEndEncryption()
auth_protocol = AuthenticationProtocol(encryption)

# Generate test key pair
public_key, private_key = encryption.generate_keypair()
user_id = b"test_user_123"

# Create authentication session
session = auth_protocol.create_authentication_session(user_id, server_id)

# Generate challenges
challenges = [
    auth_protocol.create_cryptographic_challenge(public_key),
    auth_protocol.create_proof_of_work_challenge(difficulty=4),
    auth_protocol.create_timestamp_challenge(),
    auth_protocol.create_nonce_challenge()
]

# Add challenges to session
for challenge in challenges:
    auth_protocol.add_challenge_to_session(session.session_id, challenge)

# Generate responses (client side)
responses = []
for challenge in challenges:
    response = generate_challenge_response(challenge, private_key)
    responses.append(response)
    auth_protocol.add_response_to_session(session.session_id, response)

# Verify session (server side)
success = auth_protocol.verify_session(session.session_id, public_key)
print(f"Authentication successful: {success}")
```

## Testing

### Authentication Test Suite

```bash
# Run authentication tests
python scripts/test_client_server_auth.py

# Test specific components
python -c "
from scripts.test_client_server_auth import test_authentication_challenges
import asyncio
asyncio.run(test_authentication_challenges())
"
```

### Test Coverage

The authentication system includes comprehensive tests for:

- **Challenge Generation**: All challenge types
- **Response Generation**: Client response creation
- **Response Verification**: Server verification logic
- **Session Management**: Session lifecycle
- **Error Handling**: Invalid responses and timeouts
- **Security**: Attack prevention mechanisms

## Best Practices

### Client Best Practices

1. **Secure Key Storage**: Store private keys securely
2. **Password Protection**: Use strong passwords for key encryption
3. **Regular Key Rotation**: Rotate keys periodically
4. **Secure Communication**: Use encrypted channels for authentication
5. **Error Handling**: Handle authentication failures gracefully

### Server Best Practices

1. **Rate Limiting**: Implement rate limiting on authentication attempts
2. **Session Cleanup**: Regularly clean up expired sessions
3. **Monitoring**: Monitor authentication success/failure rates
4. **Logging**: Log authentication events for security analysis
5. **Configuration**: Use secure default configurations

### Security Best Practices

1. **Strong Passwords**: Use strong passwords for key protection
2. **Regular Updates**: Keep authentication system updated
3. **Monitoring**: Monitor for suspicious authentication patterns
4. **Backup**: Backup authentication data securely
5. **Testing**: Regularly test authentication system

## Troubleshooting

### Common Issues

#### Authentication Failures
- **Invalid credentials**: Check user ID and public key
- **Challenge timeout**: Ensure responses are sent within timeout
- **Proof of work failure**: Check difficulty settings
- **Timestamp mismatch**: Synchronize system clocks

#### Session Issues
- **Session expiration**: Check session timeout settings
- **Session cleanup**: Verify automatic cleanup is working
- **Session binding**: Ensure sessions are properly bound to users

#### Network Issues
- **Connection timeout**: Check network connectivity
- **SSL/TLS errors**: Verify certificate configuration
- **Firewall issues**: Check firewall settings

### Debug Information

```python
# Get authentication status
auth_status = auth_protocol.get_authentication_status()
print(f"Active sessions: {auth_status['active_sessions']}")
print(f"Active challenges: {auth_status['active_challenges']}")
print(f"Authenticated sessions: {auth_status['authenticated_sessions']}")

# Get session information
session = auth_protocol.get_session(session_id)
if session:
    print(f"Session status: {session.status.value}")
    print(f"Challenges: {len(session.challenges)}")
    print(f"Responses: {len(session.responses)}")
    print(f"Authenticated: {session.is_authenticated}")
```

## Conclusion

The secIRC authentication system provides robust security through multi-challenge authentication, comprehensive session management, and strong attack prevention mechanisms. The system is designed to be secure, scalable, and easy to use while providing maximum protection against various types of attacks.

The multi-challenge approach ensures that even if one challenge type is compromised, the overall authentication remains secure. The system is highly configurable and can be adapted to different security requirements and threat models.
