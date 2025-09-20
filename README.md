# secIRC

A secure IRC (Internet Relay Chat) client and server implementation.

## Overview

secIRC is a modern, secure IRC implementation designed with security and privacy in mind. It provides both client and server functionality with enhanced security features.

## Features

- **Secure Communication**: End-to-end encryption for IRC messages
- **Modern Protocol**: Enhanced IRC protocol with security extensions
- **Cross-Platform**: Works on Linux, macOS, and Windows
- **Web Interface**: Modern web-based client interface
- **Mobile Support**: Responsive design for mobile devices
- **Authentication**: Secure user authentication and authorization
- **Logging**: Comprehensive audit logging for security monitoring

## Project Structure

```
secIRC/
├── src/                    # Source code
│   ├── client/            # IRC client implementation
│   ├── server/            # IRC server implementation
│   ├── protocol/          # IRC protocol definitions
│   └── security/          # Security and encryption modules
├── web/                   # Web interface
├── docs/                  # Documentation
├── tests/                 # Test suite
├── config/                # Configuration files
└── scripts/               # Utility scripts
```

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+ (for web interface)
- Git

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd secIRC
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install Node.js dependencies:
```bash
cd web
npm install
```

### Running the Server

```bash
python src/server/main.py
```

### Running the Web Client

```bash
cd web
npm start
```

## Configuration

Configuration files are located in the `config/` directory. See `config/README.md` for detailed configuration options.

## Security

This project implements several security measures:

- TLS/SSL encryption for all communications
- Message authentication codes (MAC)
- Secure key exchange protocols
- User authentication and authorization
- Audit logging and monitoring

## Contributing

Please read `CONTRIBUTING.md` for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.

## Contact

For questions and support, please open an issue on GitHub.
