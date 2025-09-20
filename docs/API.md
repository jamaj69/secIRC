# secIRC API Documentation

## Overview

secIRC provides a RESTful API for managing IRC connections, channels, and users. The API is built with FastAPI and provides both HTTP and WebSocket endpoints.

## Base URL

- Development: `http://localhost:8000`
- Production: `https://your-domain.com`

## Authentication

All API endpoints require authentication using JWT tokens. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Endpoints

### Authentication

#### POST /auth/login
Authenticate a user and receive a JWT token.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### POST /auth/register
Register a new user account.

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

### IRC Server Management

#### GET /servers
List all configured IRC servers.

**Response:**
```json
[
  {
    "id": 1,
    "name": "string",
    "host": "string",
    "port": 6667,
    "ssl": false,
    "connected": false
  }
]
```

#### POST /servers
Add a new IRC server.

**Request Body:**
```json
{
  "name": "string",
  "host": "string",
  "port": 6667,
  "ssl": false,
  "username": "string",
  "password": "string"
}
```

### Channels

#### GET /channels
List all channels for a server.

**Query Parameters:**
- `server_id`: Server ID

**Response:**
```json
[
  {
    "id": 1,
    "name": "#general",
    "topic": "string",
    "users": 10,
    "joined": true
  }
]
```

#### POST /channels/join
Join a channel.

**Request Body:**
```json
{
  "server_id": 1,
  "channel": "#general",
  "password": "string"
}
```

### Messages

#### GET /messages
Get messages from a channel or private conversation.

**Query Parameters:**
- `server_id`: Server ID
- `channel`: Channel name or user nick
- `limit`: Number of messages to retrieve (default: 50)

**Response:**
```json
[
  {
    "id": 1,
    "timestamp": "2025-01-15T10:30:00Z",
    "sender": "user123",
    "message": "Hello world!",
    "type": "message"
  }
]
```

#### POST /messages
Send a message to a channel or user.

**Request Body:**
```json
{
  "server_id": 1,
  "target": "#general",
  "message": "Hello everyone!"
}
```

## WebSocket Events

Connect to `/ws` for real-time updates.

### Events

#### message
Received when a new message arrives.

```json
{
  "event": "message",
  "data": {
    "server_id": 1,
    "channel": "#general",
    "sender": "user123",
    "message": "Hello world!",
    "timestamp": "2025-01-15T10:30:00Z"
  }
}
```

#### user_join
Received when a user joins a channel.

```json
{
  "event": "user_join",
  "data": {
    "server_id": 1,
    "channel": "#general",
    "user": "newuser",
    "timestamp": "2025-01-15T10:30:00Z"
  }
}
```

#### user_leave
Received when a user leaves a channel.

```json
{
  "event": "user_leave",
  "data": {
    "server_id": 1,
    "channel": "#general",
    "user": "olduser",
    "timestamp": "2025-01-15T10:30:00Z"
  }
}
```

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {}
  }
}
```

### Common Error Codes

- `INVALID_CREDENTIALS`: Authentication failed
- `SERVER_NOT_FOUND`: IRC server not found
- `CHANNEL_NOT_FOUND`: Channel not found
- `PERMISSION_DENIED`: Insufficient permissions
- `RATE_LIMITED`: Too many requests
- `CONNECTION_FAILED`: Failed to connect to IRC server

## Rate Limiting

API requests are rate limited to prevent abuse:

- Authentication endpoints: 5 requests per minute
- Message sending: 10 messages per second
- General API: 100 requests per minute

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642252800
```
