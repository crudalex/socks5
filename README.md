# SOCKS5 Proxy Server

This project implements a SOCKS5 proxy server using Python's `asyncio` library. The server listens for incoming connections and forwards them to the target server.

## Requirements

- Python 3.12 or higher

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/socks5-py.git
    cd socks5-py
    ```

2. Install dependencies using Poetry:
    ```sh
    poetry install
    ```

## Usage

Run the SOCKS5 proxy server with default settings:
```sh
python socks5.py
```

You can customize the host, port, timeout, and enable debug logging using command-line arguments:
```sh
python socks5.py --host 127.0.0.1 --port 1080 --timeout 10 --debug
```

## Command-Line Arguments

- `-l`, `--listen_address`: Host to listen on (default: `0.0.0.0`)
- `-p`, `--port`: Port to listen on (default: `1080`)
- `-t`, `--timeout`: Connection timeout in seconds (default: `5`)
- `-d`, `--debug`: Enable debug logging