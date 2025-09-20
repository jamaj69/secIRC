# Configuration Guide

This directory contains configuration files for the secIRC project.

## Configuration Files

- `server.yaml` - Server configuration
- `client.yaml` - Client configuration  
- `security.yaml` - Security settings
- `logging.yaml` - Logging configuration

## Environment Variables

The following environment variables can be used to override configuration:

- `SECIRC_SERVER_HOST` - Server host address
- `SECIRC_SERVER_PORT` - Server port
- `SECIRC_SSL_CERT` - SSL certificate path
- `SECIRC_SSL_KEY` - SSL private key path
- `SECIRC_LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

## Security Configuration

Security settings should be carefully configured for production use:

- Use strong encryption algorithms
- Enable TLS/SSL for all connections
- Configure proper authentication mechanisms
- Set up audit logging

See individual configuration files for detailed options.
